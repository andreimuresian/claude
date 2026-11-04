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
