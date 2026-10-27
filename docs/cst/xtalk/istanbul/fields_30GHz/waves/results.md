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
