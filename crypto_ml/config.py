"""
config.py — Central configuration for the Crypto ML Threat Detection pipeline.
"""

# ──────────────────────────────────────────────
# FreeCryptoAPI credentials
# ──────────────────────────────────────────────
API_KEY = "pa6sx2sr34yxxci1xnph"
BASE_URL = "https://api.freecryptoapi.com/v1"

# ──────────────────────────────────────────────
# Target coins to predict
# ──────────────────────────────────────────────
SYMBOLS = ["BTC", "ETH", "SOL"]

# ──────────────────────────────────────────────
# Prediction settings
# ──────────────────────────────────────────────
# If price goes UP by this % within LOOKAHEAD_DAYS → label BUY (+1)
# If price goes DOWN by this % within LOOKAHEAD_DAYS → label SELL (-1)
# Otherwise → HOLD (0)
LABEL_THRESHOLD_PCT = 1.5      # % change threshold — BUY if > +1.5%, SELL if < -1.5%
LOOKAHEAD_DAYS      = 1        # next candle (4h ahead with 4h interval)

# ──────────────────────────────────────────────
# Historical data window
# ──────────────────────────────────────────────
HISTORY_DAYS = 730             # 2 years — needed for SMA-200 and rich training data

# ──────────────────────────────────────────────
# Model settings
# ──────────────────────────────────────────────
TEST_SIZE      = 0.2           # 80/20 train-test split
RANDOM_STATE   = 42
MODEL_DIR      = "crypto_ml/models"       # directory for model_7d.pkl, model_14d.pkl, model_30d.pkl
MODEL_PATH     = "crypto_ml/models/crypto_model.pkl"   # kept for backwards compat
RAW_DATA_DIR   = "crypto_ml/data/raw"
PROC_DATA_DIR  = "crypto_ml/data/processed"

# ──────────────────────────────────────────────
# Label map (for display)
# ──────────────────────────────────────────────
LABEL_MAP = {1: "BUY 🟢", 0: "HOLD 🟡", -1: "SELL 🔴"}
