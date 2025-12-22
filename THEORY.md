# THEORY — Satz Lifetime Diagnostics

This repository studies beta-decay and electron-capture lifetimes using two
distinct quantities historically referred to as “G” in the literature and 
prior exploratory analyses. These are **not** interchangeable and are kept 
explicitly separate.

---

## Distinct G Definitions

- `G_satz`: **Satz-style neutron-excess index** (structure / composition proxy)

  \[
  G_{\text{satz}} = N - Z
  \]

- `G`: **phase-space / relativistic factor** derived from decay kinematics

  \[
  G \equiv G_{\text{phase}} \approx
  F(Z)\left(\frac{Q}{m_e c^2}\right)^5,
  \qquad m_e c^2 = 0.511\ \mathrm{MeV}
  \]

  with a simple Coulomb correction (Primakoff–Rosen style):

  \[
  F(Z)=\frac{\eta}{1-e^{-\eta}},\quad
  \eta = 2\pi\alpha Z,\quad
  \alpha \approx \frac{1}{137.036}
  \]

These are intentionally separated:

- `G_satz` is a **structural index** derived from nuclear composition
- `G` is a **kinematic / phase-space factor** derived from \(Q\) and \(Z\)

### Historical provenance

The neutron-excess index `G_satz = N − Z` is named after its use in
Satz’s work *Theory of Subatomic and Atomic Masses and Half-Lives*,
which explored systematic regularities in nuclear half-lives.

In the present repository, `G_satz` is retained **only** as a structural
diagnostic variable. It does not appear in the frozen Phase I hazard law,
and is used solely for residual analysis in Phase II.

---

## Phase I — Frozen Universal Hazard Law

Phase I uses a factorized hazard law:

\[
\log_{10}\tau = \alpha + \delta\,\log ft - \log_{10}G
\]

where:
- \(\tau\) is the mean lifetime (seconds)
- \(G\) is the phase-space factor defined above
- `logft` is the ENSDF dominant-branch log ft (channel-aware)
- coefficients \(\alpha,\delta\) are **frozen** after Phase I

Frozen coefficients are stored at:

- `data/processed/frozen_law_phase1.json`

### Interpretation

- \(-\log_{10}G\) captures the dominant phase-space acceleration
- \(\delta\,\log ft\) captures matrix-element / forbiddenness resistance
- residuals encode **structural modulators**
  (shell closures, deformation, configuration effects, branch mismatch)

---

## Data Schema

Primary Phase I working table:

`data/processed/beta_vertical_stacks.csv`

Columns:

- `Z` : proton number
- `A` : mass number
- `N` : neutron number
- `G_satz` : Satz neutron-excess index = `N - Z`
- `mode` : decay mode (e.g. `beta-`, `EC`)
- `half_life_s` : half-life in seconds
- `tau_s` : mean lifetime in seconds (\(\tau = T_{1/2}/\ln 2\))
- `Q_mev` : decay energy (MeV) for the dominant channel
- `logft` : ENSDF dominant branch log ft
- `G` : phase-space factor computed from `Z` and `Q_mev` using the 0.511 normalization

---

## Phase II (Planned) — Mapping Structural Modulators

Phase II applies the frozen Phase I law across the full dataset to map:

\[
\Delta \equiv \log_{10}\tau_{\text{obs}} - \log_{10}\tau_{\text{pred}}
\]

Large coherent regions in \(\Delta\) define “Islands of Structure”:
- shell closures (e.g. near \(N=82\))
- odd-even effects
- deformation regions
- channel-mismatch artifacts (where dominant branch does not match assumed \(Q\))

Phase II **does not refit** the hazard law.
All structure is inferred from residuals against the frozen Phase I baseline.