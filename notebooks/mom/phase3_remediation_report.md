# Phase 3 Remediation — common-mesh differencing and root-finder audit

Scope: the two targeted fixes only, on the same 5 rows (118, 416, 121, 38, 49),
at h = 9 um.  Kernel, assembly, eigenvalue and RLGC extraction reused verbatim
from Phase 3.  Compared against a Phase 3 run at the **same** h = 9 um with
independent meshes, so exactly one thing changes between the two columns.

## Headline

**Neither fix improved the failing gates.**  Both produced decisive negative
information, and the audit found one real defect (row 49).  The most useful
output of this remediation is not a repaired number — it is that the error in
dC is now known *not* to be discretisation, and the quantity that is actually
validated has been correctly identified.

## Gate 3R.1 — common-mesh construction: PASS

The remediation spec had the construction backwards.  It proposed meshing the
etched geometry and flipping an "is metal" flag on triangles inside the slot;
but the RWG unknowns live on metal only, so the etched mesh has no triangles
inside the slot and there is nothing there to re-tag.  The construction must
run the other way: mesh the **unetched** metal with the tee outline embedded as
an internal constraint (the slot is a separate gmsh surface, fragmented against
the surrounding ground so the triangulation is conformal across its rim), then
**delete** the slot triangles to obtain the etched cell.

Consequently the spec's stated invariant — identical triangle counts — is
unsatisfiable, and equal counts would mean the slot had not been cut.  The
correct invariant, verified on every row, is that the etched triangle set is a
strict subset of the unetched one with bit-identical shared rows
(`shared_identical=True`), on one shared `nodes` array.

| row | Nt unetched | Nt etched | Nt slot | Ne unetched | Ne etched | slot area frac |
|---|---|---|---|---|---|---|
| 118 | 782 | 656 | 126 | 1128 | 919 | 0.137 |
| 416 | 962 | 880 | 82 | 1390 | 1252 | 0.032 |
| 121 | 954 | 738 | 216 | 1379 | 1027 | 0.186 |
| 38 | 928 | 664 | 264 | 1339 | 909 | 0.262 |
| 49 | 962 | 772 | 190 | 1391 | 1066 | 0.115 |

The slot triangle fraction reproduces the analytic metal-area ratio (row 38:
0.262 measured vs 1.03e-8 / 3.93e-8 = 0.262), confirming the tagging.

One bug was found and fixed during the build: classifying gmsh surfaces as
metal/slot by a centroid point-in-polygon test fails, because the etched ground
is a C-shape around the tee whose centroid lies **inside** the notch.  The
fragment map is used instead.

## Gate 3R.2 — root audit: PASS on 9 of 10 cells, row 49 etched FLAGGED

The spec asked for a `sigma_min(Z(beta))` sweep.  That diagnostic does not work
here and Phase 3 had already established why: the EFIE carries a large loop
(divergence-free) near-null subspace whose singular values are O(w) and almost
independent of beta, pinning `sigma_min` at ~4.7e-11 flat from n = 0.5 to
n = 232.  The sweep would have returned a horizontal line.  Substituted
`|g(beta)| = 1/(y^T Z^-1 y)` with the transmission-line test vector — the
quantity the solver already root-finds on — which projects out the loop
subspace.  It is also nearly free, being the bracketing scan the driver runs
anyway on a finer grid (14 points, n = 1.30 to 3.15).

| row | unetched dip | depth | etched dip | depth |
|---|---|---|---|---|
| 118 | n = 2.296 | 5.6x | n = 2.581 | 3.1x |
| 416 | n = 2.296 | 4.4x | n = 2.438 | 5.3x |
| 121 | n = 2.296 | 5.5x | n = 2.723 | 8.4x |
| 38 | n = 2.296 | 5.1x | n = 2.865 | 5.3x |
| 49 | n = 2.296 | 4.6x | **none in window** | — |

**No spurious modes.**  Nine of ten cells show exactly one local minimum in the
window, so the secant had no competing root to converge to.

**Seed-lock is ruled out.**  The Phase 3 unetched index was near-constant at
~2.23–2.30 and sat next to the old 7-point grid node at n = 2.2, which looked
like the secant walking to its seed.  The open 14-point sweep finds a genuine
isolated minimum at n = 2.296 with |g| rising monotonically to both ends of the
window; the old grid node merely happened to be adjacent to the true root.  The
etched roots move to 2.44–2.87, far from any old grid node, so the secant
demonstrably tracks the root when the root moves.

**Row 49 etched is flagged.**  |g| is still falling at the n = 3.150 window
edge, so there is no interior minimum; the seed fell back to the edge and the
secant ran to n = 3.1708 — above the window and only 4.2 % below the TM0
surface-wave index (3.309).  Its overlap with the transmission-line test vector
is 0.390, against 0.54–0.64 on every other cell.  That root is **not a
confirmed guided mode**, and row 49 is one of the two rows that fail dL.  This
is the risk the spec named, and the audit caught it.

## V3.4c (dC) and V3.4a (d_alpha): FAIL, unimproved

All errors in %, h = 9 um, independent-mesh column rescored with the correct
x P lumped conversion.

| row | d_alpha indep | d_alpha common | dL indep | dL common | dC indep | dC common |
|---|---|---|---|---|---|---|
| 118 | 79.7 | 70.3 | 1.0 | 1.0 | 41.6 | 50.2 |
| 416 | 419.7 | 547.7 | 67.1 | 65.7 | 41.1 | 57.2 |
| 121 | 177.4 | 167.6 | 0.5 | 0.5 | 87.3 | 91.3 |
| 38 | 344.6 | 346.1 | 5.8 | 6.4 | 118.5 | 124.3 |
| 49 | 77.2 | 77.1 | 49.7 | 49.7 | 65.3 | 67.7 |
| **median** | 177.4 | **167.6** | 5.8 | **6.4** | 65.3 | **67.7** |
| **worst** | 419.7 | **547.7** | 67.1 | **65.7** | 118.5 | **124.3** |

Gates: V3.4a d_alpha FAIL (167.6 % vs 25 % median).  V3.4c dC FAIL (67.7 % vs
20 % median).  Every quantity moved by a few percent, most of them slightly
worse.  Forcing the two cells onto one triangulation changed essentially
nothing.

Per the remediation spec's own branch, this means **the dC error is not
mesh-driven**.  The Phase 3 diagnosis — that uncorrelated discretisation error
in a small difference of two large numbers explained the dC failure — is
refuted.  That diagnosis was mine, and it was wrong.

## Gate 3R.3 — dL regression: no degradation

dL median 5.8 % -> 6.4 %, worst 67.1 % -> 65.7 %.  Within run-to-run noise; the
common mesh neither helps nor harms dL.  (dL fails the per-row gate both before
and after, so this is not a regression introduced here.)

## The loop-mode hypothesis: REFUTED

`line_rlgc` takes the mode as `Vh[-1]`, the smallest singular vector.  Given the
pinned loop near-null subspace, this might have been a divergence-free loop
current rather than the transmission-line mode — which would have made
`q = C_b x` near-zero and C a ratio of two small numbers, an independent second
bug behind dC.  Tested by computing C and L from both `Vh[-1]` and from one
step of inverse iteration `x = Z^-1 y` (which targets the longitudinal-current
mode by construction).

**The two agree to every printed digit on all 10 cells**, with identical test-
vector overlaps.  At the converged root the smallest singular vector *is* the
transmission-line mode.  There is no second bug here.

## What is actually validated: the fractional index perturbation

The comparison that survives is the dimensionless fractional index shift — a
direct ratio of two numbers on each side, with no unit conversion and no
cancellation:

| row | d(n_m)/n_m MoM | d(n_m)/n_m CST | ratio | dC/C MoM | dC/C CST | ratio |
|---|---|---|---|---|---|---|
| 118 | +0.1574 | +0.1632 | **0.96** | -0.0402 | -0.0832 | 0.48 |
| 416 | +0.0803 | +0.0769 | **1.04** | -0.0205 | -0.0438 | 0.47 |
| 121 | +0.1904 | +0.1784 | **1.07** | -0.0068 | -0.0793 | 0.09 |
| 38 | +0.2499 | +0.2546 | **0.98** | +0.0215 | -0.0859 | **-0.25** |
| 49 | +0.3999 | +0.2986 | 1.34 | -0.0347 | -0.1051 | 0.33 |

The Bloch eigenvalue perturbation matches CST to **4–7 % on four of five rows**.
The fifth is row 49, the row the audit flagged as not a confirmed guided mode.
The capacitance perturbation over the same geometries is wrong by factors of
2 to 11 and has the wrong sign on row 38.

This also **qualifies the Phase 3 headline**, which credited dL as validating
the kernel, assembly, eigenvalue and RLGC extraction simultaneously.
Decomposing dL = d(beta^2)/(w^2 C) - (beta^2/w^2) dC/C^2 shows dC contributes
only 2.3–14.2 % of dL:

| row | dL total | via d(beta^2) | via dC | dC share |
|---|---|---|---|---|
| 118 | 1.158e10 | 9.938e9 | 1.644e9 | 14.2 % |
| 416 | 5.676e9 | 4.951e9 | 7.249e8 | 12.8 % |
| 121 | 1.357e10 | 1.326e10 | 3.071e8 | 2.3 % |
| 38 | 1.888e10 | 2.005e10 | -1.171e9 | 6.2 % |
| 49 | 3.002e10 | 2.797e10 | 2.055e9 | 6.8 % |

dL is 86–98 % a restatement of d(beta^2).  It was never a strong test of the
capacitance extraction, and its accuracy on rows 118/121 depends partly on the
too-large absolute L cancelling against the too-small dC/C.  **d(n_m)/n_m is
the better-founded statement of the same validated physics**, and it should
replace dL as the headline result.

The remaining defect is therefore localised to the charge/potential extraction
in `line_rlgc`, not to the kernel, the periodic assembly, or the eigensolver.

## Second finding: the absolute index is geometry-blind

Recorded because it is a sharper statement of the V3.3 failure than "20.9 %
high", and it was free to obtain (one dataset read, no compute).

| | spread of unetched n_m over the 5 rows |
|---|---|
| CST `nm_baseline_val` | **17.8 %** (1.744 – 2.054) |
| CST, all 500 rows | 42.6 % (1.510 – 2.153) |
| MoM unetched n_m | **1.2 %** (2.268 – 2.296) |

Across WS 56–70 um and GAP 8.6–18.7 um, CST's baseline index moves 17.8 % and
the MoM's moves 1.2 %.  The absolute error is therefore not an offset that a
constant would absorb — the solver is nearly **insensitive to the CPW
geometry** in n_m while recovering roughly the right magnitude, and it recovers
the *perturbation* accurately.  Note the two facts are consistent: a
multiplicative bias on beta cancels in the ratio d(n_m)/n_m.

Untested candidate, recorded and not pursued (out of scope): Phase 3 measured a
large rho-independent term in the periodic scalar kernel, Im(G_q,per) ~ -1.19e13
constant across the cell, matching the n = 0 surface-wave harmonic.  A term
depending on the stack but not on WS/GAP would pin n_m this way.  This has NOT
been tested and is not an established cause.

## Observation on d_alpha, flagged as untested

d_alpha remains the worst gate (167.6 % median).  The etched index exceeds the
TE0 surface-wave index (2.540) on four of five rows, so those modes are
phase-matched to leak into TE0:

| row | etched n_m | excess over TE0 | MoM alpha_etched / CST alpha_final |
|---|---|---|---|
| 416 | 2.4415 | -0.10 | 1.14 |
| 118 | 2.6397 | +0.10 | 1.27 |
| 121 | 2.7048 | +0.16 | 1.45 |
| 38 | 2.8335 | +0.29 | 2.79 |
| 49 | 3.1708 | +0.63 | 1.61 |

The ordering is suggestive but not monotonic (row 49 breaks it), and Phase 3
already produced one confident ordering prediction that failed.  This is
recorded as an observation, **not** as a diagnosis.

## Verdict

| item | result |
|---|---|
| 3R.1 common-mesh construction | PASS (spec corrected: unetched -> delete slots) |
| 3R.2 root audit, spurious modes | PASS — one clean minimum on 9/10 cells |
| 3R.2 row 49 etched | **FAIL — no minimum in window, root above it, near TM0** |
| V3.4c dC | FAIL 67.7 % (was 65.3 %) — **not mesh-driven** |
| V3.4a d_alpha | FAIL 167.6 % (was 177.4 %) |
| 3R.3 dL regression | no degradation (5.8 % -> 6.4 % median) |
| loop-mode second bug | **refuted** — svd and inverse iteration identical |
| d(n_m)/n_m vs CST | **4–7 % on 4 of 5 rows** |

Which fix worked: **neither**.  What was gained: the dC failure is excluded
from being a discretisation effect; the loop-mode hypothesis is excluded; row
49's eigenvalue is exposed as unconverged onto a guided mode; and the validated
result is restated on firmer ground as d(n_m)/n_m rather than dL.

Not started, pending approval: any change to `line_rlgc`, any investigation of
the geometry-insensitivity, any thick-metal work, Phase 4.

## Files

| file | role |
|---|---|
| `common_mesh.py` | mesh-once differencing (unetched -> delete slot triangles) |
| `root_audit.py` | `|g(beta)|` sweep + local-minimum detection |
| `phase3r.py` | remediation driver (audit + both eigenvector extractions) |
| `phase3r_plot.py` | scatter, common vs independent mesh |
| `data/phase3r_h9.json` | full results incl. every scan curve |
| `data/phase3r_audit_h9.txt` | the |g| tables for all 10 cells |
| `phase3_remediation.png` | scatter plot |

No `phase3_floquet.ipynb` exists in the repository (Phase 3 was driven from
`.py` files); the spec's request to update it is therefore not applicable.
