"""
00_generate_sample_data.py
---------------------------
Run this once to create a PLACEHOLDER backend/data/dataset.csv so everyone
can develop and test their scripts before Person 3 delivers the
real dataset.

DO NOT use this file's output in the final submission. It exists purely to
unblock parallel development. The moment real data lands in
backend/data/dataset.csv, every other script keeps working unchanged.

Run:
    python3 backend/scripts/00_generate_sample_data.py
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "dataset.csv")


def generate_sample_data(n_days: int = 45, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    start_date = datetime.today() - timedelta(days=n_days - 1)
    dates = [start_date + timedelta(days=i) for i in range(n_days)]

    base = 32.5
    trend = np.linspace(0, 1.2, n_days)
    noise = np.random.normal(0, 1.8, n_days)
    temps = base + trend + noise

    outlier_days = np.random.choice(n_days, size=2, replace=False)
    temps[outlier_days] += np.random.uniform(4, 6, size=2)
    temps = np.round(temps, 1)

    return pd.DataFrame({
        "date": [d.strftime("%Y-%m-%d") for d in dates],
        "max_temp_c": temps
    })


if __name__ == "__main__":
    df = generate_sample_data()
    out_path = os.path.abspath(OUTPUT_PATH)
    df.to_csv(out_path, index=False)
    print(f"Generated {len(df)} placeholder days -> {out_path}")
    print(df.head())
    print("\nTHIS IS PLACEHOLDER DATA. Person 3 must replace this file with")
    print("the real, sourced, cleaned dataset before final submission.")
