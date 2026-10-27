# RF Cordoba (60 GHz) with optional SiO2 buffer and ALD

Notebook: `VPI_RF_Cordoba_buffer_ALD.ipynb` (repo root) is the reference version: volumetric gold only
(cell 5), IBC cells removed. Set `BUFFER_H` (0 or 0.200 um) and `T_ALD` (0 or 0.040 um) in cell 0;
`TAN_ALD` sets an optional ALD loss tangent. `make_nb.py` only builds the earlier IBC-containing
intermediate version. Results: `cases.txt`, `rf_fom_cases.csv`, plots `rf_*.png`.
