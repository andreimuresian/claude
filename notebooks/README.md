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

## Status against the recorded COMSOL rows

`L = Z0 * n_m / c` reproduces COMSOL to **0.1-0.3%** on all five recorded rows,
and `Z0_voltage_IBC` to better than 1%. The residual sits in `C`: 2.9-5.2% low,
growing with `gap`, which leaves `n_m` 1.4-2.5% low and `Z0` 1.5-2.9% high.
Every single-parameter change that fixes `n_m` (`box_h`, `tfln`, `eps_SiO2`, a
gap-spanning cap) degrades `Z0` by a comparable amount, so they cannot be
told apart from these five rows and none is applied.

`Attenuation` is 20-45% low, and this is *not* a discretisation artefact. The
conductor loss has been checked three independent ways:

| | contour FEM | Wheeler incremental inductance | Ghione | COMSOL |
|---|---|---|---|---|
| row 1 | 4.43 | 4.91 | 2.24 | 5.66 |
| row 5 | 2.97 | 3.20 | 1.65 | 5.42 |

Wheeler's rule uses only `C_air` for slightly receded conductors and shares no
machinery with the contour integral; its derivative is linear across step
sizes, so it is converged. Corner refinement with P2 elements moves the loss
integral by 5-9% and then plateaus at 0.83 (row 1) and 0.56 (row 5) of the
value COMSOL's attenuation implies. All three methods agree the ohmic loss
*falls* as the gap widens; COMSOL's attenuation is flat at 5.4-5.7 dB/cm
across rows whose ohmic loss varies by 35%. A mesh error shrinks under
refinement and does not invert a trend, so the missing loss is not ohmic.

A stretched-coordinate PML was implemented to test substrate leakage (the
eigensolver supports the full `mu` tensor, so a PML is only a material change).
It does not converge for this problem: `Im(n_eff)` spans 0.06-1.75 dB/cm across
PML thickness and strength, and `Mode_Score` drifts away from 0.5, meaning the
PML contaminates the mode. No leakage number from it is trustworthy.
