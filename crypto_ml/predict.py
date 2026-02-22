# -*- coding: utf-8 -*-
"""
predict.py  --  Live signals for optimized classification
"""

import os, sys, joblib
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_ml.config import SYMBOLS, MODEL_PATH, LABEL_MAP
from crypto_ml.data_collector import (
    fetch_ohlcv, fetch_macro, fetch_fear_greed,
    compute_indicators, fetch_live_price, _ffill_to_4h
)

def build_row(symbol: str, m_df: pd.DataFrame, f_df: pd.DataFrame) -> pd.DataFrame | None:
    df = fetch_ohlcv(symbol, days=250)
    if df is None: return None
    df = compute_indicators(df)
    if not m_df.empty: 
        df = pd.concat([df, _ffill_to_4h(m_df, df.index)], axis=1)
    if not f_df.empty:
        df = pd.concat([df, _ffill_to_4h(f_df, df.index)], axis=1)
    
    row = df.iloc[[-1]].copy()
    live = fetch_live_price(symbol)
    for k, v in live.items(): row[k] = v
    return row

def run_prediction(symbols=None):
    symbols = symbols or SYMBOLS
    bundle = joblib.load(MODEL_PATH)
    model, le, feats = bundle["model"], bundle["le"], bundle["features"]
    
    m_df = fetch_macro(); f_df = fetch_fear_greed()
    
    print(f"\n{'='*72}")
    print(f"{'CRYPTO MARKET THREAT DETECTOR  --  LIVE SIGNAL':^72}")
    print(f"{'='*72}")
    
    for sym in symbols:
        row = build_row(sym, m_df, f_df)
        if row is None: continue
        
        # Match features
        X = row.reindex(columns=feats).fillna(0)
        probs = model.predict_proba(X)[0]
        pred_enc = np.argmax(probs)
        label = le.inverse_transform([pred_enc])[0]
        conf = probs[pred_enc] * 100
        
        # Breakdown
        brk = f"SELL: {probs[0]*100:4.1f}%  HOLD: {probs[1]*100:4.1f}%  BUY: {probs[2]*100:4.1f}%"
        print(f"  {sym:5} {LABEL_MAP.get(label, str(label)):<10} {conf:>6.1f}%   {brk}")
    print(f"{'='*72}\n")

if __name__ == "__main__": run_prediction()
