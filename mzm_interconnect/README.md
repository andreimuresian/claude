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

## Getting the code, and keeping it up to date

Clone once, then pull. Downloading files individually from the GitHub web page
is the slow path and it is easy to miss one.

```bat
cd /d "T:\Personal_Folders\Muresian\0 INTERCONNECTS\MZM BLOCK\INTERFACE"
git clone -b Lumerical-Interconnect https://github.com/andreimuresian/claude.git
```

After that, one command picks up every change:

```bat
cd /d "T:\...\INTERFACE\claude"
git pull
```

Or just double-click **`update_and_run.bat`** in the repo root: it pulls the
latest code and launches the GUI. It also accepts a Touchstone path:

```bat
update_and_run.bat "D:\data\lab_5NK0050_line_7.s2p"
```

Keep your `.s2p` files and outputs **outside** the clone, so a pull can never
collide with your data:

```
INTERFACE\
├── claude\          <- the clone; never edit by hand, just pull
│   ├── update_and_run.bat
│   ├── run_mzm_studio.py
│   └── mzm_interconnect\
└── data\            <- your Touchstone files and exported tables
```

In VS Code the same thing is Ctrl+Shift+P -> "Git: Clone", then the refresh
arrows in the Source Control panel to pull. No git at all? The whole branch as
one ZIP:
`https://github.com/andreimuresian/claude/archive/refs/heads/Lumerical-Interconnect.zip`

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

Requirements: `numpy scipy matplotlib scikit-rf` (+ `tkinter` for the GUI, + `scikit-fem` for the FEM verification in the Bend window).
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

## The Bend window

Header button **Bend window** (or the button next to *Bend line from* in the
sidebar). The electrode bend is a coplanar line of its own; this window sets
its cross-section and shows what it does.

* **Cross-section**: signal S, gap W, ground Wg, gold thickness and
  conductivity, SiO2 buffer / LN slab / buried oxide under the bend (Si 550 um
  below). The same parameters as in the sidebar: edit either.
* **Bend line at 60 GHz**: |Zc|, n_m, alpha, updated as you type (~0.5 s for a
  new cross-section, then instant), and the target |Zc| (the modulating line's,
  from the Touchstone fit, unless you type one).
* **Bend RF delay and length**: the bend length is the one at which the RF
  takes the required time through the bend, L_b = c tau / n_m(60 GHz), with
  tau either the bend optical delay or the **walk-off compensated** delay
  (optical delay - (n_m - n_g) x mean section length / c; the right choice
  when the modulating line is not velocity-matched, identical when it is).
  *Set the bend length to this value* copies it into the device.
* **Inverse design**: S, W, Wg inside editable ranges such that |Zc(60 GHz)|
  equals the target, with the smallest loss per bend alpha x L_b (i.e. the
  smallest alpha / n_m: a slower line needs a shorter bend). Line model on a
  3x3x3 grid, quadratic response surfaces, constrained search, then a polish
  with the line model itself (the reported numbers are the model's). If the
  target cannot be reached inside the ranges it says so and gives the
  closest geometry. *Apply proposal* writes S, W, Wg and the bend length.
* **Verify with the 2D FEM reference**: the current cross-section solved with
  the validated reference (quasi-static FEM capacitance + the current inside
  the gold, no surface-impedance approximation), drawn over the model curves
  with a table of differences. Needs `scikit-fem`; about 10 s per frequency.
* **alpha(f), n_m(f), |Zc|(f)** of the bend from the line model, which is
  also what the device cascade and the INTERCONNECT tables use (Bend line from
  = cross-section). *fitted values* keeps the old fixed Z / n and
  a.sqrt(f) + b.f loss (or a bend S21 file), e.g. for a 3D simulation of the
  real bend.

The line model (`bend_cpw/model.py`) and its validation are documented in
`tools/bend_cpw/README.md`.

## Crosstalk: two adjacent electrodes

Header selector **Model**: *Single line* is the device exactly as before.
*Crosstalk (two lines)* opens the **Crosstalk window**; the single-line
model, its tabs and its INTERCONNECT build are not touched. The choice is
saved with the session.

The crosstalk model is tied to ONE line: the **200 um pitch, uniform (non
slow-wave) GSG line**, from its own CST crosstalk simulations
(`data/xtalk_200um/`). The sidebar Touchstone file and *Extract + analyse*
are not used; only the circuit settings come from the sidebar (n_g, source,
termination), and the length is its own (*Crosstalk electrode length*).

Two identical electrodes side by side, A (driven, the aggressor) and B (idle,
the victim), are one coupled line: two independent uniform lines, the even
mode (V_A = V_B) and the odd mode (V_A = -V_B), each the single TL line
element, recombined: own line = (even + odd)/2, other line = (even - odd)/2.
That holds for the S-matrix, for the voltage the light integrates
(closed-form integral, no slicing) and for the end voltages.

* **Line** (loss, n_m, Zc): from the 3-D crosstalk runs
  `LINEA0_1MM/5MM_200UM_PITCH.s4p`, even/odd average, two-length
  de-embedding (`docs/cst/xtalk/line_from_s4p.py`). It agrees with the
  single-line runs (cascade) within 0.6 % in n_m, 3.6 % in Zc and 2-6 % rms
  in loss; the 14 mm crosstalk differs by 0.3 dB at most. Stored as the
  single-line extraction's fit forms (fitted 0.5-60 GHz), which also extend
  the INTERCONNECT tables above 60 GHz.
* **Coupling**: n_even - n_odd from the 2-D port modes of the pair
  (`portmode_betas.txt`, PEC metal) scaled by `dn_scale` = 1.146 to the gold
  eigenmode value (0.001731 at 28.9 GHz); Ze/Zo - 1 = 0.21-0.61 % from the
  gold eigenmode (GSG three-mode to power-voltage definition; the figures
  draw the band). The 3-D runs cannot resolve either (error floor).
* **Compute**: NEXT and FEXT at 50 ohm (as a VNA), the voltage the light
  integrates on each line, the EO crosstalk (victim / aggressor modulation)
  and the victim's near- and far-end voltages, with the device's source and
  load (the victim's input ends in its own idle source).
* **Export tables**: `coupled_even.txt`, `coupled_odd.txt` (Ze/Zo - 1 = 0.61 %)
  for the **Coupled TL** scripted element,
  `lumerical/coupled_element_setup.lsf` (by hand:
  `lumerical/create_coupled_element.lsf`). Ports A1, A2, B1, B2; outputs
  `modulation A/B`, optionally `modulation 2 A/B`, `far end A/B`,
  `near end A/B`.
* **INTERCONNECT check**: builds the element in a Compound with
  ENA -> source -> A1, idle source on B1, loads on A2 and B2, reads every
  output, and compares it with the twin (`xtalk_test.py`, report
  `xtalk_check/xtalk_check_report.txt`). The victim gets the aggressor's
  phase-convention, latency and scale corrections, so its error is the
  coupling error alone.
* **Full MZM cascade** (ENA + check, or eyes): two modulators, A and B, each
  the single-line build's interferometer (laser, Y branches, bias, arm-2
  loss, push-pull or single arm, from the sidebar), on one Coupled TL
  electrode of the crosstalk length. In one Compound: SRC_A (Zs) -> A1,
  LOAD_B1 (Zs, B's idle driver) -> B1, LOAD_A / LOAD_B (Rt) on A2 / B2;
  `modulation A` / `modulation 2 A` drive A's arms, `modulation B` /
  `modulation 2 B` drive B's. ENA input 1 reads PIN_A, input 2 PIN_B: their
  ratio is the EO crosstalk in the receiver, checked against the twin
  (`xtalk_cascade.py`, report `xtalk_cascade/xtalk_cascade_ena_report.txt`).
  Eye mode: EYE_1 = A on the coupled line, EYE_2 = what reaches B's receiver
  with its driver idle. Straight electrode only: bends are not modelled.

Code: `coupled_line.py` (Python twin, reuses `scripted_line.tl_sparams`),
`gui_xtalk.py`, `xtalk_test.py`, `xtalk_cascade.py`. Checks: `docs/cst/xtalk/coupled_twin_check.py`.

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

## Exporting the response as Touchstone

**Export Touchstone** on the Response tab writes both traces on that tab at
whatever is currently in the sidebar: S11 of the loaded electrode, and the
electro-optic S21, each as magnitude and phase. The full parameter set that
produced the file goes into the header as `!` comments, so a file can always be
traced back to the settings behind it.

The EO phase is a real model output, not a placeholder. ``eo_transfer`` is
complex throughout -- both the reflection term and the velocity walk-off term
carry phase -- and the magnitude-only plot simply discards it at the last step.
Its group delay comes out at 125.3 ps against an optical transit n_g.L/c of
124.9 ps for a 16.5 mm device, which is a quantity nothing in the fit was aimed
at reproducing.

Three settings control the file, under **Export**:

* `ts_format` -- `DB` (dB + degrees, matching the plots), `MA` (linear + degrees)
  or `RI` (real + imaginary).
* `ts_ports` -- `4-column` writes exactly frequency + S11 pair + EO S21 pair, as
  four data columns. That is *not* a valid 2-port Touchstone file and a strict
  reader will reject it, so `full 2-port` pads S12 and S22 with zeros. S12 = 0
  is honest rather than a fudge: the electro-optic path is unidirectional, and
  the detected photocurrent does not feed back into the RF port.
* `ts_normalised` -- whether the EO magnitude matches the plot (0 dB at the
  low-frequency reference) or is the raw transfer function. The header records
  the reference level either way, so the two are interconvertible.

From the CLI, add `--touchstone` to `analyse`.

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
* `dispersion_check()` answers "is the n_m dispersion real, or is it noise?"
  by fitting each model on the lower half of the measured band and scoring it
  on the upper half, which it has never seen. On a line with genuine dispersion
  the saturating model predicts the unseen half 11x better than a constant; on
  a noisy file where n_m barely moves, the two score alike and the honest
  answer is the spread between them.
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
