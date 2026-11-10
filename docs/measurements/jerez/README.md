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

## Results (2026-11-10)
Scripts (shared with CORDOBA, run from `../ald_cordoba8mm`): `wafer_analysis.py 6JZ0011 ../jerez` (log
`out_6JZ0011_log.txt`, figures and CSVs in `out_6JZ0011/`); `figs_v2.py` and `box_both_medians.py` with
`--base ../jerez --wafers 6JZ0011 --nm 2.22 2.29 0.01 --z0 42 44 0.25` (`out_6JZ0011/v2_*.png`, `v2_box_wafer*.png`,
`box_medians.log`); deck `deck/build_jerez_deck.py` -> `ALD_RF_impact_JEREZ.pptx` (5 slides).
Files renamed on placement to `raw/6JZ0011/6JZ0011_<noALD|ALD>_NN.s2p` (NN = chip). All 30 files pass the checks
(reciprocity median 0.8-1.1 %, passivity <= 0.916); no chip excluded.
Median per-chip change ALD - no ALD (chips up / 15): n_m @ 60 GHz +0.0177 (15/15); Re Z0 10-43 GHz -0.078 ohm (2/15);
alpha @ 30 GHz -0.030 dB/cm (0/15); alpha @ 60 GHz -0.021 dB/cm (5/15); |S21| @ 30 GHz +0.029 dB (15/15); @ 60 GHz
+0.014 dB (9/15). Outlier (3 MAD): no-ALD chip 04 in n_m.
Against CORDOBA: n_m rise about half (+0.018 vs +0.035/+0.038); loss change at 30 GHz of opposite sign.
