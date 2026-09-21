# Phase 1 report -- layered-medium Green's function

Method: a surface-integral-equation kernel with unknowns only on the metal surface (Phase 2); the metal's finite conductivity enters as a surface-impedance BC, and the layered substrate is folded *exactly* into the Green's function -- nothing is averaged or treated volumetrically.

Table stack: air | LiNbO3 0.225 um etched slab (= 0.46 um film - 0.235 um median etch; eps 34.7) | SiO2 4.7 um (eps 3.9) | Si 550 um (eps 11.7, sigma 0.00025) | air, at 60 GHz.  device_layers(t_LN) is parametrised: the etched thickness t_LN = 0.46 um - ETCH_DEPTH varies across the dataset ([0.10, 0.36] um), and CST's own HF Multilayer background uses this etched SLAB_H, not the full film.

**TE0 surface-wave pole (unetched film): n = 2.54141** (ref 2.5414, residual 6.4e-05); TM0 (unetched) n = 3.31373.  Table stack (t_LN = 0.225 um): TE0 2.54019, TM0 3.30963.

## Validation gate

| test | what | error | threshold | result |
|---|---|---|---|---|
| V1.1 | free-space limit | 8.41e-14 | 1e-04 | PASS |
| V1.2 | PEC-ground image | 8.66e-08 | 1e-03 | PASS |
| V1.3 | single interface eps=3.9 | 2.62e-04 | 1e-02 | PASS |
| V1.4 | TE0 pole, unetched (=2.5414) | 1.00e-05 | 1e-03 | PASS |
| V1.5 | independent-integrator xcheck | 1.27e-13 | 1e-06 | PASS |
| V1.6 | table interp (self-consist.) | 4.72e-05 | 1e-03 | PASS |

V1.1-V1.6 all PASS. Table: 90 log-spaced rho points (10 nm - 10 mm), built in 15.7 s.

**What each gate proves (honest).** V1.1-V1.4 are the independent physics checks (free-space Sommerfeld identity, PEC image, static two-dielectric image, and the known unetched TE0 surface wave). V1.5 is a numerical cross-check of the production integrator against an independent tail-summation method (not a new physics limit). V1.6 is interpolation self-consistency of the saved table -- it confirms the sampling, not the physics.

## V1.7 -- LN-thickness sensitivity (informational)

G at the etched-slab extremes t_LN = 0.10 vs 0.36 um:

| rho | |dGq|/|Gq| | |dGA|/|GA| |
|---|---|---|
| 1 um | 3.63e-01 | 3.15e-05 |
| 10 um | 3.74e-02 | 1.98e-04 |
| 100 um | 7.42e-03 | 8.46e-04 |

G_A is insensitive to the LN slab thickness (< 0.1 %); G_q is strongly sensitive at short range (~36 % at 1 um, ~4 % at 10 um, < 1 % at 100 um).  Consequence for Phase 2: the near-field (capacitive) MoM terms must use the per-geometry t_LN = 0.46 um - ETCH_DEPTH (build or interpolate the kernel per row); the far-field and all of G_A are effectively thickness-independent.  Note the *integrated* line parameters are only weakly sensitive to ETCH_DEPTH (empirical |r| < 0.07 with n_m, z0 over the 500 rows) because they are dominated by the electrode geometry -- but that downstream cancellation is not a licence to build the kernel at the wrong t_LN.

## Known approximation carried into Phase 2 (validation risk)

LiNbO3 is modelled isotropically with the geometric-mean proxy eps = sqrt(28*43) ~ 34.7.  This is NOT pinned by the TE0 pole (that pole is Si-slab dominated and shifts only 2.540 -> 2.542 as eps_LN goes 28 -> 43).  CST uses anisotropic LN (43, 28, 43), which changes the local permittivity under the metal by ~+/-20 %.  If Phase 2's delta_alpha misses alpha_delta_val by ~10-20 %, the anisotropic-LN kernel is the first thing to check.

Figure: `phase1_greens.png` -- (a) |G_q|, (b) |G_A|, (c) lossy spectral kernels with both surface-wave poles (each a peak).

G_q at rho=1 um: 2.0943e+15-3.9542e+12j;  at rho=100 um: 1.3035e+13-3.8027e+12j.
