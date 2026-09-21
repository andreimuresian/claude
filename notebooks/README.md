# RF notebooks

| notebook | what it is |
|---|---|
| `RF_interface_optimized.ipynb` | the 2D RF baseline — the Python twin of the COMSOL mode analysis |
| `RF_perturbation_unitcell.ipynb` | the tee perturbation: `delta n_m`, `delta Z0`, `delta alpha` for one etched period |

`data/cst_multilayer_500.csv` is reference data only -- neither notebook reads
it. It holds the 500-LHS sweep: the 8 CST design variables, the COMSOL 2D baseline
(`n_m`, `Z0`, `alpha`), and the three multilayer numbers from the `N+1 - N`
differential extraction (`alpha_ML_unetched`, `alpha_ML_etched`, `delta_ML`).

---

# `RF_interface_optimized.ipynb` — 2D RF baseline

Python twin of the COMSOL *Electromagnetic Waves, Frequency Domain* mode
analysis that produced the unetched `n_m`, `Z0` and RF attenuation baseline of
the 500-LHS dataset. Structured as the optical `VPI_interface_optimized.ipynb`,
so each stage can be inspected on its own.

| cell | what it does |
|---|---|
| `[0]` | COMSOL parameter block, materials, Goldilocks domain, mesh, cross-section + mesh plot |
| `[1]` | anisotropic quasi-static extraction — `C`, `C_air`, `L`, `n_m`, `Z0`, Wheeler `R'`; sets the eigensolver shift |
| `[2]` | anisotropic vector eigensolver (`ElementTriN1 x ElementTriP1`), PEC electrodes = the COMSOL IBC edges |
| `[3]` | `Z0_IBC`, `Z0_voltage_IBC`, `Mode_Score`, the three-filter pipeline, and the mode gallery |
| `[4]` | figures of merit, the IBC surface-inductance correction, selected-mode and surface-current plots |
| `[5]` | comparison against the recorded COMSOL rows |

## Running it

```bash
pip install numpy scipy scikit-fem femwell gmsh meshio shapely matplotlib
jupyter lab notebooks/RF_interface_optimized.ipynb
```

On Linux `gmsh` also needs `libglu1-mesa libxrender1 libxcursor1 libxft2
libxinerama1`. One geometry takes roughly 55 s (~157 k triangles, ~315 k DOF, ~3 GB).

To sweep a geometry, edit the parameter block at the top of cell `[0]`
(`auc_w`, `gap`, `au_h`, `cap_w`, `wg_h`) and re-run `[0]`-`[5]`.
`MESH_FACTOR` scales every mesh size; check any number you intend to trust at
`MESH_FACTOR = 0.6`.

## Physics notes

* LN enters as the COMSOL tensor `eps_rf = diag(28, 44, 44)`, X-cut, with the
  extraordinary axis across the gap. `[1]` and `[2]` both use it.
* The gold interior is not solved: every DOF inside the electrodes is pinned.
  That is the `Rs = 0` limit of the COMSOL Impedance Boundary Condition, and the
  IBC is then restored as a first-order perturbation. The IBC enters the
  eigenproblem at order `Rs/eta0 = 1.9e-4`, so the perturbation error is
  `O((Rs/eta0)^2) ~ 4e-8` -- the same physics to eight decimal places. It is
  done this way because in the mixed formulation the z-row is Gauss's law
  rather than the z-component of curl-curl, so the IBC's `E_z` term has no row
  to occupy, and its `1/beta` scaling would make the eigenproblem nonlinear.
* `CORNER_RES` sets the mesh size in refinement boxes on the electrode corners,
  where the surface current is singular. It is the knob that controls the loss
  integral; `|Isig| contour / exact` printed by cell `[4]` is the convergence
  probe (1.0 = converged).
* The conductor current is obtained from the **variational residual** of the
  Gauss row over the pinned DOFs plus surface charge conservation,
  `I = (omega/beta) * Q`, rather than by integrating `Jsz` along the contour.
  The contour integral under-resolves the re-entrant corners of the electrodes
  and inflates `Z0_IBC` by 15-20%; cell `[4]` prints the ratio of the two as a
  mesh-quality probe.
* A PEC solve returns the external inductance only. The same contour integral
  that gives `R'` also gives the IBC surface inductance `L_int = R'/omega`, and
  `n_m` and `Z0` both scale with `sqrt(L_ext + L_int)`. For thick electrodes
  over a narrow gap this is a 3-5% effect, applied in cell `[4]` as `kappa`.
* Wheeler's incremental-inductance rule is **not** an independent check on the
  contour integral. The shape derivative of `C_air` under a uniform recession of
  every conductor wall reduces exactly to `Rs * closed-integral |E|^2 dl / S^2`,
  which is the contour formula itself. Evaluating it by finite differences only
  adds remeshing noise, so cell `[1]` uses the contour form directly.
* At a 90 degree metal wedge the surface charge goes as `r^(-1/3)`, so the loss
  integral converges as `h^(1/3)` and a naive refinement never looks converged.
  It does converge: extrapolating `R'(h) = R'_inf - C h^(1/3)` for row 1 gives
  2406 ohm/m with P1 and 2409 ohm/m with P2 -- two element orders agreeing to
  0.1%. That limit is *not* the answer to use. An impedance boundary cannot
  support the full PEC singularity, because the field penetrates about a skin
  depth into the metal, so the physical cutoff is `delta/2 = 152 nm` rather than
  the mesh size. `CORNER_RES = 0.05 um` sits in that range and is where COMSOL's
  own IBC lands; refining past it overshoots by ~10%.

## Status against the recorded COMSOL rows

Reference: the corrected 500-LHS export (`FINAL_DATASET_nmZ0_alpha_new.xlsx`).
An earlier export of the same sweep carried an attenuation column roughly 2x
too large, together with `n_m` 1.8% high, `Z0` 1.5% low and `Mode_Score` above
0.5 instead of below. Numbers quoted against that older table elsewhere in the
repo history are superseded.

Row 1 (`auc_w 60.952, gap 4.448, au_h 13.336, cap_w 3.340, wg_h 0.267`):

| quantity | this code | COMSOL | delta |
|---|---|---|---|
| `n_m` | 1.65178 | 1.65277 | **-0.06%** |
| `Z0_IBC` | 21.6505 | 21.5855 | +0.30% |
| `Z0_voltage_IBC` | 21.4109 | 21.4999 | -0.41% |
| `Mode_Score` | 0.49520 | 0.49823 | -0.61% |
| `Attenuation` | 4.43008 | 4.39295 | **+0.85%** |
| `L = Z0 n_m / c` | 119.289 | 119.002 | +0.24% |
| `C = n_m / (Z0 c)` | 254.486 | 255.406 | -0.36% |

Across all 500 geometries, the quasi-static extraction of cell `[1]` (run at a
coarser preset than the notebook default) gives `C` **+0.86% +/- 0.14%**,
`n_m` **-1.12% +/- 0.30%** and a conductor loss correlating with COMSOL's
attenuation at **0.9977**. The two attenuations obey the same power law in the
five design variables, which is the real test that the mechanism is right:

| exponent of | `auc_w` | `gap` | `au_h` | `cap_w` | `wg_h` |
|---|---|---|---|---|---|
| COMSOL `Attenuation` | -0.105 | -0.628 | -0.046 | +0.009 | -0.029 |
| this code, ohmic | -0.142 | -0.693 | -0.045 | +0.008 | -0.025 |

So the recorded attenuation of the **uniform** line is ohmic: there is no
missing radiation or substrate-leakage channel, and none is modelled. The
etched line is a different matter — see the second notebook. That is consistent with the
`.mph` materials, where every dielectric is lossless to within rounding
(`Si` 1e-12 S/m, `SiO2` 1e-13 S/m, `LN` 1e-3 S/m, i.e. `tan d = 6.8e-6`, worth
0.01 dB/cm), leaving the gold IBC as the only loss mechanism in the model.

## Open point

The `.mph` carries two gold material nodes with different conductivities,
`4.1e7 S/m` (`mat3`) and `4.56e7 S/m` (`mat6`). The notebook uses `4.56e7`.
Since `Rs` goes as `1/sqrt(sigma)`, picking the other one would raise the
conductor loss by 5.5%. Worth confirming which node is bound to the electrode
boundaries before the last percent of the attenuation is argued over.




---

# `RF_perturbation_unitcell.ipynb` — the tee perturbation

Four cells, about 26 s, one figure. Same cross-section as the baseline
notebook, with a T-shaped slot cut through the ground electrodes every
`PITCH` micrometres. Edit the parameter block at the top of cell `[0]` and
re-run; cell `[3]` prints what the tee does to the line.

| cell | what it does |
|---|---|
| `[0]` | parameter block, materials, mesh; cross-section at the gap to scale, and the same period from above |
| `[1]` | quasi-static extraction (`C`, `C_air`, `L`, `R'`, `n_m`, `Z0`, `alpha`), run on the unetched cross-section |
| `[2]` | the etched line: the cross-sections one period splits into, averaged by length, plus the current detour |
| `[3]` | `delta C'`, `delta L'`, `delta R'`, `delta Z0`, `delta n_m`, `delta alpha` — and what they do not contain |

Nothing reads a dataset. Cell `[1]`'s unetched numbers are directly comparable
with `RF_interface_optimized.ipynb`, which is the check to run before trusting
anything below it. `MESH_FACTOR` in cell `[0]` scales every mesh size; the
default 2.5 is about five times faster than the baseline notebook's setting
and puts `alpha` a couple of percent low, a bias that cancels in every delta.

## Why the period splits into sections

The slot is two rectangles of different lengths along the line, so walking one
period you meet a small number of distinct cross-sections — with `L2 > L1`:
both rectangles open for `L1`, the cap alone for `L2 - L1`, solid ground for
the rest. The pitch is 13x shorter than the guided wavelength, so the line
homogenises: charge adds in parallel along z, flux and dissipation in series.
Cell `[2]` solves each section and averages by length.

Averaging cross-sections leaves each section's current in its own 2D pattern,
which misses one ohmic effect: the slot interrupts the inner ground, so once
per period the return current has to travel out to the surviving rim and back.
Cell `[2]` adds that as a sheet-conduction problem on the ground seen from
above. It is charged at the full `Rs` on one face and at the unetched `Z0`,
both of which overstate it, so that term is an upper bound.

## Sanity checks

* Set `W1 = W2 = 0`. Every delta must come out exactly zero — the etched cell
  is then its own unetched reference on the same mesh. Run this first.
* Compare cell `[1]` against `RF_interface_optimized.ipynb` on the same
  cross-section.
* `delta n_m` and `delta Z0` are reactive and complete; check them against a
  CST run of the same geometry.

## What `delta alpha` does not contain

A line can also lose power by launching a wave that leaves. That needs a wave
the layer stack can carry more slowly than the mode, and cell `[3]` settles it
with one transfer-matrix solve of the stack. With a silicon handle the answer
is yes: the substrate's TE0 surface wave sits at `n = 2.54` against
`n_m = 1.5..2.15`, so the channel is open for every geometry, the slot is an
aperture into it, and a quasi-static cell has no radiation channel at all.
`delta n_m` and `delta Z0` are unaffected. `delta alpha` is the ohmic part
only, and a lower bound.

Cell `[3]` prints the gauge for how much that costs: what fraction of the
topological ohmic ceiling the detour is already using. Near 100 % means most
of the real penalty has to be coming from somewhere other than gold.

Closing that gap needs either a layered-medium reciprocity integral for the
surface-wave coupling (cheap, first order) or a layered-medium MoM (the real
translation of CST's multilayer solver). Neither is in the repo.
