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
