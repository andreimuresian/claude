# Eigenmode validation of the even/odd split: uniform 200 um pitch line

Goal: reproduce the 2-D port-mode split (dn ~ 0.0015, Ze/Zo - 1 ~ 0.30-0.45 %)
with the CST eigenmode solver on one short cell. Only then move to the
slow-wave (T-loaded) cell, which the 2-D port solver cannot handle.

## Model (built from scratch)
- Both lines, full cross-section, uniform along z; cell length p (50-330 um).
  Both end faces must have identical cross-sections (no stray metal pieces).
- Boundaries: z periodic with phase phi; x, y electric (PEC) where the 2-D
  port frame was.
- Symmetry plane YZ exactly midway between the signal centres:
  magnetic (Ht = 0) -> even mode; electric (Et = 0) -> odd mode.
  CST then solves one line plus the wall.
- Materials as in the time-domain model, anisotropic LiNbO3 included
  (check the solver accepts it).
- Solver: eigenmode, ~10 modes, accuracy 1e-6 or tighter, same mesh settings
  for both runs. The quasi-TEM mode is the one near the expected frequency
  with E across the gaps; box modes barely move with phi.

## Phase and expected frequencies
phi (deg) = beta_avg * p * 180/pi, beta_avg = (beta_e + beta_o)/2 from
portmode_betas.txt.

| ref GHz | phi, p = 50 um | phi, p = 330 um | even GHz | odd GHz | odd - even |
|---|---|---|---|---|---|
| 6  | 0.6797 | 4.486  | 5.9976  | 6.0024  | 4.8 MHz  |
| 18 | 2.0393 | 13.459 | 17.9928 | 18.0072 | 14.4 MHz |
| 30 | 3.3991 | 22.434 | 29.9880 | 30.0120 | 24.0 MHz |
| 42 | 4.7591 | 31.410 | 41.9831 | 42.0169 | 33.9 MHz |
| 60 | 6.8000 | 44.880 | 59.9751 | 60.0249 | 49.8 MHz |

Start with 30 GHz only. The even/odd difference is what matters
(8e-4 relative); the absolute frequency may be off by a few 0.1 %.

## Send back (each run)
Quasi-TEM eigenfrequency, run time, field picture, E and H exported on the
mid-cell cross-section plane (as for the 2-D ports) -> Ze/Zo - 1 from
port_voltages_sweep.py, adapted.

## Results

### Run A: 10 um cell, PEC metal, lossless Si, 64,507 tets (coarse)
phi = 0.6798 deg -> beta = 1186.47 1/m. General (Lossy), tet, order 2.
Solver time 95 s (even), 88 s (odd); peak memory 6.6 GB.

| mode set | mode 1 | mode 2 | mode 3 (CPW) |
|---|---|---|---|
| even (XZ magnetic) | 25.7572 | 27.6336 | 29.8984 GHz |
| odd (XZ electric)  | 25.2692 | 27.6308 | 29.9212 GHz |

Modes 1-2: line-vs-frame and slot modes (higher index, more field in Si);
mode 3: CPW pair (field plot confirmed for even).

| | n_even | n_odd | dn |
|---|---|---|---|
| eigenmode (coarse) | 1.89344 | 1.89199 | 0.001447 |
| 2-D port solve, 30 GHz | 1.88781 | 1.88630 | 0.001511 |

dn within 4.2 % of the 2-D reference on the first, coarse mesh;
absolute index 0.3 % higher. Next: refined pair (convergence), then
Ze/Zo from the mode fields.
