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
python validate_mqs.py      # gold-interior solve checks  -> validate_mqs.txt
python run_mqs.py           # gold-interior R', L_int      -> run_mqs.json (~6 min, 4 cores)
python report_mqs.py        # assessment with it          -> report_mqs.txt
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

## Assessment with the gold-interior conductor model (`report_mqs.txt`)

Same 14 rows and sections. C, G and C_air come from the quasi-static solve as
before. R′ and L_int come from the gold-interior solve of notebook v2 cell [6]
(`mqs2d.py`, see the section on conductor loss below), with the finger floating.

**Baseline (section C vs the COMSOL baseline of the dataset)**

- n is −0.19 to +0.06 % and Z0 is −0.52 to −0.05 %. The gold L_int raises both
  by +0.06 to +0.22 % over the IBC value.
- α (gold) is −3.6 % to +18.2 % above COMSOL, median +8 %.
- The notebook IBC is 7–16 % below gold on every row.
- The COMSOL gap depends on the row (≈ 0 on rows 38 and 220, +16–18 % on
  rows 118 and 130), so it can't be applied as a flat correction. It costs
  one gold solve per geometry (20–90 s).

**Perturbation (2D: average − section C; dataset: final − baseline)**

Errors are a % of the final value. The α reference is the dataset final with
the COMSOL baseline replaced by the gold section C:
α_ref = α_final − α_base + α_C,gold.

| | n | Z0 | α |
|---|---|---|---|
| 2D average, median / max abs error | 2.2 / 7.9 % | 3.0 / 6.3 % | 21.1 / 66.0 % |
| ignoring the tee (section C alone) | 14.0 / 25.4 % | 20.7 / 41.4 % | 13.0 / 74.5 % |
| share of the dataset's change reproduced, median (range) | 70 % (44–94 %) | 83 % (68–94 %) | sign wrong on 7 of 14 rows |

α split by what the tee does in the dataset (median / max abs error):

| rows | 2D average | ignoring the tee |
|---|---|---|
| 9 rows, Δα ≤ +0.5 dB/cm | 9.9 / 26.6 % | 6.4 / 21.3 % |
| 5 rows, Δα > +0.5 dB/cm (+1.05 … +8.29) | 59.3 / 66.0 % | 56.3 / 74.5 % |

- **n and Z0.** The average reproduces most of the tee's effect and cuts the
  error of ignoring the tee by about 6×. Every error is negative: the slices
  miss part of the slow-wave loading. Expect about −2 to −3 %, at worst −8 %.
  The conductor model moves these by ≤ 0.2 %.
- **α.** No skill. The average says the tee lowers α on 12 of 14 rows
  (Z0 rises, R′ changes little), while the dataset has it raising α on 8 of 14.
  Overall it does no better than ignoring the tee.
  - The gold model fixes the baseline (0–18 %) but moves Δα by ≤ 0.1 dB/cm.
  - The missing loss is in the 3D current path around the slot: x-directed
    current at the slot ends and crowding in the stem. No z-uniform slice
    carries it.

## Mesh convergence (`conv.json`)

Rows 49, 118, 408, all three sections, up to 1.45 M elements (bulk mesh 2×
finer, corner and skin collars 2× finer than the notebook):

- n: notebook mesh within 0.05 % of the finest;
- Z0: within 0.23–0.29 %, closing monotonically under bulk refinement;
- α: sensitive to the corner collar. Halving the 0.05 µm corner size raises α
  by 2.2–4.8 %; the IBC integrand is singular at the 90° corners. Δα moves by
  ~5 %. The notebook's corner size is kept, since it reproduces COMSOL on its
  validation row. The gold-interior solve removes this problem (see the
  section on conductor loss).

## Side findings on the baseline (section C vs dataset baseline, 14 rows)

- quasi-static + IBC: n −0.1 to −0.3 %, Z0 −0.3 to −0.7 %.
- notebook full-wave: Z0 +0.0 to +3.6 %, growing as the mode score drops from
  0.497 to 0.481 (coupling to the PEC box). On sections A and B the eigen
  solve is worse: no mode passes the filters on 8 of 14 A sections, and a 2D
  eigenmode cannot tie the finger to ground. So the report uses quasi-static.
- α (both solvers agree): −10.9 % to +1.4 % against the dataset baseline.
  - An earlier version of this note blamed σ, because
    `../validation/GEOMETRY_SPEC.md` says COMSOL used 4.1e7. But the notebook
    labels its 4.56e7 as COMSOL's "Au (Gold)" node, and COMSOL's built-in gold
    is 45.6e6 S/m, so σ is probably not the cause. The spread follows the
    corner resolution instead: see the gold-interior table above.
  - The additive form uses the dataset baseline, so this does not enter Δα.

## Conductor loss: gold-interior solve (notebook v2 cell [6]) vs IBC

`mqs2d.py` is cell [6] ported verbatim: same equations, same graded tensor mesh,
same P2 elements and half domain. It accepts any ground pieces, and the finger
is its own conductor with zero net current. On row 86 it reproduces the cell
exactly: R′ 3590.1006 Ω/m, L_int 10.7647 nH/m.

Checks (`validate_mqs.txt`):

| check | result |
|---|---|
| DC limit, 1 kHz | R′ = exact R_dc (291.5054 Ω/m) to 1e-6 |
| round gold wire in a PEC tube vs exact Bessel solution, 60 GHz, a = 5 and 1 µm | R′ within 0.011 %, L_int within 0.084 % |
| surface cell 0.06 / 0.03 / 0.015 µm, interior cell 0.5 / 0.25 µm, grading 1.15 / 1.08 | R′ within 0.001 %, L_int within 0.09 % |
| box 600 → 1200 µm | R′ and L_int unchanged |

It converges normally because there is no corner singularity. Inside a
conductor of finite σ the field is smooth at the corner: the r^−1/3 singularity
belongs to the PEC limit, and within about one skin depth of the corner the real
current spreads out.

**Two fixes to cell [6]**

1. **`L_ext_box`.** The PEC reference pins A = 1 on the signal and A = 0 on the
   ground *and* on the box, so the box acts as a third conductor.
   - The box returns 5.0 % of the current (3.9 % with a 1200 µm box).
   - L_ext_box comes out 0.37 % low, so L_int = L′ − L_ext_box is 13 % high:
     10.76 instead of 9.49 nH/m. It also depends on the box: 10.50 nH/m at
     1200 µm.
   - Fix: impose the gold solve's net currents (±1/2, A constant on each
     conductor). This gives L_int = 9.491 nH/m, independent of the box, with
     ωL_int/R′ = 0.997, the strong-skin-effect value.
   - Effect on row 86: n 1.71465 → 1.71161, Z0 62.774 → 62.663 Ω, α 2.4838 →
     2.4882 dB/cm.
2. **`_graded` endpoint.** `_graded` returns a + (b − a) as its last point,
   which can miss b by one ulp. `np.unique` then keeps both copies, and the
   zero-width elements make the matrix singular (row 398, section A). Fix: set
   the last point to b.

**Gold vs IBC, section C** (Ω/m; % relative to gold):

| row | MTX µm | gold | notebook IBC (notebook mesh) | converged IBC (Wheeler) | ωL_int/R′ |
|---|---|---|---|---|---|
| 86 | 9.14 | 3590.1 | 3157.9 (−12.0 %) | 3674.7 (+2.4 %) | 0.997 |
| 49 | 3.93 | 2393.2 | 2128.4 (−11.1 %) | 2520.9 (+5.3 %) | 1.025 |
| 118 | 1.96 | 2631.6 | 2251.7 (−14.4 %) | 2783.8 (+5.8 %) | 1.022 |
| 408 | 7.52 | 3009.1 | 2729.1 (−9.3 %) | 3134.2 (+4.2 %) | 1.017 |

Both IBC values are off, for different reasons:
- the notebook's because its corners are under-resolved: 7–16 % low over the
  14 rows;
- the converged one because the surface-impedance model itself fails within
  about δ of a 90° corner: 2–6 % high.

The gold solve has neither problem, so it is the reference here.

### Wheeler's rule and the IBC limit (`wheeler_check.py`, `wheeler_verify.py`)

Wheeler's incremental-inductance rule is evaluated here with the same FEM, not
as a formula: C_air of the electrodes with every face receded by a, and
R′ = Rs (L(a) − L(0))/(μ0 a). It is the same quantity as the IBC contour
integral (the shape derivative of the magnetic energy), but it converges fast.

- With rounded corners the contour integral converges and matches Wheeler to
  0.6 % (ρ = 0.1 µm: 2360 vs 2374; ρ = 0.3 µm: 2289 vs 2302 Ω/m, row 49).
- With sharp corners the contour integral is still rising at 12.5 nm cells
  (2126 / 2197 / 2271 vs 2521).

So Wheeler gives the *converged IBC*. That is a statement about the IBC model,
which the gold solve shows to be 2–6 % high at sharp corners. A real corner
radius lowers every value somewhat. The earlier "notebook 13–19 % low" was
measured against Wheeler; against the gold solve it is 7–16 %.

## Section lengths: top view vs the cross-section figure

Following the top view (stem W1 × L1 at the gap, head W2 × L2 behind it), the
section through the stem has no metal between the gap and the head. That gives
the full W1 + W2 recess over L1, and the W1 finger only where the head extends
past the stem, over L2 − L1. The code uses this. Swapping the two lengths (finger
over L1, recess over L2 − L1) on the 11 rows with L2 > L1, floating finger:

- n median abs error 2.2 % → 5.3 %, max 7.9 % → 13.0 %;
- Z0 max abs error 6.3 % → 31.7 %.
