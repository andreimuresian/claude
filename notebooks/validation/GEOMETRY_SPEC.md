# Geometry, materials and parameters — validation checklist

Status 2026-09-29: all questions answered by the author (section C). Geometry and
materials confirmed; two new findings in section D.

Sources checked:
- the CST Multilayer history list (`2.5D_history_list.txt`, 159 steps, final state reconstructed);
- the COMSOL parameter table (`Z0nmalpha_500LHS__new_lateral_spacing_recovered_data.txt`);
- the thesis text;
- the dataset `EVALUATED_FULL_LHS_DATASET.xlsx`.

Drawings: `geometry_row118.png`, `geometry_row416.png` (`python draw_geometry.py <row>`).

## A. Matches the CST model (code already does this)

| # | Item | Code | CST history |
|---|---|---|---|
| 1 | Signal: centred, width WS, thickness MTX, on top of the LN slab | yes | `CENTRAL ELECTRODE` Y ±WS/2, vertical 0..MTX |
| 2 | Grounds: 70 µm wide from WS/2+GAP, thickness MTX; no metal beyond | yes | `GROUND ELECTRODE RIGHT` Y ±WG/2 shifted by WS/2+GAP+WG/2, mirrored |
| 3 | Slot through the full metal thickness, vacuum-filled. Stem at the ground inner edge: W1 deep × L1 long. Head behind it: W2 deep × L2 long. Stem and head share one centre along the line | yes | steps 8–19: stem Y 0..W1, Z ±L1/2; WCS shifted by W1; head Y 0..W2, Z ±L2/2; material Vacuum; then `Solid.Insert` into the grounds |
| 4 | Both grounds slotted, mirror images, at the same position along the line | yes | mirror about the Y plane |
| 5 | One tee per 200 µm cell, centred in the cell | yes | 3 tees at −L/2 + {−200, 0, +200} µm |
| 6 | Stack: air / LN slab (0.460 − ETCH_DEPTH) / SiO₂ 4.7 µm / Si 550 µm / air; layers laterally infinite; open boundaries | yes | layer stack: Vacuum 200 µm, LN `SLAB_H`, SIO2 `BOX_H`, Si 550 µm; all boundaries open. COMSOL: `slab_h = 0.460 um − wg_h`, `box_h = 4.7 um` |
| 7 | SiO₂ ε = 3.9; Si ε = 11.7, σ = 2.5e-4 S/m | yes | `material1`→`SIO2` ε 3.9; final `Silicon (lossy)` ε 11.7, σ 2.5e-4 |
| 8 | No optical rib, no SiO₂ cap | yes | LN/SiO₂/Si bricks deleted (step 85); layer stack only |
| 9 | Gold σ = 4.561e7 S/m | yes | `Gold` lossy metal σ 4.561e7 (COMSOL uses 4.1e7) |

## B. Where the code does NOT match the CST model

| # | Item | Code | CST | Proposed fix |
|---|---|---|---|---|
| 10 | LiNbO₃ permittivity (**author: anisotropy is essential; extraordinary axis = lateral**) | **isotropic 34.7 everywhere** (2D baseline, MoM, 3D probe) | anisotropic: lateral 28, vertical 43, along the line 43 (after CST's −90° rotation: X = line, Y = lateral, Z = vertical). COMSOL: {28, 44, 44} | **Done in the 2D solver (2026-09-29):** `solve_cs(eps_LN=(28, 43))`, exact tests in `test_cpw_2d_aniso.py`, 50-row re-run in `diagnostics/aniso_50row.py`. The 3D solver still has to follow |
| 11 | Outer boundary | grounded box: 1200 µm lateral, 800 µm above, 150 µm below the Si | open | Numerical choice; to be verified by a padding sweep, not by assumption |

## C. Author's answers

| # | Answer |
|---|---|
| Q1 | 400 µm model: 2 tees, centred at 100 and 300 µm (verified in its history: −L/2 ± 100 µm) |
| Q2 | `deltaL/deltaC lumped` come from ONE 200 µm cell, etched vs unetched, at 60 GHz: L = Im(B)/ω, C = Im(C_abcd)/ω of the cell's ABCD matrix (`touchstone_extractor_lumped_delta.py`). N+1−N (400/600 µm) was used only for Δα |
| Q3 | No CST warning; anisotropy is essential. Extraordinary axis (ε 28) is lateral, since the gap field is lateral. Vertical and along-line are 43 |
| Q4 | Yes, SLAB_H = 0.460 µm − ETCH_DEPTH in every run |
| Q5 | L1 > L2 is legitimate in the LHS; W1 + W2 ≤ 65 µm |
| Q6 | Lumped values per 200 µm cell |
| Q7 | Drawings agree. MTX = thickness of all three electrodes |

## D. New findings (from the author's scripts and histories)

**D1. The lumped ΔC is not ΔC per unit length × pitch.** The cell's ABCD gives
per-length × P × sin θ/θ, with θ = β·P ≈ 0.48 rad unetched and 0.57 rad etched.
The factor does not cancel in the difference. From the dataset alone
(`lumped_definition_check.py`):
- lumped ΔC / (per-length ΔC·P): 1.09–1.65, median 1.24; more than 30% off on 188/500 rows;
- lumped ΔL / (per-length ΔL·P): 0.89–0.93.

Phase 3 compared per-length `(Ce − Cu)·P` with the lumped value. Re-scored
like-for-like, the MoM ΔC median error goes 73% → 57% and ΔL 7.7% → 5.6%. The
mismatch explains part of the past ΔC error, not most of it. **Any new ΔC/ΔL must
be scored with the same cell-ABCD definition.**

**D2. Mesh inconsistency in the CST reference — confirmed by the author** (etched grounds visibly coarser). The author judges the Multilayer results valid regardless, given their agreement with the 3D time-domain N+1−N extraction. Kept as a note, not pursued. In both etched histories
(400 and 600 µm), local mesh group `meshgroup1` (5 µm) holds `CENTRAL ELECTRODE`,
`GROUND RIGHT ELECTRODE`, `GROUND RIGHT ELECTRODE_1`. Those grounds are later
deleted and rebuilt as `GROUND ELECTRODE RIGHT/LEFT`, which are never added to
the group. In the unetched history the grounds stay in the group. So the etched
grounds, where the tees are, may use the coarser global mesh while the unetched
grounds use 5 µm. **To confirm in CST:** Groups → meshgroup1 members, or the
surface-mesh view of an etched ground.
