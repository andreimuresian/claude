# Layered MoM (exact open boundary, CST's method)

Background: air half-space over LN (28, 43, 43) / SiO2 / Si 550 um / Si half-space, as CST.
Thick metal (the earlier MoM in ../mom used zero-thickness sheets and isotropic LN: its
plain-line n was 2.296 instead of ~1.95).

## Step 1: stack plane-wave response (`stack.py`, `test_stack.py` -> `test_stack.txt`)
4x4 transfer of tangential fields (LN is not uniaxial about the normal, TE/TM couple).
Checks: Fresnel TE/TM, oblique incidence, layers of the same medium, air gap
(R exp(-2 j ky d)), LN static image (1 - sqrt(28*43))/(1 + sqrt(28*43)), sheet source.  All pass.

## Step 2: 2D thick-metal MoM of the plain line (`mom2d.py`, `fw.py`, `run_fw2d.py`)
Surface currents on the metal contours (rooftop J_t, pulse J_z).  Free-space part in the
spatial domain (K0, log singularity analytic); reflected part spectral (all components) with
the LN quasi-static image extracted and added back spatially.  Leaky modes: outgoing
(improper) silicon waves inside the radiation region |kx| < sqrt(eps_Si k0^2 - beta^2).

Statics (`test_static.py` -> `test_static.txt`): C_air 46.91 pF/m (FEM 47.01, grounded box);
C with the stack gives n = 1.951 (2D full-wave FD: 1.952).

Row 49 plain line, PEC (`run_fw2d.txt`, contour mesh 0.2 and 0.1 um):

| GHz | n: MoM / FD / CST | alpha dB/cm: MoM / FD / CST |
|---|---|---|
| 20 | 1.9510 / 1.952 / 1.969 | 0.0074 / 0.009 / 0.000 |
| 60 | 1.9527 / 1.954 / 1.972 | 0.0494 / 0.051 / 0.109 |
| 100 | 1.9634 / 1.959 / 1.972 | 0.1420 / 0.153 / 0.144 |

Mesh refinement moves n by 0.03 %, alpha by < 0.1 %.  40-75 s per frequency.
