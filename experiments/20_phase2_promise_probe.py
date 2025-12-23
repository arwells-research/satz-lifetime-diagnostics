#!/usr/bin/env python3
"""
Phase II Promise Probe (Stratified) — CORRECT Phase I Residuals
---------------------------------------------------------------
Fast viability test for Phase II residual structure WITHOUT refitting Phase I.

Key correction vs earlier probe:
- Uses frozen Phase I coefficients (alpha, delta) loaded from:
    data/processed/frozen_law_phase1.json
  and computes:
    log10(tau_pred) = alpha + delta*logft - log10(G)
    residual        = log10(tau_obs) - log10(tau_pred)

Stratifies by decay mode:
- ALL
- beta-
- EC   (exact match "EC" case-insensitive/whitespace-tolerant)

INPUTS:
- data/processed/beta_vertical_stacks.csv  (must include: Z,N,tau_s,logft,G,Q_mev,mode)
- data/processed/frozen_law_phase1.json    (must include: alpha, delta)

OUTPUTS:
- reports/figures/20_phase2_promise_probe_stratified.png
- reports/tables/20_promise_probe_summary.csv
- reports/tables/20_promise_probe_metrics.csv
- reports/tables/20_promise_probe_outlier_tags.csv

RULES:
- Phase I law is frozen. We do NOT refit alpha/delta.
- Residuals are diagnostics, not errors.
- No regression/smoothing/corrections, only stratified cartography & checks.
"""

from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pandas as pd

from scipy.stats import spearmanr  # type: ignore

import matplotlib.pyplot as plt


# ----------------------------
# CONFIG
# ----------------------------

DATA_PATH = Path("data/processed/beta_vertical_stacks.csv")
FROZEN_LAW_PATH = Path("data/processed/frozen_law_phase1.json")

OUT_DIR = Path("reports")
FIG_DIR = OUT_DIR / "figures"
TAB_DIR = OUT_DIR / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

MAGIC_NS = [50, 82, 126]
LOW_Z_MAX = 20
OUTLIER_TOP_K = 30

PLOT_SUBSET_ORDER = ["ALL", "beta-", "EC"]


# ----------------------------
# LOAD FROZEN COEFFS
# ----------------------------

def load_frozen_coeffs(path: Path) -> tuple[float, float]:
    if not path.exists():
        raise RuntimeError(f"Frozen law JSON not found: {path}")
    obj = json.loads(path.read_text())
    if "alpha" not in obj or "delta" not in obj:
        raise RuntimeError(f"Frozen law JSON missing alpha/delta: {path}")
    alpha = float(obj["alpha"])
    delta = float(obj["delta"])
    return alpha, delta


ALPHA, DELTA = load_frozen_coeffs(FROZEN_LAW_PATH)


# ----------------------------
# HELPERS
# ----------------------------

def _require_columns(df: pd.DataFrame, cols: set[str]) -> None:
    missing = cols - set(df.columns)
    if missing:
        raise RuntimeError(f"Missing required columns: {sorted(missing)}")


def _norm_mode(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    s = s.where(~s.str.fullmatch("ec", case=False), "EC")
    return s


def run_probe(subdf: pd.DataFrame, subset_name: str, alpha: float, delta: float) -> tuple[pd.DataFrame, pd.DataFrame, dict, dict]:
    """
    Compute residuals, regime tags, summary table, correlations, outlier tag fractions for one subset.
    Returns:
      d_with_resid, summary_df, metrics_dict, outlier_tag_fracs_dict
    """
    d = subdf.copy()

    # Phase I prediction (frozen):
    # log10(tau_pred) = alpha + delta*logft - log10(G)
    d["log_tau_obs"] = np.log10(d["tau_s"].astype(float))
    d["log_tau_pred"] = alpha + delta * d["logft"].astype(float) - np.log10(d["G"].astype(float))
    d["residual"] = d["log_tau_obs"] - d["log_tau_pred"]

    # Regime tags (annotation only)
    Z = d["Z"].astype(int)
    N = d["N"].astype(int)
    d["parity"] = np.where(
        (Z % 2 == 0) & (N % 2 == 0), "even-even",
        np.where((Z % 2 == 1) & (N % 2 == 1), "odd-odd", "odd-A")
    )
    d["magic_N"] = N.apply(lambda n: any(abs(int(n) - m) <= 1 for m in MAGIC_NS))
    d["low_Z"] = Z < LOW_Z_MAX

    # Summary table (medians/IQR by grouping)
    rows = []

    def summarize(group_col: str) -> None:
        for key, g in d.groupby(group_col):
            vals = g["residual"].astype(float).to_numpy()
            if len(vals) == 0:
                continue
            q75, q25 = np.percentile(vals, [75, 25])
            rows.append({
                "subset": subset_name,
                "grouping": group_col,
                "group": str(key),
                "count": int(len(vals)),
                "median_residual": float(np.median(vals)),
                "iqr": float(q75 - q25),
            })

    summarize("parity")
    summarize("magic_N")
    summarize("low_Z")

    summary = pd.DataFrame(rows)

    # Correlations (guard against tiny subsets)
    if len(d) >= 5:
        rho_G, p_G = spearmanr(d["residual"], np.log10(d["G"].astype(float)))
        rho_Q, p_Q = spearmanr(d["residual"], d["Q_mev"].astype(float))
        rho_G = float(rho_G)
        p_G = float(p_G)
        rho_Q = float(rho_Q)
        p_Q = float(p_Q)
    else:
        rho_G = p_G = rho_Q = p_Q = float("nan")

    metrics = {
        "subset": subset_name,
        "n": int(len(d)),
        "alpha": float(alpha),
        "delta": float(delta),
        "rho_resid_log10G": rho_G,
        "p_resid_log10G": p_G,
        "rho_resid_Q_mev": rho_Q,
        "p_resid_Q_mev": p_Q,
    }

    # Outlier tag fractions among top-K |residual|
    if len(d) > 0:
        top = d["residual"].abs().sort_values(ascending=False).head(OUTLIER_TOP_K)
        out = d.loc[top.index]
        outlier_tags = {
            "subset": subset_name,
            "K": int(len(out)),
            "frac_magic_N": float(out["magic_N"].mean()),
            "frac_low_Z": float(out["low_Z"].mean()),
            "frac_odd_odd": float((out["parity"] == "odd-odd").mean()),
        }
    else:
        outlier_tags = {
            "subset": subset_name,
            "K": 0,
            "frac_magic_N": float("nan"),
            "frac_low_Z": float("nan"),
            "frac_odd_odd": float("nan"),
        }

    return d, summary, metrics, outlier_tags


def _median_span(summary: pd.DataFrame, grouping: str) -> float:
    s = summary[summary["grouping"] == grouping]
    if len(s) == 0:
        return float("nan")
    meds = s["median_residual"].astype(float).to_numpy()
    return float(np.max(meds) - np.min(meds))


# ----------------------------
# MAIN
# ----------------------------

def main() -> None:
    df = pd.read_csv(DATA_PATH)

    _require_columns(df, {"Z", "N", "tau_s", "logft", "G", "Q_mev", "mode"})
    df["mode"] = _norm_mode(df["mode"])

    subsets = {
        "ALL": df,
        "beta-": df[df["mode"] == "beta-"],
        "EC": df[df["mode"] == "EC"],
    }

    probe_data: dict[str, pd.DataFrame] = {}
    summaries = []
    metrics_rows = []
    outlier_rows = []

    for name, sdf in subsets.items():
        d, summ, met, out = run_probe(sdf, name, ALPHA, DELTA)
        probe_data[name] = d
        summaries.append(summ)
        metrics_rows.append(met)
        outlier_rows.append(out)

    summary_all = pd.concat(summaries, ignore_index=True) if summaries else pd.DataFrame()
    metrics_df = pd.DataFrame(metrics_rows)
    outliers_df = pd.DataFrame(outlier_rows)

    summary_path = TAB_DIR / "20_promise_probe_summary.csv"
    metrics_path = TAB_DIR / "20_promise_probe_metrics.csv"
    outliers_path = TAB_DIR / "20_promise_probe_outlier_tags.csv"
    fig_path = FIG_DIR / "20_phase2_promise_probe_stratified.png"

    summary_all.to_csv(summary_path, index=False)
    metrics_df.to_csv(metrics_path, index=False)
    outliers_df.to_csv(outliers_path, index=False)

    # Plot: subsets x groupings (parity, magic_N, low_Z)
    fig, axes = plt.subplots(len(PLOT_SUBSET_ORDER), 3, figsize=(14, 4 * len(PLOT_SUBSET_ORDER)), sharey=True)

    for i, subset in enumerate(PLOT_SUBSET_ORDER):
        d = probe_data.get(subset, pd.DataFrame())
        if len(d) == 0:
            for j in range(3):
                axes[i, j].axis("off")
            continue

        d.boxplot(column="residual", by="parity", ax=axes[i, 0])
        axes[i, 0].set_title(f"{subset}: Residual by Parity")
        axes[i, 0].set_ylabel("Δ = log10 τ_obs − log10 τ_pred")

        d.boxplot(column="residual", by="magic_N", ax=axes[i, 1])
        axes[i, 1].set_title(f"{subset}: Residual by Magic N (±1)")

        d.boxplot(column="residual", by="low_Z", ax=axes[i, 2])
        axes[i, 2].set_title(f"{subset}: Residual by Low-Z (Z < {LOW_Z_MAX})")

    plt.suptitle(f"Phase II Promise Probe — Stratified (ALL vs β⁻ vs EC)\nFrozen law: alpha={ALPHA:.3f}, delta={DELTA:.3f}")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=150)
    plt.close()

    # Console report
    print("\n=== Phase II Promise Probe (Stratified) ===\n")
    print(f"Frozen law: alpha={ALPHA:.6g}, delta={DELTA:.6g}")
    print(f"Input:  {DATA_PATH}")
    print(f"Figure: {fig_path}")
    print(f"Tables: {summary_path}")
    print(f"        {metrics_path}")
    print(f"        {outliers_path}\n")

    print("Metrics (Spearman):")
    print(metrics_df.to_string(index=False))

    print("\nOutlier tag fractions (top K by |residual|):")
    print(outliers_df.to_string(index=False))


    # ------------------------------------------------------------
    # EXTRA CHEAP STRATIFICATION:
    # Parity separation within log10(G) bins (beta-) to test whether
    # parity signal survives conditioning on phase-space.
    # ------------------------------------------------------------
    d = probe_data.get("beta-", None)
    if d is not None and len(d) >= 12:
        d = d.copy()
        d["log10G"] = np.log10(d["G"].astype(float))
        # 3 quantile bins (balanced counts); duplicates="drop" guards tiny data
        d["Gbin"] = pd.qcut(d["log10G"], q=3, duplicates="drop")

        print("\nParity separation within log10(G) bins (beta-):")
        for b, g in d.groupby("Gbin", observed=False):
            meds = g.groupby("parity")["residual"].median()
            if len(meds) >= 2:
                span = float(meds.max() - meds.min())
                print(f"  {str(b):30s}  n={len(g):2d}  span={span:.3f}  medians={meds.to_dict()}")
            else:
                print(f"  {str(b):30s}  n={len(g):2d}  span=NA (need ≥2 parity classes)")
        print("")


    # ------------------------------------------------------------
    # EXTRA CHEAP STRATIFICATION:
    # Parity separation within logft bins (beta-)
    # Tests whether structure survives conditioning on transition class
    # ------------------------------------------------------------

    if d is not None and len(d) >= 12:
        d2 = d.copy()
        # Coarse bins: allowed-ish / mixed / forbidden-ish
        bins = [-np.inf, 5.5, 6.5, np.inf]
        labels = ["allowed-ish", "mixed", "forbidden-ish"]
        d2["logft_bin"] = pd.cut(d2["logft"].astype(float), bins=bins, labels=labels)

        print("Parity separation within logft bins (beta-):")
        for b, g in d2.groupby("logft_bin", observed=False):
            meds = g.groupby("parity")["residual"].median()
            if len(g) == 0:
                continue
            if len(meds) >= 2:
                span = float(meds.max() - meds.min())
                print(f"  {str(b):15s}  n={len(g):2d}  span={span:.3f}  medians={meds.to_dict()}")
            else:
                print(f"  {str(b):15s}  n={len(g):2d}  span=NA (need ≥2 parity classes)")
        print("")

    if len(summary_all) == 0:
        print("\nNo summary rows produced (empty dataset?)")
        return

    print("\nMedian residual spans by grouping (per subset):")
    for subset in PLOT_SUBSET_ORDER:
        s = summary_all[summary_all["subset"] == subset]
        if len(s) == 0:
            continue
        span_par = _median_span(s, "parity")
        span_mag = _median_span(s, "magic_N")
        span_low = _median_span(s, "low_Z")
        print(f"  {subset:5s}  span(parity)={span_par:.3f}  span(magic_N)={span_mag:.3f}  span(low_Z)={span_low:.3f}")

    print("\nHeuristic GO/NO-GO (per subset):")
    print("  - Primary criterion (Phase II promise): parity separation persists under conditioning.")
    print("  - Conditioning checks are evaluated within the beta- subset:")
    print("      (a) parity median-span within log10(G) bins >= 0.40 dex in any bin")
    print("      (b) parity median-span within logft bins >= 0.40 dex in any bin")
    print("  - Global residual–G correlation is reported but NOT treated as a failure in this probe.\n")

    def _max_parity_span_within_bins(d: pd.DataFrame, bin_col: str) -> float:
        """Return max (max(median residual by parity) - min(...)) across bins."""
        max_span = float("nan")
        for _, g in d.groupby(bin_col, observed=False):
            meds = g.groupby("parity")["residual"].median()
            if len(meds) < 2:
                continue
            span = float(meds.max() - meds.min())
            if np.isnan(max_span) or span > max_span:
                max_span = span
        return max_span

    # Conditioning spans (beta- only; other subsets may be empty)
    beta_d = probe_data.get("beta-", None)
    max_span_gbin = float("nan")
    max_span_logftbin = float("nan")
    if beta_d is not None and len(beta_d) >= 12:
        bd = beta_d.copy()
        bd["log10G"] = np.log10(bd["G"].astype(float))
        bd["Gbin"] = pd.qcut(bd["log10G"], q=3, duplicates="drop")
        max_span_gbin = _max_parity_span_within_bins(bd, "Gbin")

        bins = [-np.inf, 5.5, 6.5, np.inf]
        labels = ["allowed-ish", "mixed", "forbidden-ish"]
        bd["logft_bin"] = pd.cut(bd["logft"].astype(float), bins=bins, labels=labels)
        max_span_logftbin = _max_parity_span_within_bins(bd, "logft_bin")

    cond_ok = (pd.notna(max_span_gbin) and max_span_gbin >= 0.40) or (pd.notna(max_span_logftbin) and max_span_logftbin >= 0.40)
 

    for _, row in metrics_df.iterrows():
        subset = str(row["subset"])
        s = summary_all[summary_all["subset"] == subset]
        if len(s) == 0:
            continue

        separation_ok = (
            (_median_span(s, "parity") >= 0.40) or
            (_median_span(s, "magic_N") >= 0.40) or
            (_median_span(s, "low_Z") >= 0.40)
        )


        # Conditioning only applies meaningfully to beta- in this probe.
        # For other subsets (ALL/EC), we still report separation but do not attempt conditioning.
        if subset == "beta-":
            go = separation_ok and cond_ok
            print(f"  {subset:5s}: separation={'OK' if separation_ok else 'no'}  "
                  f"cond(parity|bins)={'OK' if cond_ok else 'no'}  "
                  f"max_span(Gbin)={max_span_gbin:.3f}  max_span(logftbin)={max_span_logftbin:.3f}  "
                  f"=> {'GO' if go else 'NO-GO'}")
        else:
            print(f"  {subset:5s}: separation={'OK' if separation_ok else 'no'}  "
                  f"cond(parity|bins)=NA  => {'GO' if separation_ok else 'NO-GO'}")
 

    print("")


if __name__ == "__main__":
    main()