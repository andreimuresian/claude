# Phase sweep, 2 mm cell (Ymax magnetic, 616 um beyond the outer ground), electric Si bottom (525 um)
Same model, mesh and solver settings as `../eigen_w2mm_mag_ebottom` (15 deg, done). Even (XZ magnetic) and odd
(XZ electric) at each phase. Project frequency range raised to 0-80 GHz (the search interval ends at its top).

| phase | frequencies above | modes | expected (constant-n estimate): strips vs bottom, A vs B, slot, CPW (GHz) |
|---|---|---|---|
| 5 deg | 6 GHz | 10 | 7.4, 8.0, 9.6, 10.3 |
| 10 deg | 12 GHz | 10 | 14.8, 15.9, 19.2, 20.7 |
| 20 deg | 24 GHz | 10 | 29.7, 31.8, 38.4, 41.4 |
| 25 deg | 30 GHz | 10 | 37.1, 39.8, 47.9, 51.7 |
| 30 deg | 36 GHz | 10 | 44.5, 47.7, 57.6, 62.1 |

Exports per mode (all modes found): gap pattern (x 0.001, y 0.2925-0.3325, z 0-0.18, step 0.005) and
cross-section (x -0.53..0.1, y 0..1.0, z 0.09, step 0.005); plus the solver log. Folder per run:
`p<phase>_<even|odd>/`. Gap file and cross-section of the same mode may be .txt and .csv (both readable).

## Results from the solver logs (2026-11-03; `summarize_logs.py` -> `summarize_logs.log`, `guided_families.csv`)
All 10 runs converged. Logs pasted in chat, saved as `p*/log_excerpt.txt` (settings + results).
**The search interval still ended at 60 GHz** (log: "(36 GHz, 60 GHz)"), not 80: CPW at 30 deg (~62 GHz)
not found in either symmetry. CPW data stop at 52 GHz; 55 and 60 GHz need extrapolation.

- Guided families continuous over 5-30 deg: strips vs bottom n 3.117-3.135, A vs B 2.897-2.983, slot
  2.40-2.44, CPW 2.269 (10 GHz) -> 2.226 (52 GHz). CPW n_g 2.21-2.22.
- Attenuation from Q (alpha = omega/(2 Q v_g)): CPW 0.12 (10 GHz) -> 0.32 dB/mm (52 GHz); A vs B the
  lossiest, 0.30-0.72 dB/mm.
- CPW even/odd split 0.9-1.3e-5 (dn 2.0-2.8e-5). Velocity-matched estimate of the crosstalk from the CPW
  beat alone, X = dbeta L/4 at L 8 mm: -101 / -95 / -91 / -87 / -84 dB at 10 / 21 / 31 / 42 / 52 GHz,
  against the electric-bottom TD EO -97 / -83 / -72 / -66 / -65 dB: the CPW beat is not the dominant path
  above ~10 GHz.
- Extra low-Q modes (Q 4-15): substrate cell modes. With the TM0 index of 525 um Si on a conductor, the odd
  family keeps a constant lateral wavenumber k_y W/(pi/2) = 1.09-1.20 from 5 to 25 deg (one quarter-wave
  pattern across the cell, tracking TM0); even modes at 1.72 and 1.96. Their frequencies depend on the
  cell width; identification to be checked on the exports.
