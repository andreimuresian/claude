# EO bandwidth of line A from the Istanbul crosstalk-run gap fields

`eo_bandwidth_fields.py` computes the EO response of the driven line from the CST gap fields:

$H_A(f) = \frac{1}{L}\int V_{gap}(z)\,e^{j\beta_o z}\,dz$, push-pull, with $n_g = 2.27$ and L = 8.75 mm.

This is the same integral as the EO crosstalk, taken on line A. The source and termination are the CST ports of each run.
Two normalisations are used:
- to the mean over 3–10.7 GHz, which is one mismatch-ripple period;
- for reference, to 1 GHz.

The data in the log and the figure came out as follows.
- **Check** (`eo_check_run_a.png`): the run (a) field result is compared with the line formula, using α, n_m and Z_c
  extracted from the run (a) s4p.
  - With the raw extracted values the agreement is rms 0.16 dB and 0.31 dB at most, but the ripples do not match: the
    correlation of the 1 GHz differences is only +0.39. The raw Z_c from the de-embedding oscillates between 52 and
    61 Ω with frequency, and that oscillation creates a ripple that is not in the fields.
  - With the fitted (smooth) values the agreement is rms 0.11 dB, 0.19 dB at most, and the ripple correlation is +0.84.
  - What still differs: above 20 GHz the fields show a ripple of about ±0.15 dB that is weaker in the formula. A
    standing-wave fit of V(z) in the gap gives a far-end reflection of 0.07–0.12, against about 0.05 for the fitted
    Z_c (55–57 Ω) between 50 Ω ports. The ends of the simulated line therefore reflect more than a uniform line between
    ideal 50 Ω ports would. A likely cause is the discrete ports, which are not in the formula, but this is not verified.
- **Results:**
  - Runs (a), (b) and (c) do not reach −3 dB by 60 GHz. At 60 GHz they are at −1.6, −1.6 and −2.3 dB.
  - Run (d) (full module) crosses −3 dB at 57.4 GHz with the plateau reference, and at 57.9 GHz with the 1 GHz reference.
    It also reaches −2.9 dB at 53 GHz, and the ripple is about ±1 dB.
- **Not included:** run (d) has a matched waveguide port on the driver trace as its source. The driver's real output
  impedance is not in it.
- **Excluded data:** the 1 GHz export of run c, and the 2 and 15 GHz exports of runs a–c, are corrupted and left out.
