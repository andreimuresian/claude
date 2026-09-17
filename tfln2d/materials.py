"""Material models for the TFLN stack, at RF and at optical frequencies."""

import numpy as np

EPS0 = 8.8541878128e-12
MU0 = 4e-7 * np.pi
C0 = 299792458.0

# --- RF (microwave) relative permittivities -------------------------------
# X-cut LiNbO3: the crystal c-axis lies in the plane of the film, so the
# in-plane permittivity across the gap is the extraordinary one.
LN_RF_EXTRAORDINARY = 28.0
LN_RF_ORDINARY = 43.0

SIO2_RF = 3.9
SI_RF_EPS = 11.7
SI_RF_SIGMA = 2.5e-4      # S/m, lossy silicon substrate
AU_SIGMA = 4.561e7        # S/m


def gold_epsilon(f_hz: float) -> complex:
    """Gold as a lossy dielectric: eps = 1 - j sigma / (omega eps0)."""
    return 1 - 1j * AU_SIGMA / (2 * np.pi * f_hz * EPS0)


def silicon_epsilon(f_hz: float) -> complex:
    return SI_RF_EPS - 1j * SI_RF_SIGMA / (2 * np.pi * f_hz * EPS0)


def surface_resistance(f_hz: float, sigma: float = AU_SIGMA) -> float:
    """Rs = sqrt(pi f mu0 / sigma), in ohm per square."""
    return np.sqrt(np.pi * f_hz * MU0 / sigma)


def skin_depth(f_hz: float, sigma: float = AU_SIGMA) -> float:
    return np.sqrt(2.0 / (2 * np.pi * f_hz * MU0 * sigma))


# --- optical Sellmeier ----------------------------------------------------
def ln_extraordinary(wl_um: float) -> float:
    w2 = wl_um ** 2
    return np.sqrt(1 + 2.9804 * w2 / (w2 - 0.02047)
                   + 0.5981 * w2 / (w2 - 0.0666)
                   + 8.9543 * w2 / (w2 - 416.08))


def ln_ordinary(wl_um: float) -> float:
    w2 = wl_um ** 2
    return np.sqrt(1 + 2.6734 * w2 / (w2 - 0.01764)
                   + 1.229 * w2 / (w2 - 0.05914)
                   + 12.614 * w2 / (w2 - 474.6))


def sio2_index(wl_um: float) -> float:
    w2 = wl_um ** 2
    return np.sqrt(1 + 0.6961663 * w2 / (w2 - 0.0684043 ** 2)
                   + 0.4079426 * w2 / (w2 - 0.1162414 ** 2)
                   + 0.8974794 * w2 / (w2 - 9.896161 ** 2))
