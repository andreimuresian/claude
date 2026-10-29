# CORDOBA high impedance, 8 mm slow-wave pair (coworker's run)

Signal 10 um, grounds 25 um, gaps 4.15 um, Au 2 um; lines at y = +/-312.5 um (pitch 625 um); substrate
per line w = 185 um (outer ground edge 58.35 um from the side boundary); LN 200 nm / SiO2 4.7 um /
Si 525 um (open bottom); T slots as in CORDOBA (W 3/4/9 um, L 20/86/66 um, start 0.13 mm, period 0.18 mm).

## Files to place here
* the s4p of the run (ports 1 A near, 2 A far, 3 B near, 4 B far)
* 24 E-field exports, port 1, f = 5, 10, ..., 60 GHz:

| file | x (mm) | y (mm) | z (mm) | step (mm) |
|---|---|---|---|---|
| `e-field_f<f>_1_A.txt` | 0.001 to 0.001 | 0.305 to 0.320 | 0 to 8 | 0.005 |
| `e-field_f<f>_1_B.txt` | 0.001 to 0.001 | -0.320 to -0.305 | 0 to 8 | 0.005 |

CST: monitor `e-field (f=<f>) [1]`, 3D Export in Volume, Use Subvolume, ASCII.
4 y columns x 1601 z points; y = +/-0.305 and +/-0.320 lie in the gaps (2.5 um from the signal edge,
1.65 um from the ground edge), +/-0.310 and +/-0.315 inside the signal (zero field).
`<f>` is the integer frequency in GHz (e.g. `e-field_f5_1_A.txt`); CST default names are also fine.
