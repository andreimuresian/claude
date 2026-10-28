# CORDOBA 8 mm slow-wave pair (coworker's run)

`LINEA_8MM_625UM_PITCH_CORDOBA.s4p`: ports 1 A near, 2 A far, 3 B near, 4 B far; lines at y = +/-312.5 um.
Signal 35 um, grounds 49.85 um, gaps 4.15 um, Au 2 um; LN 200 nm / SiO2 4.7 um / Si 525 um (open bottom, so
semi-infinite Si); substrate continuous between the lines, open side boundaries 21 um from the outer ground
edges; T slots recessed into the grounds, period 180 um; about 15 TD cells across the gaps. All open, no symmetry.
Field monitors: E and H volume, 0-60 GHz every 5 GHz.

`analyse.py` -> `results.txt` (side by side with Istanbul 5 mm and std LOW_Z 8 mm).

| | CORDOBA 8 mm | Istanbul 5 mm | std LOW_Z 8 mm |
|---|---|---|---|
| n (30 GHz), n_g (5-50 GHz) | 2.240, 2.227 | 2.108, 2.076 | 1.934, 1.911 |
| Z (30 GHz) | 45 ohm | 66 ohm | 37 ohm |
| n_e - n_o (30-60 GHz) | +0.0001 to +0.0003 | +0.003 to +0.007 (eigenmode CPW 0.0043) | +0.0001 to +0.0004 |
| NEXT / FEXT at 30 GHz | -62.3 / -66.4 dB | -37.2 / -49.6 dB | -69.6 / -69.4 dB |
| NEXT / FEXT group delay vs through | 2.09x / 1.07x | 2.29x / 1.68x | 2.08x / 1.12x |
| A/B asymmetry, end asymmetry | 3e-6, 3e-4 | 8e-5, 3e-4 | 2e-4, 1e-6 |

Through delay 59.4 ps = 8 mm at n_g 2.227: port 2 is at z = 8 mm (the 2.5 in the history's port record is stale).
