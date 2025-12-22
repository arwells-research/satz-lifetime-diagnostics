# experiments/06_beta_Q_plus_G_diagnostics.py
import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/beta_vertical_stacks.csv").copy()

required = ["Z", "A", "G", "tau_s", "Q_mev"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")

df["log_tau"] = np.log10(df["tau_s"])
df["log_Q"] = np.log10(df["Q_mev"])

# Design matrix: [1, logQ, G]
X = np.column_stack([
    np.ones(len(df)),
    df["log_Q"].to_numpy(),
    df["G_satz"].to_numpy(),
])
y = df["log_tau"].to_numpy()

# OLS (no regularization, no tricks)
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
a, b, c = beta

df["log_tau_pred"] = X @ beta
df["residual"] = df["log_tau"] - df["log_tau_pred"]

print("\n=== Global Q + G fit ===")
print(f"log(tau) = {a:.6f} + ({b:.6f})*log(Q) + ({c:.6f})*G")
print("Median |residual|:", float(np.median(np.abs(df["residual"]))))

# Compare to Q-only quickly (for reference)
beta_q, *_ = np.linalg.lstsq(
    np.column_stack([np.ones(len(df)), df["log_Q"].to_numpy()]),
    y,
    rcond=None
)
a0, b0 = beta_q
res0 = y - (a0 + b0 * df["log_Q"].to_numpy())
print("\n=== Reference Q-only fit (recomputed) ===")
print(f"log(tau) = {a0:.6f} + ({b0:.6f})*log(Q)")
print("Median |residual|:", float(np.median(np.abs(res0))))

# Residual structure vs G
corr_r_G = np.corrcoef(df["residual"], df["G_satz"])[0, 1]
corr_absr_G = np.corrcoef(np.abs(df["residual"]), df["G_satz"])[0, 1]
print("\n=== Residual structure vs G (global, after adding G) ===")
print("corr(residual, G)      =", float(corr_r_G))
print("corr(|residual|, G)    =", float(corr_absr_G))

grp_G = (
    df.groupby("G")
      .agg(
          n=("G", "size"),
          median_residual=("residual", "median"),
          mad_residual=("residual", lambda x: np.median(np.abs(x - np.median(x))))
      )
      .reset_index()
)
print("\nResidual summary by G (after adding G):")
print(grp_G.to_string(index=False))

# Within-Z stack checks (should flatten vs G if G term is doing its job)
print("\n=== Within-Z stack diagnostics (after adding G) ===")
for Z, g in df.groupby("Z"):
    if len(g) < 3:
        continue
    corr = np.corrcoef(g["residual"], g["G"])[0, 1]
    print(f"\nZ = {Z}  (n={len(g)})")
    print("  corr(residual, G) =", float(corr))
    print(
        g[["A", "G", "Q_mev", "tau_s", "residual"]]
        .sort_values("G")
        .to_string(index=False)
    )