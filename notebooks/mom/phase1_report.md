# Phase 1 report -- layered-medium Green's function

Stack: air | LiNbO3 0.46 um (eps 34.7) | SiO2 4.7 um (eps 3.9) | Si 550 um (eps 11.7, sigma 0.00025) | air, at 60 GHz.

**TE0 surface-wave pole: n = 2.54141** (residual 1.6e-14); TM0 pole n = 1.15066.

## Validation gate

| test | what | error | threshold | result |
|---|---|---|---|---|
| V1.1 | free-space limit | 8.41e-14 | 1e-04 | PASS |
| V1.2 | PEC-ground image | 8.66e-08 | 1e-03 | PASS |
| V1.3 | single interface eps=3.9 | 2.62e-04 | 1e-02 | PASS |
| V1.4 | TE0 pole (=2.5414) | 1.00e-05 | 1e-03 | PASS |
| V1.5 | reciprocity / rho-symmetry | 0.00e+00 | 1e-12 | PASS |
| V1.6 | table interpolation | 4.75e-05 | 1e-03 | PASS |

All six PASS. Table: 90 log-spaced rho points (10 nm - 10 mm), built in 17.0 s.

Figure: `phase1_greens.png` -- (a) |G_q|, (b) |G_A|, (c) spectral kernels with the TM and TE surface-wave poles.

G_q at rho=1 um: 1.5309e+15-3.9879e+12j;  at rho=100 um: 1.3120e+13-3.8345e+12j.
