# EO bandwidth of line A from the Istanbul crosstalk-run gap fields

`eo_bandwidth_fields.py` computes the EO response of the driven line from the CST gap fields:

$H_A(f) = \frac{1}{L}\int V_{gap}(z)\,e^{j\beta_o z}\,dz$, push-pull, with $n_g = 2.27$ and L = 8.75 mm.

This is the same integral as the EO crosstalk, taken on line A. The source and termination are the CST ports of each run.
Two normalisations are used:
- to the mean over 3–10.7 GHz, which is one mismatch-ripple period;
- for reference, to 1 GHz.

The data in the log and the figure came out as follows.
- **Check** (`eo_check_run_a.png`): the run (a) field result was compared with the line formula, using α, n_m and Z_c extracted from the run (a) s4p.
  They agree to 0.12 dB (median) and 0.31 dB at most. The field normalisation is therefore consistent across frequency.
- **Results:**
  - Runs (a), (b) and (c) do not reach −3 dB by 60 GHz. At 60 GHz they are at −1.6, −1.6 and −2.3 dB.
  - Run (d) (full module) crosses −3 dB at 57.4 GHz with the plateau reference, and at 57.9 GHz with the 1 GHz reference.
    It also reaches −2.9 dB at 53 GHz, and the ripple is about ±1 dB.
- **Not included:** run (d) has a matched waveguide port on the driver trace as its source. The driver's real output
  impedance is not in it.
- **Excluded data:** the 1 GHz export of run c, and the 2 and 15 GHz exports of runs a–c, are corrupted and left out.
