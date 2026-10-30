# CORDOBA 8 mm standard, widened (coworker's run)

Same model as `../cordoba_8mm` (signal 35 um, grounds 49.85 um, gaps 4.15 um, Au 2 um, LN 200 nm,
SiO2 4.7 um, Si 525 um open bottom, T slots W1/W2/W3 = 3/4/9 um, L1/L2/L3 = 20/86/66 um, pitch
180 um), except that the substrate extends 625 um beyond each outer ground edge (was 21 um).
Port 1 (A near end) driven; ports 2-4 are 50 ohm discrete ports, not driven.

Purpose: test hypothesis 1. Is the extra wave seen on the victim in the narrow run (n ~ 2.45-2.50,
2.5-3 dB/cm, A-vs-B-like pattern; `../cordoba_8mm/modefit/results.md`) an artefact of the
lateral open boundary 21 um from the outer grounds? If it is, it disappears here.

## Files to place here
1. `LINEA_8MM_625UM_PITCH_CORDOBA_WIDE.s4p` (any name ending in .s4p): the Touchstone export
   of the run. Only column 1 (S11, S21, S31, S41) is meaningful; it is used for the S-parameter
   comparison with the narrow run, not for the field EO crosstalk.
2. 24 field files, E field, port 1, f = 5, 10, ..., 60 GHz, two subvolumes per frequency:

| setting | value |
|---|---|
| tool | 3D Export in Volume, Use Subvolume, ASCII |
| monitor | `e-field (f=<f>) [1]` |
| x min = x max | 0.001 |
| line A: y min / y max | 0.2925 / 0.3325 |
| line B: y min / y max | -0.3325 / -0.2925 |
| z min / z max | 0 / 8 |
| step | 0.005 |
| file name | `e-field_f<f>_1_A.txt`, `e-field_f<f>_1_B.txt` (CST default names are also fine) |

Identical to the narrow-run export, so every analysis (field EO, five-mode fit, free-index scan,
remainder envelope) runs unchanged and the two runs compare point by point.
