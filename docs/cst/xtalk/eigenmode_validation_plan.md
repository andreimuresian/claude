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

### Impedance split from the eigenmode fields (run A)
eigenmode/eig_impedance.py: Z = |V|^2/(2P), V = gap voltage on rows inside the
metal, P = Poynting flux of the half domain (99.3 % within |x| <= 40 um).

| row x | Ze/Zo - 1, eigenmode | Ze/Zo - 1, 2-D port modes 5/6 |
|---|---|---|
| 0.5 um | 0.536 % | 0.447 % |
| 1.0 um | 0.540 % | 0.453 % |
| 1.5 um | 0.540 % | 0.440 % |
| 2.0 um (top surface) | - | 0.300 % |

The eigenmode value is consistent across rows; the 2-D modes were not pure
even/odd (line B/A amplitude 1.083 / 0.921) and their ratio assumed equal
power, the eigenmode imposes exact symmetry and integrates P. 14 mm hybrid
model at 30 GHz: NEXT -59.7 / -56.9 / -55.4 dB for 0.30 / 0.45 / 0.54 %;
FEXT unchanged (-48.3 dB). Mesh convergence still to be checked.

### Mesh convergence (run B: refined, 168,416 tets; slab 0.5 um, edge 0.3 um)
Solver 264 s / 275 s, peak memory 20 GB (coarse: 95 s, 6.5 GB).

| | coarse (64.5k) | refined (168k) | change |
|---|---|---|---|
| f even / odd (GHz) | 29.8984 / 29.9212 | 29.9576 / 29.9803 | +0.2 % abs. |
| odd - even | 22.870 MHz | 22.715 MHz | -0.7 % |
| dn | 0.001447 | 0.001432 | -1.0 % |
| Ze/Zo - 1 (rows 0.5/1/1.5 um) | 0.536/0.540/0.540 % | 0.520/0.525/0.541 % | -2.0 % (mean 0.528 %) |

Both splits move < 5 %: the coarse recipe is adequate (<= 10 % budget,
~1 dB on crosstalk). Scaling: time ~ N^1.07, memory ~ N^1.18.

### Impedance definition check (refined fields, eigenmode/eig_z_definitions.py)
| | Z_PV = V^2/2P | Z_VI = V/I | Z_PI = 2P/I^2 | 3-D cascade Zc (gold) |
|---|---|---|---|---|
| even | 45.25 | 41.46 | 37.99 | 36.6 ohm |
| odd | 45.02 | 41.62 | 38.48 | |
| Ze/Zo - 1 | +0.51 % | -0.38 % | -1.27 % | |

P != V I / 2 (by 9 %): mode 3 is not a pure signal-vs-own-ground mode, so the
impedance, and its even/odd split, depend on the definition. Model NEXT at
1 mm / 30 GHz: 0.26 % reproduces CST (-59.6 dB); VI -56.1, PV -53.2, PI -45.4 dB.
Open question before the eigenmode Z can be used.

### Conductor currents of mode 3 (eigenmode/eig_conductor_currents.py, refined)
| | I_g1/I_s (inner) | I_g2/I_s (outer) | net line current / I_s |
|---|---|---|---|
| even | -0.505 | -0.553 | -0.057 |
| odd | -0.552 | -0.545 | -0.097 |

The grounds carry 6-10 % more current than the signal: the excess returns via
the enclosure (even) or the neighbour (odd). Mode 3 is not a pure GSG mode,
hence P != VI/2 and the definition dependence. For a GSG port (V signal-to-
ground, I in the signal) the circuit-consistent impedance is Z_VI.

### Gold + lossy Si (coarse mesh), mode 3
Even: 28.8644 GHz, Q = 18 -> n = 1.9613 (3-D 1.9498 / 1.9486), alpha ~ 2.79 dB/cm
with n_g = 1.91 from 3-D data (3-D 2.90 / 3.02 dB/cm). Solver 131 s, 8 GB.

| | Z_PV | Z_VI | Z_PI |
|---|---|---|---|
| even | 46.20 | 42.53 | 39.15 ohm |
| odd | 45.92 | 42.73 | 39.76 ohm |
| Ze/Zo - 1 gold | +0.61 % | -0.47 % | -1.53 % |
| Ze/Zo - 1 PEC (coarse) | +0.54 % | | |

Net line current / I_s: even -6.6 %, odd -11.2 % (PEC: -5.7 / -9.7 %).
