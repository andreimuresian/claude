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
