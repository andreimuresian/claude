# Quasi-static 3D unit cell: ΔL, ΔC of the tee-loaded CPW

`qs3d.py` builds one 200 µm cell exactly as the CST Multilayer model: thick metal,
LN slab (0.460 − ETCH) with (lateral 28, vertical 43, along-line 43), SiO₂ 3.9,
Si 11.7, tees in both 70 µm grounds. Two solves per geometry:

- electrostatic → C′;
- high-frequency magnetostatic → L′ (current detour around the tees).

The cell's own L and C distribution (energy per slice) is cascaded into its ABCD
matrix, and the author's extractor (L = Im B/ω, C = Im C/ω) is applied to it.

```
python run5.py          # 5 reference rows -> run5.json   (~3 min, 4 cores)
python conv.py          # grid refinement check on rows 38, 118
```

Checks:
- L′·C′_air·c² = 1.006–1.010 on unetched cells (TEM identity).
- Unetched C′ agrees with the 2D solver to 0.2%.
- The slice cascade equals the uniform formula to 2e-16.
- Doubling the grid moves ΔC and ΔL by ≤ 0.1%.

Results vs the dataset (CST Multilayer lumped deltas):

| row | ΔC err | ΔL err | n_final err | Z₀_final err | time (1 core) |
|---|---|---|---|---|---|
| 118 | −22.9% | −7.1% | −0.13% | −2.16% | 142 s |
| 416 | −14.7% | −2.8% | +0.09% | −0.58% | 145 s |
| 121 | −35.7% | −10.0% | −0.20% | −3.18% | 115 s |
| 38 | −44.3% | −12.3% | −0.60% | −4.58% | 144 s |
| 49 | −46.9% | −14.8% | −0.91% | −6.08% | 51 s |

## Second-order (coupled) correction and open boundary — tested, not sufficient

`coupled.py` adds the magnetic energy of the charging currents of the open
half cell (displacement currents plus conduction to every metal surface,
fingers included) to the lumped C. `python run5_coupled.py` (~9 min, 4 cores):

| row | ΔC err, cascade | ΔC err, coupled | n_final err | Z₀_final err |
|---|---|---|---|---|
| 118 | −22.9% | −19.2% | −0.13% → −0.30% | −2.16% → −2.00% |
| 416 | −14.7% | −14.6% | +0.09% → +0.09% | −0.58% → −0.58% |
| 121 | −35.7% | −30.5% | −0.20% → −0.42% | −3.18% → −2.97% |
| 38 | −44.3% | −36.7% | −0.60% → −0.94% | −4.58% → −4.25% |
| 49 | −46.9% | −38.8% | −0.91% → −1.35% | −6.08% → −5.65% |

The term enters as ω²C_h(L_e − L_h) ≈ 0.05–0.07 of C, so it cannot supply the
~5% of the cell C missing on row 49. On the no-slot cells L_e/L_h = 0.364–0.391
instead of 1/3 (box charge and non-TEM field of the stack); the etched − no-slot
difference removes this.

`python frame_check.py 49 118`: floating (open-equivalent) far frame instead of
the grounded box, which holds 13% of the signal charge. ΔC err: row 49
−46.9% → −47.1%, row 118 −22.9% → −18.9%.

Open: the ΔC gap (15–47%, growing with finger size) is zeroth order. Candidate
on the reference side: D2 in `../validation/GEOMETRY_SPEC.md` (etched grounds
not in the 5 µm mesh group).

## Step 1: conductor loss of the cell (`loss.py`, `run_loss.py`, `report_loss.py` → `report_loss.txt`)

**Question:** is the dataset's large α_delta (up to +8.3 dB/cm) ohmic loss from
the return current crowding around the tee? The 2D section average can't carry
that current path; this 3D cell does.

```
python run_loss.py      # 14 rows of ../xsec + grid checks on rows 49, 118  -> run_loss.json (~12 min, 4 cores)
python report_loss.py   #                                                   -> report_loss.txt
```

**Method.** R′ comes from the high-frequency magnetostatic solve that already
gives L′ (PEC metal, I = 1 A), with Rs = 1/(σδ) and σ = 4.56e7. Two ways:

- **Wheeler's rule:** R′ = Rs (L′(a) − L′(0))/(μ0 a), with every metal face
  receded by a = δ/2, including the slot walls. Both solves share one grid
  (`qs3d.build(lines=a, rec=a)`).
- **Direct surface integral:** Rs ∮|H_t|² over every metal face (kept as a
  cross-check).

The tee's effect is reported as factors, tee cell over no-slot cell on the same
grid: F_R, F_n, F_Z, and F_α = F_R/F_Z (since α_c = R′/2Z0, with
L = L′ + R′/ω). `qs3d.build` and `qs3d.inductance` are unchanged with default
arguments: row 49's stored C′ and L′ are reproduced to 1e-16.

**Checks**

| check | result |
|---|---|
| no-slot cell, Wheeler R′ vs the independent 2D FEM converged IBC (../xsec), rows 49, 118, 408 | −0.1, +0.1, +0.0 % |
| no-slot cell, direct surface integral | 15–18 % low (edges under-resolved, as in 2D) → Wheeler is used |
| tee factor F_R: recession a/2, edge cell /2, z and near grid /2 (rows 49, 118) | moves ≤ 0.3 % (F_n, F_Z ≤ 0.01 %) |
| slice-cascade Bloch index vs c√(L′C′) | equal to ≤ 0.13 % |

**Results** (14 rows; Δα on the COMSOL baseline, dB/cm):

| row | strip µm | Δα CST | Δα 3D ohmic | Δα 2D slices |
|---|---|---|---|---|
| 118 | 37.7 | −0.51 | −0.49 | −0.69 |
| 408 | 43.3 | −0.35 | −0.43 | −0.55 |
| 355 | 40.1 | −0.16 | +0.03 | −0.08 |
| 448 | 34.9 | −0.11 | −0.08 | −0.23 |
| 416 | 11.9 | −0.01 | +0.12 | −0.25 |
| 206 | 35.2 | +0.03 | −0.04 | −0.14 |
| 302 | 13.1 | +0.06 | −0.75 | −0.94 |
| 398 | 35.0 | +0.10 | −0.15 | −0.28 |
| 121 | 24.5 | +0.34 | −0.12 | −0.26 |
| 363 | 15.6 | +1.05 | −0.23 | −0.44 |
| 38 | 14.4 | +1.33 | +0.05 | −0.10 |
| 220 | 5.3 | +1.89 | +0.03 | −0.13 |
| 130 | 7.6 | +5.06 | +0.24 | +0.15 |
| 49 | 8.9 | +8.29 | +0.95 | +0.94 |

- **Gate: failed.**
  - The 9 rows with Δα ≤ +0.5 dB/cm agree to 0.12 dB/cm median (0.81 max).
  - On the 5 rows with large Δα, the 3D ohmic loss gives 4 % of the CST value
    (−22 to +11 %).
  - Current crowding is real: R′ rises up to 1.89× on row 49. But Z0 rises
    with it, so α_c rises at most 1.37×.
  - The 3D cell and the 2D slices agree on Δα to ≤ 0.3 dB/cm on every row.
    The large CST Δα is therefore **not quasi-static conductor loss**. It is
    either a full-wave loss (radiation or leakage into the substrate) or an
    artifact of the CST runs. No quasi-static or analytical model can produce
    it.
- **n.** In the dataset's convention (COMSOL baseline + lumped ΔL, ΔC of one
  CST cell, Im B/ω and Im C/ω), the 3D cell reproduces n_final to 0.2 %
  median, 0.8 % max. That convention sits 1–4 % below the Bloch index
  c√(L′C′) on the strongly loaded rows, because a single 200 µm cell spans
  0.5–0.75 rad of phase and its lumped extraction carries sin θ/θ. The physical
  n_m is the Bloch value: 1–4 % above the dataset's n_final.
- **Z0.** The convention changes Z0 by ≤ 1 %. The remaining gap (−0.2 to
  −10.5 %, largest on rows 220, 49, 38) is explained on row 49 in
  "Z0 gap on row 49" below; rows 220 and 38 are not checked yet.
- **Run time:** 65–170 s per geometry on one core (tee cell + no-slot cell, C,
  L(0), L(a)).

**Discriminating CST runs** (row 49, the existing 2- and 3-cell lines, minutes
each):

1. **PEC metal.** If α_delta stays near +8 dB/cm, it is radiation or leakage.
   If it drops to about +1, it is conductor loss in CST, contradicting the
   converged 3D value: refine the etched grounds (D2 in GEOMETRY_SPEC).
2. **Frequency, 30 / 45 / 60 GHz.** Ohmic Δα scales as √f; substrate leakage
   grows much faster.

## CST check on row 49 (author's runs; `cst_row49.py` → `cst_row49.txt`)

The author's CST multilayer runs of row 49:
- 400 and 600 µm lines, with and without tees, gold and PEC electrodes, at
  20, 60 and 100 GHz;
- then a 600 µm (rerun with the ground mesh fixed) and a 1000 µm PEC tee line,
  at 60 GHz.

Files: `../mom/data/MULTILAYER SOLVER TOUCHSTONES`.

The header parameters that differ (CAP_W, SI_H) are not geometry differences:
the model has no caps, and Si is 550 µm in all runs (author). Below the 550 µm
layer the solver's bottom half-space is also silicon (solver log: "Half space:
Silicon (lossy)"), so power radiated into the substrate never comes back.

### 1. The 400/600 µm runs (sections 2–3)

Extraction exactly as the author's: α per cell from the 600 − 400 µm
subtraction of Re acosh A.

| | 20 GHz | 60 GHz | 100 GHz |
|---|---|---|---|
| gold: α tee / α no tee (dB/cm) | 1.80 / 1.24 | 10.65 / 2.39 | 1.59 / 3.12 |
| gold: Δα (dB/cm) | +0.56 | **+8.25** (dataset +8.29) | −1.53 |
| PEC: α tee / α no tee (dB/cm) | 0.003 / 0.000 | **5.91** / 0.11 | **−1.96** / 0.14 |
| PEC tee: power lost, 400 / 600 µm | 0.001 / 0.002 % | 0.24 / 2.72 % | 9.9 / 10.6 % |
| n ratio tee / no tee, gold (PEC) | 1.351 (1.350) | 1.410 (1.408) | 1.360 (1.356) |

The 3D quasi-static cell gives α ratio 1.373 and n ratio 1.3498, both
frequency-independent.

- **The reproduction holds.** The gold runs give the dataset's Δα at 60 GHz.
- **Most of the 60 GHz Δα is not conductor loss.** With PEC electrodes the tee
  line still loses 5.9 dB/cm, 70 % of the gold Δα. Silicon absorption is
  negligible (σ = 2.5e-4 S/m in the material card), so this is radiation.
- **At 20 GHz CST and the 3D quasi-static cell agree.**
  - α ratio: 1.45 vs 1.37, i.e. Δα +0.56 vs +0.46 dB/cm.
  - n ratio: 1.3495 (PEC) and 1.3512 (gold) vs 1.3498.
- **The PEC electrodes stayed thick.** n of the no-tee line, gold over PEC, is
  1.012; the internal inductance of gold, √(1 + R′/(ωL)), predicts about 1.013.
- The radiation depends strongly on frequency: about 0 at 20 GHz, 5.5 at 60 GHz
  and 1.9 dB/cm at 100 GHz (line-line values below). That points to a resonance
  of the cell, which fits the author's colleague's report of resonances on tees
  with large L2 (row 49: L2 = 166.6 µm of the 200 µm period).

### 2. Line-line check (section 4)

The subtraction of Re acosh A cancels the end transitions only in special
cases. An exact version, if both lines have the same ends:
- M400 = E_a T² E_b and M600 = E_a T³ E_b, so M600 M400⁻¹ = E_a T E_a⁻¹ has the
  cell's eigenvalues, cosh γP = tr(M600 M400⁻¹)/2.
- The same model fixes the two ends joined, E_a E_b = (M600 M400⁻¹)⁻² M400,
  which must be passive if the lines are cascades of identical cells.

| tee line, dB/cm per cell | 20 GHz | 60 GHz | 100 GHz |
|---|---|---|---|
| PEC: line-line / subtraction | 0.003 / 0.003 | 5.52 / 5.91 | 1.91 / −1.96 |
| gold: line-line / subtraction | 1.80 / 1.80 | 10.14 / 10.65 | 5.50 / 1.59 |
| joined ends E_a E_b, PEC: power lost | −0.002 % | **−5.3 %** (gain) | +7.6 % |

- **No-tee lines:** both methods agree to 0.02 dB/cm at every frequency, and
  the joined ends are passive within 0.07 %.
- **100 GHz:** the subtraction's negative α was an end effect. With the ends
  removed exactly, the cell has a positive α.
- **60 GHz:** the joined ends would need 5 % gain, so the lines are not
  "passive ends + identical cells". Section 4 below shows why: the cells next to
  the ports lose much less than the inner ones.

### 3. Ground mesh (section 5): not the cause

- **Finding.** The tee projects rebuild the grounds under new names
  (GROUND ELECTRODE RIGHT/LEFT) and never add them back to the 5 µm mesh group.
  So their grounds fall back on the automatic mesh. This is the coarser ground
  mesh the author saw, and why the tee runs are faster than the no-tee runs.
- **Test.** The author reran the 600 µm PEC tee line with the grounds in the
  5 µm group.
- **Result.**
  - Lost power at 60 GHz: 2.722 % → 2.718 %.
  - |S21|: 0.98322 → 0.98378.
  - |S11|: 0.078 → 0.071.
- The mesh does not explain the loss.

### 4. Length series (section 6): the loss is a property of the line

PEC tee lines at 60 GHz: 400 µm (2 cells), 600 and 1000 µm (3 and 5 cells,
both with the 5 µm ground mesh).

| cells | 2 | 3 | 5 |
|---|---|---|---|
| power lost | 0.24 % | 2.72 % | **7.63 %** |

| pair | subtraction (dB/cm) | line-line (dB/cm) | n per cell |
|---|---|---|---|
| 2 → 3 | 5.86 | 5.55 | 2.773 |
| 3 → 5 | **6.50** | **6.44** | 2.580 |
| 2 → 5 | 6.29 | 6.01 | 2.645 |

- **The loss grows linearly with length:** 2.48 % per added cell from 2 to 3
  cells, 2.46 % from 3 to 5. The 7.7 % predicted before the 1000 µm run, for a
  real per-cell loss, came out as 7.63 %. It is a real attenuation of the
  periodic line: radiation, since the metal is PEC.
- **The ends lose less, not more.** The straight line through 3 and 5 cells
  gives −4.7 % at zero cells and predicts 0.26 % for 2 cells (measured 0.24 %).
  - So the cell next to each port loses almost nothing, and only the inner
    cells radiate their full 2.5 %.
  - This is why the ends looked "active" in the line-line check. It is also why
    the 2-cell line, made of two end cells, sees no loss.
- **The 2/3-cell subtraction underestimates the per-cell loss by about 10 %**
  (5.9 vs 6.5 dB/cm, PEC). The dataset's 8.29 dB/cm for row 49 comes from that
  pair, so the long-line value is likely about 10 % higher.
- **The per-cell n also depends on the pair** (2.77 vs 2.58). The dataset's n
  for row 49 (2.581, from the 1-cell lumped extraction) matches the 3 → 5 value.
- **For the fast model:**
  - The 3D quasi-static cell reproduces n and the ohmic part of Δα.
  - In the narrow-strip, long-L2 corner, Δα is dominated by resonant
    radiation, a full-wave effect that a quasi-static solve cannot produce.

### Where the large Δα lives in the dataset (`dataset_regime.py` → `dataset_regime.txt`)

This describes the test fixture; nothing is fitted to it.

- **Strongest correlate: the outer ground strip behind the slot,
  70 − W1 − W2** (Spearman −0.70). Next is L2 (+0.49).
- **Strip 5–10 µm with L2 > 100 µm:** Δα > 2 dB/cm in 40 of 43 rows, with
  medians of 3–7 dB/cm. Row 49 is one of them (strip 8.9 µm, L2 167 µm).
- **Strip > 40 µm:** none of the 86 rows has Δα > 2 dB/cm.
- So the radiating geometries sit in one corner of the design space: a narrow
  outer strip with a long head slot.

## Z0 gap on row 49 (`zbloch_row49.py` → `zbloch_row49.txt`)

**Question.** The 3D cell matches the dataset's n but not its Z0 (row 49: −5.4 %).
Why, when both come from the same L′ and C′?

**Why n can agree while Z0 does not.**
- n ∝ √(L′C′) and Z0 ∝ √(L′/C′), so δn = (δL + δC)/2 and δZ = (δL − δC)/2.
- Errors of opposite sign in L′ and C′ cancel in n and add in Z0.
- Row 49, dataset convention: δn = −0.2 %, δZ = −5.4 %. So the 3D cell has 5.6 %
  less L and 5.2 % more C than the dataset's cell.

**Method: measure the tee cell's impedance on the CST lines.** The dataset's Z0
comes from one CST cell between two ports at 60 GHz. Here it is measured on the
400 and 600 µm lines instead.
- The ports sit on cell boundaries, so a line of N cells is M_N = P T^N P~, with P
  the port transition and T the symmetric cell.
- The eigenvectors of M600 M400⁻¹ are P[±Z_B, 1]: the cell's Bloch impedance seen
  through P.
- P is fitted on the no-tee lines. A lumped port transition has a = d, which fixes
  the impedance scale.
  - It gives Z_u = 36.40 Ω (PEC, 20 GHz); the 3D no-slot cell gives 36.51 Ω.
  - The port transition is small and does not change with frequency: −4.3 pH
    series, −3.3 fF shunt, i.e. the port plane sits about 18 µm inside the line.
- The eigenvector Z_B is insensitive to P to first order. The tee lines with their
  own port fit and no no-tee runs give 50.910 Ω; the no-tee port fit gives
  50.908 Ω. So **a future check needs only the two fast tee lines.**
- The model ("same ends, identical cells") holds at 20 GHz: the two wave
  impedances, which should be ±Z_B, sum to 0.29 Ω, 0.6 % of Z_B. At 60 GHz they
  sum to 2.8 Ω (5 %), at 100 GHz to 10.7 Ω (17 %).

**Results** (PEC; gold gives F_Z within 0.3 % up to 60 GHz):

| | 20 GHz | 60 GHz | 100 GHz |
|---|---|---|---|
| CST no-tee line Z_u (Ω) | 36.40 | 36.33 | 36.12 |
| CST tee cell Z_B (Ω), line-line 2 → 3 | 50.91 | 53.11 | 62.2 |
| CST F_Z = Z_B / Z_u | **1.3985** | 1.462 | 1.72 |
| 3D cell F_Z (static L′, C′; only the cascade's phase changes) | **1.3776** | 1.3871 | 1.4088 |
| CST tee n, line-line 2 → 3 | 2.655 | 2.771 | 2.655 |

At 60 GHz the 3 → 5 pair (5 µm ground mesh) gives Z_B = 54.49 Ω, F_Z = 1.500.

**Row 49 rebuilt in the dataset's convention** (gold, 60 GHz, one cell between the
ports, COMSOL baseline + lumped ΔL/P, ΔC/P):

| cell | ports | ΔL (pH) | ΔC (fF) | Z0_final (Ω) | n_final |
|---|---|---|---|---|---|
| 3D quasi-static | none | 37.80 | −2.04 | 50.52 | 2.571 |
| 3D quasi-static | CST's | 36.92 | −2.74 | 50.78 | 2.532 |
| CST cell, de-embedded from the 2 → 3 lines | none | 45.79 | −2.74 | 53.35 | 2.659 |
| CST cell, de-embedded from the 2 → 3 lines | CST's | 44.71 | −3.58 | 53.73 | 2.610 |
| dataset (one CST cell) | | 43.20 | −3.78 | 53.46 | 2.581 |

**Findings**
- **The dataset's Z0 is the CST tee cell's impedance at 60 GHz.** The long-line
  cell, put through the ports and the one-cell extractor, gives 53.73 Ω against
  the dataset's 53.46 Ω (+0.5 %).
  - The ports and the one-cell convention move Z0 by ≤ 0.7 %. They are not the
    cause.
  - The ports do move ΔC by 30 % (−2.74 → −3.58 fF). Part of the old ΔC
    "disagreement" was this, but it barely moves Z0.
- **At 20 GHz the 3D cell is 1.5 % below CST on F_Z, and n agrees to 0.1 %.**
  - Part of the 1.5 % may be CST's mesh. The 20 GHz tee runs have the grounds on
    the automatic mesh. At 60 GHz the 5 µm ground mesh moved the 3-cell Z_B by
    −0.85 % and the 2 → 3 value by −0.2 %.
  - Part may be the start of the dispersion below. If it grows as f², it is about
    0.5 % at 20 GHz. This is not measured.
- **From 20 to 60 GHz, CST's F_Z rises by 4.5 %; the 3D cell's rises by 0.7 %**
  (the cascade's phase).
  - The extra ~4 % is a full-wave effect of the cell, in the band where row 49
    radiates. With PEC metal it is not skin effect.
  - n rises with it (2.655 → 2.771). So it is mostly an increase of the series
    inductance: L ∝ nZ rises 9 %, while C ∝ n/Z is flat.
  - At 100 GHz F_Z is 1.72, and the cells near the ports no longer match the inner
    ones.
- **So on row 49 the 5.5 % splits as:**
  - ~4 % dispersion at 60 GHz, which a quasi-static cell cannot produce;
  - ≤ 1.5 % static, the size of CST's own mesh effect;
  - 0.5 % ports.
- **The n agreement at 60 GHz was partly a coincidence.** At 60 GHz the long lines
  give n = 2.58 to 2.77 depending on the pair, and the dataset's single cell gives
  2.581. At 20 GHz, where the pairs agree, the 3D cell's n ratio matches to 0.1 %.
- **The 3D cell's absolute n is 1.4 % low on both cells** (no-slot 1.941 vs CST
  1.969, PEC). This cancels in the factors applied to the 2D baseline.
- **Rows 220 (−9.6 %) and 38 (−4.1 %) are not checked: there are no CST runs.**
  - Row 220 has the largest head slot of the 14 rows: 53 × 185 µm, with a 5.3 µm
    strip.
  - Checking it needs the 400 and 600 µm tee lines only, with the grounds in the
    5 µm mesh group, at 20 and 60 GHz.
