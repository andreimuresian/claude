"""Physical constants and the layered stack for the TFLN travelling-wave
modulator, at the RF extraction frequency.  Values taken from the CST
`HF Multilayer` history and the COMSOL material cards; kept in one place so
every phase of the MoM translation reads the same numbers.

The metal (all conductors coplanar) lies in the plane z = 0.  Above: air.
Below, in order: LiNbO3 film (at its *etched* thickness, see below), buried
SiO2, silicon handle, then air.  Thicknesses in metres.

LiNbO3 thickness -- the etched slab, not the full film
------------------------------------------------------
The rib etch removes LiNbO3 down to a slab of thickness  t_LN = TFLN - ETCH,
and the RF electrodes sit on that etched slab (the ~0.8 um optical rib is a
negligible-width feature on the RF scale).  CST's own `HF Multilayer`
background is defined as  vacuum / LN SLAB_H / SiO2 BOX_H / Si 550 um  with
SLAB_H = 0.460 um - wg_h, i.e. the etched thickness -- so the layered kernel
must use  t_LN = TFLN - ETCH_DEPTH , which VARIES across the dataset
(ETCH_DEPTH in [0.10, 0.36] um  ->  t_LN in [0.10, 0.36] um).

`device_layers(t_LN=...)` is therefore parametrised by LN thickness.  The
default is the dataset-median etched slab, SLAB_REF.  Phase 1 quantifies the
sensitivity of the kernel to t_LN (gate V1.7): G_A is insensitive (<0.1 %),
G_q is sensitive at short range (~36 % at rho=1 um, ~4 % at 10 um), so Phase 2
must build/interpolate the kernel at the per-geometry t_LN for the near-field
(capacitive) terms.  The integrated line parameters are nonetheless weakly
sensitive to ETCH_DEPTH (empirical |r| < 0.07 with n_m, z0 over the 500 rows),
because they are dominated by the electrode geometry, not the thin LN skin.
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
TFLN   = 0.46e-6                   # total LiNbO3 film thickness (process const)
ETCH_MEDIAN = 0.235e-6            # dataset-median rib-etch depth (fixture value)
SLAB_REF = TFLN - ETCH_MEDIAN     # ~0.225 um: representative etched LN slab
BOX_H  = 4.7e-6                    # buried SiO2         (BOX_H)
SI_H   = 550.0e-6                  # silicon handle

# ---- relative permittivities at 60 GHz ------------------------------------
# LiNbO3 is anisotropic (COMSOL diag(28,44,44); CST (43,28,43)).  Phase 1 uses
# the isotropic geometric-mean proxy  EPS_LN = sqrt(28*43) ~ 34.7.  NOTE: this
# is NOT pinned by the TE0 surface-wave pole -- that pole is Si-slab dominated
# and shifts only 2.540 -> 2.542 as EPS_LN goes 28 -> 43.  Anisotropy is a
# Phase-2 VALIDATION RISK (it changes the local permittivity under the metal by
# ~+/-20 %): if Phase 2's delta_alpha misses alpha_delta_val by ~10-20 %, the
# anisotropic-LN kernel is the first thing to check.
EPS_AIR  = 1.0
EPS_LN   = 34.7
EPS_SIO2 = 3.9
EPS_SI   = 11.7
SIGMA_SI = 2.5e-4                  # S/m, CST "Silicon (lossy)"

# complex Si permittivity (small loss, pushes the surface-wave pole off axis)
EPS_SI_C = EPS_SI - 1j * SIGMA_SI / (2 * np.pi * F0 * EPS0)


def device_layers(t_LN=SLAB_REF, lossy=True):
    """(eps, thickness) for the finite layers below the metal plane, top->down.

    t_LN : etched LiNbO3 slab thickness (m).  Defaults to the dataset-median
    etched slab SLAB_REF; pass TFLN - ETCH_DEPTH for a specific geometry.
    """
    eps_si = EPS_SI_C if lossy else EPS_SI
    return [(EPS_LN, float(t_LN)), (EPS_SIO2, BOX_H), (eps_si, SI_H)]


# reference TE0 surface-wave index (validation target, from the earlier
# validated 2D baseline work); Si-slab dominated, insensitive to the LN detail
N_TE0_REF = 2.5414
