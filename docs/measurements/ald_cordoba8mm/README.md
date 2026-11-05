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
Fitted curves behind the boxplots: `out_<wafer>/<n_m|Z0|alpha|S21>_fits.png` (raw thin, fitted thick, 60 GHz dots).
4CA0162: alpha and S21 fits follow the data closely at 60 GHz (S21 model also reproduces the mismatch waviness);
n_m fits within about 0.005 at 60 GHz but miss the 10-30 GHz shape of lines 00 and 04; Re Z0 fits are smooth averages
through the pad ripple (+-1 ohm before, +-4 ohm after ALD), so the 60 GHz Z0 values carry about +-1 ohm.

## Wafer 4CA0163 (`wafer_analysis.py 4CA0163`; `out_4CA0163/`, `out_4CA0163_log.txt`)
All 30 files present (1601 points, 50 ohm, RI). ALD line 04 fails the checks (reciprocity median 4.9 %, max 35 %;
|S21| rises from about -8 dB at 10 GHz to -4.6 dB at 16 GHz; the alpha fit collapses to a constant 7.0 dB/cm): a bad
measurement, flagged, still in the plots. Its noALD measurement is normal.
Medians at 60 GHz, noALD -> ALD, per-line change (all 15 / without line 04):
n_m +0.0375 / +0.0383 (14 of 14 lines up without 04); Re Z0 +0.10 / +0.07 ohm; alpha -0.056 / -0.062 dB/cm
(13 of 14 lines down); |S21| +0.031 / +0.035 dB.
Comparison with 4CA0162: n_m rises by the same amount on both wafers (+0.035 / +0.038); attenuation rises on 4CA0162
(+0.21 dB/cm, 14 of 15 lines) but falls slightly on 4CA0163 (-0.06 dB/cm, 13 of 14 lines).

## Line 04 of 4CA0163 excluded (both states, paired analysis); attenuation sign (`alpha_sign.py`, `alpha_sign.png/.log`)
4CA0163 now uses 14 lines. Raw per-line change of the de-embedded attenuation (1 GHz running median):
* 4CA0162: +0.13 (2 GHz), +0.22..+0.27 dB/cm at 5-50 GHz, every line up; flat in frequency.
* 4CA0163: +0.09..+0.13 dB/cm at 2-20 GHz (every line up), falling to about 0 above 40 GHz, with dips to -0.1/-0.2 at
  42 and 58 GHz that follow the ~8 GHz pad ripple.
So ALD raises the attenuation on both wafers; the size differs (about 2x at 10 GHz). The negative fitted 60 GHz change
on 4CA0163 (-0.06 dB/cm) comes from the top of the band, where the change is within the ripple (fitted change crosses
zero near 45 GHz). Both wafers: |S21| at 1-5 GHz drops after ALD on every line (-0.16 / -0.11 dB); Z0 ripple grows
the same way (0.6 -> 2.3 ohm std), mean |S11| unchanged, n_m +0.036 / +0.038.

## Fit reliability check (`fit_check.py`, `fit_check.log`)
Criteria fixed before computing (wafer agreement is not one): (a) stability = change of the value when the fit stops
at 50 GHz; (b) bias = raw median near the evaluation frequency minus the fit; (c) same behaviour in all four groups.
* alpha, extractor fit (A0): its automatic sign-constrained refit triggers 3/15 (4CA0162 noALD), 6/15 (4CA0162 ALD),
  0/14, 0/14 (4CA0163): the fit does not behave the same way in all groups (fails c). Unconstrained robust
  a sqrt f + b f + c (A1): same model without the branch. At 30-40 GHz both: stability <= 0.022, bias within +-0.02
  dB/cm in every group; at 60 GHz: stability 0.03-0.07, bias -0.06..-0.09 dB/cm in every group. Without the constant
  (A2): bias up to -0.13 and stability up to 0.21 dB/cm: rejected.
* n_m, extractor saturating fit (N0): stability <= 0.002, bias <= 0.004 at 20-60 GHz in every group: reliable at 60 GHz.
* Re Z0 (kept as is): stability 0.07-0.5 ohm; local bias -2.2..+4.2 ohm after ALD at 30-60 GHz (the pad ripple): the
  change in Z0 is not resolved below about 0.5 ohm, and its sign changes with the evaluation frequency.
Follow-up (`fit_check2.py`, `fit_check2.log`): imposing a, b >= 0 on every file is the same as the extractor fit (the
bound is active only where the free fit goes negative: 3, 6, 0, 0 files): still not uniform. The free fit (A1) is the
only variant without a data-dependent branch; it differs from the extractor only at 50-60 GHz on 4CA0162.
Re Z0 as a plain average of the raw curve over whole ripple periods (10.0-42.8 GHz, 4 periods): 42.13 / 41.70 ohm
before ALD; change -0.41 / -0.26 ohm, every line down on both wafers; shifting the band by half a period changes the
change by <= 0.01 ohm, using 3 periods by <= 0.11 ohm.
