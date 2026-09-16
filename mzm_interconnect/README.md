# MZM Studio

A single tool that takes a CST (or lab VNA) Touchstone file of a traveling-wave
electrode and gives you the electro-optic bandwidth of the modulator built
around it -- interactively, as a parametric sweep, and as a Lumerical
INTERCONNECT schematic built from exactly the same numbers.

It merges the two scripts that used to run separately (`EXTRACTOR_NEW.py` and
`MZM_API_launcher_new.py`) into one pipeline with a GUI on top.

```
   CST / VNA .s2p
        │  ABCD de-embedding + physical fits        (extractor.py)
        ▼
   LineFit:  α(f) [dB/cm]   Zc(f) [Ω]   n_m(f)      intrinsic, per unit length
        │  closed-form traveling-wave transfer fn   (physics.py, ~1 ms)
        ▼
   EO S21(f)  →  bandwidth, V_pi, ER, chirp, S11
        │                                   └─────► parametric sweep (sweep.py)
        │  loss.txt / z0.txt / nm.txt / sim_params.json
        ▼
   Lumerical INTERCONNECT schematic + solver cross-check  (interconnect.py)
```

## Running it

```bash
python run_mzm_studio.py                        # GUI, dark theme
python run_mzm_studio.py TEST/line_7.s2p        # GUI with a file preloaded
python run_mzm_studio.py --light                # light theme

python -m mzm_interconnect.cli analyse line.s2p --L_target_mm 8 --Rt_R 40 --plot
python -m mzm_interconnect.cli sweep   line.s2p --param Rt_R --from 10 --to 100 --n 91
python -m mzm_interconnect.cli sweep   line.s2p --param Rt_R --from 10 --to 100 \
        --series L_target_mm --series-from 4 --series-to 12 --series-n 5
python -m mzm_interconnect.cli export  line.s2p --out_dir ./tables
python -m mzm_interconnect.cli build   line.s2p     # needs lumapi
```

Requirements: `numpy scipy matplotlib scikit-rf` (+ `tkinter` for the GUI).
Lumerical is optional -- nothing imports `lumapi` until you press
**Build + run in INTERCONNECT**.

## Why the split matters

The Python model and INTERCONNECT solve the same device two different ways,
and they agree. That agreement is what licenses the division of labour:

* **Python** evaluates the closed-form transfer function in about a
  millisecond, so a 300-point two-dimensional sweep finishes before
  INTERCONNECT could open a project. This is the fast evaluator.
* **INTERCONNECT** runs the real circuit solver on a schematic other people
  can open, extend and reuse -- and it is the only one of the two that leads
  to eye diagrams, PAM-4/BER, fibre propagation and nested IQ structures.

Use Python to *find* the operating point; use INTERCONNECT to *verify* it and
to build the system model around it.

## The GUI

| Tab | What it shows |
|---|---|
| Response | Normalised EO S21 with the bandwidth marker, plus electrical S11 into the loaded line |
| Line diagnostics | α(f), Zc(f), n_m(f): de-embedded points against the physical fit, with n_g drawn in |
| Sweep | Pick any sweepable parameter, sweep it, plot any metric; optional second parameter gives a family of curves |
| INTERCONNECT | Export the tables, build the schematic, run it, overlay the solver trace on the Python one |
| Log | Everything the engine said, including every warning about extrapolation |

The KPI strip across the top always shows EO bandwidth, effective V_pi,
V_pi·L, extinction ratio, chirp parameter, velocity walk-off at the bandwidth
frequency, and worst-case S11.

## Adding a parameter

Every knob lives in `parameters.py` as one `ParamSpec`. Add an entry and the
sidebar widget, its tooltip, the sweep menu entry and the CLI flag all appear
on their own. Then consume the new key wherever the physics needs it -- almost
always in `physics.eo_response` or `physics.link_metrics`.

```python
ParamSpec("bend_count", "Electrode bends", 0, "Device geometry", "-",
          kind="int", sweepable=True, sweep_default=(0, 8, 9),
          affects="circuit",
          help="Number of 90-degree coplanar bends in the routed electrode.")
```

## Metrics available in a sweep

`bw_GHz`, `s21_at_probe_dB`, `s11_worst_dB`, `walkoff_at_bw`,
`alpha_at_bw_dB_cm`, `vpi_eff_V`, `vpi_L_Vcm`, `er_dB`, `chirp_alpha`.

A bandwidth point drawn as an open triangle means the response never reached
the criterion inside the sweep ceiling, so the plotted value is a lower bound;
raise **Sweep ceiling** in the Analysis group to resolve it.

## Drive configuration

`single-arm` reproduces the original validated topology: one modulated arm, a
static phase shifter in the other. Chirp parameter 1, full single-arm V_pi.

`push-pull` models what an X-cut LN G-S-G device physically does -- both
waveguides sit in the two gaps and see opposite horizontal field, so one
electrode modulates both arms with opposite sign. The microwave bandwidth is
unchanged; V_pi halves and the chirp goes to zero. If the installed
INTERCONNECT will not fan one electrical output out to two modulation ports,
the builder falls back to a lumped equivalent that preserves |S21| and V_pi
exactly (only the chirp asymmetry is lost) and says so in the log.

## Normalisation: why the 0 dB reference is averaged, not a point

A mismatched electrode rings. Forward and backward microwave waves interfere,
so the response carries a standing-wave ripple of period `c/(2 n_m L)` -- on a
16.5 mm line at n_m = 2.29 that is 3.96 GHz, about half a dB peak to peak. Take
the 0 dB reference at one frequency and you are anchoring on a random phase of
that ripple: on a real file the same device came out anywhere from 94 to 110 GHz
depending only on whether the anchor sat at 0, 1, 2 or 5 GHz.

`norm_mode = "plateau"` (the default) averages the response over a whole number
of ripple periods, which cancels it. The window is also capped at a fraction of
the roll-off so it can never reach into the skirt and flatter the result; if not
even one period fits below that cap -- a short line whose ripple period is
comparable to its bandwidth -- it falls back to the lowest measured frequency
and says so. The reported bandwidth is then identical for any `f_norm`.

`norm_mode = "point"` keeps the older single-frequency behaviour (and the usual
textbook convention) for when you need to match someone else's number.

The fits are also held at their lowest measured value below the measured band:
the `1/sqrt(f)` and `1/f` terms in the Zc form are singular at DC, and
extrapolating into that singularity used to give Zc = 282 + 610j ohm at 10 MHz
and infinity at f = 0, which turned the whole curve into NaN. Normalising at
DC now works.

## Extrapolation and the honest uncertainty

A test pattern is measured over a limited band and is usually much shorter than
the device. When the -3 dB point lands outside the measured band, its value is
decided by the *form* of the fit, not by the data. The tool says so:

* **n_m** is fitted with a bounded, saturating form whose corner is pinned
  inside the measured range, so the model can never claim dispersion it did not
  resolve. The older polynomial `beta(f)` fit is kept as `nm_model="cubic-beta"`
  only for reproducing earlier numbers -- on a real 0-80 GHz dataset it reached
  n_m = 3.2 at 300 GHz and 6.7 at 600 GHz, inventing a velocity walk-off that
  does not exist.
* **alpha** is refitted with non-negative conductor- and dielectric-loss
  coefficients if the free fit lands somewhere unphysical.
* Every fit is **outlier-robust**: a soft-L1 refit scaled to the measured
  residual spread, which is skipped entirely when the data is already clean.
* `bandwidth_spread()` reports the bandwidth over the whole family of
  defensible fits. Quote the range, not the midpoint.
* `extraction_warnings()` says plainly when the loss is poorly determined, when
  the alpha fit had to be constrained, and how far past the data the answer sits.

On a real 2.5 mm test pattern measured to 80 GHz and scaled to 16.5 mm, that
family spans 105-113 GHz. Any single number quoted to better than that is false
precision.

## Validation

`physics.eo_response` with every perturbation knob at its default (scales 1.0,
offsets 0.0, purely resistive source and load) is bit-for-bit the expression
from the original extractor -- checked directly on identical inputs, agreeing to
8e-15 dB across the curve. With `nm_model="cubic-beta"` the whole pipeline
reproduces the original extractor's bandwidth to within 1e-6 GHz, so older
results stay reachable.

On a synthetic line with known truth (`n_m = 2.34 - 0.10 exp(-f/25)`), the
saturating model gives n_m(300 GHz) = 2.363 against a true 2.340, where the
cubic gives 1.441; and the robust fits recover the exact synthetic coefficients
for alpha, Re(Zc) and Im(Zc).
