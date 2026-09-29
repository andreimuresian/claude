# Geometry, materials and parameters — validation checklist

Nothing downstream (3D ΔC/ΔL) runs until every item here is confirmed by the author.

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
| 10 | LiNbO₃ permittivity | **isotropic 34.7 everywhere** (2D baseline, MoM, 3D probe) | anisotropic: lateral 28, vertical 43, along the line 43 (after CST's −90° rotation: X = line, Y = lateral, Z = vertical). COMSOL: {28, 44, 44} | Use the CST tensor. It is a two-line change in the FV solver. The 2D baseline check must be re-run afterwards |
| 11 | Outer boundary | grounded box: 1200 µm lateral, 800 µm above, 150 µm below the Si | open | Numerical choice; to be verified by a padding sweep, not by assumption |

## C. Questions only the author can answer

| # | Question |
|---|---|
| Q1 | The history builds the **3-tee (600 µm)** line. Does the **400 µm** model have 2 tees centred at 100 and 300 µm? If the same recipe was reused unchanged, the tees would sit at 0, 200 and 400 µm, i.e. split at the ports. |
| Q2 | Exactly how were `deltaL lumped` and `deltaC lumped` computed? Which S-parameter files (single 200 µm cell? N+1 − N?) and which Π-network formula? The thesis formula is unreadable in the text export. A script like the α extractor would settle it. |
| Q3 | The CST LN layer is **in-plane anisotropic** (ε_X = 43 ≠ ε_Y = 28). Did the Multilayer solver accept this without a warning? Layered solvers often only support a different *vertical* ε. What CST actually used is what must be matched. |
| Q4 | In each CST run, was `SLAB_H` = 0.460 µm − ETCH_DEPTH? |
| Q5 | The dataset breaks the thesis constraints: 65 rows have L1 > L2, and 84 have W1 + W2 > 60 µm (max 64.9, so no slot cuts through a ground). Row 416 (drawn) has L1 = 48.4, L2 = 6.5 µm. Is that what CST built, or are columns swapped? |
| Q6 | Are `deltaL lumped` [H] and `deltaC lumped` [F] totals per 200 µm cell? |
| Q7 | Do the two drawings match what your CST model looks like for those rows? |
