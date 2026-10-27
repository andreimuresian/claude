# Field planes at 30 and 60 GHz (5 mm, w = 1 mm): EO crosstalk reference and wave content

Export: E at x = 1 um, y -0.40..0.40, z -0.04..5.04, step 5 um, port 1 (A near end) driven.
(Raw export 24 MB, not stored; gap fields in gapV.npz.)

## EO crosstalk from the fields (push-pull, ports 50 ohm as simulated)
| n_g | CST fields | s4p, Ze = Zo | s4p, exact terminals |
|---|---|---|---|
| 2.00 | -57.8 dB | -52.1 dB | -32.6 dB |
| 2.27 | -56.3 dB | -52.3 dB | -33.2 dB |
| 2.40 | -55.0 dB | -52.3 dB | -33.4 dB |

60 GHz (gapV60.npz):

| n_g | CST fields | s4p, Ze = Zo | s4p, exact terminals |
|---|---|---|---|
| 2.00 | -38.1 dB | -42.4 dB | -36.9 dB |
| 2.27 | -38.0 dB | -42.5 dB | -35.9 dB |
| 2.40 | -37.5 dB | -42.2 dB | -35.4 dB |

* 30 GHz: 'exact terminals' overstates by ~23 dB, 'Ze = Zo' by ~4-5 dB.
* 60 GHz: 'Ze = Zo' understates by ~4.5 dB, 'exact terminals' overstates by ~2 dB.
* Neither equivalent line is accurate or conservative across frequency: from the s4p alone the
  EO crosstalk is known to about +-5 dB (Ze = Zo).
* B's common gap field (cancels in push-pull) is 21 % of the differential one at 30 GHz, 46 % at
  60 GHz; a single inner-gap arm sees -51 dB (30 GHz) and -39..-40 dB (60 GHz).
* On B, the common gap field (same in both gaps) is 21 % of the differential one (A: 0.3 %). It
  comes from the extra waves and cancels in push-pull: a single inner-gap arm would see -51 dB.

## Wave content (not final)
Matrix pencil and constrained fits over the plane (mmp.py, sect.py, vp.py): besides the line
modes (n = 2.08-2.10 in the gaps), waves with n ~ 2.4-2.7 travel in both directions, in both the
mirror-even and the mirror-odd parts of the field, dominant outside the gaps and at 10-14 % in
the gaps. Their amplitudes vary along z (fitted 'losses' of -30..+15 dB/cm), so they are not
single clean modes over the plane; an exact count needs more work (end fields and radiation in
the weak region between the lines).

## All exported frequencies (gap_eo.py; gapV_<f>.npz), n_g 2.0 / 2.27 / 2.4, push-pull

| f (GHz) | CST fields | single arm | B common / diff | s4p Ze = Zo | s4p exact |
|---|---|---|---|---|---|
| 10 | -59.3 / -58.5 / -58.2 | -58.1 | 0.10 | -56.9 | -72.3 |
| 20 | -54.9 / -54.0 / -53.3 | -52.8 | 0.20 | -54.9 | -55.4 |
| 30 | -57.8 / -56.3 / -55.0 | -51.0 | 0.21 | -52.3 | -33.2 |
| 45 | -45.0 / -44.7 / -44.1 | -43.5 | 0.29 | -51.4 | -33.3 |
| 60 | -38.1 / -38.0 / -37.5 | -40.5 | 0.46 | -42.5 | -35.9 |
| 80 | -46.7 / -47.5 / -45.5 | -44.1 | 0.99 | -35.2 | -34.0 |

(s4p columns at n_g 2.27.) Ze = Zo minus fields: +1.6, -0.9, +4.0, -6.7, -4.5, +12.3 dB.
Caveat: one point per gap at mid-metal height (x = 1 um); at 80 GHz B's common gap field equals
the differential one, so the one-point estimate of the gap voltage is least reliable there.

## Check of the one-point gap estimate (gap_check_80GHz.py)
80 GHz, line B, one full 200 um cell (z 2.4-2.6 mm), 0.25 um steps across both gaps, at x = 1 um
and at mid-LN depth (x = -0.1375 um).
* Centre point / gap integral (x = 1 um), cell-averaged: inner/outer = 0.972, -2.2 deg.
* LN integral / x = 1 um integral: 0.896 (outer) vs 0.892 (inner): inner/outer 0.996.
* LN centre / x = 1 um centre: 0.953 vs 0.947.
* Effect on the push-pull voltage: (eps/2)|V_common/V_diff| with eps = 0.03 and |V_c/V_d| = 0.58 in
  this cell (0.99 over the line): 0.9-1.5 %, i.e. 0.1 dB. The one-point, x = 1 um estimate of the
  EO crosstalk B/A holds to about 0.1-0.2 dB at 80 GHz; the table above stands.
