import pandas as pd
import numpy as np

df = pd.read_csv("data/processed/satz_tableI_isotope_masses.csv").copy()

# Simple derived features
df["N"] = df["A"] - df["Z"]
df["N_minus_Z"] = df["N"] - df["Z"]
df["A_over_Z"] = df["A"] / df["Z"]

print("Counts by G:")
print(df["G_satz"].value_counts().sort_index().to_string())

# Band summaries
grp = df.groupby("G").agg(
    n=("G","size"),
    Z_min=("Z","min"),
    Z_max=("Z","max"),
    A_min=("A","min"),
    A_max=("A","max"),
    mean_A=("A","mean"),
    mean_NZ=("N_minus_Z","mean"),
    mean_AoZ=("A_over_Z","mean"),
    mean_abund=("nat_abund_pct","mean"),
).reset_index()

print("\nBand summaries by G:")
print(grp.to_string(index=False))

# Quick “separation” check: do G bands have distinct N-Z means?
if grp["mean_NZ"].nunique() > 1:
    print("\nmean(N-Z) range across G:", grp["mean_NZ"].min(), "..", grp["mean_NZ"].max())