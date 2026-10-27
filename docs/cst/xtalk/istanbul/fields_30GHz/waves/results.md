# Wave content of the 5 mm Istanbul line from E and H planes (10, 20, 30, 45, 60, 80 GHz)

Data: E and H at x = 1 um, y -0.40..0.40, z 0..5 mm, step 5 um, port 1 driven (raw files 24 MB
each, not stored). Channels: Ex, Ey, eta0 Hx, eta0 Hy at every y.

## Counting (model-free)
`bloch.py`: one sample per 200 um cell at the same cell position (Bloch-exact: every cell
harmonic of a wave coincides with its fundamental), 10 cell positions, interior 0.3-4.7 mm
(22 cells). Singular values of the stacked Hankel matrices:

| f | singular values | clear waves | residual (all y) |
|---|---|---|---|
| 10 | 1, 0.46, 0.11, 0.031, 0.009, 0.003 | 5 | 0.9 % (5) |
| 20 | 1, 0.80, 0.13, 0.031, 0.008, 0.002 | 5 | 1.2 % (6) |
| 30 | 1, 0.82, 0.23, 0.05, 0.010, 0.003 | 5 | 0.2 % (6) |
| 45 | 1, 0.78, 0.15, 0.09, 0.019, 0.005 | 5 | 1.4 % (6) |
| 60 | 1, 0.61, 0.16, 0.09, 0.05, 0.014, 0.004 | 6 | 3.7 % (8) |
| 80 | 1, 0.42, 0.26, 0.20, 0.14, 0.05, 0.014, 0.004 | 7 | 7.4 % (8) |

The moving cell average used before (`waves.py`) leaves cell harmonics (~ beta Lambda / 2 pi of
their amplitude) and produced a false residual floor in the line footprints (3.7 % at 30 GHz,
12.6 % at 80 GHz); the Bloch sampling removes it.

## Identification: not unique on 5 mm
The decomposition into individual waves is not unique: at 30 GHz, M = 5 and M = 6 fit to 2 % and
0.2 % with different indices; at 10-20 GHz the indices returned (3-11, growth > 100 dB/cm) are
unphysical. Two waves are separable along L only if |n1 - n2| >~ lambda0 / L: 6 at 10 GHz, 2 at
30 GHz, 0.75 at 80 GHz for L = 5 mm, against index differences of 0.3-0.7 here.
Recurring at 30-60 GHz (M = 6): forward n = 2.09-2.22 (strongest, the line mode), forward
n = 2.65-2.80, backward n = 2.3-2.6 and 2.6-2.9; power-flow direction agrees with beta for these.

## Joint 3 mm + 5 mm fit (joint_3mm_5mm.py)
Same cross-section and cells (T positions checked identical, z = 0.065 / 0.140 mod 0.2 mm in both),
same mesh family. Model: shared transverse patterns and gamma, per-length amplitudes; control:
same gamma, separate patterns. 30 GHz, 2740 channels, 13 + 23 cells:

| modes | shared residual | separate residual | distinct index sets within 2 % of best |
|---|---|---|---|
| 2 | 16.6 % | 9.7 % | - |
| 3 | 8.3 % | 2.2 % | 2 |
| 4 | 2.7 % | 0.47 % | 3 |
| 5 | 1.2 % | 0.12 % | >= 5 |
| 6 | 0.45 % | 0.05 % | >= 5 (losses at the 80 dB/cm bound or negative) |

Transverse ranks (1 %): 3 mm 5-7, 5 mm 7-10, combined 10-15 (10-80 GHz), in every region (gaps,
footprints, between, outside). Not a falsification of shared patterns (single lengths under-count
close-index waves), but the fit is not unique: each wave's pattern is a free vector of ~2700 values
against 34 samples along z, so many index sets are absorbed. Conclusion: the fields of the 3 and
5 mm lines do not identify the modes; independent mode information (eigenmode solve of the cell
with open boundaries) is needed.

## Exact EO crosstalk of the 3 mm line (fields_3mm gap columns, 50 ohm, push-pull, n_g 2.27)
| f (GHz) | 3 mm fields | 3 mm s4p Ze=Zo | 5 mm fields | 5 mm s4p Ze=Zo |
|---|---|---|---|---|
| 10 | -67.3 | -59.9 | -58.5 | -56.9 |
| 20 | -55.7 | -51.9 | -54.0 | -54.9 |
| 30 | -54.8 | -55.3 | -56.3 | -52.3 |
| 45 | -47.6 | -46.3 | -44.7 | -51.4 |
| 60 | -42.5 | -41.7 | -38.0 | -42.5 |
| 80 | -40.1 | -38.8 | -47.5 | -35.2 |
