#!/usr/bin/env python3
"""
Refactor helper:
Replace df["G"] -> df["G_satz"] in Python sources.

Use case:
- You are repurposing df["G"] to mean "phase-space / relativistic factor"
- You want the old Satz neutron-excess index to be df["G_satz"]

By default:
- scans experiments/ and src/
- ignores .bak files unless --include-bak is passed
- does a dry-run unless --apply is passed
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Hit:
    path: Path
    count: int


PATTERNS = [
    'df["G"]',
    "df['G']",
]

REPLACEMENTS = {
    'df["G"]': 'df["G_satz"]',
    "df['G']": "df['G_satz']",
}


def iter_targets(root: Path, include_bak: bool) -> list[Path]:
    targets: list[Path] = []
    for base in ["experiments", "src"]:
        d = root / base
        if not d.exists():
            continue
        for p in d.rglob("*.py"):
            if not include_bak and p.name.endswith(".bak"):
                continue
            # Also skip editor swap files, etc.
            if p.name.endswith(".swp") or p.name.endswith(".swo"):
                continue
            targets.append(p)
    return targets


def refactor_file(path: Path) -> tuple[int, str, str]:
    before = path.read_text(encoding="utf-8", errors="replace")
    after = before
    for pat, rep in REPLACEMENTS.items():
        after = after.replace(pat, rep)
    # Count replacements as count of pattern occurrences in original
    count = sum(before.count(pat) for pat in PATTERNS)
    return count, before, after


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="Repo root (default: .)")
    ap.add_argument("--include-bak", action="store_true", help="Also modify *.bak files")
    ap.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    ap.add_argument("--fail-if-any", action="store_true", help="Exit nonzero if any hits found")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    targets = iter_targets(root, include_bak=args.include_bak)

    hits: list[Hit] = []
    for p in targets:
        count, before, after = refactor_file(p)
        if count <= 0:
            continue
        hits.append(Hit(path=p, count=count))
        print(f"[HIT] {p.relative_to(root)}  ({count} occurrences)")
        if args.apply:
            p.write_text(after, encoding="utf-8")

    if not hits:
        print("No df['G'] / df[\"G\"] occurrences found (within scan scope).")
        return 0

    total = sum(h.count for h in hits)
    print(f"\nTotal occurrences: {total}")
    if not args.apply:
        print("Dry-run only. Re-run with --apply to write changes.")

    if args.fail_if_any:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

