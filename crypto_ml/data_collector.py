# -*- coding: utf-8 -*-
"""
data_collector.py  --  Crypto ML data collector (Final Optimized Version)

Sources:
  Binance   -> 4h OHLCV (free, no key)
  yfinance  -> Macro (free, no key)
  F&G Index -> Daily Sentiment (free, no key)
"""

import os, sys, warnings, requests, time
import numpy as np
import pandas as pd
import pandas_ta as ta
import yfinance as yf
from datetime import datetime, timedelta, timezone

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_ml.config import API_KEY, BASE_URL, SYMBOLS, HISTORY_DAYS, RAW_DATA_DIR

BINANCE_KLINES  = "https://api.binance.com/api/v3/klines"
CANDLE_INTERVAL = "4h"

BINANCE_SYMBOLS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
MACRO_TICKERS   = {"SPY": "spy", "QQQ": "qqq", "DX-Y.NYB": "dxy", "GC=F": "gold", "^VIX": "vix"}

def fetch_ohlcv(symbol: str, days: int = HISTORY_DAYS) -> pd.DataFrame | None:
    pair  = BINANCE_SYMBOLS.get(symbol.upper(), f"{symbol.upper()}USDT")
    end   = int(datetime.now(timezone.utc).timestamp() * 1000)
    start = int((datetime.now(timezone.utc) - timedelta(days=days + 2)).timestamp() * 1000)
    
    COLS = ["open_time","open","high","low","close","volume","close_time","qv","tr","tb","tq","ig"]
    all_rows, cursor = [], start
    try:
        while cursor < end:
            r = requests.get(BINANCE_KLINES, params={"symbol": pair, "interval": CANDLE_INTERVAL, "startTime": cursor, "endTime": end, "limit": 1000}, timeout=20)
            r.raise_for_status()
            batch = r.json()
            if not batch or isinstance(batch, dict): break
            all_rows.extend(batch)
            cursor = batch[-1][6] + 1
            if len(batch) < 1000: break
    except Exception as e:
        print(f"  Binance error {symbol}: {e}")
        return None

    df = pd.DataFrame(all_rows, columns=COLS)
    df["date"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("date")[["open","high","low","close","volume"]]
    for c in df.columns: df[c] = pd.to_numeric(df[c], errors="coerce")
    return df[~df.index.duplicated()].sort_index()

def fetch_macro(days: int = HISTORY_DAYS + 10) -> pd.DataFrame:
    end, start = datetime.now(), datetime.now() - timedelta(days=days)
    frames = {}
    for ticker, label in MACRO_TICKERS.items():
        try:
            df = yf.download(ticker, start=start, end=end, progress=False, auto_adjust=True)
            if df.empty: continue
            close = df["Close"].squeeze()
            close.index = pd.to_datetime(close.index).normalize().tz_localize("UTC")
            if label == "vix": frames["vix"] = close
            else: frames[f"{label}_ret"] = close.pct_change() * 100
        except Exception: pass
    return pd.DataFrame(frames).sort_index()

def fetch_fear_greed(days: int = HISTORY_DAYS) -> pd.DataFrame:
    try:
        r = requests.get("https://api.alternative.me/fng/", params={"limit": 1000}, timeout=15)
        data = r.json().get("data", [])
        rows = [{"date": pd.Timestamp(int(d["timestamp"]), unit="s", tz="UTC").normalize(), "fg_val": int(d["value"])} for d in data]
        return pd.DataFrame(rows).set_index("date").sort_index()
    except Exception: return pd.DataFrame()

def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    for p in [20, 50, 200]:
        df[f"ema_{p}"] = ta.ema(df["close"], length=p)
        df[f"sma_{p}"] = ta.sma(df["close"], length=p)
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    if macd is not None: df["macd_h"] = macd.iloc[:, 2]
    bb = ta.bbands(df["close"], length=20)
    if bb is not None: df["bb_pct"] = bb.iloc[:, 4]
    df["atr"] = ta.atr(df["high"], df["low"], df["close"]) / df["close"] * 100
    df["obv"] = ta.obv(df["close"], df["volume"])
    # Crossovers
    df["ema20_x_50"] = df["ema_20"].astype(float).gt(df["ema_50"].astype(float)).astype(int)
    return df

def _ffill_to_4h(macro_daily: pd.DataFrame, target_idx: pd.DatetimeIndex) -> pd.DataFrame:
    """Forward-fill daily data into a 4h target index."""
    combined = target_idx.union(macro_daily.index).sort_values()
    return macro_daily.reindex(combined).ffill().reindex(target_idx)


def fetch_live_price(symbol: str) -> dict:
    try:
        r = requests.get(f"{BASE_URL}/getData", headers={"Authorization": f"Bearer {API_KEY}"}, params={"symbol": symbol}, timeout=10)
        s = r.json().get("symbols", [{}])[0]
        return {"live_price": float(s.get("last", 0)), "live_chg": float(s.get("daily_change_percentage", 0))}
    except Exception: return {}

def collect_symbol(symbol: str, macro_df: pd.DataFrame, fg_df: pd.DataFrame) -> pd.DataFrame | None:
    df = fetch_ohlcv(symbol)
    if df is None: return None
    df = compute_indicators(df)
    if not macro_df.empty:
        c_idx = df.index.union(macro_df.index).sort_values()
        df = pd.concat([df, macro_df.reindex(c_idx).ffill().reindex(df.index)], axis=1)
    if not fg_df.empty:
        c_idx = df.index.union(fg_df.index).sort_values()
        df = pd.concat([df, fg_df.reindex(c_idx).ffill().reindex(df.index)], axis=1)
    df["symbol"] = symbol
    return df

def run_collection():
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    m_df = fetch_macro(); f_df = fetch_fear_greed()
    for sym in SYMBOLS:
        df = collect_symbol(sym, m_df, f_df)
        if df is not None: df.to_csv(os.path.join(RAW_DATA_DIR, f"{sym}_raw.csv"))
    return SYMBOLS

if __name__ == "__main__": run_collection()
