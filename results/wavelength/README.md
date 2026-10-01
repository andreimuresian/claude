# Lifted electrodes vs wavelength: 1525 / 1550 / 1575 nm

Same geometry as before; only the wavelength and the material dispersion change.

* No buffer: gap 4.2 um (cell0_lifted.py, the model of results/lift_sweep.csv).
* Buffer: 200 nm SiO2, gap 3.2 um (cell0_lifted_buffer.py).
* x_lift from 6.5 to 11.0 um in 0.1 um steps: 46 points per curve, 184 new runs.

## Materials (anchor values at 1575 nm unchanged)

| wavelength | ne / no (Zelmon 1997) | n_SiO2 | eps_Au |
|---|---|---|---|
| 1525 nm | 2.138286 / 2.211964 | 1.439348 | -113.17 - 10.96j |
| 1550 nm | 2.137560 / 2.211111 | 1.439050 | -116.99 - 11.44j |
| 1575 nm | 2.136842 / 2.210268 | 1.438749 | -120.70 - 11.90j |

How each was obtained:

* **LN:** the model's 1575 nm values are exactly Zelmon 1997 (undoped congruent LN), so that Sellmeier is used directly.
* **Au:** Johnson & Christy, interpolated linearly in eps vs photon energy, gives -120.37 - 11.93j at 1575 nm, i.e. the model's anchor within 0.3 %. The anchor is scaled by the J&C ratio eps(lambda) / eps(1575), separately for the real and imaginary parts.
* **SiO2:** the anchor 1.438749 matches no refractiveindex.info dataset. It is shifted by the Malitson dispersion: +0.0003 per 25 nm, which is negligible.
* **r33 and the DC permittivities:** unchanged.

## Results

| | 1525 nm | 1550 nm | 1575 nm |
|---|---|---|---|
| No buffer: IL range over x_lift (dB/cm) | 0.11-0.55 | 0.14-0.68 | 0.18-0.88 |
| No buffer: Fabry-Perot fit IL_inf (dB/cm) | 0.265 | 0.331 | 0.412 |
| No buffer: ripple period, fit vs 1D (um) | 0.849 / 0.863 | 0.872 / 0.888 | 0.895 / 0.912 |
| No buffer: Vpi*L (V*cm) | 2.167 | 2.215 | 2.265 |
| Buffer 200 nm: IL (dB/cm), flat to +-0.2 % | 0.0333 | 0.0401 | 0.0481 |
| Buffer 200 nm: Vpi*L (V*cm) | 2.054 | 2.101 | 2.148 |
| Cutoff buffer thickness, 1D (nm) | 37.8 (36.7-38.8) | 38.0 (36.7-39.2) | 38.0 (36.8-39.2) |

The cutoff range spans the two in-plane LN permittivities.

2D field checks against the 1D model (validation_1D_vs_2D.csv) agree everywhere:

* ripple period at 0 and 25 nm: within 1.3-6.3 %;
* lateral decay at 50 and 200 nm: within 0.1-4.1 %.

Files:

* lift_sweep_vs_wavelength.csv
* fabry_perot_fit_vs_wavelength.json
* summary_vs_wavelength.json
* cutoff_and_materials.csv
* IL_VpiL_vs_xlift_3wavelengths.png
* cutoff_vs_wavelength.png
