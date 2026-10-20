# ============================================================
# 1. FIXED PHYSICAL & GEOMETRIC PARAMETERS
# ============================================================
wl = 1.310          # um (O band)
wl_m = wl * 1e-6
k0 = 2.0 * np.pi / wl               # 1/um
k0_m = k0 * 1e6                     # 1/m
L_cm = 1.0          # cm
V_bias = 1.0        # V
r33 = 30.8e-12      # m/V
n_guess = 1.90
num_modes_search = 12

# ---- Danube cross-section selectors -------------------------------------------
TEE = False         # False: outside of tee (28 um ground, 2 um gold)
                    # True : inside of tee (ground = 2.0 x 0.5 um stub on the slab)
OE = 0.0            # SiO2 BOX over-etch depth (um) everywhere outside the LN slab
                    # footprint, vertical walls; 0.0 = standard, 0.7 = over-etched

# Geometry Dimensions (um), y = 0 at the BOX / LN interface.  One arm of the
# push-pull GSG modulator: the structure is mirror-symmetric about the signal
# centre, which lies inside the gold, so the right domain edge is placed there.
BOX_H = 4.7
TECN = 0.450
WG_H = 0.225
SLAB_H = TECN - WG_H                # 0.225 um LN slab
WG_TOP = 0.8
ALPHA = 60.0                        # rib sidewall angle (deg)
ALPHA_SLAB = 60.0                   # slab-end sidewall angle (deg): the process value
GAP = 4.15
SIG_W = 10.0                        # full signal width (both arms) -> SIG_W / 2 per arm
GND_W = 28.0                        # outside of tee: ground width
STUB_W = 2.0                        # inside of tee: ground stub width (from the gap edge)
STUB_H = 0.5                        # inside of tee: ground stub thickness (on the slab top)
MTX = 2.0                           # gold thickness (conformal)
MARGIN = 5.0                        # vacuum/BOX beyond the ground (outside of tee) edge
CLAD_H = 15.0                       # air above the slab
CAP_W = 2.0
CAP_H = 1.40
SLAB_W = 10.15                      # LN slab TOP width (bottom wider by 2 SLAB_H / tan(ALPHA_SLAB))

basetta = WG_H / np.tan(np.deg2rad(ALPHA))
WG_BOTTOM = WG_TOP + 2.0 * basetta
SLAB_DX = SLAB_H / np.tan(np.deg2rad(ALPHA_SLAB))
X_R = round(GAP / 2.0 + SIG_W / 2.0, 9)            # right domain edge: signal centre (symmetry plane)
X_L = round(-(GAP / 2.0 + GND_W + MARGIN), 9)      # left domain edge (same for both tee cases)
DEV_W = X_R - X_L
assert CAP_W > WG_BOTTOM and GAP > CAP_W and SLAB_W > GAP, "rib / cap / gap / slab inconsistent"
assert SLAB_W / 2.0 + SLAB_DX < X_R - 0.3, "slab must end under the signal, before the symmetry plane"
SLAB_EXT = (SLAB_W - GAP) / 2.0                    # slab top edge beyond the gap edge (per side)

