# Madrid 1 surrogate: offline package
* `Madrid1_LHS_dataset.xlsx` / `.csv`: 112 FEM points (32 corners + 80 LHS), inputs, Vπ·L, IL, Γ, n_eff; sheet "FEM validation".
* `gp_build.py`: fits the GP surrogates (log10 IL; Vπ·L), 10-fold CV, writes `models/gp_*.pkl` and `models/model_card.json`.
  Needs numpy, scikit-learn, matplotlib. Expects the dataset as `../sweep_gp.txt`; to use the CSV, replace `load()` (columns are named).
* `predictor.py`: single-geometry predictor from `model_card.json` (numpy only).
* `optimise.py` / `optimise_robust.py`: exhaustive grid search on the surrogate (env GAP_MIN for a minimum gap).
  Nominal: min Vπ·L s.t. IL upper-95 % ≤ IL_MAX and buffer ≥ BUF_MIN. Robust: same at buffer − 40 nm.
* `madrid1_predictor.html`: GUI, open in a browser (model embedded).
