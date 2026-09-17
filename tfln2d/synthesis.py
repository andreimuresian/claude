"""Composite synthesis: 2D baseline + lumped periodic penalties -> 3D kinematics.

This is the algebra of the thesis' "Kinematic Synthesis Engine" (the lumped
composite, which beat the distributed one).  The 2D cross-section supplies the
smooth distributed line; the unit cell supplies the discrete reactive step that
the T-stubs add to each period.

    L_2D = Z0_2D * n_m_2D / c0          C_2D = n_m_2D / (Z0_2D * c0)
    L_cell = L_2D * d + dL              C_cell = C_2D * d + dC
    n_m_3D = c0 sqrt(L C)               Z0_3D  = sqrt(L / C)
"""

from dataclasses import dataclass

import numpy as np

C0 = 299792458.0


@dataclass
class Composite:
    n_m_2D: float
    Z0_2D: float
    n_m_3D: float
    Z0_3D: float
    L_2D: float      # H/m
    C_2D: float      # F/m
    L_3D: float      # H/m
    C_3D: float      # F/m
    alpha_2D: float = float("nan")   # dB/cm
    d_alpha: float = 0.0             # dB/cm
    alpha_3D: float = float("nan")   # dB/cm


def synthesize(n_m_2D, Z0_2D, dL, dC, pitch_um=200.0,
               alpha_2D=float("nan"), d_alpha=0.0):
    """Fuse the 2D baseline with the per-cell penalties dL [H], dC [F]."""
    L2 = Z0_2D * n_m_2D / C0
    C2 = n_m_2D / (Z0_2D * C0)

    d = pitch_um * 1e-6
    L3 = (L2 * d + dL) / d
    C3 = (C2 * d + dC) / d

    return Composite(
        n_m_2D=n_m_2D, Z0_2D=Z0_2D,
        n_m_3D=C0 * np.sqrt(L3 * C3), Z0_3D=np.sqrt(L3 / C3),
        L_2D=L2, C_2D=C2, L_3D=L3, C_3D=C3,
        alpha_2D=alpha_2D, d_alpha=d_alpha, alpha_3D=alpha_2D + d_alpha,
    )
