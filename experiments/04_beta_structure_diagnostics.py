import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/beta_lifetimes.csv")

df["log10_T12"] = np.log10(df["half_life_s"])
df["A_over_Z"] = df["A"] / df["Z"]

print("Rows:", len(df))
print("Modes:", df["mode"].value_counts().head(20).to_string())

# Quick summaries by G
grp = df.groupby("G").agg(
    n=("G","size"),
    median_logT=("log10_T12","median"),
    mad_logT=("log10_T12", lambda x: np.median(np.abs(x - np.median(x)))),
    mean_AoZ=("A_over_Z","mean"),
).reset_index()

print("\nTop 20 G by count:")
print(grp.sort_values("n", ascending=False).head(20).to_string(index=False))

# Simple check: does lifetime shift monotonically with G in aggregate?
grp2 = grp.sort_values("G")
corr = np.corrcoef(grp2["G"].to_numpy(), grp2["median_logT"].to_numpy())[0,1]
print("\nCorr(G, median_log10(T1/2)) across G bins:", corr)