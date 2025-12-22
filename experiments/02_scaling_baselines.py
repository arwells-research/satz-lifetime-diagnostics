import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/lifetimes_clean.csv")

df = df.dropna(subset=["tau_s", "Q_mev"])
df["log_tau"] = np.log10(df["tau_s"])
df["log_Q"] = np.log10(df["Q_mev"])

# Robust baseline fit
coef = np.polyfit(df["log_Q"], df["log_tau"], 1)
a, b = coef

df["residual"] = df["log_tau"] - (a + b * df["log_Q"])

print("Baseline: log(tau) = a + b log(Q)")
print("a =", a, "b =", b)
print("Median abs residual:", np.median(np.abs(df["residual"])))