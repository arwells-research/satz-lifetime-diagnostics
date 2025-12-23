# Satz Lifetime Diagnostics — Universal β-Decay Hazard Law

**Author:** A. R. Wells  
**Affiliation:** Dual-Frame Research Group  
**License:** MIT  
**Repository:** `arwells-research/satz-lifetime-diagnostics`  
**Status:** Phase I Complete (Frozen Law) · Phase II Scope Frozen (Structural Residual Mapping)

---

## Overview

This repository establishes and validates a **universal scaling law for β-decay lifetimes** across fission-range nuclides.

The goal of this project is **not** to construct a detailed nuclear-structure model, but to **isolate a minimal, global hazard law** governing decay times, and to clearly separate:

- **Global decay dynamics** (phase space only) Neutron excess enters only as a residual diagnostic variable (G_satz = N − Z) in Phase II.
- **Local structural suppressions** (shells, odd-A effects, configuration hindrance)

All results are obtained using **frozen coefficients**, strict channel awareness, and out-of-sample validation.

See `THEORY.md` for the complete Phase I math definition and feature/schema conventions.
This includes definitions for \( \tau \), \(Q_\mathrm{eff}\), \(G\), \(\log ft\), residuals, and Phase I/II scope.

---

## Phase Structure

This project is intentionally divided into phases to prevent theory creep.

## Phase I — Universal Hazard Law (Frozen) Verification

Phase I establishes a **frozen, channel-aware hazard law** for beta/EC lifetimes using:
- the **dominant transition** (via ENSDF `logft`)
- a **phase-space / relativistic factor** \(G\) computed from \(Q\) and \(Z\)
- strict unit normalization using \(m_e c^2 = 0.511\ \mathrm{MeV}\)

### Phase I Law (Frozen)

We use a factorized form:

\[
\log_{10}\tau = \alpha + \delta\,\log ft - \log_{10} G
\]

where:
- \(\tau\) is the mean lifetime in seconds (`tau_s`)
- \(G\) is the **phase-space / relativistic factor** (dimensionless), computed as:
  \[
  G \approx F(Z)\left(\frac{Q}{0.511}\right)^5,\quad
  F(Z)=\frac{\eta}{1-e^{-\eta}},\quad
  \eta = 2\pi\alpha Z
  \]
- `logft` is the **dominant-branch** ENSDF value (ingested from `data/raw/logft/ensdf_logft.csv`)

Frozen coefficients are stored as a reproducible artifact:

- `data/processed/frozen_law_phase1.json`

### What Phase I Demonstrates

✔ A frozen law can validate stacks outside the fit source once `logft` is channel-correct  
✔ Unit discipline matters: \(Q\) is always interpreted in **electron-mass units** via the \(0.511\) normalization  
✔ Residual outliers are interpretable as **local structure modulators** (shell / configuration effects) rather than global-law failure

### Confirmatory Tests (Phase I)

#### Blind-set channel-aware validation

Run:

    python experiments/10_blind_test_validation.py

This tests a small blind set where \(Q_{\mathrm{eff}}\) is used when the dominant branch feeds an excited state.

#### Frozen validation on an independent vertical stack (Sr)

Run:

    python experiments/11_sr_stack_frozen_validation.py

This script:
- loads the Sr stack from `data/processed/beta_vertical_stacks.csv`
- recomputes \(G\) using the \(0.511\) normalization
- applies the frozen Phase I law
- reports median |residual| and produces `reports/figures/11_sr_validation.png`

Phase I acceptance target:
- median |residual| \(\le 0.35\) dex
- at most 1 outlier above 0.8 dex (stack sizes are small)

### Phase II — Structural Residual Mapping (Frozen Scope)

**Objective:**  
Phase II maps **systematic, structure-dependent deviations** from the frozen Phase I lifetime law.  
It does **not** attempt to improve numerical lifetime predictions.

Instead, Phase II answers:

> *When and why should the universal hazard law be expected to over- or under-predict a lifetime?*

**Key principles:**
- The Phase I law remains **unchanged**
- Residuals are treated as **diagnostics**, not errors
- Structure affects **access to the clock**, not the clock itself

**Primary structural axis (frozen):**
- **Parity class**
  - even–even
  - odd-A
  - odd–odd

**What Phase II does:**
- Maps residuals relative to the frozen law
- Demonstrates that parity-dependent suppression persists after conditioning on:
  - phase space (\(G\))
  - transition class (`log ft`)
- Produces **interpretability**, not correction factors

**Explicitly out of scope for Phase II:**
- Any refitting of \(\alpha\), \(\delta\), or \(G\)
- Structure-dependent lifetime corrections
- Regression or smoothing of residuals
- EC / β⁺ analysis (requires additional data)
- Shell-model or microscopic mechanism claims

Phase II establishes **where the universal law is structurally blocked**, not how to modify it.

---


## Phase I Result: **Frozen Universal Hazard Law**

Phase I concludes with a **factorized, frozen hazard law** for beta and
electron-capture decay mean lifetimes:

\[
\boxed{
\log_{10}\tau = \alpha + \delta\,\log ft - \log_{10} G
}
\]

where the **phase-space (relativistic) factor** is defined as:

\[
\boxed{
G = F(Z)\left(\frac{Q}{0.511}\right)^5,
\qquad
F(Z)=\frac{\eta}{1-e^{-\eta}},\;
\eta=2\pi\alpha_{\mathrm{fs}}Z
}
\]

All apparent dependencies on \(Q\), \(Z\), and relativistic phase space
are **fully absorbed into \(G\)**.

No explicit \(\log Q\), \(Z\), or neutron-excess terms appear in the frozen law.

The coefficients \(\alpha\) and \(\delta\) are **frozen** after Phase I and are
not refit in any subsequent validation or analysis.

### Historical note (provenance only)

Exploratory regressions performed prior to Phase I included explicit
\(\log Q\), \(Z\), and \(N-Z\) terms. These were used **only** to motivate the
factorization into the phase-space hazard \(G\).

After coefficient freezing, all such terms are subsumed by \(G\) and are not
used in Phase I or beyond.

---

## What This Repository Does

✔ Uses **evaluated nuclear data** (ENSDF / NuDat-consistent)  
✔ Enforces **channel-aware Q-values** (effective Q to populated states)  
✔ Freezes all coefficients after Phase I  
✔ Performs **blind predictive tests**  
✔ Separates **global law** from **local structure** via residuals  

🚫 No shell-model fitting  
🚫 No isotope-specific tuning  
🚫 No refitting during validation  
🚫 No structure terms in Phase I

---

## Repository Structure

NOTE: Shown in plain indented format to avoid nested fenced code blocks.

    satz-lifetime-diagnostics/
    ├── pyproject.toml
    ├── LICENSE
    ├── README.md
    ├── THEORY.md
    ├── data/
    │   ├── raw/
    │   │   └── logft/
    │   │       └── ensdf_logft.csv
    │   └── processed/
    │       └── beta_vertical_stacks.csv
    ├── experiments/
    │   ├── 01_ingest_satz_pdf_tableI.py
    │   ├── 05_beta_residual_diagnostics.py
    │   ├── 06_beta_Q_plus_G_diagnostics.py
    │   ├── 07_beta_Q_plus_G_plus_F_diagnostics.py
    │   ├── 08_ingest_logft.py
    │   ├── 09_beta_Q_G_logft_diagnostics.py
    │   ├── 10_blind_test_validation.py
    │   └── 11_sr_stack_frozen_validation.py
    ├── reports/
    │   └── figures/
    │       └── 11_sr_validation.png
    └── tests/
        └── test_ingest_and_merge.py

Generated locally (not committed):

    data/derived/
      residual_tables_*.csv
      validation_plots_*.png

---

## Phase I Validation Summary

### Training / Internal Validation
- Z-stacks: Ca, Ni, Cu, Zn, Rb, Cd, Sn, Te, Xe
- Median |residual| ≈ **0.31–0.34 dex**
- Residual–\(G\) trends can still appear in small or biased slices (e.g. a single Z-stack
  or limited vertical-stack selections), even with frozen \(\log ft\) and \(G\) included.
  Phase II therefore evaluates structural signals using **conditioning** (e.g. parity
  separation within \(\log_{10}G\) bins and within `logft` bins), rather than requiring a
  globally flat residual–\(G\) relationship.

### Blind Tests (Frozen Coefficients)

| Isotope | Regime | Residual (dex) | Interpretation |
|-------|--------|----------------|----------------|
| Cu-72 | Fluid | −0.28 | Bullseye |
| K-44 | Low-Z | +0.74 | Proton-hole regime |
| I-135 | N=82 | +0.93 | Magic-shell blockade |

### Independent Validation

- **Strontium stack (Z=38)**  
  Median |residual| = **0.34 dex**  
  Confirms law holds outside training set

---

## Interpretable Deviations (Not Failures)

Observed large residuals fall into *distinct physical classes*:

- **Magic shells:** N ≈ 82 (Te-132, I-135)
- **Low-Z regime:** Z < 20 (e.g. K-44)
- **Odd-A hindrance:** configuration-specific slowdowns

These effects motivate **Phase II**, whose purpose is to *map and classify* such deviations
without modifying or refitting the Phase I law.

---

## Installation

    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install -U pip
    pip install -e .[dev]

---

## Reproduce Key Results

Run the frozen-law validation:

    python experiments/11_sr_stack_frozen_validation.py

Run blind tests:

    python experiments/10_blind_test_validation.py

---

## License

MIT. See `LICENSE`.

---

## Citation

If you use this repository in research or derivative work, please cite appropriately (software DOI to be added upon archival).

---

## Notes on Scope

This repository is intentionally limited to:

- global hazard law identification
- frozen-coefficient validation
- channel-aware diagnostics

Structure-specific effects are handled in **Phase II as residual classification only**.
Any attempt to produce adjusted or conditioned lifetime predictions would constitute a
separate, future phase and is **explicitly out of scope here**.