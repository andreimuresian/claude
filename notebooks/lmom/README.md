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

## Step 3a: periodic cell, plain line (`cell3d.py`, `run_cell3d_plain.py` -> `run_cell3d_plain.txt`)

One 200 um period, Bloch-periodic currents, no ports.  The 3D matrix is a sum over Floquet
harmonics k_m = beta + 2 pi m / P of the validated 2D kernel (Line2D.Z at beta = k_m), weighted
by the z-spectra of the basis functions (J_t: contour rooftop x z pulse; J_z: segment pulse x
z rooftop).  Same stack, same leaky-branch handling, same LN image extraction as step 2; no
Ewald split, so the surface-wave poles that broke ../mom Phase 3 do not enter.  beta by the
complex secant on the Bloch eigenproblem.  Harmonics |m| > 1 are computed once and reused
across secant steps (checked: identical to 6 digits).

Plain cell must reproduce the 2D mode (row 49, PEC, same contour mesh):

| GHz | 2D n / alpha | 3D, Nz 8: n err / alpha err | 3D, Nz 16 (60 GHz) |
|---|---|---|---|
| 20 | 1.94916 / 0.00737 | -0.0003 % / 0.00 % | |
| 60 | 1.95086 / 0.04948 | -0.0029 % / 0.00 % | -0.0003 % / 0.00 % |
| 100 | 1.96156 / 0.14222 | -0.0082 % / +0.01 % | |

Error falls ~ h^2.5-3 with the z cell size h = P/Nz; harmonic range M = 2 Nz is converged.
~2 min per frequency at Nz 8.  Limitation of this test: with uniform 25 um z cells it does not
exercise the large harmonics (|k_z| up to ~1e7) that the tee's fine z mesh at the slot ends
will need; that is checked in step 3b.
