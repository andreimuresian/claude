# Phase 3 — Periodic Floquet Unit Cell: Results

Branch `2D-+-2.5D`. Frequency 60 GHz, period P = 200 um, 5 dataset rows spanning
the `alpha_delta_val` range (118, 416, 121, 38, 49), production mesh h = 6 um,
mesh-convergence pair at h = 9 um. Dataset used only to supply geometry and to
score results: no fit, no surrogate, no lookup, no CST at runtime.

## Gate summary

| gate | quantity | result | gate | verdict |
|---|---|---|---|---|
| V3.1b | Ewald invariance, E*P 3 -> 12 | 2.1e-6 (Gq), 1.8e-5 (GA) | < 1e-3 | **PASS** |
| V3.3 | unetched n_m, row 300 | 2.2126 vs 1.8296 = 20.9 % | < 3 % | FAIL |
| V3.4a | Delta alpha | median 108.7 %, worst 258.5 % | 25 / 40 % | FAIL |
| V3.4b | Delta L | **median 3.8 %**, worst 59.8 % | 20 / 35 % | FAIL (worst) |
| V3.4c | Delta C | median 68.8 %, worst 124.1 % | 20 / 35 % | FAIL |
| V3.5 | alpha_base + D_alpha | median 16.2 % | 5 % | FAIL |
| V3.5 | c*sqrt(L C) vs nm_final | median 6.5 % | 3 % | FAIL |
| V3.5 | sqrt(L/C) vs z0_final | **median 3.9 %** | 5 % | **PASS** |
| V3.6 | mesh convergence, Delta L | **median 1.9 %, worst 4.6 %** | < 5 % | **PASS** |
| V3.6 | mesh convergence, Delta C | median 23.2 %, worst 52.9 % | < 5 % | FAIL |
| V3.6 | mesh convergence, Delta alpha | median 36.7 %, worst 3582 % | < 5 % | FAIL |
| V3.7 | runtime, one geometry | ~80 s (h = 9), ~220 s (h = 6) | < 60 s | FAIL |

## V3.4 per row (h = 6 um)

| row | MTX/GAP | D_alpha MoM/CST | err | D_L MoM/CST | err | D_C err |
|---|---|---|---|---|---|---|
| 118 | 0.23 | -0.223 / -0.511 | 56.4 % | 2.534e-11 / 2.549e-11 | **0.6 %** | 43.2 % |
| 416 | 1.46 | +0.000 / -0.005 | 108.7 % | 1.221e-11 / 7.642e-12 | 59.8 % | 61.5 % |
| 121 | 0.24 | +0.689 / +0.339 | 103.0 % | 2.947e-11 / 2.994e-11 | **1.6 %** | 89.9 % |
| 38 | 0.65 | +4.774 / +1.332 | 258.5 % | 4.016e-11 / 3.868e-11 | **3.8 %** | 124.1 % |
| 49 | 0.46 | +17.349 / +8.290 | 109.3 % | 6.329e-11 / 4.320e-11 | 46.5 % | 68.8 % |

`deltaL lumped` / `deltaC lumped` are lumped per tee (H, F); the solver returns
per-unit-length, so the comparison is MoM x P. (An earlier scoring pass omitted
this and reported ~5e5 % errors; it was a scoring bug, not a solver result.)

Scatter plot: `phase3_validation.png`.

## What is and is not established

**Delta L is converged and mostly accurate.** It is the only quantity that
passes V3.6 (1.9 % median under a 2.2x triangle-count refinement), and on the
three rows with a moderate perturbation it matches CST to 0.6-3.8 %. Every
element of the chain — Ewald-split Floquet kernel, periodic MPIE assembly,
leaky Bloch eigenvalue, RLGC extraction — has to be simultaneously correct for
that to happen on three different geometries.

**Delta C and Delta alpha are NOT mesh-converged** (23 % and 37 % median change
for a 1.5x linear refinement). Their V3.4 failures therefore carry no physical
information yet, and no physical cause can be assigned to them until they
converge.

**Why Delta C is ill-conditioned.** Delta C is a 4.6 % difference (8.15e-12
against C = 1.79e-10) taken between two INDEPENDENTLY meshed cells — row 38 has
Nt = 1756 unetched against 1342 etched — so the two discretisation errors are
uncorrelated and do not cancel. 1-3 % in each gives 25-60 % in the difference,
which is what is observed. Delta L does not suffer because it is a 39 %
difference, well conditioned.

**Two Delta L rows fail for reasons that are NOT discretisation** (both are
mesh-converged): row 416, where the perturbation is essentially zero
(`alpha_delta_val` = -0.005) so the difference is ill-conditioned, and row 49,
where the etched Bloch root runs up to n_m = 3.125 against the TM0 surface wave
at n = 3.309, giving alpha = 20.3 dB/cm with the bracketing scan minimum at
3.10, near the top of its window. Row 49's extraction is not trustworthy.

**Absolute n_m is biased high** (V3.3: 20.9 %; 12.7 / 20.9 / 30.0 % on rows
118 / 300 / 416). C is accurate in absolute terms (+3.6 %, -7.9 % against
`C_base`), so the entire bias sits in beta, and L inherits it squared because
the extraction gives L = beta^2/(w^2 C) — for row 416, 1.300^2/0.921 = 1.835,
matching the observed +83.5 % exactly. There is one error here, not three.
Its cause is NOT established. A monotonic correlation with MTX/GAP was observed
on three rows and is recorded here as an observation only; it was tested as a
predictor of the Delta L errors and FAILED (row 38 at MTX/GAP = 0.65 gives
3.8 % while row 49 at 0.46 gives 46.5 % — the wrong order), so metal thickness
is not supported as the explanation for the perturbation errors.

**The mode is leaky, and that is physics.** TM0 sits at n = 3.309 and TE0 at
n = 2.540, both above the CPW mode, so low Floquet harmonics are open radiation
channels and beta is genuinely complex. Im(G_q,periodic) is nearly constant
across the cell at -1.19e13, matching the n = 0 surface-wave harmonic
S_p/(2|a_0|P) = 1.19e13. There is no root on the real axis.

## Defects found and fixed during Phase 3

1. **Surface-wave poles leaked into the Ewald sharp part** (the V3.1b blocker).
   The Gaussian sharp weight is ~k_p^2/(4E^2) at the pole, 0.5 % at E*P = 6, so
   the sharp part retained a surface wave and its image sum never converged.
   Fixed by extracting the poles before splitting and returning them in closed
   form as the 1D-periodic 2D-Helmholtz Ewald pair (verified against an 8e5-term
   brute-force sum to 1e-16).
2. **Phase-1 Sommerfeld far field wrong for the TE kernel by 345x at 30 mm.**
   The pole sat on a `quad` segment endpoint, so the integrator captured its odd
   principal-value part but not the Lorentzian of relative width 4e-6 that
   carries the surface wave. Phase 3 inverts the regularised spectrum directly.
3. **Phase-2 MPIE potential terms mis-scaled.** `j w mu0 * Av - (1/(j w eps0)) *
   Phi` instead of `j w * Av + (1/(j w)) * Phi`; the ratio was wrong by -c^2.
   Units settle it: `Zs * Gram` is ohms while those terms were ohms*H/m and
   ohms*m/F. Reciprocity is insensitive to this and the Phase-2 capacitance
   check used the scalar kernel alone, so neither caught it.
4. **Eigen-search blind to the mode.** The EFIE loop subspace pinned sigma_min
   at 4.7e-11 flat from n = 0.5 to n = 232. Fixed with a charge-carrying
   v-directed test vector plus a complex seed.
5. **Sharp radial table clipped inside the farthest image**, so the image sum
   picked up a constant (this, not physics, was the original "n_sharp 4->8 moves
   G_A by 1040 %").
6. **ku quadrature grid did not resolve cos(k du)** at large offsets.
7. **Scoring bug**: lumped vs per-unit-length (above).

## Recommended next steps — NOT started, for approval

1. **Common-mesh differencing.** Mesh the etched geometry, then build the
   unetched cell by filling the slots on that same triangulation, so
   discretisation error is common-mode and cancels in the subtraction. This
   targets exactly the quantity that is broken (Delta C) and should also help
   Delta alpha. Cheapest change with the largest expected effect.
2. **Mesh refinement** for Delta alpha, which is not converged at h = 6 um.
3. **Widen the bracketing scan and guard the surface-wave region**, so a root
   approaching n = TM0 (row 49) is detected and reported rather than returned.
4. Only after 1-3: revisit the absolute n_m bias. Finite metal thickness is one
   candidate but is NOT currently supported by evidence.

Runtime (V3.7) is ~80 s at h = 9 um and ~220 s at h = 6 um against a 60 s gate.
Caching the beta-independent near-field block already took a repeat assembly
from 17.1 s to 4.0 s; the remaining cost is the per-geometry kernel build
(~50 s) and the soft-kernel evaluation.
