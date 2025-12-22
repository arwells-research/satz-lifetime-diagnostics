"""
Phase-space and relativistic factors for decay modeling.

This module is the single source of truth for phase-space G definitions.
Do not inline these formulas elsewhere.
"""

import numpy as np

ELECTRON_MASS_MEV = 0.511


def compute_G_phase_space(Q_mev: float) -> float:
    """
    Compute the relativistic phase-space factor:

        G = (Q / m_e)^5

    Parameters
    ----------
    Q_mev : float
        Decay Q-value in MeV.

    Returns
    -------
    float
        Dimensionless phase-space factor.
    """
    return (Q_mev / ELECTRON_MASS_MEV) ** 5