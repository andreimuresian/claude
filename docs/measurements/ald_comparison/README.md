# ALD RF impact: CORDOBA, JEREZ, HELSINKI comparison
`build_comparison.py` reads `summary_FOM.csv` (set "all") of `../ald_cordoba8mm/out_4CA0162`, `out_4CA0163`,
`../jerez/out_6JZ0011`, `../helsinki/out_5HK0005` and writes `change_comparison.png` (median per-chip change with IQR)
and `ALD_RF_impact_comparison.pptx` (4 slides: title, samples and no-ALD values, changes, conclusions).
`combined_plots.py`: all designs on one graph: `combined_box_n_m.png`, `combined_box_Z0.png` (CORDOBA axes, medians in
red) and `combined_S11.png`, `combined_S21.png` (mean measured |S| over chips, solid no ALD, dashed ALD; S21 axis to
-7 dB so the 13 mm HELSINKI line is not clipped).
