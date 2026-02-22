# -*- coding: utf-8 -*-
"""
train.py  --  Train optimized XGBoost classifier
"""

import os, sys, joblib, glob
import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from crypto_ml.config import PROC_DATA_DIR, MODEL_PATH, RANDOM_STATE

def run_training():
    files = glob.glob(os.path.join(PROC_DATA_DIR, "*_features.csv"))
    dfs = [pd.read_csv(f, index_col=0, parse_dates=True) for f in files]
    df = pd.concat(dfs).sort_index()
    
    y = df["label"].astype(int)
    X = df.drop(columns=["label", "symbol"], errors="ignore")
    
    le = LabelEncoder()
    y_enc = le.fit_transform(y) # -1,0,1 -> 0,1,2
    
    # Compute class weights to combat HOLD dominance
    counts = np.bincount(y_enc)
    weights = len(y_enc) / (len(counts) * counts)
    sample_weights = weights[y_enc]

    model = XGBClassifier(n_estimators=500, max_depth=6, learning_rate=0.03, random_state=RANDOM_STATE, n_jobs=-1)
    model.fit(X, y_enc, sample_weight=sample_weights)
    
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump({"model": model, "le": le, "features": list(X.columns)}, MODEL_PATH)
    print(f"  Model trained on {len(X)} rows. Saved to {MODEL_PATH}")
    return True

if __name__ == "__main__": run_training()
