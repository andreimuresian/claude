# 8 mm uniform pairs, 625 um pitch: GAP 4.15 um (LOW_Z) vs 15 um (HIGH_Z)

Coworker's runs. Headers differ in GAP (0.00415 / 0.015) and in w (0.15 / 0.185); WG, ws,
CHANNEL_PITCH and the rest are equal. `compare.py` (model-free):

| | LOW_Z | HIGH_Z |
|---|---|---|
| NEXT, mean 2-20 / 20-40 / 40-60 GHz | -76.2 / -69.3 / -65.4 dB | -71.3 / -64.2 / -59.9 dB |
| FEXT, same bands | -83.8 / -68.5 / -60.9 dB | -79.6 / -63.0 / -53.4 dB |
| S21 at 30 GHz | -2.46 dB | -1.15 dB |
| group delay NEXT / through (5-50 GHz) | 2.08 | 2.05 |
| group delay FEXT / through | 1.12 | 1.09 |

* HIGH_Z couples more: NEXT +5 dB, FEXT +4 to +7.5 dB.
* NEXT arrives with ~2x the through delay on both: a round trip from the far end, as on
  Istanbul, not the distributed near-end coupling of the two-mode (delta) picture.
* FEXT arrives with ~1.1x the through delay: distributed forward coupling.
* HIGH_Z also has less line loss (-1.15 vs -2.46 dB through at 30 GHz): over one length that
  alone lifts FEXT by ~1.3 dB, and a round trip lifts NEXT by ~2.6 dB.
* Consistency: crosstalk terms that symmetry makes equal (S31/S42, S41/S32) agree to better than
  -130 dB; that checks internal consistency, not mesh accuracy.
