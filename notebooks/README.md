# RF notebooks

| notebook | what it is |
|---|---|
| `RF_interface_optimized.ipynb` | the 2D RF baseline — the Python twin of the COMSOL mode analysis |
| `RF_perturbation_unitcell.ipynb` | what the CST multilayer tee perturbation actually is, and how to translate it |

`data/cst_multilayer_500.csv` holds the 500-LHS reference both notebooks are
checked against: the 8 CST design variables, the COMSOL 2D baseline
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

# `RF_perturbation_unitcell.ipynb` — the tee perturbation, simulated

A **self-contained simulator**. Nothing in cells `[0]`–`[4]` reads a dataset:
you type a cross-section and a tee into cell `[0]`, re-run, and it solves for

    delta C', delta L', delta R', delta Z0, delta n_m, delta alpha

of one period of the etched line against its own unetched reference. Cell `[5]`
puts that number next to the recorded CST sweep **if** it finds
`data/cst_multilayer_500.csv`, and prints one line and stops if it does not.

| cell | what it does |
|---|---|
| `[0]` | **your geometry** — layer stack, metal blocks, tee, mesh controls; plan view and the cross-sections the period decomposes into |
| `[1]` | can this stack carry a wave slower than the mode? Floquet harmonics, Bragg and grating-lobe pitches, surface waves from a 1D transfer matrix |
| `[2]` | the periodic unit cell: per-section 2D quasi-static extraction, the homogenised line, the exact ABCD Bloch cascade as the check that averaging was allowed |
| `[3]` | the longitudinal current detour — sheet conduction on the ground footprint, on the *developed* surface so multi-level electrodes work |
| `[4]` | the result table, how to carry it across to the baseline, and what is not in it |
| `[5]` | optional context against the recorded CST sweep |

About 66 s end to end for one geometry (four cross-sections at `MF = 2.5`).

## Entering a geometry

Cell `[0]` takes rectangles. Metal blocks may sit at **any height and any
number of levels** — the solver only ever sees polygons, so a conformal or
stepped electrode is expressible without touching the formulation:

```python
signal = [(x_lo, x_hi, y_lo, y_hi), ...]   # given in full, straddling x = 0
ground = [(x_lo, x_hi, y_lo, y_hi), ...]   # one ground, x > 0, mirrored for you
blocks = [(material, x_lo, x_hi, y_lo, y_hi), ...]   # oxide pedestals, caps
layers = [(material, y_lo, y_hi), ...]     # full-width background
```

`flat_cpw()` reproduces the COMSOL cross-section; `stepped_cpw()` is a template
for a multi-level electrode (low inner tongue, riser, raised outer body on an
oxide pedestal). The tee is given as slot bands measured outwards from the
innermost ground metal edge, and is cut through the full metal thickness at
whatever height that metal sits.

## What it computes, and what it does not

The perturbation is **additive by construction**: set `W1 = W2 = 0` and every
delta collapses to zero identically, because the etched cell is then its own
unetched reference on the same mesh. So it cannot double count anything the 2D
FEM baseline already carries.

It covers two channels — the cross-section change (`delta C'`, `delta L'`,
`delta Z0`, `delta n_m`, and the loss that follows) and the longitudinal
current detour. It does **not** cover radiation, and a quasi-static cell never
can: there is no radiation channel in a static formulation. Cell `[1]` plus the
`n_m` from cell `[2]` decide whether that matters for your stack — if no
background wave is slower than the mode, nothing can carry power away and the
ohmic answer is the whole answer. For the silicon-handle stack it is not: the
Si slab TE0 surface wave sits at `n = 2.54` against `n_m = 1.51..2.15`, so the
channel is open and `delta alpha` is a **lower bound**.

Cell `[4]` prints the gauge that says how much that costs you: what fraction of
the *topological* ohmic ceiling the detour is already using. At 93 % of the
ceiling, on the worst tee in the recorded sweep, the ohmic account reaches
`+3.39` of a recorded `+17.22` dB/cm.

## Evidence behind that split

Established against the 498-row reference and reproducible from
`data/cst_multilayer_500.csv`:

* The multilayer solver's unetched differential sits **below** COMSOL by
  **7.04 ± 1.71 %**, on every single row, and the shortfall tracks `GAP`
  (-0.41) and `MTX` (+0.30). An extra loss channel would push it *up*; an
  under-resolved `r^(-1/3)` edge singularity pushes it down. So leakage on the
  **uniform** line is below the meshing residual — which is exactly why the 2D
  FEM baseline is free to be a purely ohmic + dielectric calculation, and why
  the composite is additive.
* Across the sweep the ohmic detour covers the median penalty row and then
  saturates: **73 of 286** penalty rows demand more squares of gold per period
  than the surviving ground rim physically has.
* The worst rows imply an equivalent `tan d = 0.185`, a Q of about 5. HR
  silicon at 2.5e-4 S/m is `6.4e-6`; the gold itself reaches 0.017 on the
  unetched line.

## Routes to closing the gap

| route | 1:1? | cost |
|---|---|---|
| **A** this notebook | no — ohmic and reactive only | ~66 s/geometry, built |
| **A+** A + a layered-medium reciprocity integral for the surface-wave coupling | first order only; at the top of the sweep 8 % of the power goes per period | seconds; days to build |
| **B** 3D Floquet full-wave cell with PML | yes | the leakage wave has a 3.0 mm lateral wavelength, so the PML must absorb a 3 mm wave while the mesh resolves a 0.1 µm slot rim — millions of DOF, hours |
| **C** layered-medium MoM (MPIE + Sommerfeld Green's function + RWG) | yes, by construction | **recommended**; unknowns live only on the gold, all metal is coplanar in the flat design so the Green's function is a 1D table, one period is ~2.5 k unknowns |
