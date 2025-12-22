import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json

# --- 1. CONFIGURATION ---
TARGET_Z = 38  # Strontium
STACK_PATH = 'data/processed/beta_vertical_stacks.csv'
REPORT_DIR = 'reports/figures'

FROZEN_PATH = "data/processed/frozen_law_phase1.json"
with open(FROZEN_PATH, "r", encoding="utf-8") as f:
    frozen = json.load(f)

FROZEN_INTERCEPT = float(frozen["alpha"])
FROZEN_SLOPE     = float(frozen["delta"])

# --- 2. HELPER: CORRECTED FERMI APPROXIMATION (Vectorized) ---
def calculate_G_phase_space(z, q_mev):
    """
    Approx phase-space / integrated Fermi-factor proxy:
        G ≈ F(Z) * (Q/m_e)^5
    where F(Z) is a simple Primakoff–Rosen-style Coulomb factor.
    """
    q_rel = q_mev / 0.511
    alpha_fs = 1.0 / 137.036
    eta = 2 * np.pi * alpha_fs * z
    coulomb_factor = eta / (1 - np.exp(-eta))
    return coulomb_factor * (q_rel ** 5)

# --- 3. LOAD & PREPARE ---
print(f"Loading stack from {STACK_PATH}...")
df = pd.read_csv(STACK_PATH)
os.makedirs(REPORT_DIR, exist_ok=True) # Fix FileNotFoundError

# Filter for Strontium
df_sr = df[df['Z'] == TARGET_Z].copy()
print(f"Found {len(df_sr)} isotopes for Z={TARGET_Z} (Sr).")

# Recalculate G for ALL validation rows to ensure unit consistency
# (Even if some existed, we overwrite to ensure the 0.511 normalization is applied)
print("Recalculating G using relativistic units (Q/0.511)^5...")
df_sr["G"] = calculate_G_phase_space(df_sr["Z"], df_sr["Q_mev"])
df_sr["log_g"] = np.log10(df_sr["G"])

# --- 4. APPLY UNIVERSAL HAZARD LAW (FROZEN) ---
# Law: log10(tau) = alpha + beta*logft - log10(G)

df_sr['log_tau_obs'] = np.log10(df_sr['tau_s'])
df_sr['log_g'] = np.log10(df_sr['G'])
df_sr['log_tau_pred'] = (FROZEN_INTERCEPT + FROZEN_SLOPE * df_sr['logft']) - df_sr['log_g']
df_sr['residual'] = df_sr['log_tau_obs'] - df_sr['log_tau_pred']

# --- 5. REPORTING ---
# Use numpy for median to avoid sklearn dependency
median_res = np.median(np.abs(df_sr['residual']))
max_res = df_sr['residual'].abs().max()
corr_g = df_sr['residual'].corr(df_sr['G'])

print("\n" + "="*40)
print(f"  STRONTIUM (Z=38) FROZEN VALIDATION")
print("="*40)
cols = ['A', 'Q_mev', 'logft', 'G', 'log_tau_obs', 'log_tau_pred', 'residual']
print(df_sr[cols].round(4).to_string(index=False))

print("\n--- METRICS ---")
print(f"Median |Residual|: {median_res:.4f} dex")
print(f"Max |Residual|:    {max_res:.4f} dex")
print(f"Corr(Res, G):      {corr_g:.4f}")

# --- 6. ACCEPTANCE ---
PASS_MEDIAN = median_res <= 0.35

OUTLIER_THRESH = 0.8
outlier_count = int((df_sr["residual"].abs() > OUTLIER_THRESH).sum())
PASS_OUTLIERS = outlier_count <= 1

PASS_TREND  = abs(corr_g) < 0.6 if len(df_sr) > 2 else True

print("\n--- RESULTS ---")
print(f"Median <= 0.35?                 [{'YES' if PASS_MEDIAN else 'NO'}]")
print(f"Outliers > {OUTLIER_THRESH}? (<=1)   [{'YES' if PASS_OUTLIERS else 'NO'}]  (count={outlier_count})")
print(f"No G-Trend? (|corr| < 0.6)      [{'YES' if PASS_TREND else 'NO'}]")

if PASS_MEDIAN and PASS_OUTLIERS:
    print("\n✅ PASSED: The Universal Hazard Law holds for Strontium (with <=1 large outlier).")
else:
    print("\n❌ FAILED: Still seeing discrepancies. Check slope coefficients.")

# --- 7. PLOT ---
plt.figure(figsize=(10, 5))
plt.scatter(df_sr['A'], df_sr['residual'], s=100, c='blue', edgecolors='k')
plt.axhline(0, color='black', linewidth=1)
plt.axhline(0.35, color='red', linestyle='--', alpha=0.5, label='Acceptance Bound')
plt.axhline(-0.35, color='red', linestyle='--', alpha=0.5)
plt.xlabel('Mass Number (A)')
plt.ylabel('Residual (dex)')
plt.title(f'Sr (Z=38) Frozen Validation\nMedian |Res| = {median_res:.3f}')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(f'{REPORT_DIR}/11_sr_validation.png')
print(f"Plot saved to {REPORT_DIR}/11_sr_validation.png")