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
