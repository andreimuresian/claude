# CORDOBA 8 mm: wave content of the gap fields (port 1, 5-60 GHz)

Files `../e-field_f<f>_1_<A|B>.txt`: x = 1 um, gap columns y = +/-0.2925, +/-0.3325 mm, z 0-8 mm, step 5 um.
Bloch sampling: 36 cell positions x 41 cells of 180 um (z = 0.31-7.69 mm).

## Line A and exact pair sectors (`sector_pencil.py`, log `sector_pencil.log`)
- Forward CPW wave dominates: n = 2.300 (5 GHz) ... 2.239 (30) ... 2.230 (60); s4p equivalent line 2.240 at 30 GHz.
  Spread over model order M = 1-4: +/-0.003 at 30 GHz.
- Slot pattern on A: 0.3 % (5 GHz) to 2.6 % (60 GHz) of the CPW pattern.
- Backward wave n = -2.2 to -2.3, about 4 % (far-end reflection, S11 about -22 dB).
- Residual floor 4-8 %, the same at all frequencies: pole pair q_main e^{+-j1.16} per cell = a fixed
  0.97 mm modulation of the sampled field (mesh/sampling artefact, not a wave).
- Sectors S+ = F1 + mir(F1), S- = F1 - mir(F1) differ only by line B's field (-50 dB below A), so the
  pair split is not visible in a sector-by-sector pencil; it is in line B.

## Line B, the victim (`line_b.py`, log `line_b.log`)
- B CPW pattern -76 dB (5 GHz) to -58 dB (40-60 GHz) re A; B slot pattern -76 to -44 dB (slot > CPW above 25 GHz).
- Dominant: backward wave, n = -2.2 to -2.3, loss about the line loss (NEXT, built at the far end).
- Forward part: z e^{-gamma z} growth (two CPW pair poles unresolved: k0 dn L ~ 1e-3 rad).
- Recurring weak backward component, n = -2.98 (25 GHz), -2.75 (30), -2.61 (35), -2.55 (40), -2.45...-2.50 (45-50),
  7-20 dB/cm, 0.1-0.4 of B (-70 to -80 dB re A); stable over M = 3-6 within 0.01-0.05. Not identified.
- No low-order exponential model represents B fully: residual 10-30 % (M = 4-6).

## Pair split from the victim's forward growth (`split_slope.py`, log `split_slope.log`)
B'_c = (A/2)(-j dbeta z) e^{-gamma z} + launch + backward terms, fitted per Bloch channel.

| f GHz | dn fields: full / first 2/3 / last 2/3 | dn s4p equivalent line |
|---|---|---|
| 5-25 | between -0.0026 and +0.0010, sign changes with window | 0.00002-0.00005 |
| 30 | +0.00007 / +0.00010 / +0.00005 | +0.00014 |
| 35 | +0.00012 / +0.00014 / +0.00013 | +0.00013 |
| 40 | +0.00005 / -0.00014 / +0.00020 | +0.00021 |
| 45 | +0.00024 / +0.00017 / +0.00033 | +0.00027 |
| 50 | +0.00020 / +0.00010 / +0.00030 | +0.00022 |
| 55 | +0.00017 / -0.00009 / +0.00045 | +0.00027 |
| 60 | +0.00032 / +0.00029 / +0.00037 | +0.00026 |

Fit residual on B's CPW pattern 25-40 %; launch term 15-80 % of the growth over L.

## Exact EO crosstalk from the fields (50 ohm source and load, push-pull, n_g 2.27)
| f GHz | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fields | -93.1 | -90.6 | -82.6 | -86.0 | -77.0 | -76.3 | -74.4 | -70.3 | -72.8 | -69.6 | -69.5 | -70.5 |
| s4p Ze = Zo | -96.9 | -88.2 | -85.4 | -76.2 | -75.9 | -70.9 | -67.8 | -67.3 | -64.9 | -66.8 | -64.5 | -63.6 |
| s4p exact terminals | -77.2 | -73.7 | -66.4 | -73.5 | -52.4 | -65.9 | -65.7 | -58.0 | -68.2 | -48.8 | -59.2 | -55.6 |

## CPW two-mode model vs the EO crosstalk (`twomode_eo.py`, log `twomode_eo.log`)
Port-1 fields (50 ohm ports = 50 ohm source and load), interior 0.31-7.69 mm, push-pull (CPW pattern), n_g 2.27.
The two-mode fit leaves 25-40 % of B's CPW pattern unexplained, yet gives the same EO crosstalk to 0.0 dB at
every frequency. This is built in: the light (n_g 2.27) is nearly velocity-matched to the forward CPW wave
(n 2.23-2.30), so the EO integral is the projection of B onto that wave, and a least-squares fit containing
that wave reproduces the projection exactly. A single line therefore cannot validate the model through the EO
crosstalk; it can through the growth slope (dbeta/2 per unit length), which must equal the eigenmode split.
