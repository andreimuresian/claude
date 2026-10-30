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

## Where the |n| ~ 2.5 field lives: 30 GHz planes (`planes_pencil.py`, `planes_pencil.log`)
Matrix pencil along z, row by row (4 waves, field components as channels):
* Midway between the lines (V1, y = 0), at every depth from 100 um above the surface to the bottom of
  the Si (-527 um), and laterally from y = -1.0 to -0.15 mm (B side, beyond B too): the leading wave is
  **backward, |n| = 2.55-2.65, 0-6 dB/cm**; a forward |n| 2.52-2.55 wave comes second (0.5-0.7).
  rms |E| at y = 0 is 2.7-2.9e2 V/m near the surface (A gap field 1.3e6, B gap field 2.8e3 V/m:
  -73 dB and -20 dB relative).
* Under line B's centre (V2, y = -0.3125), all depths: leading wave backward, |n| 2.5-2.9.
* Close to A (y = +0.15 ... +0.45): A's own forward wave (n 2.26-2.39) dominates; beyond A
  (y = +0.6 ... +1.0) forward 2.54-2.62 and backward 2.55-2.58 with similar amplitudes.
So the wave is not bound to line B: it fills the substrate and the air above across the whole width
of the chip, mostly travelling toward the near end. NEXT group delay = 2.09 x the through delay
(both runs) = forward on A (n_g 2.227) plus a return at n_g = 2.43: consistent with a wave created
at A's far end and travelling back across the chip.

## Does it enter the EO crosstalk? (`eo_decomp.py`)
30 GHz, B's push-pull pattern, kept samples of the interior: contributions to H (relative to H[data]):
CPW pair forward 3.09 at -55 deg, extra wave forward 2.96 at +95 deg, CPW pair backward 0.60,
extra wave backward 0.79, slot pairs 0.17 / 0.003; sum 0.996 (residual 0.005). The forward CPW pair
(n 2.237) and the forward extra wave (n 2.475) differ by 1.1 rad over 7.4 mm: the fit cannot separate
them, their EO contributions are each three times the total and cancel. The wave's share of the EO
crosstalk is therefore not determined by this fit; it is not shown to be small.

## Where it is born (`s31_time.py`)
Band-limited impulse response of NEXT (S31): rms 0.009 / 0.007 in 0-50 / 50-100 ps, 0.564 in
100-140 ps, peak at 128 ps. Td = 59.5 ps, so the near-end crosstalk is a return from A's far end:
128 - 59.5 = 68.7 ps over 8 mm -> n_g = 2.57, the |n| of the backward chip-wide wave in the planes.
A distributed coupled-line NEXT (spread over 0-119 ps) is absent. The far-end region of the model
holds the discrete port 2 on its PEC bridge, the end of the electrodes and the end of the substrate
(40 um beyond the line, then the open boundary); this run does not tell which of them launches it.
