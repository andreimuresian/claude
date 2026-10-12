# Field components: theory vs simulation (Lisbon lifted, etched slab, slab_w 8.2 µm)

The notebook parameters are unchanged. The FEM solve reproduces n_eff = 1.884033 and IL = 0.2225 dB/cm.

## Scripts

- `run_solve.py` re-runs cells 0–4 of the notebook and exports the field to `mode_fields.npz`. The `.npz` is not committed (10 MB); regenerate it in about 7 minutes.
- `slab1d.py` is the 1D anisotropic TE/TM multilayer solver.
- `theory_figs.py` builds the figures in `figs/F1`–`figs/F11` and writes `theory_numbers.json`.

## Deck

The deck is `deck/Field_components_theory.pptx`, built by `deck/build_deck.js`.

## Key checks (FEM vs theory)

| quantity | FEM | theory |
|---|---|---|
| decay in the gap (dB/µm) | −28.1 | −28.2 |
| phase of Ez relative to Ex | 90.000° | 90° |
| Ez/Ey under the gold (dB) | −9.8 | −10.0 |
| half-period of the lateral wave (µm), from the IL sweep fit | 0.895 | 0.897 |
| round-trip decay 2α (µm⁻¹) | 0.180 | 0.182 |
| buffer cutoff t_c | — | ≈ 40 nm |
