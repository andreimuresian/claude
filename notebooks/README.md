# `RF_interface_optimized.ipynb` — 2D RF baseline

Python twin of the COMSOL *Electromagnetic Waves, Frequency Domain* mode
analysis that produced the unetched `n_m`, `Z0` and RF attenuation baseline of
the 500-LHS dataset. Structured as the optical `VPI_interface_optimized.ipynb`,
so each stage can be inspected on its own.

| cell | what it does |
|---|---|
| `[0]` | COMSOL parameter block, materials, Goldilocks domain, mesh, cross-section plot |
| `[1]` | anisotropic quasi-static extraction — `C`, `C_air`, `L`, `n_m`, `Z0`, Wheeler `R'`; sets the eigensolver shift |
| `[2]` | anisotropic vector eigensolver (`ElementTriN1 x ElementTriP1`), PEC electrodes = the COMSOL IBC edges |
| `[3]` | `Z0_IBC`, `Z0_voltage_IBC`, `Mode_Score`, and the three-filter selection pipeline |
| `[4]` | figures of merit, including the first-order IBC surface-inductance correction |
| `[5]` | comparison against the recorded COMSOL rows |

## Running it

```bash
pip install numpy scipy scikit-fem femwell gmsh meshio shapely matplotlib
jupyter lab notebooks/RF_interface_optimized.ipynb
```

On Linux `gmsh` also needs `libglu1-mesa libxrender1 libxcursor1 libxft2
libxinerama1`. One geometry takes roughly 20 s at `MESH_FACTOR = 1.0`
(~45 k triangles, ~200 k DOF, ~2 GB).

To sweep a geometry, edit the parameter block at the top of cell `[0]`
(`auc_w`, `gap`, `au_h`, `cap_w`, `wg_h`) and re-run `[0]`-`[5]`.
`MESH_FACTOR` scales every mesh size; check any number you intend to trust at
`MESH_FACTOR = 0.6`.

## Physics notes

* LN enters as the COMSOL tensor `eps_rf = diag(28, 44, 44)`, X-cut, with the
  extraordinary axis across the gap. `[1]` and `[2]` both use it.
* The gold interior is not solved: every DOF inside the electrodes is pinned,
  which is the PEC limit of the COMSOL Impedance Boundary Condition.
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

`L = Z0 * n_m / c` reproduces COMSOL to **±0.3%** on all five recorded rows.
The residuals sit in `C`: 2.6-5.2% low, growing with `gap`. `n_m` lands
1.5-2.5% low and `Z0` 1.2-2.9% high as a consequence.

`Attenuation` is 25-50% low. The notebook reports conductor loss only; it has
no radiating boundary, so any substrate leakage COMSOL's Scattering Boundary
Condition absorbs is missing here. The residual grows with `gap`, which is what
a leakage channel would do.
