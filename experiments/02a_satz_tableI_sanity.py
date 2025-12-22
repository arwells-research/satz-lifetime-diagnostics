import pandas as pd

df = pd.read_csv("data/processed/satz_tableI_isotope_masses.csv")

print("Rows:", len(df))
print("Elements:", df["element"].nunique())
print("Z range:", df["Z"].min(), "..", df["Z"].max())
print("A range:", df["A"].min(), "..", df["A"].max())

missing = df.isna().mean().sort_values(ascending=False)
print("\nMissing fraction by column:")
print(missing.to_string())

dups = df.duplicated(subset=["Z","A"]).sum()
print("\nDuplicate (Z,A) rows:", dups)

print("\nTop 10 by abundance:")
print(df.sort_values("nat_abund_pct", ascending=False).head(10).to_string(index=False))