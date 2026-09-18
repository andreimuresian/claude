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

# `RF_perturbation_unitcell.ipynb` — the tee perturbation

Does not merge the baseline with the perturbation. It answers two questions
about the perturbation itself: why the composite
`alpha = alpha_2D + [alpha_ML(etched) - alpha_ML(unetched)]` works, and whether
that differential can be reproduced by a unit cell in code.

| cell | what it does |
|---|---|
| `[0]` | the CST multilayer model as built, the T-slot geometry, the z-sections it cuts the period into, and the generalised cross-section mesher |
| `[1]` | Floquet harmonics, the Bragg and grating-lobe pitches, and the surface-wave modes of the layer stack from a 1D transfer matrix |
| `[2]` | the periodic quasi-static unit cell: per-section 2D extraction, the homogenised line, the exact ABCD Bloch cascade, and the orthogonality check |
| `[3]` | the ohmic ceiling — sheet conduction on the slotted ground, solved for all 498 footprints |
| `[4]` | confrontation with the 500-row multilayer sweep |
| `[5]` | verdict, and the four routes to a code perturbation |

Runs end to end in about 130 s; cell `[2]` is 110 s of that (five geometries,
four 2D meshes each).

## What it establishes

**The multilayer solver carries three loss channels, the 2D FEM two.** CST's
`HF Multilayer` is a surface-integral method whose Green's function is the one
of the whole stack, laterally infinite and open. That puts the lossy-metal
surface impedance, the `Silicon (lossy)` conduction loss *and* radiation /
substrate leakage in it at once — the last one because the layered Green's
function carries the surface-wave poles. The 2D FEM solves for a bound
eigenmode in a closed box and structurally cannot return a leaky one.

**That does not matter for the baseline, and the data proves it.** Over all 498
rows the multilayer unetched number sits *below* COMSOL, by **7.04 ± 1.71 %**,
on every single geometry, and the shortfall tracks `GAP` (-0.41) and `MTX`
(+0.30). An extra loss channel would push it *up*; a first-order surface mesh
under-resolving the `r^(-1/3)` edge singularity pushes it down. So leakage on
the uniform line is below the 7 % meshing residual.

**Which is why the composite is additive.** The baseline supplies the uniform
line's ohmic loss where it is computed best; the differential is identically
zero when the tee is absent, so it cannot double count; and it carries both the
channel the baseline lacks and — as a bonus — cancels the multilayer solver's
own -7 % ohmic bias, which is present in both of its runs.

**The perturbation itself is a mixture.** At `p = 200 µm` every Floquet harmonic
but `m = 0` is evanescent (the `m = -1` lobe needs `p > 1064 µm`) and
`beta_0 p = 0.54 rad`, so the period homogenises. But `n_m = 1.51..2.15` sits
*below* the TE0 surface wave of the 550 µm silicon slab at `n = 2.5414`, so
exactly one radiative channel is open — and it is open for every geometry.

| channel | what it gives | how it was closed |
|---|---|---|
| cross-section change | `delta` in `[-0.40, -0.08]` dB/cm on rows spanning `[-1.07, +17.22]` | homogenised cell, cell `[2]`; the exact ABCD cascade agrees with it to a few % |
| longitudinal current detour | covers the median penalty row (1.05x) then saturates | sheet conduction, cell `[3]`; **73 of 286** penalty rows demand more squares of gold per period than the surviving ground rim physically has |
| leakage into the Si TE0 surface wave | the remainder | not modelled anywhere in this repo |

The worst rows sit at an equivalent `tan d = 0.185`, a Q of about 5. Nothing in
this stack dissipates like that: HR silicon at 2.5e-4 S/m is `tan d = 6.4e-6`,
and the gold itself only reaches 0.017 on the unetched line.

The ohmic shortfall ranks with the slot **depth** (`MTX`, rho = +0.44 — a slot
through thicker gold is a longer below-cutoff channel, so it leaks less) and
with its length (`L2/p`, rho = -0.35), and not at all with the surviving rim
(rho = -0.06). That is an aperture signature. The attribution still rests on
elimination rather than on that ranking.

## Routes to a code perturbation

| route | 1:1? | additive? | cost |
|---|---|---|---|
| **A** periodic quasi-static unit cell | no — no radiation channel exists in a static formulation | yes, proved to machine zero | ~20 s/geometry, built |
| **A+** A + a layered-medium reciprocity integral for the TE0 coupling | first order only; at the top of the sweep 8 % of the power goes per period | yes | seconds; days to build |
| **B** 3D Floquet full-wave cell with PML | yes | yes | the leakage wave has a 3.0 mm lateral wavelength, so the PML must absorb a 3 mm wave while the mesh resolves a 0.1 µm slot rim — millions of DOF, hours |
| **C** layered-medium MoM (MPIE + Sommerfeld Green's function + RWG) | yes, by construction | yes | **recommended**; all metal is coplanar so the Green's function is a 1D table in rho, and one period is ~2.5 k unknowns |

Route **C** is fast for the same reason CST's is: the substrate, the 3 mm
lateral reach and the open boundary all live in the Green's function and cost
nothing, because unknowns exist only on the gold. Built periodic it needs no
ports and no `N+1 - N` subtraction at all; built as finite `N` and `N+1` lines
it reproduces the existing reference numbers port artifact included, which
makes it directly checkable against the 500 rows already in hand.
