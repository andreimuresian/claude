# Section average of 2D cross-sections (author's slides), tested on 14 rows

`xsec2d.py` is the author's 2D FEM notebook (`unetched_nmZ0_aRF_Claude.ipynb`)
ported unchanged: geometry with rib and cap, ε_LN (28, 44, 44), mesh controls,
quasi-static extraction, eigen solver, mode filters, IBC correction. The only
addition: the ground can be split into metal pieces. On row 86 section C it
reproduces the notebook to the printed digits (n 1.708941, Z0 62.5650,
α 2.1922 dB/cm, same 292 767 DOF).

The 4-dof tee gives three cross-sections per 200 µm period, with lengths fixed
by the geometry (nothing fitted):

| section | length | right ground metal |
|---|---|---|
| A, stem + head | min(L1, L2) | x_gi + W1 + W2 … x_go |
| B, L2 > L1 | L2 − L1 | finger x_gi … x_gi + W1, ground x_gi + W1 + W2 … x_go |
| B, L1 > L2 | L1 − L2 | x_gi + W1 … x_go |
| C, no slot | P − max(L1, L2) | x_gi … x_go (the baseline) |

L, C, R, G are length-averaged; n = c√(LC), Z0 = √(L/C), α = R/2Z0 + GZ0/2.
"Additive" = dataset baseline + (average − section C).

```
python conv.py 49 118 408   # mesh convergence            -> conv.json
python run_rows.py          # 14 rows x 3 sections        -> run_rows.json (~15 min, 4 cores)
python report.py            # tables                      -> report.txt
```

## The slide-4 result rests on a typo

Slide 4 lists C(centre of T) = 9.346e-10 F/m. Its own n and Z columns give
2.049 / (73.16 · c) = 9.34e-11, and removing metal can only lower C. The quoted
n 2.315 (−3.1%) and Z0 39.84 (−2.1%) reproduce only with the 10× value. With
9.34e-11 the same weights give n = 2.080 (−12.9%) and Z0 = 44.35 (+9.0%).

## Results (14 rows, quasi-static + IBC, notebook mesh)

Rows: the 5 with 3D quasi-static results (`../qs3d`), 7 at the 5–95 %
quantiles of nm_final/nm_baseline (1.04–1.34), 2 with L1 > L2.

| finger treatment | median abs error n / Z0 / α | max abs error n / Z0 / α |
|---|---|---|
| slides: the finger carries current like the rest of the ground | 10.5 / 9.5 / 15.3 % | 22.1 / 24.2 / 78.9 % |
| floating: grounded for C, no net current for L and R | 2.3 / 2.9 / 21.5 % | 7.9 / 6.3 / 69.3 % |

(Additive form. For n and Z0 the absolute form is within 0.6 % of it.) All n and Z0 errors are
negative. On the qs3d rows the 3D unit cell does better on n (≤ 0.9 %) and
about the same on Z0 (−0.6 to −6.1 %).

Why the slides version cannot work: every section on its own is a uniform
quasi-TEM line with n_i ≈ n_baseline, and averaging L and C of such lines
cannot reach the slow-wave index. The tee works because the finger keeps the
gap capacitance (it is at ground potential) while the return current cannot
use it (it is attached at one end only). Treating it as a floating conductor
for the magnetic part encodes exactly that.

Where the floating version still misses (row 302, n −7.9 %; rows 130, 363,
−5 %): the slot is short along the line compared with its depth, so the
current spreads in 3D beyond the section boundaries and the slices
under-count ΔL.

Run time: 59 s per geometry on one core (row 220, largest mesh, three
quasi-static solves).

## α: not reproducible with this method

Δα (dB/cm), dataset vs 2D floating-finger average:

| row | 355 | 448 | 416 | 206 | 408 | 398 | 130 | 118 | 121 | 363 | 38 | 302 | 49 | 220 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| dataset | −0.16 | −0.11 | −0.01 | +0.03 | −0.35 | +0.10 | **+5.06** | −0.51 | +0.34 | **+1.05** | **+1.33** | +0.06 | **+8.29** | **+1.89** |
| 2D | −0.07 | −0.21 | −0.24 | −0.13 | −0.51 | −0.25 | +0.13 | −0.59 | −0.23 | −0.39 | −0.10 | −0.88 | +0.79 | −0.15 |

The 2D average reproduces the ohmic relief where Δα is small (Z0 rises, R
changes little). It misses every large positive Δα. A slice is uniform along
the line: it has no slot ends, so no radiation or substrate-mode excitation and
no current crowding at the slot corners.

## Mesh convergence (`conv.json`)

Rows 49, 118, 408, all three sections, up to 1.45 M elements (bulk mesh 2×
finer, corner and skin collars 2× finer than the notebook):

- n: notebook mesh within 0.05 % of the finest;
- Z0: within 0.23–0.29 %, closing monotonically under bulk refinement;
- α: sensitive to the corner collar. Halving the 0.05 µm corner size raises α
  by 2.2–4.8 %; the IBC integrand is singular at the 90° corners. Δα moves by
  ~5 %. The notebook's corner size is kept, since it reproduces COMSOL on its
  validation row.

## Side findings on the baseline (section C vs dataset baseline, 14 rows)

- quasi-static + IBC: n −0.1 to −0.3 %, Z0 −0.3 to −0.7 %.
- notebook full-wave: Z0 +0.0 to +3.6 %, growing as the mode score drops from
  0.497 to 0.481 (coupling to the PEC box). On sections A and B the eigen
  solve is worse: no mode passes the filters on 8 of 14 A sections, and a 2D
  eigenmode cannot tie the finger to ground. So the report uses quasi-static.
- α (both solvers agree): −10.9 % to +1.4 % against the dataset baseline. Part
  of it is the conductivity: the notebook uses σ = 4.56e7, while
  `../validation/GEOMETRY_SPEC.md` notes COMSOL used 4.1e7 (≈ 5.5 % in α).
  The additive form uses the dataset baseline, so this does not enter Δα.

## Conductor loss at the corners: the notebook value is 13–19 % low

`conv_corner.py`: refining only the corner/edge cells (0.05 → 0.00625 µm) raises
R′ by a near-constant 2.3–3.4 % per halving, still growing at the finest level.
The field next to the corner has the expected r^−1/3 form; the integral is
finite, but the mesh value approaches it too slowly to extrapolate.

`wheeler_check.py` (`wheeler_check.txt`): Wheeler's incremental-inductance rule
gives the same R′ from C_air of the line with every metal face receded. It is
mesh-converged (≤ 0.3 % between two mesh levels) and independent of the
recession (δ/8 and δ/2 agree to ≤ 0.6 %), so it is the converged value.

| row | MTX µm | notebook R′ vs converged |
|---|---|---|
| 408 | 7.5 | −12.9 % |
| 49 | 3.9 | −15.4 % |
| 118 | 2.0 | −19.1 % |

α_c ∝ R′, so the notebook's conductor loss is low by the same amount. The effect
on n and Z0 (through L_int = R′/ω) is about +0.2 %. The notebook matches the COMSOL
baseline α to ~1 % on these rows, so the dataset's COMSOL α likely carries a
similar underestimate.

### Why Wheeler's rule is a valid reference (`wheeler_verify.py`, `wheeler_verify.txt`)

The two are the same quantity. Receding a perfectly conducting wall by `a` changes
the magnetic energy by (μ0/2)|H_t|² a per unit area, which is exactly the contour
integrand. They differ only numerically: the contour integral squares a singular
gradient, while Wheeler takes a difference of C_air, which converges fast.

Test on row 49's electrodes in free space (the air problem both methods use),
with the corners rounded so the contour integral can converge:

| corner radius | contour integral, three meshes | Wheeler (central difference) | gap |
|---|---|---|---|
| 0.1 µm | 2350.7 / 2359.3 / 2360.1 | 2374.1 | −0.6 % |
| 0.3 µm | 2281.1 / 2288.8 / 2288.7 | 2302.3 | −0.6 % |
| sharp | 2125.7 / 2196.7 / 2271.3 (still rising) | 2521.3 | −9.9 % at 12.5 nm cells |

Units are Ω/m. The sharp case reproduces the section solver (2128 / 2517–2525).

The loss also depends on the real corner radius. Against the notebook's sharp-
corner value at its own mesh (2126), the loss is +8 % higher at a 0.3 µm radius,
+12 % at 0.1 µm and +19 % at sharp corners. The fabricated corner radius must be
part of the model.

## Section lengths: top view vs the cross-section figure

Following the top view (stem W1 × L1 at the gap, head W2 × L2 behind it), the
section through the stem has no metal between the gap and the head. That gives
the full W1 + W2 recess over L1, and the W1 finger only where the head extends
past the stem, over L2 − L1. The code uses this. Swapping the two lengths (finger
over L1, recess over L2 − L1) on the 11 rows with L2 > L1, floating finger:

- n median abs error 2.2 % → 5.3 %, max 7.9 % → 13.0 %;
- Z0 max abs error 6.3 % → 31.7 %.
