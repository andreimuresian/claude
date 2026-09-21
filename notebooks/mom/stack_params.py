"""Physical constants and the layered stack for the TFLN travelling-wave
modulator, at the RF extraction frequency.  Values taken from the CST
`HF Multilayer` history and the COMSOL material cards; kept in one place so
every phase of the MoM translation reads the same numbers.

The metal (all conductors coplanar, on the LiNbO3 top surface) lies in the
plane z = 0.  Above: air.  Below, in order: LiNbO3 film, buried SiO2, silicon
handle, then air.  Thicknesses in metres.
"""
import numpy as np

C0   = 299792458.0
EPS0 = 8.8541878128e-12
MU0  = 4.0e-7 * np.pi

F0 = 60.0e9                        # Hz, the single extraction frequency

# ---- gold (lossy-metal surface impedance, as in the CST history) ----------
SIGMA_AU = 4.561e7                 # S/m
SKIN_AU  = np.sqrt(2.0 / (2 * np.pi * F0 * MU0 * SIGMA_AU))
RS_AU    = 1.0 / (SIGMA_AU * SKIN_AU)          # ohm/square (~72.07 mOhm/sq)

# ---- layer thicknesses (m) ------------------------------------------------
TFLN  = 0.46e-6                    # LiNbO3 thin film   (SLAB_H)
BOX_H = 4.7e-6                     # buried SiO2         (BOX_H)
SI_H  = 550.0e-6                   # silicon handle

# ---- relative permittivities at 60 GHz ------------------------------------
# LiNbO3 is anisotropic (COMSOL diag(28,44,44); CST (43,28,43)).  Phase 1 uses
# the isotropic value that reproduces the substrate TE0 surface wave, 34.7;
# the anisotropic kernel is a Phase 2 refinement and is flagged there.
EPS_AIR  = 1.0
EPS_LN   = 34.7
EPS_SIO2 = 3.9
EPS_SI   = 11.7
SIGMA_SI = 2.5e-4                  # S/m, CST "Silicon (lossy)"

# complex Si permittivity (small loss, pushes the surface-wave pole off axis)
EPS_SI_C = EPS_SI - 1j * SIGMA_SI / (2 * np.pi * F0 * EPS0)


def device_layers(lossy=True):
    """(eps, thickness) for the finite layers below the metal plane, top->down."""
    eps_si = EPS_SI_C if lossy else EPS_SI
    return [(EPS_LN, TFLN), (EPS_SIO2, BOX_H), (eps_si, SI_H)]


# reference TE0 surface-wave index of the lossless stack (validation target)
N_TE0_REF = 2.5414
