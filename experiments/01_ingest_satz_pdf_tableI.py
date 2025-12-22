from __future__ import annotations

from pathlib import Path
import re
import pandas as pd
import pdfplumber

PDF_PATH = Path("data/raw/satz/mathcad-isotopic_mass3.pdf")
OUT_CSV  = Path("data/processed/satz_tableI_isotope_masses.csv")

def to_float(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    # strip weird unicode, commas, percent signs
    s = s.replace("%", "")
    s = re.sub(r"[^\d\.\-\+eE]", "", s)
    try:
        return float(s)
    except Exception:
        return None

def main():
    assert PDF_PATH.exists(), f"Missing PDF: {PDF_PATH}"

    rows = []
    with pdfplumber.open(str(PDF_PATH)) as pdf:
        # Table I starts around PDF page ~12 (0-index 11) and continues for several pages.
        # We scan all pages and keep rows matching the expected 6-column table structure.
        for pno, page in enumerate(pdf.pages):
            tbl = page.extract_table()
            if not tbl:
                continue

            for r in tbl:
                if not r:
                    continue

                # Heuristic: Table I rows have 6 fields like:
                # Element, Z, A, nat_abund_%, G, calc_mass_u (or similar)
                if len(r) < 6:
                    continue

                # Header row begins with "Element"
                if str(r[0]).strip() == "Element":
                    continue

                element = (r[0] or "").strip()
                z = to_float(r[1])
                a = to_float(r[2])
                nat_abund = to_float(r[3])
                g = to_float(r[4])
                mass_calc_u = to_float(r[5])

                # Filter out obvious non-data lines
                if z is None or a is None or mass_calc_u is None:
                    continue
                if z <= 0 or a <= 0:
                    continue

                rows.append({
                    "element": element if element else None,
                    "Z": int(z),
                    "A": int(a),
                    "nat_abund_pct": nat_abund,
                    "G": int(g) if g is not None else None,
                    "mass_calc_u": mass_calc_u,
                    "source_pdf_page_1indexed": pno + 1,
                })

    df = pd.DataFrame(rows)

    # Forward-fill element symbols where blank (continuation lines for same element)
    if not df.empty:
        df["element"] = df["element"].ffill()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    print("PDF:", PDF_PATH)
    print("Wrote:", OUT_CSV)
    print("Rows:", len(df))
    if len(df):
        print(df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()