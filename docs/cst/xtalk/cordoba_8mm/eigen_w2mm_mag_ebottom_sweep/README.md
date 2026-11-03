# Phase sweep, 2 mm cell (Ymax magnetic, 616 um beyond the outer ground), electric Si bottom (525 um)
Same model, mesh and solver settings as `../eigen_w2mm_mag_ebottom` (15 deg, done). Even (XZ magnetic) and odd
(XZ electric) at each phase. Project frequency range raised to 0-80 GHz (the search interval ends at its top).

| phase | frequencies above | modes | expected (constant-n estimate): strips vs bottom, A vs B, slot, CPW (GHz) |
|---|---|---|---|
| 5 deg | 6 GHz | 10 | 7.4, 8.0, 9.6, 10.3 |
| 10 deg | 12 GHz | 10 | 14.8, 15.9, 19.2, 20.7 |
| 20 deg | 24 GHz | 10 | 29.7, 31.8, 38.4, 41.4 |
| 25 deg | 30 GHz | 10 | 37.1, 39.8, 47.9, 51.7 |
| 30 deg | 36 GHz | 10 | 44.5, 47.7, 57.6, 62.1 |

Exports per mode (all modes found): gap pattern (x 0.001, y 0.2925-0.3325, z 0-0.18, step 0.005) and
cross-section (x -0.53..0.1, y 0..1.0, z 0.09, step 0.005); plus the solver log. Folder per run:
`p<phase>_<even|odd>/`. Gap file and cross-section of the same mode may be .txt and .csv (both readable).

## Results from the solver logs (2026-11-03; `summarize_logs.py` -> `summarize_logs.log`, `guided_families.csv`)
All 10 runs converged. Logs pasted in chat, saved as `p*/log_excerpt.txt` (settings + results).
**The search interval still ended at 60 GHz** (log: "(36 GHz, 60 GHz)"), not 80: CPW at 30 deg (~62 GHz)
not found in either symmetry. CPW data stop at 52 GHz; 55 and 60 GHz need extrapolation.

- Guided families continuous over 5-30 deg: strips vs bottom n 3.117-3.135, A vs B 2.897-2.983, slot
  2.40-2.44, CPW 2.269 (10 GHz) -> 2.226 (52 GHz). CPW n_g 2.21-2.22.
- Attenuation from Q (alpha = omega/(2 Q v_g)): CPW 0.12 (10 GHz) -> 0.32 dB/mm (52 GHz); A vs B the
  lossiest, 0.30-0.72 dB/mm.
- CPW even/odd split 0.9-1.3e-5 (dn 2.0-2.8e-5). Velocity-matched estimate of the crosstalk from the CPW
  beat alone, X = dbeta L/4 at L 8 mm: -101 / -95 / -91 / -87 / -84 dB at 10 / 21 / 31 / 42 / 52 GHz,
  against the electric-bottom TD EO -97 / -83 / -72 / -66 / -65 dB: the CPW beat is not the dominant path
  above ~10 GHz.
- Extra low-Q modes (Q 4-15): substrate cell modes. With the TM0 index of 525 um Si on a conductor, the odd
  family keeps a constant lateral wavenumber k_y W/(pi/2) = 1.09-1.20 from 5 to 25 deg (one quarter-wave
  pattern across the cell, tracking TM0); even modes at 1.72 and 1.96. Their frequencies depend on the
  cell width; identification to be checked on the exports.

## Six-mode fits at the 12 TD monitor frequencies (2026-11-03)
Exports unpacked from the user's zips into `p<phase>_<sym>/eig_<sym>_mode<k>_e.txt` and `_xsec.csv`
(cross-sections now reach y = 1.0). Identification on the gap patterns (CPW/slot ratio): CPW 246-262,
slot 0.004-0.006, strips vs bottom 0.60 (5 deg) -> 0.97 (30 deg), A vs B 0.32-0.38; consistent with the log
order in every run. Scripts: `sweepfit.py` (module), `run_sweepfit.py`, `diag_sweepfit.py`,
`extra_sweepfit.py`, `dn_sweepfit.py`, `dn2_sweepfit.py`, `zloc_sweepfit.py`, `launch_sweepfit.py` (logs alongside).

- Line A, CPW pattern: residual 0.005-0.035 at 5-60 GHz.
- Line B, CPW pattern (joint fit, A slot x10): 0.73, 0.50, 0.37, 0.21, 0.12, 0.14, 0.23, 0.31, 0.41, 0.59,
  0.86, 1.06 at 5..60 GHz. Fitting B alone: 0.05-0.10 at 20-45 GHz, 0.26-0.54 at 5-10, 0.34-0.58 at 55-60.
- Hold-out (fit 0.3-4 mm, predict 4-7.7 mm): B residual >= 0.54 at every frequency. The six modes describe
  B's field locally, not its evolution along the line.
- Not the cause: CPW index (A prefers +0.004..+0.010, as TD n_g 2.229 vs eigen 2.212; B unchanged); index
  shifts of strips vs bottom and A vs B up to +-0.2 (optimum on the grid edge, sign changes with f);
  the substrate cell modes or any single extra guided wave at 45-60 GHz.
- At 5-15 GHz B's field is 1.4-2.0x its line mean in the first mm and drops to 0.1-0.4 beyond 3 mm; an extra
  wave born at z = 0 is best fitted with n ~ 0 and 8-12 dB/mm (decay length ~0.7-1 mm): a non-propagating
  near field of the launch (port region), absent from any guided-mode basis.
- EO: model and data agree within 0.6 dB on the fitted samples at all 12 frequencies, including 60 GHz where
  the B residual is 1.06: projection identity (the forward CPW pair, n 2.23, is close to the optical kernel,
  n_g 2.27), not a validation. Hold-out EO errors -12 to +18 dB. The excluded samples matter: full-line EO
  vs interior without stems differs by up to 11 dB (15 GHz: -86.1 vs -97.2 dB); at 5-15 GHz the two 0.31 mm
  end zones alone exceed the interior contribution.
- Interpolation: n(f) = n_inf + b/sqrt(f) + c f fits CPW to 1.3e-4 (alpha to 0.3 %), slot to 1e-3, A vs B
  6e-3, strips vs bottom 3e-3 (alpha 17 %: its n has a minimum at 15 deg; needs another form). Gap patterns
  change per eigen step by 0.8 % (CPW), 0.9 % (slot), 1.5-3 % (A vs B), 6 % (strips vs bottom); nearest and
  interpolated patterns give the same fits to 0.004. CPW split 2.0e-5 -> 2.8e-5, smooth.
- Hold-out away from the launch (`holdout_nolaunch.py`): fit 1.5-4.5 mm, predict 4.5-7.2 mm: B residual 0.27,
  0.33, 0.39 at 25, 30, 35 GHz; 0.75-1.7 at 40-60 GHz; 0.8-14 at 5-20 GHz. Excluding the launch zone does not
  make the six modes predictive outside 25-35 GHz.
