# CORDOBA 8 mm measured lines: effect of the 40 nm Al2O3 (ALD) protection layer
Data: two wafers x 15 fields, one CORDOBA 8 mm line per field, measured before and after ALD (2-port, 40 MHz-60 GHz,
1601 points, RI, 50 ohm). Files in `raw/` (untrusted measurement files, read only).
Method: MZM Studio extractor (`mzm_interconnect.extractor.extract_line_fit`): ABCD -> gamma and Zc, per unit length
with L = 8 mm (pads included in the 2-port: they bias the absolute values the same way before and after ALD).

## Field 3 (`compare_line.py raw/3_no_ALD.s2p raw/3_ALD.s2p field3`; `field3_compare.png`, `field3_compare.log`)
* n_m: +0.045 (+1.9 %), flat over 10-60 GHz (+0.05..+0.09 below 8 GHz).
* Re Z0: band mean (5-50 GHz) 42.82 -> 42.29 ohm (-1.2 %); fitted model -0.8 / -0.4 / -0.25 ohm at 10 / 30 / 50 GHz; point by point the difference oscillates +-3 ohm with an ~8 GHz period
  (= c / (2 n L): the pad/probe mismatch ripple, shifted in frequency because n_m changed); only band averages or the
  smooth fit are meaningful. n_m x Z0 (proportional to the inductance per length, which a dielectric layer does not
  change) rises by +0.7 %: mostly, but not entirely, consistent with ALD adding capacitance only.
* alpha: +0.3..+0.5 dB/cm at 8-35 GHz (+7 %), within the noise above 40 GHz.

## Wafer 4CA0162, 15 lines (`wafer_analysis.py 4CA0162`; figures in `out_4CA0162/`, log `out_4CA0162_log.txt`)
Files: `raw/4CA0162/4CA0162_<noALD|ALD>_NN.s2p` (from `collect_ald_files.py`), all 1601 points, 50 ohm, RI.
Checks: reciprocity |S21-S12|/|S21| median 0.6-1.0 % (max 7-16 % at the noisy top of the band), passivity <= 0.93: all
files pass. Figures: raw curves of all lines per state (`*_all_lines.png`), mean over lines at each frequency with
+-1 std (`*_mean.png`), fitted 60 GHz values per line as boxplots with paired lines (`boxplots_60GHz.png`,
`values_60GHz.csv`). S21 at 60 GHz is synthesised from the fitted line (alpha, n_m, Zc, L = 8 mm) between 50 ohm.
Medians noALD -> ALD at 60 GHz: n_m 2.251 -> 2.290 (+0.035), Re Z0 42.22 -> 42.17 ohm (-0.11), alpha 5.94 -> 6.19
dB/cm (+0.21), |S21| -4.81 -> -5.04 dB (-0.18). Lines 00 and 04: much higher loss in both states (outliers, 3 MAD).
After ALD the Re Z0 ripple (8 GHz period, pad/probe mismatch) grows from about +-1 to +-4 ohm.
