# Widened CORDOBA, electric Si bottom, accuracy -40 dB, dense field monitors
Same model as `../cordoba_8mm_wide_ebottom` (-27 dB) and `../cordoba_8mm_wide_ebottom_60dB` (stopped at -44.5 dB),
one port excited. Solver: steady-state criterion met at -40 dB (6,015,354 of 14,746,216 time steps, 8.16 pulse widths,
about 0.48 ns), OpenCL GPU solver (Quadro RTX 6000), total 11 h 56 min, finished 2026-11-05 05:58.
Field monitors: 60 E-field monitors f = 1..60 GHz (1 GHz steps), subvolume x 0..0.002, y -0.34..0.34, z 0..8 mm.

Files to place here:
* zip of the line A exports (template prefix `A_`): x 0.001, y 0.2925..0.3325, z 0..8, step 0.005, 60 frequencies;
* zip of the line B exports (prefix `B_`): x 0.001, y -0.3325..-0.2925, z 0..8, step 0.005, 60 frequencies;
* the s4p of this run;
* the end of the solver log (txt).
The zips are kept in git; they are unpacked locally for the scripts (unpacked folders not committed).

## First results (2026-11-05)
Exports: two zips (A: txt; B: CST CSV), 60 frequencies each plus the full-volume reference monitors at 5 and 10 GHz;
grids checked (1 x 9 x 1601, x 0.001, both gap columns live); unpacked to `unpacked/` and `unpacked_fullvol/`
(txt layout, not committed).
* `dense_overview.py`: subvolume and full-volume monitors identical at 5 and 10 GHz (difference 0). Convergence, B CPW
  pattern, |B(-44.5) - B(-40)| / |B(-44.5)|: 1.47, 1.23, 0.38 at 5, 10, 15 GHz; 0.05-0.23 at 20-60 GHz. Ratio
  |B40-B27| / |B45-B40| 5.6-8.5 at 20-60 GHz (5.1 expected if the error scales with the tail amplitude), 1.1-2.7 at
  5-15 GHz. EO -40 vs -44.5 dB: within 0.6 dB at 20-60 GHz except 25 GHz (1.8 dB); 1.2, 2.3, 0.8 dB at 5, 10, 15 GHz.
  Dense EO curve `dense_eo.png`, `dense_eo.csv`.
* `dense_modefit.py` (six modes at 60 frequencies): A CPW 0.005-0.047; B CPW 0.04-0.15 at 7-30 GHz, rising steadily
  to 0.45 at 49 GHz and ~1.0 at 58-60 GHz; poor below 7 GHz (dispersion extrapolated). With 1 GHz steps the B-side
  coefficient phases are continuous above ~20 GHz. Forward B coefficients (CPW, strips-bottom, A vs B, slot) carry a
  group delay of ~140-150 ps at 5-35 GHz (slot at all f), i.e. the round trip CPW out (n 2.23) + strips-bottom back
  (n 3.12: 143 ps) or A vs B back (n 2.90: 137 ps); above ~35 GHz their delay drops to ~0 (direct launch dominates).
  Backward B coefficients: delay 7-17 ps, phase within 4-18 deg of a straight line at 20-50 GHz. The magnitudes dip
  every ~7 GHz: beat of a direct and a round-trip contribution (1/143 ps = 7.0 GHz), the period of the EO ripple.

## End-scattering model on the dense data (`dense_endmodel.py`, `dense_endmodel.log`)
Band 20-40 GHz (21 frequencies). Pre-registered tests: A = train every 2 GHz, predict the odd GHz, success if median EO
complex error < 0.3; B = train every 4 GHz, success if < 0.3 and < half the spline error. The polynomial order K was not
fixed in advance; three were run.
| K | fit on all 21: median EO error | test A model (spline) | test B model (spline) |
|---|---|---|---|
| 0 | 0.31 | 0.37 (0.43) fail | 0.72 (1.46) fail |
| 1 | 0.20 | 0.22 (0.43) pass | 0.50 (1.46) fail |
| 2 | 0.13 | 0.37 (0.43) fail | 1.68 (1.46) fail |
One pass in six tests, at the order that happened to work: not evidence of a predictive model. The model describes the
dense data (K = 2: EO within ~1 dB at most frequencies) but does not predict reliably from sparser sampling than 1-2 GHz.

## EO vs FEXT and NEXT (`eo_vs_ports.py`, `eo_vs_fext_next.png`)
EO - FEXT: median -6.0 dB, 5-95 % range -10.2 .. -1.6 dB, correlation of the dB curves 0.95 (NEXT 0.69). Expected for
forward, velocity-matched coupling growing linearly along the line: the co-propagating optics reads B's average,
half its end value (FEXT), i.e. -6 dB. Solver cost per time step: 7.04 ms (60 subvolume monitors) vs about 7.1 ms
(12 + 12 full-volume monitors, -44.5 dB run): monitors are not the bottleneck.
Sampling of the extraction: 1 mm block averages give the EO within 0.1 / 0.7 / 1.4 dB at 10 / 20 / 30 GHz.
