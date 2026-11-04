# Widened CORDOBA, electric Si bottom, accuracy target -60 dB (aborted at about -44.5 dB energy)
Same model as `../cordoba_8mm_wide_ebottom` (accuracy -27 dB), one port excited. Run on CPU (CUDA driver too old for
CST 2025.5), aborted by the user after ~21 h at 79 % of the maximum duration, field energy about -44.5 dB
(energy curve: -27 dB at ~0.15 ns, then a straight tail of ~27.5 dB/ns from -31 dB at 0.2 ns to -44.5 dB at 0.69 ns).
The modeler crashed on abort; on reopening, the field monitors were present.

Files: s4p; 24 gap exports `e-field_f<f>_1_<A|B>.txt` (x 0.001, y 0.2925..0.3325 / -0.3325..-0.2925, z 0..8,
step 0.005: 1 x 9 x 1601 points each, both gap columns non-zero). Line B arrived as CST CSV (semicolon, no padding:
one third the size, same 14409 points) and was rewritten in the txt layout; values identical (checked).

## Results (`compare_27_vs_60.py`, `compare_s4p.py`, logs; fits run with TDDIR pointing here)
* Line A CPW pattern changed 0.2-0.4 %; S11, S21 within 0.1-0.4 dB: the strong quantities were converged at -27 dB.
* Line B changed by 41-241 % (CPW pattern) and 48-187 % (slot pattern); A's slot pattern by 59-320 %.
* EO crosstalk (dB, 5..60 GHz): -27 dB run -96.5 -97.1 -86.2 -83.4 -78.7 -71.6 -69.9 -65.8 -65.9 -64.9 -62.9 -66.5;
  this run -83.8 -82.4 -74.6 -65.0 -69.8 -68.0 -63.9 -68.6 -67.8 -65.0 -63.7 -64.7 (change +13 to +18 dB at
  5-20 GHz, within 3 dB above 40 GHz).
* NEXT and FEXT changed by up to ~20 dB (e.g. NEXT 10 GHz -68.2 -> -87.3, 20 GHz -63.7 -> -56.0; FEXT 5 GHz
  -106 -> -79).
* Convergence of this run is not demonstrated (two levels only). Estimate, assuming the truncation error scales with
  the field amplitude of the tail (sqrt of the energy: -27 -> -44.5 dB is a factor 7.5): remaining error of B about
  1/7.5 of the change, i.e. 5-30 % of B, EO uncertainty roughly 0.5-3 dB.
* Six-mode fit (2 mm electric-bottom sweep modes, A slot x10): B CPW residual 0.10 0.14 0.10 0.07 0.10 0.15 0.18
  0.23 0.32 0.47 0.66 0.98 at 5..60 GHz (-27 dB run: 0.73 0.50 0.37 0.21 0.12 0.14 0.23 0.31 0.41 0.59 0.86 1.06).
  Hold-out (fit 1.5-4.5 mm, predict 4.5-7.2): 0.38 0.78 0.40 0.11 0.30 0.53 0.45 0.61 0.76 0.73 0.80 0.74
  (-27 dB: 14, 2.4, 1.8, 0.81, 0.27, 0.33, 0.39, 0.75, 1.0, 1.25, 1.74, 1.73).
* The pencil "sign test" is not a valid diagnostic (`pencil_selftest_60dB.log`): on the six-mode model of B
  (physical waves only) plus a residual of the fit's own size, it reports 70-94 % "wrong-way" waves. Withdrawn.

## Smoothness test (`smoothness.py`, `coeff_noise.py`, `smoothness_coeffs.png`; logs)
Six-mode coefficients normalised by A's forward CPW amplitude (backward ones also by exp(-gamma_cpw L)), eigen
patterns aligned to the family's 15 deg pattern.
* A side, smooth: far-end CPW reflection 0.048 -> 0.056, phase +23 -> -32 deg over 5-60 GHz (about 5 deg per step).
* B side (pair differences (e-o)/2, strips vs bottom, A vs B): magnitudes 1e-4 .. 3e-2 with phase jumps of 50-180 deg
  between neighbouring monitors; not smooth.
* Not random noise: with 10 % white noise added to B, coefficient scatter is 1-14 % (one case 84 %, sb bwd 55 GHz),
  EO scatter 0.04-0.45 dB.
* Leave-one-out at the 10 interior monitors: modal interpolation of the coefficients median |dX|/|X| 0.77, direct
  spline of X 0.80; errors up to 20 dB at 10-15 GHz. The EO on the fitted samples moves -72 -> -62 -> -66 dB from
  15 to 25 GHz.
* Expected frequency scales: a backward wave read by the co-propagating optics gives EO ripple with period
  c/((n_opt + n_wave) L) = 8.3 GHz (CPW) and 7.0 GHz (strips vs bottom); a round trip CPW + strips vs bottom changes
  phase by about 4.5 rad per 5 GHz. The 5 GHz monitor spacing is below the sampling these need, so amplitudes that
  contain multiple reflections cannot be interpolated; only end-conversion coefficients with the propagation phases
  written explicitly (multimode line with end scattering) are candidates for slow variation.

## End-scattering model (`endmodel.py`, `endmodel.log`, `endmodel_eo_K*.png/csv`)
Six modes propagating with the eigen gamma(f); one end-scattering matrix R for both ends (z-symmetric ends), block
diagonal in even/odd (A <-> B symmetry), source vector s; R and s polynomials of order K in f; fitted (linear least
squares, A/B combinations weighted by their size) to the normalised six-mode amplitudes at the 12 monitors.
* K = 0, 1, 2: B CPW field residual 0.25-3.3 (best 0.25-0.35 at 20-40 GHz with K = 2; >1 at 5-15 and 60 GHz);
  leave-one-out EO median |dX|/|X| 0.61 / 0.85 / 1.07 (coefficient interpolation 0.77, direct spline 0.80).
* Restricted to 15-45 GHz (K = 1): median equation residual 5-23 % per frequency.
* Not a working interpolator with these data. Candidate causes, not separated: remaining truncation error of B
  (estimated 5-30 %); index errors accumulated over L in P (0.01 in n = 0.1 rad at 60 GHz; strips vs bottom and
  A vs B indices from a cell with a different side boundary); 12 frequencies too few to fit R together with index
  corrections. The dense run (monitors every 1-2 GHz) is needed to test it properly.

## Accuracy comparison plot (`plot_accuracy.py` -> `accuracy_eo_comparison.png`, `plot_accuracy.log`)
EO of both runs with the change in dB, and the change of each line's CPW gap pattern relative to its own level:
A 0.2-0.4 %, B 41-241 %. In units of A's CPW rms: change on A -47..-53 dB, change on B -55..-67 dB, B itself
-52..-75 dB: on B the truncation error is as large as the field.

## S-parameter end-junction model (`sparam_endmodel.py`, `sparam_endmodel.log`, `sparam_endmodel_K0.png`)
Pre-registered test (criterion stated before running): fit on the 12 monitor frequencies only, predict NEXT and FEXT
on the 972 other points 1-60 GHz; success = median complex relative error < 0.3 for both and below half of a spline
through the same 12 points. K = 0 (constant junctions, 46 real parameters, 96 real data): NEXT 0.109 (spline 1.52),
FEXT 0.164 (spline 0.49); S11 0.088 (0.69), S21 0.018 (0.063). Passed. Caveats: index corrections fitted for the
slot modes are large (+0.12 even, +0.19 odd; CPW +0.02/+0.03, strips-bottom -0.017, A vs B +0.030), so the slot
terms may act as generic absorbers; below 5 GHz the model misses the deep nulls; a fit on every 4th dense point
reached a worse minimum (median 0.09-0.17, 8 starts): the optimiser is not global.

## Fields and EO from the junction model (`junction_fields.py`, `junction_fields.log`)
Modal amplitudes from the S-parameter junction model (K = 0, fitted at the 12 monitors), six constant field scales c_m
and a per-frequency monitor scale fitted to the gap fields. With the junction's own indices (consistent version):
A CPW residual 0.05-0.90, B CPW residual 0.39-1.70, EO error +12/-2 dB in sample; leave-one-out EO median
|dX|/|X| 2.43 (with the eigen CPW split instead: 0.84). The junction model reproduces the port data with an internal
mode mix that is not the one in the fields: its fitted CPW even/odd index difference is 8e-4, 40 times the eigen split
(2e-5), and the slot indices move by +0.12/+0.19. It is a usable interpolator of the S-parameters, not a physical
model of B's field or of the EO crosstalk. (K = 1 run stopped: not needed.)
