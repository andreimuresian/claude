# Madrid 1 surrogate with rib width (WG 1.0–1.5 µm)
* `madrid1_predictor.html`: open in a browser, fully offline. Sliders: GAP, BUFFER_H, CAP_W (≥ 2·WG), CAP_H, MTX_small, WG.
* Data: `sweep_gp_baseline.txt` (original 112 FEM points, WG = 1.4) + `sweep_wg.txt` (76 new: 16 corners at WG 1.0 + 60 augmented LHS) ; `sweep_wg_val.txt` 8 held-out validation points.
* Inputs: GAP, BUFFER_H, CAP_F, CAP_H, MTX_SMALL, WG with CAP_F = (GAP − CAP_W)/(GAP − 2·WG).
* `gp_build.py` (edit PATHS to point at the two data files), `predictor.py` (numpy only, `P.predict(GAP, BUFFER_H, CAP_W, CAP_H, MTX_SMALL, WG)`), `optimise.py`, `optimise_robust.py`.
* Accuracy: 10-fold CV IL MAPE 2.6 %, Vπ·L 0.16 %; 8 held-out FEM points: IL ≤ 4.5 %, Vπ·L ≤ 0.25 %, all within the 95 % band.
