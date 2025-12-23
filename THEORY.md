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

In this repository, `G_satz` is retained solely as a *descriptive structural label*.
It is never used as a predictor, fit variable, or correction term.

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

Note: residual–\(G\) correlation can still appear in small or biased subsets
(e.g. a single Z-stack or a narrow vertical-stack slice), even under the frozen
Phase I law. For Phase II, structural effects are therefore assessed using
**conditioning** (e.g. parity separation within \(\log_{10}G\) bins and within `logft` bins),
not by requiring globally trend-free residuals.

Residuals are diagnostics of structure, not failures of the frozen hazard law.

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

## Phase II — Structural Residual Mapping (Frozen Scope)

Phase II applies the frozen Phase I law to compute diagnostic residuals:

\[
\Delta_{\text{struct}} \equiv
\log_{10}\tau_{\text{obs}} - \log_{10}\tau_{\text{Phase I}}
\]

The purpose of Phase II is **not** to improve numerical lifetime predictions.
Its purpose is to identify **systematic, structure-dependent suppression**
relative to the universal hazard law.

### Interpretation of Phase II residuals

- \(\Delta_{\text{struct}} > 0\): structure *blocks or delays* access to the decay clock  
- \(\Delta_{\text{struct}} < 0\): structure *enhances or unblocks* decay pathways  
- \(\Delta_{\text{struct}} \approx 0\): decay proceeds at the universal rate

Residual coherence indicates **structural classes**, not correction terms.

### Frozen Phase II scope

- Decay mode: **β⁻ only** (EC / β⁺ require additional data)
- Primary structural axis: **parity class**
  - even–even
  - odd-A
  - odd–odd
- Conditioning variables:
  - phase space (\(G\))
  - transition class (`log ft`)

Phase II demonstrates that parity-dependent suppression persists
even when phase space and forbiddenness are held fixed.

### Explicit exclusions

Phase II does **not**:
- refit \(\alpha\), \(\delta\), or \(G\)
- introduce structure-dependent correction factors
- perform regressions on \(Z\), \(N\), or \(N-Z\)
- claim microscopic mechanisms
- produce adjusted lifetime predictions

Any attempt to condition or correct lifetimes numerically would constitute
a **separate future phase**, not an extension of Phase II.