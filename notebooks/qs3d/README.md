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
  −10.5 %, largest on rows 220, 49, 38) is the ΔC disagreement above and is
  still open.
- **Run time:** 65–170 s per geometry on one core (tee cell + no-slot cell, C,
  L(0), L(a)).

**Discriminating CST runs** (row 49, the existing 2- and 3-cell lines, minutes
each):

1. **PEC metal.** If α_delta stays near +8 dB/cm, it is radiation or leakage.
   If it drops to about +1, it is conductor loss in CST, contradicting the
   converged 3D value: refine the etched grounds (D2 in GEOMETRY_SPEC).
2. **Frequency, 30 / 45 / 60 GHz.** Ohmic Δα scales as √f; substrate leakage
   grows much faster.
