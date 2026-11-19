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

## Deck
docs/cst/Equalization/deck/build_equalisation.py (13 slides, company template); images shown to the user, export only at the end.

## Next
- Step 4: two-mode bend model from L+B+S (coplanar + parasitic, reciprocity + mirror symmetry, backward conversion neglected),
  then step 5 (compare with the two-port on the full run) and step 6 (longer L2).
- Pending runs from the user: single bend (20 um buried stubs, PEC-bridged ports), long equaliser L1 10 / L2 5 / L3 5 mm,
  both with H monitors (field_monitors_H_130GHz.bas). Export macros for H still to be written when the runs finish.
