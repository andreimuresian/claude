# Progress

## Current state (as of 2026-09-21T10:05Z)

**Project.** Translating a TFLN travelling-wave modulator RF workflow out of
COMSOL + CST Studio into a closed Python environment. Two pieces: a 2D FEM
baseline for the *unetched* line (`n_m`, `Z0`, `alpha_RF` at 60 GHz), and the
*perturbation* those figures take when T-shaped slots ("tees") are etched into
the ground electrodes every 200 um. Branch: `2D-+-2.5D`.

### DONE and verified

- **`notebooks/RF_interface_optimized.ipynb`** — the 2D baseline. Six cells,
  Python twin of the COMSOL *Electromagnetic Waves, Frequency Domain* mode
  analysis. Reproduces the recorded COMSOL rows to n_m -0.06 %, Z0_IBC +0.30 %,
  attenuation +0.85 %. Committed at `0cd4ef3`, refined at `a976433`,
  `3a5d576`, `5018302`. The user considers this notebook good and it is the
  reference for style: straight to the point, easy to test and debug.

- **`notebooks/RF_perturbation_unitcell.ipynb`** — the perturbation simulator.
  Four cells, ~27 s, one figure, latest rebuild at `2c924ad` plus an
  uncommitted cosmetic fix (see below). Reads no dataset. Structure:
  `[0]` parameters/materials/mesh + cross-section at the gap to scale and the
  period from above; `[1]` quasi-static extraction on the unetched
  cross-section (checkable against the baseline notebook); `[2]` the etched
  line — the z-sections one period splits into, averaged by length, plus the
  current detour; `[3]` `delta C'`, `delta L'`, `delta R'`, `delta Z0`,
  `delta n_m`, `delta alpha`.

- **Zero-tee sanity check PASSES exactly.** Verified by running the rebuilt
  notebook with `W1 = W2 = 0`: every delta comes out identically `0.000000e+00`
  and the detour returns `-2.2e-16` extra squares. This is the additivity
  guarantee — the etched cell collapses onto its own unetched reference on the
  same mesh, so the perturbation cannot double count the baseline.

- **Physics finding, backed by the 498-row CST reference**
  (`notebooks/data/cst_multilayer_500.csv`, reference data only, no notebook
  reads it):
  - CST's multilayer (MoM + layered Green's function) carries three loss
    channels: metal surface impedance, substrate conduction, and
    radiation/surface-wave leakage. The 2D FEM carries only the first two and
    structurally cannot carry the third (bound-mode eigenproblem in a closed box).
  - That does not hurt the baseline: over all 498 rows the multilayer unetched
    number sits BELOW COMSOL by 7.04 +/- 1.71 %, on every row, and the shortfall
    tracks GAP (-0.41) and MTX (+0.30) — a mesh/edge-singularity signature, not
    a loss channel. So leakage on the uniform line is below the meshing residual.
  - The tee perturbation is a MIXTURE. Homogenised quasi-static gives delta in
    [-0.40, -0.08] dB/cm on rows whose true delta spans [-1.07, +17.22]. The
    longitudinal current detour covers the median penalty row and then saturates:
    73 of 286 penalty rows demand more squares of gold per period than the
    surviving ground rim physically has. Worst rows imply tan d = 0.185, Q ~ 5,
    which nothing in the stack can dissipate.
  - The open channel is the silicon substrate's TE0 surface wave at n = 2.5415
    against n_m = 1.51..2.15. Open for every geometry in the sweep. The user
    confirmed silicon is present in the new designs too, so it does not close.

### IN PROGRESS

- Nothing. Working tree is clean and the branch is in sync with
  `origin/2D-+-2.5D`. The last change was a cosmetic fix in cell `[3]` so the
  ohmic-ceiling gauge does not print `-0.0 of 0.0 (-0 %)` on the zero-tee run;
  notebook re-executed clean (26.9 s) and committed alongside this file.

### NOT started / deferred

- **Multi-level (stepped / conformal) electrodes.** Built once, was WRONG —
  I modelled separate metal blocks on oxide pedestals; the user's actual CST
  cross-section has the metal draping *conformally* over the topography.
  Removed entirely at `2c924ad`. Deferred by the user: do the simple coplanar
  case first. When resumed, get the real layer thicknesses from the user
  rather than guessing at the shape.
- **The leakage term.** Not modelled anywhere in the repo. Two routes costed
  but neither started:
  - *A+*: layered-medium reciprocity integral for the aperture-to-TE0 coupling.
    Seconds to run, a few hundred lines to write, first order only — already
    strained where 8 % of the power leaves per period.
  - *C* (recommended): layered-medium MoM (MPIE + Sommerfeld Green's function
    + RWG). Unknowns only on the gold. For the FLAT design all metal is
    coplanar so the Green's function is a 1-D table in rho; for the stepped
    design it becomes a table over the discrete metal levels.
- Mesh-convergence pass on the perturbation notebook. Offered, not authorised.

### Known failures / do not retry blindly

- **A fitted/empirical correction to alpha is forbidden.** The user was
  explicit. The 500-row dataset is a diagnostic and a reference only. No
  calibration term exists anywhere in the code and none should be added.
- **I once concluded the missing loss was substrate radiation on the basis of
  a one-parameter fit hitting R^2 = 0.98 over 500 rows. That was wrong** — it
  was fitting an artifact in a superseded dataset. Retracted. Do not rebuild
  an argument on correlation strength alone.
- **A quasi-static periodic unit cell cannot be 1:1 with the CST differential.**
  Verified numerically, not assumed: it has no radiation channel of any kind.
  It is additive and orthogonal, and complete for `delta n_m` / `delta Z0`, but
  `delta alpha` is ohmic-only and a lower bound.
- **3D Floquet full-wave with PML is not viable in Python at the required
  speed.** The leakage wave has a 3.0 mm lateral wavelength, so the PML must
  absorb a 3 mm wave while the mesh resolves a 0.1 um slot rim — millions of
  DOF, hours.
- Splitting a shapely MultiPolygon into one femwell entry per piece makes its
  boolean pass hand gmsh empty shapes (opaque `IndexError` inside pygmsh).
  Pass the MultiPolygon whole and sanitise slivers first.
- Sheet-conduction meshes must have nodes stranded inside the removed slot
  dropped, or the stiffness matrix gets empty rows and the solve returns NaN.

### Open questions needing a human decision

1. Which of A+ / C to build for the leakage term — or neither for now.
2. The stepped-electrode geometry: needs the real layer thicknesses and the
   conformal metal profile from the user before it can be rebuilt.
3. New CST multilayer runs on the stepped cross-section will be needed to
   validate anything built for that family; the 498 rows are all flat-electrode.
4. Unresolved since early in the project: the COMSOL `.mph` carries two gold
   nodes, `4.1e7` and `4.56e7` S/m. The notebooks use `4.561e7`. Picking the
   other would move conductor loss by 5.5 %.

## Next steps

1. Hand the notebook to the user to run against their own CST geometries:
   zero-tee first, then compare `delta n_m` and `delta Z0` (complete) and
   `delta alpha` (ohmic lower bound).
2. On the user's decision, start route A+ or route C for the leakage term.
3. Only after that, revisit the stepped-electrode cross-section, built from
   supplied dimensions rather than inferred from a screenshot.

## Log

### 2026-09-21T13:45Z
- Direction reset by the user: the section-average perturbation was never the
  agreed method and is wrong (C right, L ~30 % low -- a stack of 2D slices
  cannot see the return current meandering around the slot in z).  Removed the
  unit-cell notebook entirely (commit eab79e3).
- Adopted the agreed method: layered-medium MoM (Route C), the 1:1 translation
  of CST HF Multilayer, built in 4 validated phases under notebooks/mom/.
- PHASE 1 COMPLETE, all six gates PASS: layered-medium mixed-potential Green's
  function.  Scalar G_q and vector G_A from the transmission-line spectral form,
  inverted by a Sommerfeld integral with quasi-static singularity extraction and
  a Hankel-split deformed contour (real head past the poles + two exponentially-
  decaying rays).  V1.1 free space 8e-14, V1.2 PEC image 9e-8, V1.3 single
  interface 3e-4, V1.4 TE0 pole n=2.54141 (=2.5414), V1.5 symmetry 0, V1.6
  interpolation 5e-5.  Table 10 nm-10 mm built in ~17 s.
- Deliverables in notebooks/mom/: layered_greens.py, stack_params.py,
  phase1_greens_function.ipynb, green_function_table.npz, te0_pole.json,
  phase1_report.md, phase1_greens.png.
- STOPPED per the spec: awaiting user approval before Phase 2 (MPIE MoM).

### 2026-09-21T10:05Z
- Created this file.
- Verified the zero-tee sanity check on the rebuilt notebook by actually
  running it: all six deltas exactly `0.000000e+00`. Previously only asserted.
- Fixed a divide-by-zero cosmetic in cell `[3]`'s ohmic-ceiling gauge that
  fired on exactly that zero-tee path; notebook re-executed clean.
- Rebuilt the perturbation notebook from six cells to four (`2c924ad`):
  dropped the multi-level electrode support (wrong and out of scope), the
  diagnostic figures, the three-panel cross-section display, the exaggerated
  vertical scale, and the CST-comparison cell.
- Earlier the same session: `dd79266` quiet mode and skfem log silencing,
  `c5e07da` made the notebook self-contained (it had required the reference
  CSV to start, which the user correctly called out as wrong for a simulator),
  `6ecdcf5` fixed the CSV path resolution, `5d19f8a` the original assessment.
