# JEREZ measured lines: RF FOM extraction (same method and figures as `../ald_cordoba8mm`)
Files to place in `raw/` (measurement touchstones, read only). Analysis, figures and deck follow the CORDOBA ALD
study: extractor `mzm_interconnect.extractor.extract_line_fit`, FOMs n_m (60 GHz, fit), Re Z0 (band average),
alpha and |S21| (30 and 60 GHz), boxplots with black dots, S11/S21 measured vs fitted line.
Inputs (user, 2026-11-10):
* line length 8 mm (as CORDOBA);
* groups: before (noALD) and after (ALD) the Al2O3 layer;
* wafer 6JZ0011; the same number = the same chip in both states (paired analysis);
* ports: port 1 input, port 2 output (to be checked on the data);
* no known bad lines (candidates flagged from the checks, decided with the user);
* axes: common to both states, chosen for this data (not the CORDOBA ranges);
* outputs: the full CORDOBA set (per-wafer figures, simplified boxplots, medians, deck).
