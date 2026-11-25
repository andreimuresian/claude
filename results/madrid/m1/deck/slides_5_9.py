import json
GP = "/home/user/claude/results/madrid/m1/gp/"
card = json.load(open(GP + "models/model_card.json"))
# 5 dataset
s = new("Dataset: 112 FEM points", "32 corners + 80 Latin hypercube · λ = 1625 nm · signal width 10 µm · 0 failures after removing the rib-base triple point")
image(s, GP + "F5_dataset.png", 0.4, 1.6, w=8.6)
box(s, 9.2, 1.7, 3.6, 4.5, [H("Notes"), ("CAP_W sampled as a fraction of (GAP − 2.8 µm)", B),
    ("Cap filled down to the slab across its width (same SiO₂ as the buffer): removes a numerical triple point; results unchanged (≤ 0.1 %)", B),
    ("IL 0.002–4 dB/cm, Vπ·L 1.55–2.6 V·cm", B), ("≈ 2.6 min per point, 4 in parallel", B)])
# 6 GP
s = new("Gaussian-process surrogate", "10-fold CV, scalers refitted inside each fold · inputs scaled to [0, 1] · ARD length scales")
image(s, GP + "gp_parity_ard.png", 0.35, 1.55, w=12.6)
ci, cv_ = card["outputs"]["IL"], card["outputs"]["VpiL"]
nm = lambda m: m["kernel"].replace("m52", "Matérn 5/2").replace("m32", "Matérn 3/2").replace("rbf", "RBF") + (" + linear mean" if m["linear_mean"] else "")
table(s, [["Target", "Model chosen", "R²", "MAPE", "max err.", "95 % cover"],
          ["log₁₀ IL", nm(ci), f"{ci['cv']['R2_phys']:.4f}", f"{ci['cv']['MAPE_pct']:.2f} %", f"{ci['cv']['maxAPE_pct']:.0f} %", f"{ci['cv']['cover95_pct']:.0f} %"],
          ["Vπ·L", nm(cv_) + (", log" if cv_["log10"] else ", linear"), f"{cv_['cv']['R2_phys']:.4f}", f"{cv_['cv']['MAPE_pct']:.2f} %", f"{cv_['cv']['maxAPE_pct']:.1f} %", f"{cv_['cv']['cover95_pct']:.0f} %"]],
      0.6, 5.55, 8.2, [1.3, 2.6, 1.0, 1.0, 1.1, 1.2], size=11)
box(s, 9.0, 5.45, 3.8, 1.35, [("Candidates: Matérn 5/2, 3/2, RBF × linear mean on/off × Vπ·L log/linear. Chosen: best MAPE with ≥ 85 % coverage. Largest IL errors at buffer ≈ 50 nm (near cut-off)", {"size": 10})])
# 6b optimiser method
s = new("How the optimiser works", "Constrained search on the surrogate: one FEM run costs ≈ 2.6 min, one surrogate evaluation ≈ 10 µs")
steps = [("1  Grid", "Every combination of GAP (0.05 µm), BUFFER_H (5 nm), CAP_F (0.1), CAP_H (0.1 µm), MTX_small (0.1 µm): 429 660 designs inside the trained box"),
         ("2  Predict", "GP mean and 95 % interval of Vπ·L and IL for every design (vectorised, ≈ 30 s in total)"),
         ("3  Constrain", "Keep designs with IL upper-95 % bound ≤ 0.4 dB/cm and BUFFER_H ≥ 100 nm (uses the surrogate's own uncertainty as margin)"),
         ("4  Rank", "Sort by predicted Vπ·L; keep the best design of each (GAP, CAP_F, CAP_H) family → top 15 distinct designs"),
         ("5  Robust variant", "Same, but the IL constraint is applied at BUFFER_H − 40 nm (process worst case)"),
         ("6  Verify", "Re-simulate the top designs with FEM, plus mesh check")]
y = 1.75
for t, d in steps:
    box(s, 0.6, y, 8.3, 0.74, [(t, {"size": 13, "bold": True, "color": NAVY, "space": 1}), (d, {"size": 11})]); y += 0.82
box(s, 9.2, 1.75, 3.6, 4.6, [H("Why not a genetic algorithm"), ("5 inputs and a microsecond surrogate: the exhaustive grid is cheaper than a GA and cannot miss the optimum", B),
    ("Every parameter is monotone, but they compete for the same IL budget: the optimum sits on IL = 0.4 and the search decides which knob spends it", B),
    ("The grid also gives the Pareto front and sensitivities for free", B)])
# 7 optimum
s = new("Optimum on the surrogate", "Exhaustive grid of 429 660 designs · min Vπ·L s.t. IL upper-95 % ≤ 0.4 dB/cm, buffer ≥ 100 nm")
image(s, GP + "F7_optimum.png", 0.35, 1.55, w=8.9)
table(s, [["", "Nominal", "Robust"], ["GAP", "3.05 µm", "3.05 µm"], ["BUFFER_H", "150 nm", "190 nm"], ["CAP_W", "3.00 µm", "3.00 µm"],
          ["CAP_H", "1.0–1.2 µm", "1.1 µm"], ["MTX_small", "1.0 µm", "1.0 µm"], ["Vπ·L / IL (FEM)", "1.747 / 0.377", "1.801 / 0.276"],
          ["buffer −40 nm (FEM)", "1.687 / 0.552", "1.747 / 0.377"]], 9.4, 1.65, 3.5, [1.15, 1.2, 1.15], size=10)
box(s, 9.4, 4.55, 3.5, 2.2, [("Gap at minimum, cap fills the gap, MTX_small max. Buffer not at minimum: at the IL limit a thick buffer + small gap beats a thin buffer + wider gap. CAP_H barely matters (≤ 0.004 V·cm). Robust: IL ≤ 0.4 also at −40 nm", {"size": 10})], fill=TINT)
# 8 validation
s = new("FEM validation of the surrogate", "Independent FEM runs at the predicted optima · mesh check at MESH_SCALE 1.0")
table(s, [["Design (GAP / BUF / CAP_W / CAP_H / MTXs)", "Vπ·L FEM", "Vπ·L GP", "IL FEM", "IL GP [95 %]"],
          ["3.05 / 150 / 3.000 / 1.1 / 1.0  (optimum)", "1.7465", "1.7465", "0.3773", "0.371 [0.358–0.386]"],
          ["3.05 / 150 / 3.000 / 1.0 / 1.0", "1.7469", "1.7470", "0.3771", "0.371 [0.357–0.385]"],
          ["3.05 / 165 / 3.025 / 1.1 / 1.0", "1.7487", "1.7472", "0.3796", "0.381 [0.367–0.394]"],
          ["3.05 / 150 / 3.000 / 1.2 / 1.0", "1.7470", "1.7474", "0.3773", "0.372 [0.359–0.386]"],
          ["3.05 / 165 / 3.025 / 1.0 / 1.0", "1.7494", "1.7475", "0.3794", "0.379 [0.366–0.393]"],
          ["optimum at buffer 110 nm (−40)", "1.6870", "1.6868", "0.5523", "0.544 [0.512–0.579]"],
          ["hold-out: baseline 3.2 / 100 / 3.0 / 0.5 / 1.0", "1.8268", "1.8221", "0.2615", "0.263 [0.240–0.288]"],
          ["hold-out: 3.2 / 50 / 3.0 / 0.5 / 1.0", "1.7237", "1.7239", "0.7800", "0.690 [0.643–0.740]"]],
      0.6, 1.7, 12.2, [4.6, 1.5, 1.5, 1.5, 3.1], size=11, highlight=(1,))
box(s, 0.6, 5.0, 12.2, 1.6, [("Vπ·L within 0.3 % everywhere; IL within 1.7 % at buffer ≥ 100 nm, −11.5 % at 50 nm (steep near cut-off, outside the optimisation range)", B),
    ("Mesh 1.0 vs 1.4 at the optimum: Vπ·L 1.7467 vs 1.7465 (0.01 %), IL 0.3713 vs 0.3773 (1.6 %); baseline IL 0.2570 vs 0.2615 (1.7 %)", B)])
# 8b gap >= 3.5
s = new("Optimum with GAP ≥ 3.5 µm", "Same search restricted to GAP ≥ 3.5 µm · FEM-verified (GP underestimates IL by 9–15 % here: CAP_W = GAP is the edge of the trained box)")
table(s, [["", "Nominal (buffer ≥ 100 nm)", "Robust (IL ≤ 0.4 at −40 nm)"],
          ["GAP / CAP_W", "3.50 / 3.50 µm (cap fills gap)", "3.50 / 3.50 µm"], ["BUFFER_H", "100 nm", "115 nm"], ["CAP_H / MTX_small", "1.1 / 1.0 µm", "1.1 / 1.0 µm"],
          ["Vπ·L / IL  (FEM)", "1.857 / 0.233", "1.880 / 0.192"], ["at buffer −40 nm (FEM)", "1.790 / 0.579", "1.816 / 0.371"],
          ["GP prediction (nominal)", "1.853 / 0.210", "1.877 / 0.170"]], 0.6, 1.8, 8.0, [2.6, 2.7, 2.7], size=12, highlight=(4,))
box(s, 8.9, 1.8, 3.9, 4.4, [H("Reading"), ("+0.11–0.13 V·cm vs GAP 3.05 µm, as expected from ≈ 0.05 V·cm per 0.1 µm", B),
    ("Buffer now hits its 100 nm floor: the wider gap frees IL budget", B), ("Robust design keeps IL < 0.4 at 75 nm buffer", B),
    ("Same picture as Madrid B (1.854 / 0.209 at gap 3.2): geometry gains are worth ≈ 0.05–0.1 V·cm; the gap dominates", B)])
# 9 predictor
s = new("Offline predictor", "madrid1_predictor.html · single file, no Python, no internet · GP maths in JavaScript from model_card.json")
image(s, GP + "gui_screenshot.png", 0.5, 1.55, w=7.6)
box(s, 8.4, 1.6, 4.4, 4.7, [H("Features"), ("Sliders for the 5 parameters, live cross-section", B), ("Vπ·L and IL with 95 % intervals", B),
    ("Worst case at buffer −40 nm", B), ("Flags: IL > 0.4, buffer < 100 nm, extrapolation", B), ("Buttons: baseline, optimiser best", B),
    ("predictor.py: same model, numpy only, batch predictions; matches scikit-learn to 1e-11", B)])

