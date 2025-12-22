#!/usr/bin/env python3
"""
Rename neutron-excess G -> G_satz in code.

Replaces:
  df["G"]  -> df["G_satz"]
  df.G     -> df.G_satz

Creates .bak backups for all modified files.
"""

from pathlib import Path
import re

ROOTS = [
    Path("experiments"),
    Path("src"),
]

PATTERNS = [
    (re.compile(r'df\["G"\]'), 'df["G_satz"]'),
    (re.compile(r"\bdf\.G\b"), 'df.G_satz'),
]

def process_file(path: Path) -> bool:
    text = path.read_text()
    original = text

    for pat, repl in PATTERNS:
        text = pat.sub(repl, text)

    if text != original:
        backup = path.with_suffix(path.suffix + ".bak")
        backup.write_text(original)
        path.write_text(text)
        return True

    return False

def main():
    modified = []

    for root in ROOTS:
        for path in root.rglob("*.py"):
            if path.name.endswith(".bak"):
                continue
            if process_file(path):
                modified.append(path)

    print("\n=== G → G_satz migration report ===")
    if not modified:
        print("No files modified.")
        return

    for p in modified:
        print(f"UPDATED: {p}")
    print(f"\nTotal files modified: {len(modified)}")
    print("Backups written with .bak extension.")

if __name__ == "__main__":
    main()
