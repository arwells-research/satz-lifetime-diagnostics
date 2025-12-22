# experiments/07_beta_Q_plus_G_plus_F_diagnostics.py
import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/beta_vertical_stacks.csv").copy()

required = ["Z", "A", "G", "tau_s", "Q_mev", "F"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")

df["log_tau"] = np.log10(df["tau_s"])
df["log_Q"] = np.log10(df["Q_mev"])
F_raw = pd.to_numeric(df["F"], errors="coerce")
n_bad = int(F_raw.isna().sum())
if n_bad:
    print(f"WARNING: {n_bad} rows have non-numeric F; defaulting them to 0.")
df["F"] = F_raw.fillna(0).astype(int)

# Design matrix: [1, logQ, G, F]
X = np.column_stack([
    np.ones(len(df)),
    df["log_Q"].to_numpy(),
    df["G_satz"].to_numpy(),
    df["F"].to_numpy(),
])
y = df["log_tau"].to_numpy()

beta, *_ = np.linalg.lstsq(X, y, rcond=None)
a, b, c, d = beta

df["log_tau_pred"] = X @ beta
df["residual"] = df["log_tau"] - df["log_tau_pred"]

print("\n=== Global Q + G + F fit ===")
print(f"log(tau) = {a:.6f} + ({b:.6f})*log(Q) + ({c:.6f})*G + ({d:.6f})*F")
print("Median |residual|:", float(np.median(np.abs(df['residual']))))

# Residual structure vs G after adding F
corr_r_G = np.corrcoef(df["residual"], df["G_satz"])[0, 1]
corr_absr_G = np.corrcoef(np.abs(df["residual"]), df["G_satz"])[0, 1]
print("\n=== Residual structure vs G (global, after adding F) ===")
print("corr(residual, G)      =", float(corr_r_G))
print("corr(|residual|, G)    =", float(corr_absr_G))

# Residual structure vs F (should be ~0 if F captured the main forbiddenness trend)
corr_r_F = np.corrcoef(df["residual"], df["F"])[0, 1] if df["F"].nunique() > 1 else float("nan")
print("\n=== Residual structure vs F (global) ===")
print("corr(residual, F)      =", float(corr_r_F))

# Within-Z stack checks
print("\n=== Within-Z stack diagnostics (after adding F) ===")
for Z, g in df.groupby("Z"):
    if len(g) < 3:
        continue
    corr = np.corrcoef(g["residual"], g["G"])[0, 1]
    print(f"\nZ = {Z}  (n={len(g)})")
    print("  corr(residual, G) =", float(corr))
    print(
        g[["A", "G", "F", "Q_mev", "tau_s", "residual"]]
        .sort_values(["G"])
        .to_string(index=False)
    )