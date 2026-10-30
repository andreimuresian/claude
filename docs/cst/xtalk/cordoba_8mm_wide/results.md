# Widened CORDOBA (substrate 625 um beyond the outer grounds) vs narrow (21 um)

## Verdict on hypothesis 1: rejected
The extra victim wave is still there, unchanged (30 GHz, `scan_free_wave.py`, `fit30_wide.log`):

| | narrow (21 um) | wide (625 um) |
|---|---|---|
| five-mode fit, residual on A (CPW pattern) | 0.013 | 0.014 |
| five-mode fit, residual on B' (CPW pattern) | 0.524 | 0.517 |
| with a free extra wave: best n, loss | 2.475, 3 dB/cm | 2.475, 3 dB/cm |
| ... residual on B' (CPW pattern) | 0.177 | 0.179 |
| extra-wave amplitude / e_cpw+ (forward, backward) | 0.078, 0.289 | 0.110, 0.308 |

The residual-vs-index curve is the same in both runs to 0.01 (minimum 2.45-2.50). Moving the lateral
open boundary from 21 to 625 um does not remove or shift the n = 2.475 wave, so it is not produced by
that boundary.

## What widening did change (`compare_narrow.py`, `diff_wave.py`)
* Line A: CPW pattern changed by 0.2-1.3 % (5-60 GHz). S11, S21 unchanged (0.02 dB); n_g 2.2269 -> 2.2292.
* Line B: field changed by 17-26 % (CPW pattern), 18-33 % (slot pattern).
  NEXT +0.6..+1.3 dB, FEXT +1.4..+2.8 dB (5-60 GHz).
* EO crosstalk (fields, 50/50 ohm, push-pull): +1.1 to +3.1 dB:

| f (GHz) | 5 | 10 | 15 | 20 | 25 | 30 | 35 | 40 | 45 | 50 | 55 | 60 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| narrow (dB) | -93.1 | -90.6 | -82.6 | -86.0 | -77.0 | -76.3 | -74.4 | -70.3 | -72.8 | -69.6 | -69.5 | -70.5 |
| wide (dB) | -90.9 | -87.5 | -81.0 | -84.3 | -74.8 | -75.2 | -72.0 | -68.8 | -70.7 | -67.7 | -68.0 | -68.5 |

* The difference field (wide - narrow, B CPW pattern, 30 GHz) is spread over the whole line (0.15-0.23
  of the narrow rms at every z) and its leading term is a backward wave, |n| = 2.39-2.44, 8-9 dB/cm
  (matrix pencil, M = 2-3).

So the 21 um boundary did perturb the victim (about 20 %, +1-3 dB of EO crosstalk), but it was not
the source of the n = 2.475 wave. The widened run is the better reference from now on.
