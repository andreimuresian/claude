# Even / odd sector test (3, 5, 8.75 mm)

`sector_fit.py`. Each sector 2-port (end-symmetrised) fitted, per frequency, with ONE uniform
mode between two identical mirrored reciprocal end junctions: 4 complex unknowns, 6 complex data
(3 lengths). Residual = max |S_model - S_file| over the three lengths.

| | median residual 2-60 GHz | peak | n at 30 GHz |
|---|---|---|---|
| even | 0.0052 (-46 dB) | 0.0097 | 2.106 |
| odd | 0.0159 (-36 dB) | 0.0344 (22-26 and 42-48 GHz) | 2.090 |

* The even residual is the floor (it includes the mesh-family difference between the 8.75 mm
  and the 3 / 5 mm runs, which affects both sectors alike).
* The odd sector is 3x above that floor, and its misfit is as large as NEXT itself
  (|S31| = 0.014 at 30 GHz, 5 mm). It oscillates in frequency, as a second mode with a
  different index would make it.
* So the content that a one-mode-per-sector (two-mode pair) model cannot carry sits in the odd
  sector only: consistent with a mode that has line A against line B.

Uniform 200 um pitch line, same port type (lumped ports + PEC bars): NEXT group delay
1.09 x through at 1 mm, 1.62 x at 5 mm (Istanbul 5 mm: 2.26 x); NEXT at 30 GHz, 5 mm:
-52.5 dB (Istanbul -37.1 dB). A far-end return is present there too, ~15 dB weaker.

## Two-wave fit of the odd sector

### Per-frequency fits: not decisive (kept for the record)
* `two_wave_fit.py`: lossless 3-port junctions, n_x scanned. Best at n_x 2.6-2.7 (median 0.0105
  vs 0.016 for one mode with a general junction), broad minimum.
* Control (`control_even.py`): the same model on the even sector, where the wave cannot exist,
  improves just as much (0.024 -> 0.008) for any n_x. The lossless constraint is wrong for these
  ends and the second mode acts as a loss channel. Discarded.
* `smooth_fit.py` (lossy junctions as cubic polynomials in f, global fit): the even control again
  improves for any n_x, with unphysical |rho_x| > 1 at some n_x; the odd one-mode global fit
  (0.041) did not even reach the per-frequency result (0.016), i.e. the optimiser does not
  converge reliably. Stopped. With three lengths from two mesh families, a fitted junction
  model has enough freedom to absorb the second wave or to fake it.

### Echo (path delay) decomposition of NEXT: decisive
`delays.py`: matrix pencil on S31(f) of each length gives a few echoes with travel times tau_k.
Fitting tau vs L across 3, 5, 8.75 mm gives, per path, the sum of the group indices of the way
out and the way back; the port regions only add an offset. Stable over bands 5-60, 10-50,
5-70 GHz and orders 6, 8 (band 5-60 GHz, M = 6 shown):

| L (mm) | echo 1 | echo 2 (strongest) | echo 3 |
|---|---|---|---|
| 3 | 39.1 ps, -53.9 dB | 47.5 ps, -46.3 dB | 55.7 ps, -51.3 dB |
| 5 | 66.1 ps, -49.6 dB | 76.7 ps, -41.3 dB | 89.0 ps, -46.1 dB |
| 8.75 | 121.5 ps, -42.0 dB | 132.9 ps, -36.1 dB | 147.1 ps, -43.3 dB |
| n_out + n_back | 4.31-4.37 | 4.46-4.59 | 4.74-4.80 |

Through path (S21): n_g = 2.06. With the extra wave at n_x:
* echo 1: CPW out, CPW back (2 x 2.06 = 4.13; measured 4.3);
* echo 3: wave x out, wave x back: n_x = 4.75 / 2 = 2.38;
* echo 2: CPW out, wave x back (or the reverse): 2.06 + 2.38 = 4.44; measured 4.46-4.59.
Two independent paths give the same n_x = 2.37-2.40, matching the field decomposition (2.39) and
the earlier group-delay estimate (~2.4). The mixed path dominates NEXT at every length.
