# Progress: equalisation study (branch Lumerical-Interconnect)

Last update: 2026-11-19, end of day.

## Done (0-130 GHz data, docs/cst/Equalization/analysis130/)
- Data check of the three reruns; L+S line extraction (touchstone vs fields), field-only extrapolation check.
- L+B+S bend block: touchstone and field routes agree; parasitic (ground-to-ground) mode: n_p 2.39, comb m c/(2 n_p 4.11 mm),
  reflected with Gamma_p ~ -1 at the PEC-bridged ports; loss in the raised straights + U-bend.
- Full equaliser (2.70 + 1.44 + 1.44 mm): electrical S21, EO (L1 only, + + -), standalone 2.70 mm line EO (L+S model).
- Steps 1-2: folds match L+S; bend pair = 2x smoothed L+B+S bend up to 40 GHz, loses less above; parasitic cancellation
  strong up to 40 GHz, none left above 80 GHz; full S21 dips above 60 GHz = parasitic comb over 7.32 mm (8.9 GHz).
- Step 3 (cascade_130.py): two-port cascade within budget up to 60 GHz (local bridging: EO 0.03 dB rms), not above
  (best 0.10 dB rms, max 0.22 dB, cubic). Slide 13.

- Step 4-5 (two_mode_gamma_p.py, two_mode_bend.py, two_mode_cascade.py): two-mode bend from L+B+S fields
  (t_c smooth 5.00 ps, kap = j 0.002 f e^{-jw 5.3 ps}, t_p 5.2 ps, rho = Zc/Zp = 1.56 by smoothness of t_c, Gamma_p = -0.98 e^{-jw 0.56 ps},
  n_p 2.38, alpha_p 1.3 alpha_c (insensitive)). Prediction of the full run: EO 0.02 dB rms (1-60), 0.07 dB rms (62-130);
  best of all models; reconversion essential. Slides 14-15.

## Deck
docs/cst/Equalization/deck/build_equalisation.py (13 slides, company template); images shown to the user, export only at the end.

## Next
- Step 6 done (long_lines_130.py, slide 16): parasitic EO cost <= 0.32 dB in all cases, 0.08 dB for 10+5+5; prediction of 10+5+5:
  EO -1.15 / -1.57 / -2.18 dB at 60/100/130 GHz, |S21| about -12 dB at 130 GHz. Next: compare with the 10+5+5 run and the single-bend run
  (H fields: export macros to write; rho = Zc/Zp from H to check the smoothness choice 1.56).
- Pending runs from the user: single bend (20 um buried stubs, PEC-bridged ports), long equaliser L1 10 / L2 5 / L3 5 mm,
  both with H monitors (field_monitors_H_130GHz.bas). Export macros for H still to be written when the runs finish.

## Optimiser (optimiser_L1_10mm.py, optimiser_plot.py, slide 17)
L1 = 10 mm, L2/L3 0.5-10 mm, two-mode model, 1-130 GHz. 10 mm alone: f-3dB 90 GHz, worst -3.9 dB. Best absolute flatness
(re 10 mm line at 1 GHz, worst level 10-130 GHz): 10+8.5+8 (peaking <= 0.25 dB): -1.4 dB, no DC loss; 10+9+9 (peaking <= 1 dB): -1.2 dB.
10+5+5: -2.4 dB. L3 > L2 flattens the normalised curve but costs low-frequency efficiency. To check against the 10+5+5 run.

## 10+5+5 run (EL_L 10.08, EL_L2 = EL_L3 5.04 mm) validation (long_run_validation.py, slide 18)
Uploaded in docs/cst/Equalization/full equalizer 10+5+5 (touchstone, E gap lines + tapers, bend maps as zip parts, 15 H planes).
Two-mode prediction: EO shape 0.01 dB rms (5-60 GHz), 0.06 dB rms (62-130) after a constant +0.06 dB offset from the 1 GHz
normalisation; |S21| 0.05 dB rms to 60 GHz, fine ripple +-0.4-0.7 dB above 105 GHz not reproduced. Parasitic effect small (as predicted).
Next: H-field analysis (Zc from current loops, power flow), offset origin at 1 GHz, single-bend run when available.
