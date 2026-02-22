# -*- coding: utf-8 -*-
"""
feature_engineer.py  --  Build 3-class classification labels (BUY/SELL/HOLD)
"""

import os, sys, glob
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_ml.config import RAW_DATA_DIR, PROC_DATA_DIR, LABEL_THRESHOLD_PCT, LOOKAHEAD_DAYS

def run_engineering():
    os.makedirs(PROC_DATA_DIR, exist_ok=True)
    files = glob.glob(os.path.join(RAW_DATA_DIR, "*_raw.csv"))
    for f in files:
        df = pd.read_csv(f, index_col=0, parse_dates=True)
        # Classify: price change in next LOOKAHEAD_DAYS (which is 1 row = 4h now)
        future = df["close"].shift(-LOOKAHEAD_DAYS)
        pct = (future - df["close"]) / df["close"] * 100
        df["label"] = np.where(pct > LABEL_THRESHOLD_PCT, 1, 
                      np.where(pct < -LABEL_THRESHOLD_PCT, -1, 0))
        df = df.dropna(subset=["close"]).iloc[:-LOOKAHEAD_DAYS]
        
        # Clean
        df = df.select_dtypes(include=[np.number]).ffill().fillna(0)
        out = os.path.join(PROC_DATA_DIR, os.path.basename(f).replace("_raw.csv", "_features.csv"))
        df.to_csv(out)
        print(f"  Processed {os.path.basename(f)}: {len(df)} rows")
    return True

if __name__ == "__main__": run_engineering()
