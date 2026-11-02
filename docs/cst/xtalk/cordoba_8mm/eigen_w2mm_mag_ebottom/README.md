# Eigenmode cell, 2 mm (Ymax magnetic, 616 um beyond the outer ground), electric Si bottom (Si 525 um), 15 deg
Same model and settings as `../eigen_w1.2mm_mag_ebottom` except the width. Purpose: convergence of the
strips-vs-bottom index and of the slot split with the wall distance; test of the mode-4 identification
(TM0 substrate wave between the cell walls: predicted at 48.3 GHz, n_z 1.44, in the odd run).

Files to place here: the two solver logs (`log_even.txt`, `log_odd.txt`); for every mode found, the gap
pattern `eig_<even|odd>_mode<k>_e.txt` (x 0.001, y 0.2925-0.3325, z 0-0.18, step 0.005); cross-sections
`eig_<even|odd>_mode<k>_xsec.txt` (x -0.53..0.1, y 0..1.0, z 0.09, step 0.005) only for new or unclear modes.
