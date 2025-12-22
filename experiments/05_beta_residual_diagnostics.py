import pandas as pd
import numpy as np

# Load the processed diagnostic table
df = pd.read_csv("data/processed/beta_vertical_stacks.csv")

# Sanity
required = ["Z", "A", "G", "tau_s", "Q_mev"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise RuntimeError(f"Missing required columns: {missing}")

# Work in log space
df = df.copy()
df["log_tau"] = np.log10(df["tau_s"])
df["log_Q"] = np.log10(df["Q_mev"])

# ------------------------------------------------------------------
# 1) GLOBAL Q-ONLY BASELINE
# ------------------------------------------------------------------
coef = np.polyfit(df["log_Q"], df["log_tau"], 1)
a, b = coef

df["log_tau_pred"] = a + b * df["log_Q"]
df["residual"] = df["log_tau"] - df["log_tau_pred"]

print("\n=== Global Q-only fit ===")
print(f"log(tau) = {a:.3f} + ({b:.3f}) * log(Q)")
print("Median |residual|:", np.median(np.abs(df["residual"])))

# ------------------------------------------------------------------
# 2) RESIDUAL vs G (GLOBAL)
# ------------------------------------------------------------------
corr_r_G = np.corrcoef(df["residual"], df["G_satz"])[0, 1]
corr_absr_G = np.corrcoef(np.abs(df["residual"]), df["G_satz"])[0, 1]

print("\n=== Residual structure vs G (global) ===")
print("corr(residual, G)      =", corr_r_G)
print("corr(|residual|, G)    =", corr_absr_G)

grp_G = (
    df.groupby("G")
      .agg(
          n=("G", "size"),
          median_residual=("residual", "median"),
          mad_residual=("residual", lambda x: np.median(np.abs(x - np.median(x))))
      )
      .reset_index()
)

print("\nResidual summary by G:")
print(grp_G.to_string(index=False))

# ------------------------------------------------------------------
# 3) WITHIN-Z STACK DIAGNOSTICS
# ------------------------------------------------------------------
print("\n=== Within-Z stack diagnostics ===")

for Z, g in df.groupby("Z"):
    if len(g) < 3:
        continue  # need vertical stack
    corr = np.corrcoef(g["residual"], g["G"])[0, 1]
    print(f"\nZ = {Z}  (n={len(g)})")
    print("  corr(residual, G) =", corr)
    print(
        g[["A", "G", "Q_mev", "tau_s", "residual"]]
        .sort_values("G")
        .to_string(index=False)
    )

# ------------------------------------------------------------------
# 4) OPTIONAL: check if slope differs by Z
# ------------------------------------------------------------------
print("\n=== Local slopes by Z (diagnostic) ===")
for Z, g in df.groupby("Z"):
    if len(g) < 3:
        continue
    coef_Z = np.polyfit(g["log_Q"], g["log_tau"], 1)
    print(f"Z={Z}: slope b_Z = {coef_Z[1]:.3f}")