# CORDOBA 8 mm slow-wave pair (coworker's run)

`LINEA_8MM_625UM_PITCH_CORDOBA.s4p`: ports 1 A near, 2 A far, 3 B near, 4 B far; lines at y = +/-312.5 um.
Signal 35 um, grounds 49.85 um, gaps 4.15 um, Au 2 um; LN 200 nm / SiO2 4.7 um / Si 525 um (open bottom, so
semi-infinite Si); substrate continuous between the lines, open side boundaries 21 um from the outer ground
edges; T slots recessed into the grounds, period 180 um; about 15 TD cells across the gaps. All open, no symmetry.
Field monitors: E and H volume, 0-60 GHz every 5 GHz.

`analyse.py` -> `results.txt` (side by side with Istanbul 5 mm and std LOW_Z 8 mm).

| | CORDOBA 8 mm | Istanbul 5 mm | std LOW_Z 8 mm |
|---|---|---|---|
| n (30 GHz), n_g (5-50 GHz) | 2.240, 2.227 | 2.108, 2.076 | 1.934, 1.911 |
| Z (30 GHz) | 45 ohm | 66 ohm | 37 ohm |
| n_e - n_o (30-60 GHz) | +0.0001 to +0.0003 | +0.003 to +0.007 (eigenmode CPW 0.0043) | +0.0001 to +0.0004 |
| NEXT / FEXT at 30 GHz | -62.3 / -66.4 dB | -37.2 / -49.6 dB | -69.6 / -69.4 dB |
| NEXT / FEXT group delay vs through | 2.09x / 1.07x | 2.29x / 1.68x | 2.08x / 1.12x |
| A/B asymmetry, end asymmetry | 3e-6, 3e-4 | 8e-5, 3e-4 | 2e-4, 1e-6 |

Through delay 59.4 ps = 8 mm at n_g 2.227: port 2 is at z = 8 mm (the 2.5 in the history's port record is stale).

## Field monitors
`e-field_f<f>_1_<A|B>.txt` (f = 5-60 GHz, port 1; A = y 0.2925-0.3325, B = y -0.3325 to -0.2925, x = 0.001,
z 0-8, step 0.005 mm): loadable in the GUI's "Crosstalk from s4p" window (field monitor folder = this folder).
Wave analysis and exact EO crosstalk: `waves/results.md`.

## Eigenmode cell (one 180 um period, 15 deg, pair-even = magnetic y-symmetry, Ymax electric at 21 um
## beyond the outer ground, Xmin/Xmax open, Au lossy, 2nd order, 1 um tets in the gaps, General (Lossy))
| mode | f (GHz) | n = 69.40 GHz / f | Q total / radiated | gap pattern |
|---|---|---|---|---|
| 1 | 26.2755 | 2.6411 | 15.3 / 18.9 | slot (same direction in both gaps), field toward the side wall |
| 2 | 30.4555 | 2.2786 | 46.1 / 1034 | slot, field toward the symmetry plane |
| 3 | 31.0607 | 2.2342 | 26.5 / 12988 | CPW |
TD at 31 GHz: 2.2395 (fields), 2.240 (s4p equivalent line). Eigenmode CPW within -0.005 (-0.25 %).

Pair-odd (electric y-symmetry), same mesh and settings:
| mode | f (GHz) | n odd | n even | n_e - n_o |
|---|---|---|---|---|
| 1 (slot, wall side) | 27.3534 | 2.5370 | 2.6411 | +0.104 |
| 2 (slot) | 30.4519 | 2.2789 | 2.2786 | -0.000265 |
| 3 (CPW) | 31.0610 | 2.234196 | 2.234219 | +0.0000233 |
CPW split from the eigenmode cell 2.3e-5 against 0.5-1.4e-4 from the TD victim growth (30-35 GHz) and 1.4e-4 from
the s4p equivalent line: the slope test of the two-CPW-mode model fails by a factor 2-6 with the electric side wall.

Magnetic Ymax (same cell, mesh and settings):
| mode | f even / odd (GHz) | n even | n odd | n_e - n_o |
|---|---|---|---|---|
| whole-line (odd only) | - / 22.5502 | - | 3.0774 (Q 8.3) | - |
| slot | 28.6627 / 28.8801 | 2.4211 | 2.4029 | +0.0182 |
| CPW | 31.00808 / 31.00907 | 2.238011 | 2.237939 | +7.2e-5 |
CPW common index: electric 2.2342, magnetic 2.2380, TD 2.2395 (wall shift 0.17 %).
CPW split: electric 2.3e-5, magnetic 7.2e-5; TD victim growth at 30 GHz 0.5-1.0e-4 (full window 0.7e-4):
consistent with the magnetic wall, not with the electric one. Slot modes are wall-controlled (2.28 vs 2.42).

Wide cell (DEV_W 1.210 mm, Ymax 220 um beyond the outer ground), electric Ymax:
| mode | f even / odd (GHz) | n even | n odd | n_e - n_o |
|---|---|---|---|---|
| strips vs wall (even, fictitious) / A vs B (odd) | 22.6460 / 24.6465 | 3.0644 (Q 4.8) | 2.8156 (Q 16.3) | - |
| slot | 28.8896 / 29.0344 | 2.40212 | 2.39014 | +0.0120 |
| CPW | 31.03040 / 31.03079 | 2.236400 | 2.236372 | +2.8e-5 |
Trend narrow electric -> wide electric (fraction of the way to narrow magnetic): CPW common index 58 %, slot even 87 %,
slot odd 90 %, A vs B 52 %, CPW split 2.3e-5 -> 2.8e-5 (11 %). The CPW split does not follow the common indices;
the wide magnetic pair decides whether the open-side split is ~3e-5 (then below the TD victim growth 0.5-1.0e-4).

Wide cell, magnetic Ymax:
| mode | f even / odd (GHz) | n even | n odd | n_e - n_o |
|---|---|---|---|---|
| A vs B (odd) | - / 22.4143 | - | 3.0961 (Q 4.6) | - |
| slot | 28.6662 / 28.8667 | 2.42085 | 2.40403 | +0.0168 |
| CPW | 31.02981 / 31.03028 | 2.236443 | 2.236409 | +3.36e-5 |
Wide cell, electric vs magnetic: CPW common 2.23640 / 2.23644 and CPW split 2.81e-5 / 3.36e-5 (converged:
open-side split ~3.1e-5 +- 0.3e-5 at 31 GHz; the narrow magnetic 7.2e-5 was a wall effect). Slot (2.402 / 2.421,
2.390 / 2.404; split 0.012 / 0.017) and A vs B (2.82 / 3.10) not converged; the magnetic values barely change
with width (slot even 2.4211 -> 2.4208, odd 2.4029 -> 2.4040, A vs B 3.077 -> 3.096).
TD victim growth needs 0.5-1.0e-4 at 30 GHz, 1.6-3.2x the converged CPW split: the CPW pair alone does not
explain it.

2 mm cell (Ymax ~620 um beyond the outer ground), electric Ymax:
| mode | f even / odd (GHz) | n even | n odd | n_e - n_o |
|---|---|---|---|---|
| strips vs wall (even, fictitious) / A vs B (odd) | 20.8768 / 23.5256 | 3.3241 (Q 1.95) | 2.9498 (Q 7.8) | - |
| slot | 28.7485 / 28.9254 | 2.41392 | 2.39915 | +0.0148 |
| CPW | 31.01962 / 31.02002 | 2.237178 | 2.237149 | +2.9e-5 |
