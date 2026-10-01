# O band (1310 / 1360 nm), 400 nm LN film, compared with the C band (550 nm film)

## Setup

Geometry: as before except the LN film.

* LN film 400 nm, etch 170 nm, slab 230 nm: `TECN = 0.400`, `WG_H = 0.170`.
* Rib top 1.0 um, 60 deg sidewall.
* Cap, lift, electrodes and x_lift definition unchanged.

Designs (same as the C-band study):

* No buffer, gap 4.2 um (cell0_lifted.py).
* 200 nm SiO2 buffer, gap 3.2 um (cell0_lifted_buffer.py).

x_lift sweep: 6.5 to 11.0 um in 0.1 um steps, 46 points per curve, 184 runs, no failures.

## Materials

| wavelength | ne / no (Zelmon) | n_SiO2 (Malitson) | eps_Au |
|---|---|---|---|
| 1310 nm | 2.145121 / 2.219967 | 1.446804 | -80.11 - 7.09j |
| 1360 nm | 2.143411 / 2.217969 | 1.446237 | -86.63 - 7.75j |

* **Au:** the anchor (-120.7 - 11.9j at 1575 nm) is scaled by the Johnson & Christy ratio.
* **SiO2:** exact Malitson, as intended.
* **Note on the C-band runs:** they used n_SiO2 = 1.438749, which is Malitson at 1954 nm, not at 1575 nm (1.443723). Check at 1575 nm, x_lift = 7 um, Malitson vs the old value:
  * IL +1.9 % (no buffer) and +2.3 % (buffer);
  * Vpi*L +0.1 %;
  * cutoff 39.0 vs 38.0 nm.
  * So the C-band conclusions are unchanged.

## Mesh check at 1310 nm

Reference mesh about 2x denser than production (138-147k triangles), x_lift = 7 um:

| | IL, reference vs production (dB/cm) | Vpi*L |
|---|---|---|
| no buffer | 0.1564 vs 0.1576 | within 0.02 % |
| buffer | 0.0176 vs 0.0179 | within 0.02 % |

## Results

| | 1310 | 1360 | 1525 | 1550 | 1575 |
|---|---|---|---|---|---|
| film / slab (nm) | 400 / 230 | 400 / 230 | 550 / 275 | 550 / 275 | 550 / 275 |
| No buffer: IL range over x_lift (dB/cm) | 0.043-0.158 | 0.075-0.269 | 0.11-0.55 | 0.14-0.68 | 0.18-0.88 |
| No buffer: Fabry-Perot limit IL_inf (dB/cm) | 0.084 | 0.147 | 0.265 | 0.331 | 0.412 |
| No buffer: ripple period (um) | 0.635 | 0.675 | 0.849 | 0.872 | 0.895 |
| No buffer: Vpi*L (V*cm) | 1.812 | 1.916 | 2.167 | 2.215 | 2.265 |
| Buffer 200 nm: IL (dB/cm), flat | 0.0179 | 0.0284 | 0.0333 | 0.0401 | 0.0481 |
| Buffer 200 nm: Vpi*L (V*cm) | 1.683 | 1.779 | 2.054 | 2.101 | 2.148 |
| Cutoff buffer, 1D (nm) | 45.7 (44.7-46.7) | 46.5 (45.3-47.7) | 37.8 | 38.0 | 38.0 |

* Cutoff range: from the two in-plane LN permittivities.
* Buffered IL is flat over x_lift to within 0.35 % at every wavelength.

## 2D validation of the 1D model (validation_1D_vs_2D_oband.csv)

| quantity | 2D vs 1D |
|---|---|
| ripple period at 0 and 25 nm | within 0.5-2.2 % |
| decay at 200 nm | 5-7 % weaker in 2D |
| decay at 50 nm, just above cutoff | 10-13 % weaker in 2D |

The 50 nm bias implies a 2D cutoff about 1 nm above the 1D value: about 46.5 nm at 1310 nm and 47.3 nm at 1360 nm.

## Files

* lift_sweep_oband.csv
* fabry_perot_fit_oband.json
* summary_O_vs_C.csv
* validation_1D_vs_2D_oband.csv
* IL_VpiL_vs_xlift_oband.png
* Oband_vs_Cband_summary.png
