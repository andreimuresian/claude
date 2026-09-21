# RF notebooks

| notebook | what it is |
|---|---|
| `RF_interface_optimized.ipynb` | the 2D RF baseline — the Python twin of the COMSOL mode analysis for the *unetched* CPW cross-section (`n_m`, `Z0`, `alpha_RF` at 60 GHz) |
| `mom/` | the tee-perturbation solver: a layered-medium Method of Moments (a 1:1 translation of CST's `HF Multilayer`), built in phases |

## Baseline — `RF_interface_optimized.ipynb`

Six cells, the Python twin of the COMSOL *Electromagnetic Waves, Frequency
Domain* mode analysis. Reproduces the recorded COMSOL rows to n_m -0.06 %,
Z0_IBC +0.30 %, attenuation +0.85 %. This is the validated baseline; the
perturbation solver adds to it.

## Perturbation — `mom/`  (in progress)

The perturbation is what the tee etching does to `n_m`, `Z0` and `alpha`. It is
being built as a **layered-medium Method of Moments** — the same method CST's
`HF Multilayer` solver uses:

* mixed-potential integral equation (MPIE) for the surface current on the metal;
* RWG basis on a triangular mesh of the conductor surfaces only — no volume
  mesh, no air box, no PML;
* a layered-medium (Sommerfeld) Green's function that carries the whole
  stratified stack (LiNbO3 / SiO2 / Si / air), laterally infinite and open, so
  surface-wave and radiation effects are in the kernel automatically;
* lossy-metal surface impedance on the conductors.

It is built in four phases, each a self-contained notebook with its own
validation gate; a later phase only consumes an earlier phase's saved outputs,
never its code.

| phase | deliverable | status |
|---|---|---|
| 1 | layered-medium Green's function table + TE0 pole | in progress |
| 2 | MPIE MoM assembly, finite N/N+1 mode | not started |
| 3 | periodic (Floquet + Ewald) reformulation | not started |
| 4 | production `simulate()` wrapper | not started |

`mom/data/EVALUATED_FULL_LHS_DATASET.xlsx` is the 500-row CST reference. It is a
**test fixture only** — loaded for validation, never for calibration. There is
no fit, no surrogate, no lookup, and no CST at runtime anywhere in the solver.

### Why the earlier "unit cell" notebook was removed

An earlier `RF_perturbation_unitcell.ipynb` approximated the perturbation by
solving 2D cross-sections and length-averaging them along the period. It was
removed because it is wrong: validated against the CST dataset, its capacitance
was correct (~2 %) but its inductance was systematically ~30 % low, because a
stack of transverse 2D slices cannot represent the return current meandering
around the slot in the propagation direction. That is a 3D effect the MoM
captures and the section-average structurally cannot.
