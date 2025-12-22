#!/usr/bin/env python3
"""
experiments/09_beta_Q_G_logft_diagnostics.py

Fit and diagnose the beta-decay lifetime model:

    log10(tau_s) = a + b * log10(Q_mev) + c * G + d * logft

Inputs
------
Reads:
  data/processed/beta_vertical_stacks.csv

Required columns:
  - Z (int)
  - A (int)
  - G (int or float)
  - mode (str)
  - tau_s (float)        mean lifetime in seconds
  - Q_mev (float)
  - logft (float)

Outputs
-------
Prints:
  - fitted coefficients
  - median |residual| in log10 space
  - global residual correlations vs G and logft
  - within-Z stack diagnostics (corr(residual, G) per Z and table)

Notes
-----
- Uses ordinary least squares via numpy.linalg.lstsq (small n, transparent).
- This is a diagnostic script (not cross-validated).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


BETA_CSV = "data/processed/beta_vertical_stacks.csv"


def main() -> None:
    df = pd.read_csv(BETA_CSV).copy()

    required = ["Z", "A", "G", "mode", "tau_s", "Q_mev", "logft"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise RuntimeError(f"Missing required columns: {missing}")

    # Basic numeric coercions
    df["Z"] = pd.to_numeric(df["Z"], errors="raise").astype(int)
    df["A"] = pd.to_numeric(df["A"], errors="raise").astype(int)
    df["G_satz"] = pd.to_numeric(df["G_satz"], errors="coerce")
    df["tau_s"] = pd.to_numeric(df["tau_s"], errors="coerce")
    df["Q_mev"] = pd.to_numeric(df["Q_mev"], errors="coerce")
    df["logft"] = pd.to_numeric(df["logft"], errors="coerce")

    # Drop rows with missing essentials
    before = len(df)
    df = df.dropna(subset=["G", "tau_s", "Q_mev", "logft"]).copy()
    after = len(df)
    if after != before:
        print(f"WARNING: Dropped {before-after} rows due to missing numeric fields.")

    # Guard against invalid values for logs
    bad_tau = (df["tau_s"] <= 0).sum()
    bad_Q = (df["Q_mev"] <= 0).sum()
    if bad_tau or bad_Q:
        raise RuntimeError(f"Invalid non-positive values: tau_s<=0: {bad_tau}, Q_mev<=0: {bad_Q}")

    df["log_tau"] = np.log10(df["tau_s"].to_numpy())
    df["log_Q"] = np.log10(df["Q_mev"].to_numpy())

    # Design matrix: [1, logQ, G, logft]
    X = np.column_stack([
        np.ones(len(df)),
        df["log_Q"].to_numpy(),
        df["G_satz"].to_numpy(),
        df["logft"].to_numpy(),
    ])
    y = df["log_tau"].to_numpy()

    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    a, b, c, d = beta

    df["log_tau_pred"] = X @ beta
    df["residual"] = df["log_tau"] - df["log_tau_pred"]

    print("\n=== Global Q + G + logft fit ===")
    print(f"log10(tau) = {a:.6f} + ({b:.6f})*log10(Q) + ({c:.6f})*G + ({d:.6f})*logft")
    print("Median |residual|:", float(np.median(np.abs(df["residual"]))))

    # Global correlations
    def corr(a: np.ndarray, b: np.ndarray) -> float:
        if np.std(a) == 0 or np.std(b) == 0:
            return float("nan")
        return float(np.corrcoef(a, b)[0, 1])

    print("\n=== Global residual structure ===")
    print("corr(residual, G)      =", corr(df["residual"].to_numpy(), df["G_satz"].to_numpy()))
    print("corr(|residual|, G)    =", corr(np.abs(df["residual"].to_numpy()), df["G_satz"].to_numpy()))
    print("corr(residual, logft)  =", corr(df["residual"].to_numpy(), df["logft"].to_numpy()))
    print("corr(|residual|, logft)=", corr(np.abs(df["residual"].to_numpy()), df["logft"].to_numpy()))

    # Within-Z diagnostics
    print("\n=== Within-Z stack diagnostics ===")
    for Z, g in df.groupby("Z"):
        if len(g) < 3:
            continue
        rG = corr(g["residual"].to_numpy(), g["G"].to_numpy())
        rL = corr(g["residual"].to_numpy(), g["logft"].to_numpy())
        print(f"\nZ = {Z}  (n={len(g)})")
        print("  corr(residual, G)     =", rG)
        print("  corr(residual, logft) =", rL)
        print(
            g[["A", "G", "mode", "Q_mev", "logft", "tau_s", "residual"]]
            .sort_values(["G"])
            .to_string(index=False)
        )

    # Optional: show worst residuals
    worst = df.copy()
    worst["abs_res"] = np.abs(worst["residual"])
    worst = worst.sort_values("abs_res", ascending=False).head(10)
    print("\n=== Top 10 |residual| rows ===")
    print(worst[["Z", "A", "mode", "Q_mev", "G", "logft", "tau_s", "residual"]].to_string(index=False))


if __name__ == "__main__":
    main()