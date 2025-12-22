import numpy as np
import pandas as pd

# Final frozen coefficients (DO NOT REFIT)
# These define the "Universal Hazard Law" for the Z=20-54 fission regime
A_CONST = -4.9789
B_LOGQ  = -2.7012
C_G     = -0.0168
D_LOGFT = 1.7706

LN2 = np.log(2.0)

def predict_log_tau(Q_eff_mev: float, G: float, logft: float) -> float:
    """
    Predict log10(mean lifetime tau_s) using the Universal Hazard Law.
    
    Parameters:
      Q_eff_mev: The effective endpoint energy for the *dominant channel*.
                 Q_eff = Q_gs - E_level (daughter excitation energy)
    """
    if Q_eff_mev <= 0:
        raise ValueError(f"Q_eff_mev must be > 0, got {Q_eff_mev}")
    
    return A_CONST + (B_LOGQ * np.log10(Q_eff_mev)) + (C_G * G) + (D_LOGFT * logft)

def tau_to_t12(tau_s: float) -> float:
    return tau_s * LN2

def t12_to_tau(t12_s: float) -> float:
    return t12_s / LN2

def get_Q_eff(item: dict) -> float:
    """
    Determines effective Q-value. Prioritizes explicit 'Q_eff_mev'.
    Falls back to 'Q_gs_mev' - 'E_level_mev' if explicit value missing.
    """
    if "Q_eff_mev" in item and item["Q_eff_mev"] is not None:
        return float(item["Q_eff_mev"])
    
    q_gs = float(item.get("Q_gs_mev", 0.0))
    e_level = float(item.get("E_level_mev", 0.0))
    return q_gs - e_level

# Blind Set (CHANNEL-AWARE / PERFECT INPUTS)
test_data = [
    # K-44: Dominant branch goes to Ca-44 2+ (1157 keV).
    # This probes the "Low-Z / Structure" boundary.
    {
        "iso": "K-44",
        "Z": 19,
        "N": 25,
        "G": 6,
        "logft": 5.3,               
        "Q_gs_mev": 5.658,
        "E_level_mev": 1.157,       
        # Q_eff computed dynamically: 5.658 - 1.157 = 4.501
        "actual_t12_s": 1328.0,
        "note": "Low-Z structure test"
    },

    # Cu-72: High-Q, High-G, no shell closures.
    # This probes the "Fluid Fission Fragment" regime (the model's core domain).
    {
        "iso": "Cu-72",
        "Z": 29,
        "N": 43,
        "G": 14,
        "logft": 5.0,               
        "Q_eff_mev": 7.587,         # Audited dominant branch Q_eff
        "actual_t12_s": 6.6,
        "note": "Fluid regime anchor"
    },

    # I-135: Exact N=82 isotone.
    # This probes the "Magic Shell Gate" suppression.
    {
        "iso": "I-135",
        "Z": 53,
        "N": 82,
        "G": 29,
        "logft": 5.4,
        "Q_gs_mev": 2.628,          
        "Q_eff_mev": 1.517,         # Audited dominant branch Q_eff (to excited state)
        "actual_t12_s": 23688.0,
        "note": "N=82 shell suppression test"
    },
]

def main():
    print(f"{'Isotope':<8} | {'Q_eff (MeV)':>11} | {'Pred T1/2 (s)':>14} | {'Actual T1/2 (s)':>15} | {'Residual (dex)':>14}")
    print("-" * 75)

    for item in test_data:
        # 1. Determine Input Physics
        Q_eff = get_Q_eff(item)
        G_val = item["G"]
        logft = item["logft"]
        t12_actual = float(item["actual_t12_s"])

        # 2. Run Model Prediction
        log_tau_pred = predict_log_tau(Q_eff, G_val, logft)
        
        # 3. Convert to Human Units
        tau_pred = 10 ** log_tau_pred
        t12_pred = tau_to_t12(tau_pred)

        # 4. Calculate Residual
        # residual = log10(tau_actual) - log10(tau_pred)
        # (Positive residual = Actual is SLOWER than predicted)
        tau_actual = t12_to_tau(t12_actual)
        residual = np.log10(tau_actual) - log_tau_pred

        print(f"{item['iso']:<8} | {Q_eff:11.3f} | {t12_pred:14.2f} | {t12_actual:15.2f} | {residual:14.4f}")

if __name__ == "__main__":
    main()