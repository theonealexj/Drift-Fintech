# -*- coding: utf-8 -*-
"""
run_pipeline.py  --  One command to run the full pipeline

  python crypto_ml/run_pipeline.py                  # full run
  python crypto_ml/run_pipeline.py --skip-collect   # skip data collection
  python crypto_ml/run_pipeline.py --skip-train     # skip training, predict only
  python crypto_ml/run_pipeline.py --predict-only   # just run predictions
"""

import os, sys, argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def section(n, title):
    print(f"\n{'='*52}\n  STEP {n}  --  {title}\n{'='*52}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-collect",  action="store_true")
    parser.add_argument("--skip-engineer", action="store_true")
    parser.add_argument("--skip-train",    action="store_true")
    parser.add_argument("--predict-only",  action="store_true")
    args = parser.parse_args()

    if args.predict_only:
        args.skip_collect = args.skip_engineer = args.skip_train = True

    if not args.skip_collect:
        section(1, "DATA COLLECTION")
        from crypto_ml.data_collector import run_collection
        if not run_collection():
            print("Collection failed.")
            sys.exit(1)

    if not args.skip_engineer:
        section(2, "FEATURE ENGINEERING")
        from crypto_ml.feature_engineer import run_engineering
        if not run_engineering():
            print("Feature engineering failed.")
            sys.exit(1)

    if not args.skip_train:
        section(3, "MODEL TRAINING")
        from crypto_ml.train import run_training
        run_training()

    section(4, "LIVE MARKET OUTLOOK")
    from crypto_ml.predict import run_prediction
    run_prediction()

    print("All done!\n")


if __name__ == "__main__":
    main()
