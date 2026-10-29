# CORDOBA 8 mm, 30 GHz: TD gap fields against the eigenmodes (1.2 mm cell, magnetic side wall)

`fit30.py`: exact pair sectors, line A and B' (B mirrored onto A) fitted jointly; fixed eigenmode
indices, losses and cell patterns, free global forward/backward amplitudes (10 complex numbers).
T-stem cell positions (zc 65-115 um) excluded: there the TD dip is broad and the eigenmode dip
narrow (sample point 1.65 um from the stem corner); elsewhere both cell profiles are flat to 1 %.

| model | A | A CPW pattern | B' | B' CPW pattern | B' slot pattern |
|---|---|---|---|---|---|
| CPW pair | 0.261 | 0.260 | 0.784 | 0.572 | 0.851 |
| CPW + slot pairs | 0.074 | 0.013 | 0.322 | 0.579 | 0.128 |
| all five | 0.067 | 0.013 | 0.291 | 0.524 | 0.114 |

(relative rms residuals). Line A is described to 1.3 % in its CPW pattern; the slot pairs carry
the victim's slot pattern (residual 11-13 %). The victim's CPW pattern (what push-pull reads) is
not: 52 % remains, nearly independent of the CPW split (0 to 1.5e-4: 0.528 -> 0.517).
Slot modes put only 0.4-0.5 % CPW pattern in the gaps (eigen exports), so they cannot carry it.

`resid30.py`: the remainder is end-localised (0.5-0.7 of the data rms within 3 mm of the near end,
0.9-1.1 within 1 mm of the far end, 0.13-0.20 at 4-5 mm), rank about 4, led by a backward wave
|n| = 2.7-3.0, 9-15 dB/cm.

`avsb_scan.py`: letting the A-vs-B wave take a free index and loss: best n = 2.45-2.50, about
2.5 dB/cm -> B' CPW residual 0.18, B' 0.14, A 0.04-0.06. Eigenmode A vs B with open-like sides:
3.08 +- 0.03, 14 dB/cm (Q 4.6). Narrow cell with the electric wall where the TD model's open
boundary sits (21 um beyond the outer ground): 2.537, Q 34 (about 2.0 dB/cm at 30 GHz).
