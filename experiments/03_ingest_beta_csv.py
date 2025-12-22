from __future__ import annotations

from pathlib import Path
import pandas as pd
import numpy as np

from src.ingest.normalize_halflife import parse_halflife_to_seconds

RAW = Path("data/raw/beta/nubase_beta.csv")   # rename if your file differs
OUT = Path("data/processed/beta_lifetimes.csv")

def main():
    assert RAW.exists(), f"Missing raw beta file: {RAW}"

    df = pd.read_csv(RAW)

    # Required columns (adapt here if your raw headers differ)
    # Expect at least Z, A, half_life, mode; optionally half_life_unit
    for col in ["Z", "A", "half_life", "mode"]:
        if col not in df.columns:
            raise RuntimeError(f"Raw file missing required column: {col}. Columns: {list(df.columns)}")

    # Normalize half-life seconds
    if "half_life_unit" in df.columns:
        df["half_life_s"] = [
            parse_halflife_to_seconds(v, u) for v, u in zip(df["half_life"], df["half_life_unit"])
        ]
    else:
        df["half_life_s"] = [parse_halflife_to_seconds(v, None) for v in df["half_life"]]

    df = df.dropna(subset=["half_life_s"])
    df["half_life_s"] = df["half_life_s"].astype(float)

    # Derived
    df["Z"] = df["Z"].astype(int)
    df["A"] = df["A"].astype(int)
    df["N"] = df["A"] - df["Z"]
    df["G_satz"] = df["N"] - df["Z"]  # Satz: G = N - Z

    # Mean lifetime
    df["tau_s"] = df["half_life_s"] / np.log(2.0)

    # Normalize mode strings
    df["mode"] = df["mode"].astype(str).str.strip()
    df["mode"] = df["mode"].str.replace("β", "beta", regex=False)
    df["mode"] = df["mode"].str.replace(" ", "", regex=False)

    # Keep a simple, stable schema
    out = df[["Z","A","N","G","mode","half_life_s","tau_s"]].copy()
    out["Q_mev"] = np.nan
    out["source"] = RAW.name

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)

    print("Read raw:", RAW)
    print("Wrote:", OUT)
    print("Rows:", len(out))
    print(out.head(10).to_string(index=False))

if __name__ == "__main__":
    main()