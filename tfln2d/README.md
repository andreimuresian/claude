# Pure-Python replacement for the COMSOL 2D + CST 2.5D pipeline

Status: **feasibility prototype**. The kinematic half is working and validated;
the loss half and the 2.5D half are specified but not yet built.

## Why this can work

The composite method never uses either simulator's *absolute* answer for the
periodic loading. It uses only three differences per geometry:

    dL     = L_etched - L_unetched          (200 um unit cell, lumped Pi)
    dC     = C_etched - C_unetched
    dalpha = alpha_inf,etched - alpha_inf,unetched   (N+1 minus N)

Because every one of those is a difference between two runs of the *same*
solver on nearly identical geometry, common-mode error cancels. A replacement
solver therefore does not have to match CST in absolute terms — it only has to
get the *difference* right. That is a far weaker requirement than reproducing
CST, and it is what makes a Python port tractable.

It also means the port is directly testable: the existing 500-geometry CST
dataset and the 200-geometry 3D time-domain set are a ready-made, fully
labelled regression benchmark.

## What is implemented

| Module | Replaces | State |
|---|---|---|
| `geometry.py` | COMSOL geometry sequence | working, 5 swept DOF |
| `materials.py` | COMSOL parameter list | working; Sellmeier matches COMSOL to 7 digits |
| `mesh.py` | COMSOL meshing | working (gmsh via femwell) |
| `quasistatic.py` | `emw` Mode Analysis (kinematics) | working and converged |
| `modesolve.py` | `emw` Mode Analysis (full-wave) | working for n_m; **loss not yet trustworthy** |

## Measured results (nominal geometry, 60 GHz)

Quasi-static extraction, mesh convergence:

| resolution | elements | n_m | Z0 (ohm) | alpha_c (dB/cm) |
|---|---|---|---|---|
| 1.0   | 25 338  | 1.9259 | 32.169 | 3.217 |
| 0.5   | 66 636  | 1.9399 | 33.208 | 3.497 |
| 0.25  | 180 562 | 1.9438 | 33.561 | 4.210 |
| 0.125 | 564 276 | 1.9444 | 33.767 | 4.512 |

`n_m` and `Z0` converge cleanly. `alpha_c` does **not** — see below.

Width sweep against the two impedance anchors quoted in the thesis
(from the CST 3D time-domain ABCD extraction):

| WS (um) | n_m | Z0 (ohm) | alpha_c (dB/cm) | CST Z0 |
|---|---|---|---|---|
| 20  | 1.9597 | 37.4 | 4.811 | ~41 |
| 35  | 1.9959 | 32.8 | 4.498 | - |
| 60  | 2.0331 | 29.3 | 4.166 | - |
| 80  | 2.0517 | 27.7 | 4.024 | - |
| 100 | 2.0646 | 26.7 | 3.896 | ~29 |

The slope is right (-10.7 ohm over the span, against -12 ohm for CST) with a
consistent ~8% offset. A uniform offset points at a fixed geometry/material
assumption rather than a solver problem; the leading suspect is the missing
LN permittivity tensor (below).

**The U-shape artifact does not appear.** `alpha_c` declines monotonically
with WS, which is the physically correct behaviour the thesis had to recover
by enlarging the COMSOL domain. The quasi-static formulation has no radiating
outer boundary, so it is structurally immune to the scattering-boundary
reflection that produced the artifact.

## Known gaps, quantified

**1. Anisotropic permittivity is mandatory, not optional.**
`femwell.maxwell.waveguide.compute_modes` multiplies by a *scalar* epsilon, so
LiNbO3 is currently isotropic. Measured sensitivity at fixed geometry:

| eps_LN | n_m | Z0 (ohm) |
|---|---|---|
| 28.0 | 1.9438 | 33.56 |
| 35.5 | 1.9943 | 32.71 |
| 43.0 | 2.0431 | 31.93 |

That is a 5% swing in `n_m` — roughly three times the composite method's
entire error budget against the 3D benchmark (1.48% MAPE). The tensor has to
go in before any of this is calibrated.

**2. Conductor loss needs an impedance boundary condition.**
Two routes were tried and neither is yet adequate:

- *Perturbative surface resistance* (`quasistatic._conductor_loss`): cheap and
  gives the right trend, but the integral does not converge under refinement
  (3.22 -> 3.50 -> 4.21 -> 4.51 dB/cm). The electrode corner current density
  is singular, so the contour integral grows without bound.
- *Gold as a lossy dielectric domain* (`modesolve`): gives 7.14 dB/cm against
  a COMSOL baseline near 4.7-5.0. The 304 nm skin depth is unresolved by the
  mesh, so the dissipated power is wrong.

The fix is the same one COMSOL uses: a Robin surface-impedance condition on
the electrode outline, Zs = (1+j)/(sigma delta). This is a boundary term in
the weak form, not a new solver.

## Next steps

1. Tensor-valued epsilon in the vector mode solver (fork the ~15-line weak
   form in `compute_modes`).
2. Surface-impedance (Robin) boundary condition on the electrodes.
3. Port the optical side: `ewfd` mode analysis + electrostatics for VpiL, plus
   the 1310/1311 nm finite difference for n_g. `femwell.coulomb` already does
   the electrostatics; the overlap integral is post-processing.
4. Port the mode filters (impedance bound, symmetry sieve, TEM purity) — pure
   post-processing, mechanical to move.
5. Regress all of the above against the 500-geometry COMSOL dataset.
6. Only then tackle the 2.5D half. See the project notes for why the
   recommended route is a 3D Floquet unit cell rather than reimplementing a
   layered-media MoM.
