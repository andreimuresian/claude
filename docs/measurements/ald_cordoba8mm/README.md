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
