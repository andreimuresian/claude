# Eigenmode cell, 2 mm (Ymax magnetic, 616 um beyond the outer ground), electric Si bottom (Si 525 um), 15 deg
Same model and settings as `../eigen_w1.2mm_mag_ebottom` except the width. Purpose: convergence of the
strips-vs-bottom index and of the slot split with the wall distance; test of the mode-4 identification
(TM0 substrate wave between the cell walls: predicted at 48.3 GHz, n_z 1.44, in the odd run).

Files to place here: the two solver logs (`log_even.txt`, `log_odd.txt`); for every mode found, the gap
pattern `eig_<even|odd>_mode<k>_e.txt` (x 0.001, y 0.2925-0.3325, z 0-0.18, step 0.005); cross-sections
`eig_<even|odd>_mode<k>_xsec.txt` (x -0.53..0.1, y 0..1.0, z 0.09, step 0.005) only for new or unclear modes.

## Even run (XZ magnetic), 15 deg, 4 modes in 15-60 GHz
| mode | f (GHz) | n | Q | 1.2 mm cell |
|---|---|---|---|---|
| 1 strips vs bottom | 22.2636 | 3.1170 | 38.3 | 3.1926, Q 172.8 |
| 2 slot | 28.7474 | 2.4140 | 30.3 | 2.4196, Q 29.9 |
| 3 CPW | 31.0442 | 2.2354 | 26.3 | 2.2360, Q 26.3 |
| 4 (not exported) | 57.6845 | 1.2030 | 6.1 | - |
Strips vs bottom: index -2.4 %, Q / 4.5, gap pattern CPW/slot 6.2 -> 0.70: not converged at 221 um; the
2 mm cell (616 um) matches the lateral extent of the widened TD model (625 um). Cross-sections exported
only to y = 0.6 mm. Mode 4: substrate (TM0) wave between the cell walls is the likely origin; half-wave
estimate 62.0 GHz against 57.7 found (the odd 1.2 mm quarter-wave estimate matched to 0.1 %): not confirmed.

Mode 4 even (exported): 89 % of the energy in the Si (63 % deeper than 100 um), 9 % in the air above, 57 %
beyond the outer ground within the exported 0.6 mm; |E|^2 nearly constant from 2.6 to 97 um above the
surface (decay length in air 1/(k0 sqrt(n^2-1)) = 1.2 mm at n 1.20); gap pattern CPW/slot 0.17, CPW per
unit energy 2.1e-3 (CPW mode 0.30). A substrate wave of the Si on the bottom conductor, partly in the air.
30 GHz test (`../../cordoba_8mm_wide_ebottom/scan_low_index.py`): adding it with its own pattern and any
n 1.0-2.3 lowers B's CPW residual only 0.168 -> 0.160, with no preferred index: not detectable in the
30 GHz gap fields. Not tested yet at 45-60 GHz, where the TM0 index reaches the CPW index.

## Odd run (XZ electric), 15 deg, 5 modes in 15-60 GHz
| mode | f (GHz) | n | Q | 1.2 mm cell |
|---|---|---|---|---|
| 1 A vs B | 23.8568 | 2.9089 | 13.6 | 2.9824, Q 9.5 |
| 2 slot | 28.9257 | 2.3991 | 34.2 | 2.4032, Q 33.9 |
| 3 CPW | 31.0445 | 2.2354 | 26.3 | 2.2360, Q 26.3 |
| 4 substrate wave, quarter wave across the cell | 49.4865 | 1.4023 | 5.2 | 56.74 GHz, n 1.223 |
| 5 substrate wave (outer region) | 58.6331 | 1.1836 | 5.3 | - |
CPW split 2.33e-5 (1.2 mm: 2.5e-5); slot split 0.0149 (1.2 mm: 0.0164).
Mode 4: predicted 48.3 GHz (n 1.44) from the TM0 wave of the Si on the bottom conductor with a quarter wave
between the electric symmetry plane and the magnetic wall at 1.0 mm; found 49.5 GHz (n 1.40): identification
confirmed (1.2 mm: 56.8 predicted, 56.74 found). Modes 4, 5 (odd) and 4 (even): 89-94 % of the energy in the
Si; their count grows with the cell width because more lateral standing-wave patterns fit below 60 GHz.
Cross-sections again only to y = 0.6 mm.
