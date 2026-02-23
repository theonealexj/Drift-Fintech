# -*- coding: utf-8 -*-
"""
main.py  --  FastAPI server for Crypto ML predictions
"""

import os, sys, ssl
# Patch SSL globally for demo environments with certificate issues
try:
    if (not os.environ.get('PYTHONHTTPSVERIFY', '') and 
        getattr(ssl, '_create_unverified_context', None)):
        ssl._create_default_https_context = ssl._create_unverified_context
except Exception: pass

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import joblib
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_ml.config import SYMBOLS, MODEL_PATH, LABEL_MAP
from crypto_ml.data_collector import (
    fetch_ohlcv, fetch_macro, fetch_fear_greed,
    compute_indicators, fetch_live_price, _ffill_to_4h
)

import logging

# Configure logging to file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("server_debug.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("drift_api")

from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Drift Crypto ML API")

# Enable CORS (still useful for some dev scenarios)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and data
MODEL_BUNDLE = None
try:
    MODEL_BUNDLE = joblib.load(MODEL_PATH)
    print(f"Loaded model from {MODEL_PATH}")
except Exception as e:
    print(f"Error loading model: {e}")

# Static files will be mounted at the end to avoid masking API routes

def get_live_row(symbol: str, m_df: pd.DataFrame, f_df: pd.DataFrame):
    df = fetch_ohlcv(symbol, days=250)
    if df is None: return None
    df = compute_indicators(df)
    if not m_df.empty: 
        df = pd.concat([df, _ffill_to_4h(m_df, df.index)], axis=1)
    if not f_df.empty:
        df = pd.concat([df, _ffill_to_4h(f_df, df.index)], axis=1)
    
    row = df.iloc[[-1]].copy()
    live = fetch_live_price(symbol)
    for k, v in live.items():
        row[k] = v
    return row

@app.get("/api/health")
def health():
    return {"status": "healthy", "model_loaded": MODEL_BUNDLE is not None}

import time

# Simple cache
PREDICTION_CACHE = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL_SEC = 900 # 15 minutes

@app.get("/api/predictions")
async def get_predictions():
    global PREDICTION_CACHE
    
    # Check cache
    now = time.time()
    if PREDICTION_CACHE["data"] and (now - PREDICTION_CACHE["timestamp"]) < CACHE_TTL_SEC:
        logger.info("Serving predictions from cache")
        return PREDICTION_CACHE["data"]

    logger.info("Received request for /api/predictions (Cache miss/expired)")
    if MODEL_BUNDLE is None:
        logger.error("Model bundle not loaded")
        return {"error": "Model not loaded"}
    
    try:
        model, le, feats = MODEL_BUNDLE["model"], MODEL_BUNDLE["le"], MODEL_BUNDLE["features"]
        logger.info("Fetching macro and sentiment data...")
        m_df = fetch_macro(); f_df = fetch_fear_greed()
        
        results = {}
        total_bullishness = 0
        
        for sym in SYMBOLS:
            logger.info(f"Processing symbol: {sym}")
            try:
                row = get_live_row(sym, m_df, f_df)
                if row is None:
                    logger.warning(f"No row data for {sym}")
                    results[sym] = {"error": "No data"}
                    continue
                    
                X = row.reindex(columns=feats).fillna(0)
                probs = model.predict_proba(X)[0].tolist() # [SELL, HOLD, BUY]
                pred_enc = np.argmax(probs)
                label = le.inverse_transform([pred_enc])[0]
                
                total_bullishness += (probs[2] - probs[0])
                
                results[sym] = {
                    "symbol": sym,
                    "signal": LABEL_MAP.get(int(label), str(label)),
                    "confidence": round(probs[int(pred_enc)] * 100, 1),
                    "probs": {
                        "sell": round(probs[0] * 100, 1),
                        "hold": round(probs[1] * 100, 1),
                        "buy": round(probs[2] * 100, 1)
                    }
                }
                logger.debug(f"Success for {sym}: {results[sym]['signal']}")
            except Exception as coin_err:
                logger.error(f"Error processing {sym}: {coin_err}")
                results[sym] = {"error": str(coin_err)}
        
        # Calculate overall market threat level
        threat_score = 50 + (total_bullishness / len(SYMBOLS) * 50)
        threat_score = max(0, min(100, threat_score))
        
        status = "Stable"
        if threat_score > 70: status = "Bullish / Safe"
        elif threat_score < 30: status = "Volatility Threat"
        
        logger.info(f"Predictions complete. Market Score: {threat_score}")
        
        response_data = {
            "market_threat": {
                "score": round(threat_score, 1),
                "status": status
            },
            "predictions": results,
            "sentiment": {
                "fear_greed": int(f_df.iloc[-1]["fg_val"]) if not f_df.empty else 50
            }
        }
        
        # Update cache
        PREDICTION_CACHE["data"] = response_data
        PREDICTION_CACHE["timestamp"] = time.time()
        
        return response_data
    except Exception as e:
        logger.exception("Global error in get_predictions")
        return {"error": str(e)}

# --- HTML Routes ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
@app.get("/index.html")
async def read_index():
    return FileResponse(os.path.join(BASE_DIR, "index.html"))

@app.get("/dashboard.html")
async def read_dashboard():
    return FileResponse(os.path.join(BASE_DIR, "dashboard.html"))

@app.get("/join.html")
async def read_join():
    return FileResponse(os.path.join(BASE_DIR, "join.html"))

@app.get("/invest.html")
async def read_invest():
    return FileResponse(os.path.join(BASE_DIR, "invest.html"))

@app.get("/learn.html")
async def read_learn():
    return FileResponse(os.path.join(BASE_DIR, "learn.html"))

@app.get("/security.html")
async def read_security():
    return FileResponse(os.path.join(BASE_DIR, "security.html"))

# Serve other static assets
app.mount("/assets", StaticFiles(directory=BASE_DIR), name="assets")
app.mount("/", StaticFiles(directory=BASE_DIR, html=True), name="root_static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
