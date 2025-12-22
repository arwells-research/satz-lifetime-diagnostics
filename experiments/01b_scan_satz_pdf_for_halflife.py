from pathlib import Path
import re
import PyPDF2

PDF_PATH = Path("data/raw/satz/mathcad-isotopic_mass3.pdf")

def main():
    reader = PyPDF2.PdfReader(str(PDF_PATH))
    hits = []
    for i, p in enumerate(reader.pages):
        t = (p.extract_text() or "")
        tl = t.lower()
        if any(k in tl for k in ["half-life", "half life", "average lifetime", "decay constant", "entrained", "neutrino"]):
            hits.append((i+1, t[:500].replace("\n", " ")))
    print("Pages with half-life/lifetime-related text:", [h[0] for h in hits])
    for pno, snippet in hits[:12]:
        print(f"\n--- page {pno} snippet ---\n{snippet}")

if __name__ == "__main__":
    main()