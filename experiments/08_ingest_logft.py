#!/usr/bin/env python3
"""
experiments/08_ingest_logft.py

Goal
----
Populate the `logft` column in:
  data/processed/beta_vertical_stacks.csv

from one or more local "logft source" CSV files you provide under:
  data/raw/logft/

This script is intentionally *offline* and *provenance-first*:
- It does NOT fetch ENSDF/NUBASE from the internet.
- You supply extracted/curated logft rows (from ENSDF/NUBASE exports, NNDC dumps, your own table parsing, etc.)
- The script chooses a single logft per (Z,A) using a deterministic rule and writes:
    1) updated beta table
    2) an audit trail of where each logft came from

Inputs expected (you provide)
-----------------------------
1) One or more CSVs in data/raw/logft/*.csv
   Each file may contain any superset of these columns:
     - Z (int)
     - A (int)
     - logft (float)
     - mode (str)              e.g. "beta-", "beta+", "EC", "EC/beta+"
     - br_pct (float)          branching ratio in percent (0..100)
     - br (float)              branching ratio as fraction (0..1) (alternative to br_pct)
     - parent (str)            optional
     - daughter (str)          optional
     - source (str)            optional (otherwise filename is used)
     - comment (str)           optional

2) Optional overrides:
   data/aux/logft_overrides.csv
   Columns:
     - Z, A, logft
     - optional: mode, note, source
   Overrides always win.

Selection rule (dominant branch)
--------------------------------
For each (Z,A) in beta_vertical_stacks.csv:
  1) If override exists -> use it.
  2) Else consider all candidate rows with same (Z,A).
     - If beta row has a mode and candidates have mode:
         prefer candidates whose mode "matches" (case-insensitive substring match).
       Mode matching is lenient:
         beta- matches rows containing "beta-"
         EC matches rows containing "EC"
         beta+ matches rows containing "beta+"
     - Among remaining candidates:
         prefer highest branching ratio if available (br_pct or br)
       If branching ratio not available:
         prefer the smallest logft (strongest transition) as a fallback heuristic.
  3) If still tied: choose the first after stable sorting.

Outputs
-------
- Overwrites: data/processed/beta_vertical_stacks.csv
  (adds/fills `logft` column; leaves existing non-empty logft values untouched unless --force)
- Writes audit: data/processed/logft_audit.csv

Usage
-----
  python experiments/08_ingest_logft.py
  python experiments/08_ingest_logft.py --force
  python experiments/08_ingest_logft.py --beta data/processed/beta_vertical_stacks.csv --logft_dir data/raw/logft

Exit codes
----------
- 0: success (even if some logft remain missing, unless --require_complete)
- 2: missing required input files
- 3: require_complete failed (still-missing logft values)
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import numpy as np
import pandas as pd


DEFAULT_BETA = Path("data/processed/beta_vertical_stacks.csv")
DEFAULT_LOGFT_DIR = Path("data/raw/logft")
DEFAULT_OVERRIDES = Path("data/aux/logft_overrides.csv")
DEFAULT_AUDIT_OUT = Path("data/processed/logft_audit.csv")


def _read_csvs(glob_path: Path) -> pd.DataFrame:
    files = sorted(glob_path.parent.glob(glob_path.name))
    if not files:
        return pd.DataFrame()
    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["__file__"] = str(f)
        dfs.append(df)
    return pd.concat(dfs, ignore_index=True)


def _normalize_candidates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize candidate columns and types:
      - require Z,A,logft
      - add br_pct (preferred) if br exists
      - add source column
      - normalize mode
    """
    if df.empty:
        return df

    out = df.copy()

    # Standardize column names (case-insensitive)
    rename_map = {}
    for c in out.columns:
        lc = c.strip().lower()
        if lc == "z":
            rename_map[c] = "Z"
        elif lc == "a":
            rename_map[c] = "A"
        elif lc in ("logft", "log_ft", "log ft"):
            rename_map[c] = "logft"
        elif lc in ("mode", "decay_mode", "decay"):
            rename_map[c] = "mode"
        elif lc in ("br_pct", "branch_pct", "branching_pct", "branching_ratio_pct"):
            rename_map[c] = "br_pct"
        elif lc in ("br", "branch", "branching", "branching_ratio"):
            rename_map[c] = "br"
        elif lc == "source":
            rename_map[c] = "source"
        elif lc == "comment":
            rename_map[c] = "comment"

    if rename_map:
        out = out.rename(columns=rename_map)

    # Must have Z,A,logft
    for col in ["Z", "A", "logft"]:
        if col not in out.columns:
            raise RuntimeError(f"logft source files must contain column '{col}' (after normalization)")

    out["Z"] = pd.to_numeric(out["Z"], errors="coerce").astype("Int64")
    out["A"] = pd.to_numeric(out["A"], errors="coerce").astype("Int64")
    out["logft"] = pd.to_numeric(out["logft"], errors="coerce")

    out = out.dropna(subset=["Z", "A", "logft"]).copy()
    out["Z"] = out["Z"].astype(int)
    out["A"] = out["A"].astype(int)

    # Mode normalization
    if "mode" in out.columns:
        out["mode"] = out["mode"].astype(str).str.strip()
    else:
        out["mode"] = ""

    # Branching ratio normalization
    if "br_pct" in out.columns:
        out["br_pct"] = pd.to_numeric(out["br_pct"], errors="coerce")
    else:
        out["br_pct"] = np.nan

    if "br" in out.columns:
        br = pd.to_numeric(out["br"], errors="coerce")
        # If br is in fraction, convert to pct when br_pct missing
        out.loc[out["br_pct"].isna(), "br_pct"] = br[out["br_pct"].isna()] * 100.0

    # Source normalization
    if "source" not in out.columns:
        out["source"] = ""
    out["source"] = out["source"].astype(str).str.strip()
    # Fall back to filename when source empty
    out.loc[out["source"] == "", "source"] = out["__file__"]

    return out


def _normalize_overrides(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["Z", "A", "logft", "mode", "source", "note"])
    df = pd.read_csv(path).copy()

    # Normalize columns similarly
    rename_map = {}
    for c in df.columns:
        lc = c.strip().lower()
        if lc == "z":
            rename_map[c] = "Z"
        elif lc == "a":
            rename_map[c] = "A"
        elif lc in ("logft", "log_ft", "log ft"):
            rename_map[c] = "logft"
        elif lc in ("mode", "decay_mode", "decay"):
            rename_map[c] = "mode"
        elif lc == "source":
            rename_map[c] = "source"
        elif lc in ("note", "notes", "comment"):
            rename_map[c] = "note"
    if rename_map:
        df = df.rename(columns=rename_map)

    for col in ["Z", "A", "logft"]:
        if col not in df.columns:
            raise RuntimeError(f"Overrides file {path} must contain '{col}'")

    df["Z"] = pd.to_numeric(df["Z"], errors="coerce")
    df["A"] = pd.to_numeric(df["A"], errors="coerce")
    df["logft"] = pd.to_numeric(df["logft"], errors="coerce")
    df = df.dropna(subset=["Z", "A", "logft"]).copy()
    df["Z"] = df["Z"].astype(int)
    df["A"] = df["A"].astype(int)

    if "mode" not in df.columns:
        df["mode"] = ""
    df["mode"] = df["mode"].astype(str).str.strip()

    if "source" not in df.columns:
        df["source"] = str(path)
    df["source"] = df["source"].astype(str).str.strip()
    df.loc[df["source"] == "", "source"] = str(path)

    if "note" not in df.columns:
        df["note"] = ""

    return df[["Z", "A", "logft", "mode", "source", "note"]]


def _mode_match_score(beta_mode: str, cand_mode: str) -> int:
    """
    Lenient matching:
      - exact contains gets 2
      - compatible (e.g., EC vs EC/beta+) gets 1
      - else 0
    """
    b = (beta_mode or "").strip().lower()
    c = (cand_mode or "").strip().lower()

    if not b:
        return 0
    if b in c and b != "":
        return 2

    # Compatibility heuristics
    if b == "ec" and "ec" in c:
        return 1
    if b == "beta+" and ("beta+" in c or "ec" in c):
        return 1
    if b == "beta-" and "beta-" in c:
        return 1

    return 0


def choose_logft_for_row(
    Z: int,
    A: int,
    beta_mode: str,
    candidates: pd.DataFrame,
    overrides: pd.DataFrame,
) -> Tuple[Optional[float], Dict[str, str]]:
    """
    Returns (logft, provenance dict)
    provenance includes: method, source, mode_used, br_pct_used, cand_mode, note
    """
    # Overrides win
    ov = overrides[(overrides["Z"] == Z) & (overrides["A"] == A)]
    if not ov.empty:
        r = ov.iloc[0]
        return float(r["logft"]), {
            "method": "override",
            "source": str(r.get("source", "")),
            "cand_mode": str(r.get("mode", "")),
            "br_pct_used": "",
            "note": str(r.get("note", "")),
        }

    cands = candidates[(candidates["Z"] == Z) & (candidates["A"] == A)]
    if cands.empty:
        return None, {"method": "missing", "source": "", "cand_mode": "", "br_pct_used": "", "note": ""}

    # Score by mode match (prefer matching candidates)
    cands = cands.copy()
    cands["mode_score"] = [
        _mode_match_score(beta_mode, m) for m in cands["mode"].astype(str).tolist()
    ]

    # Prefer best mode score
    best_score = cands["mode_score"].max()
    if best_score > 0:
        cands = cands[cands["mode_score"] == best_score]

    # Prefer highest branching ratio if available (br_pct)
    has_br = cands["br_pct"].notna().any()
    if has_br:
        # fill missing br_pct with -inf so they sort last
        cands["_br_sort"] = cands["br_pct"].fillna(-np.inf)
        cands = cands.sort_values(["_br_sort", "logft"], ascending=[False, True])
        top = cands.iloc[0]
        return float(top["logft"]), {
            "method": "candidate_highest_br",
            "source": str(top["source"]),
            "cand_mode": str(top["mode"]),
            "br_pct_used": "" if pd.isna(top["br_pct"]) else f"{float(top['br_pct']):.6g}",
            "note": "",
        }

    # Fallback: choose smallest logft (strongest transition)
    cands = cands.sort_values(["logft"], ascending=[True])
    top = cands.iloc[0]
    return float(top["logft"]), {
        "method": "candidate_min_logft",
        "source": str(top["source"]),
        "cand_mode": str(top["mode"]),
        "br_pct_used": "",
        "note": "",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--beta", type=Path, default=DEFAULT_BETA, help="Path to beta_vertical_stacks.csv")
    ap.add_argument("--logft_dir", type=Path, default=DEFAULT_LOGFT_DIR, help="Directory containing logft source CSVs")
    ap.add_argument("--overrides", type=Path, default=DEFAULT_OVERRIDES, help="Optional overrides CSV")
    ap.add_argument("--audit_out", type=Path, default=DEFAULT_AUDIT_OUT, help="Audit output CSV")
    ap.add_argument("--force", action="store_true", help="Overwrite existing non-empty logft values")
    ap.add_argument("--require_complete", action="store_true", help="Fail if any beta rows lack logft after ingestion")
    args = ap.parse_args()

    if not args.beta.exists():
        print(f"ERROR: missing beta table: {args.beta}")
        return 2

    beta = pd.read_csv(args.beta).copy()

    # Ensure required columns exist
    for col in ["Z", "A", "mode", "tau_s", "Q_mev"]:
        if col not in beta.columns:
            raise RuntimeError(f"Beta table missing required column '{col}'")

    # Ensure logft column exists
    if "logft" not in beta.columns:
        beta["logft"] = np.nan

    # Read candidate sources
    args.logft_dir.mkdir(parents=True, exist_ok=True)
    candidates_raw = _read_csvs(args.logft_dir / "*.csv")
    if candidates_raw.empty and not args.overrides.exists():
        print(f"ERROR: no logft sources found in {args.logft_dir} and no overrides file present.")
        print("Provide one or more CSVs in data/raw/logft/ with columns Z,A,logft (and optionally mode, br_pct).")
        return 2

    candidates = _normalize_candidates(candidates_raw) if not candidates_raw.empty else pd.DataFrame(
        columns=["Z", "A", "logft", "mode", "br_pct", "source"]
    )

    overrides = _normalize_overrides(args.overrides)

    audit_rows: List[Dict[str, object]] = []
    updated = 0
    skipped = 0
    missing = 0

    for i, row in beta.iterrows():
        Z = int(row["Z"])
        A = int(row["A"])
        beta_mode = str(row.get("mode", "")).strip()

        cur = row.get("logft", np.nan)
        has_cur = (pd.notna(cur) and str(cur).strip() != "")

        if has_cur and not args.force:
            skipped += 1
            audit_rows.append({
                "Z": Z, "A": A,
                "logft": float(cur),
                "method": "kept_existing",
                "source": "",
                "beta_mode": beta_mode,
                "cand_mode": "",
                "br_pct_used": "",
                "note": "",
            })
            continue

        logft, prov = choose_logft_for_row(Z, A, beta_mode, candidates, overrides)
        if logft is None:
            missing += 1
            audit_rows.append({
                "Z": Z, "A": A,
                "logft": np.nan,
                "method": prov["method"],
                "source": prov["source"],
                "beta_mode": beta_mode,
                "cand_mode": prov["cand_mode"],
                "br_pct_used": prov["br_pct_used"],
                "note": prov["note"],
            })
            continue

        beta.at[i, "logft"] = float(logft)
        updated += 1
        audit_rows.append({
            "Z": Z, "A": A,
            "logft": float(logft),
            "method": prov["method"],
            "source": prov["source"],
            "beta_mode": beta_mode,
            "cand_mode": prov["cand_mode"],
            "br_pct_used": prov["br_pct_used"],
            "note": prov["note"],
        })

    # Write outputs
    args.beta.parent.mkdir(parents=True, exist_ok=True)
    beta.to_csv(args.beta, index=False)

    args.audit_out.parent.mkdir(parents=True, exist_ok=True)
    audit = pd.DataFrame(audit_rows)
    audit = audit.sort_values(["Z", "A"]).reset_index(drop=True)
    audit.to_csv(args.audit_out, index=False)

    print(f"Wrote: {args.beta}  (updated={updated}, kept_existing={skipped}, missing={missing})")
    print(f"Wrote: {args.audit_out}")

    if args.require_complete:
        still_missing = beta["logft"].isna().sum()
        if still_missing:
            print(f"ERROR: require_complete set but {still_missing} rows still missing logft.")
            return 3

    return 0


if __name__ == "__main__":
    raise SystemExit(main())