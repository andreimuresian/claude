# Layered MoM (exact open boundary, CST's method)

Background: air half-space over LN (28, 43, 43) / SiO2 / Si 550 um / Si half-space, as CST.
Thick metal (the earlier MoM in ../mom used zero-thickness sheets and isotropic LN: its
plain-line n was 2.296 instead of ~1.95).

## Step 1: stack plane-wave response (`stack.py`, `test_stack.py` -> `test_stack.txt`)
4x4 transfer of tangential fields (LN is not uniaxial about the normal, TE/TM couple).
Checks: Fresnel TE/TM, oblique incidence, layers of the same medium, air gap
(R exp(-2 j ky d)), LN static image (1 - sqrt(28*43))/(1 + sqrt(28*43)), sheet source.  All pass.

## Step 2: 2D thick-metal MoM of the plain line (`mom2d.py`, `fw.py`, `run_fw2d.py`)
Surface currents on the metal contours (rooftop J_t, pulse J_z).  Free-space part in the
spatial domain (K0, log singularity analytic); reflected part spectral (all components) with
the LN quasi-static image extracted and added back spatially.  Leaky modes: outgoing
(improper) silicon waves inside the radiation region |kx| < sqrt(eps_Si k0^2 - beta^2).

Statics (`test_static.py` -> `test_static.txt`): C_air 46.91 pF/m (FEM 47.01, grounded box);
C with the stack gives n = 1.951 (2D full-wave FD: 1.952).

Row 49 plain line, PEC (`run_fw2d.txt`, contour mesh 0.2 and 0.1 um):

| GHz | n: MoM / FD / CST | alpha dB/cm: MoM / FD / CST |
|---|---|---|
| 20 | 1.9510 / 1.952 / 1.969 | 0.0074 / 0.009 / 0.000 |
| 60 | 1.9527 / 1.954 / 1.972 | 0.0494 / 0.051 / 0.109 |
| 100 | 1.9634 / 1.959 / 1.972 | 0.1420 / 0.153 / 0.144 |

Mesh refinement moves n by 0.03 %, alpha by < 0.1 %.  40-75 s per frequency.

## Step 3a: periodic cell, plain line (`cell3d.py`, `run_cell3d_plain.py` -> `run_cell3d_plain.txt`)

One 200 um period, Bloch-periodic currents, no ports.  The 3D matrix is a sum over Floquet
harmonics k_m = beta + 2 pi m / P of the validated 2D kernel (Line2D.Z at beta = k_m), weighted
by the z-spectra of the basis functions (J_t: contour rooftop x z pulse; J_z: segment pulse x
z rooftop).  Same stack, same leaky-branch handling, same LN image extraction as step 2; no
Ewald split, so the surface-wave poles that broke ../mom Phase 3 do not enter.  beta by the
complex secant on the Bloch eigenproblem.  Harmonics |m| > 1 are computed once and reused
across secant steps (checked: identical to 6 digits).

Plain cell must reproduce the 2D mode (row 49, PEC, same contour mesh):

| GHz | 2D n / alpha | 3D, Nz 8: n err / alpha err | 3D, Nz 16 (60 GHz) |
|---|---|---|---|
| 20 | 1.94916 / 0.00737 | -0.0003 % / 0.00 % | |
| 60 | 1.95086 / 0.04948 | -0.0029 % / 0.00 % | -0.0003 % / 0.00 % |
| 100 | 1.96156 / 0.14222 | -0.0082 % / +0.01 % | |

Error falls ~ h^2.5-3 with the z cell size h = P/Nz; harmonic range M = 2 Nz is converged.
~2 min per frequency at Nz 8.  Limitation of this test: with uniform 25 um z cells it does not
exercise the large harmonics (|k_z| up to ~1e7) that the tee's fine z mesh at the slot ends
will need; that is checked in step 3b.

## Z0 in mom_code and mom_cell (`fw.impedance`, `cell3d.plain_impedance`)

Definition as fem_code: power-current, Z_PI = 2P/|I|^2, written as N/I^2 with
N = int (E x H).z dA unconjugated (= 2P for a lossless mode; well defined for leaky modes).
N comes from reciprocity between the mode and its z-reversed partner (J_t kept, J_z reversed):
N = (j/2) Jb^T dZ/dbeta J  (per period: divided by P).  No field evaluation is needed, and
the same formula holds for the periodic cell.  I = total J_z on the signal (at z = 0 in the cell).
Check: using J instead of Jb gives -51.6 ohm (meaningless), Jb gives 36.69 ohm.

mom_code, row 49 plain line, PEC (`run_z0_2d.txt`), contour mesh hmin 0.4 / 0.2 / 0.1 um:

| GHz | Z_PI (ohm) | FD solver Z_PI / Z_VI | CST |
|---|---|---|---|
| 20 | 36.690 / 36.654 / 36.638 | 36.54 / 36.40 | 36.40 |
| 60 | 36.793 / 36.757 / 36.741 | 36.62 / 36.39 | 36.33 |
| 100 | 36.785 / 36.749 / 36.733 | - | 36.12 |

Quasi-static check: 1/(c sqrt(C C_air)) = 36.45 ohm (C from test_static.txt).
Same definition as the FD solver: +0.3 %.  CST's port impedance is ~1 % lower; the three
definitions (PI, VI, PV) already differ by 0.7 % in the FD solver.

fem_code is not the same geometry: it has the etched LN rib and SiO2 cap under the gap
(COMSOL model), mom_code and CST Multilayer a flat LN slab 0.46 - ETCH.  So mom_code vs
fem_code on Z0 compares geometries as well as solvers.

mom_cell vs mom_code on the plain period (`run_z0_cell.txt`, hmin 0.4 um mesh):

| GHz | mom_code Z_PI | mom_cell Nz 4 | mom_cell Nz 8 |
|---|---|---|---|
| 20 | 36.690 | -0.021 % | -0.006 % |
| 60 | 36.793 | -0.188 % | -0.054 % |
| 100 | 36.785 | -0.527 % | -0.151 % |

Converges as h^2 (h = P/Nz).  Z0 needs a finer z mesh than n for the same accuracy; for the
tee the differential (tee cell - plain cell on the same z mesh) removes most of this error.

## Step 3b: general periodic cell (`tee3d.py`, `tee3d_kern.py`, `tee3d_solve.py`), plain-line check

Frequency-domain MoM eigenmode solver of one 200 um period, metal surfaces meshed in 3D, any
in-plane metal shape (tees).  Validated on the plain line (zero-size tee), row 49, 60 GHz, PEC.

Reference: mom_code on the same cross-section mesh (`ref2d_same_mesh.py`).  How converged is it
(`ref2d_conv.txt`, `ref2d_grade.txt`): alpha is converged (0.0494-0.0495 dB/cm on every mesh);
n and Z0 drift slowly with the smallest cell at the metal corners only (largest cell, growth
rate, spectral cutoff: no effect): n 1.9510 / 1.9521 / 1.9527 / 1.9533 for 0.4 / 0.2 / 0.1 /
0.05 um, Z0 36.80 / 36.76 / 36.74 / 36.73 ohm.  Both codes shift together when refined, so the
comparison is made on the same mesh.

Bug found and fixed: only the nearest periodic copy of each face was integrated exactly; with
long faces the next copy touches the face but was treated as distant (2 cells along the line:
n -1.7 %, alpha +10 % against the Floquet cell on the same discretization).  Now the three
nearest copies are exact.

Residual after the fix (insensitive to harmonics count, spectral cutoff, quadrature, cell
length along the line): n +0.04 %, alpha +1.3 % (0.0007 dB/cm), Z0 +0.02 %.  A fixed bias of
the plain line; it cancels in the tee - plain difference.

## Step 3c: tee cell, first dataset row (row 161, 60 GHz)

Row 161: α_final 3.11 dB/cm in the dataset (a typical row; row 49, 10.8 dB/cm, is an outlier).
Run: `ROW=161 python run_tee_cell.py 60 {tee|plain} 1.5 12 4 10 <n guess> <cache prefix>`.

**Mode finder (`Solver.solve_driven`).** The signal line is driven and the line mode is the
zero of 1/h(β), h = yᵀ Z(β)⁻¹ y (Newton inside the local linear model of Z, rebuilt around each
estimate; secant on the build-point fixed point).  No choice among the thousands of eigenvalues
of the pencil.  Every Z(β) is cached on disk (a container restart costs one build).

**Bugs found on the way** (each made the tee answer wrong while the plain line looked right):

| bug | symptom | fix |
|---|---|---|
| z grading: a fine end next to a coarse end was not graded | row 49: one 16.7 µm cell at the slot ends | `grade` lays the smaller step first, no slivers |
| fixed 220 µm lateral cutoff | row 161 plain α 0.020 instead of 0.058 (cell 223 µm wide) | cutoff covers the whole cell |
| cutoff, k grid and harmonic set chosen from Re β | Z not analytic (m = 5: 98 %), α oscillating between passes, Z0 30 Ω | chosen from the harmonic index |
| long-range harmonic on the real k axis | not analytic in β | complex path above the Si branch point |
| k step ignored the piece width | aliases of 12 µm pieces ~1 µm away | dk = 2π/(4 gmax + 2 wmax) |
| decay 25 in the evanescent cutoff | spurious poles beside the line mode: n 2.296 / 2.320, Z0 50 / 36 Ω | decay 150 |

Cutoff convergence (tee, 60 GHz, PEC): decay 100 / 150 / 250 (one pass from 150): n 2.3077 /
2.3113 / 2.3111, α 1.260 / 1.327 / 1.324 dB/cm, Z0 49.0 / 48.5 / 48.5 Ω.  Plain cell unchanged
(n 1.98568, α 0.0584, Z0 42.49 Ω; 2D reference 1.9847, 0.0577, 42.2).

**Row 161 against the dataset** (60 GHz):

| | mom_cell | qs3d | dataset |
|---|---|---|---|
| n tee / plain | 1.164 | 1.165 | 1.136 |
| Z0 tee (Ω) | 48.5 | 49.1 | 50.2 |
| Δα substrate + radiation (PEC, tee − plain) | +1.27 | – | |
| Δα ohmic (qs3d, on the COMSOL baseline) | +0.13 | +0.13 | |
| Δα total | +1.40 | | +1.05 |
| α_final = COMSOL baseline 2.06 + Δα | 3.46 | | 3.11 |

n and Z0 agree with qs3d to 0.1 % and 1 %; the dataset's n is 2.4 % lower (COMSOL rib vs flat
slab), its Z0 3 % higher.  α_final is 11 % above the dataset, the size of the expected offset
(COMSOL baseline α ~10 % low).  Runtime: ~2 h per tee solve (N 3476, 4 cores, 2 builds per pass).
