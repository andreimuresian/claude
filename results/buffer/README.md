# Lifted electrodes on a 200 nm SiO2 buffer (gap 3.2 / 10 um)

Notebook: `VPI_interface_optimized_Lisbona_lifted_buffer.ipynb` (executed; cells 0, 1, 5 changed
w.r.t. the lifted notebook, cells 2-4 unchanged). Cell sources: `cells/cell0_lifted_buffer.py`,
`cells/cell1_lifted_buffer.py`, `cells/cell5_lifted_buffer.py`.

Nominal design (x_lift = 7.0 um, lambda 1575 nm): **IL = 0.048 dB/cm, Vpi*L = 2.148 V*cm**,
67k triangles, ~75-85 s for an 8-mode search.

## Mesh convergence (`mesh_convergence_buffer200nm.csv`)
| case | triangles | IL (dB/cm) | Vpi*L (V*cm) |
|---|---|---|---|
| reference (everything near the mode 1.5-2x finer) | 220k | 0.0473 | 2.1493 |
| production (skin 18 nm, buffer 50 nm = 4 layers) | 67k | 0.0481 | 2.1484 |
| one-at-a-time refinements (buffer, skin, slab, corners, step, far field, gap/cap/core) | 84-122k | 0.0475-0.0482 | 2.1479-2.1489 |

## BUFFER_H = 0
Gives back the plain lifted model: gap 4.2, x_lift 7.0 -> IL 0.2220 dB/cm, Vpi*L 2.2648 V*cm
(previous lifted notebook: 0.2216 / 2.2647). Full notebook executed at BUFFER_H = 0 without errors.

## x_lift sweep (`lift_sweep_buffer200nm.csv`, `IL_vs_xlift_buffer.png`)
x_lift = 3.8-12.0 um in 0.1 um steps + 16, 20, 24, 28, 30.1 um (88 points):
IL = 0.0480-0.0481 dB/cm everywhere, Vpi*L = 2.148-2.157 V*cm (slightly higher only when the column comes within ~2 um of the gap). No standing wave.

Same gap, other buffers (`lift_sweep_comparison.csv`):
| buffer | IL range over x_lift 5-9 um | behaviour |
|---|---|---|
| 0 nm | 4.0 - 32.7 dB/cm | standing wave, period 0.9 um |
| 25 nm | 4.0 - 17.0 dB/cm | standing wave, period ~1.8 um |
| 50 nm | 0.3256 - 0.3259 dB/cm | flat |
| 200 nm | 0.0480 - 0.0481 dB/cm | flat |

## Why (`surface_wave_cutoff.png`, `surface_wave_index_vs_buffer_1D.csv`)
The wave guided along the gold/(buffer)/LN-slab stack has index 2.07 with no buffer (> rib 1.884):
at the rib's propagation constant it travels sideways under the metal and bounces off the lift
-> standing wave, IL period pi/k_x. The buffer lowers its index (1.69 at 200 nm); below the rib
index it can no longer propagate sideways, the field under the metal is evanescent (-29 dB/um
at 200 nm) and never reaches the lift. 1D cutoff: ~38 nm. Predicted ripple period at 25 nm:
1.9 um (simulated ~1.8 um).

## Gap trade-off at 200 nm (`gap_scan_buffer200nm.csv`, `gap_scan_buffer200.png`)
| gap (um) | 2.4 | 2.6 | 2.8 | 3.0 | 3.2 | 3.4 | 3.6 |
|---|---|---|---|---|---|---|---|
| Vpi*L (V*cm) | 1.635 | 1.770 | 1.899 | 2.025 | 2.148 | 2.271 | 2.392 |
| IL (dB/cm) | 0.651 | 0.326 | 0.169 | 0.090 | 0.048 | 0.026 | 0.014 |
