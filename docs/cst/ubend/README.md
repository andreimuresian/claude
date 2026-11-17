# Folded line with two U-bends: field monitors and exports

Geometry from the user's history list (parameters: WS 34.7 um, GAP 4.45 um, GAP2 4.8 um in the bends and their
straight extensions, BEND_RADIUS 0.1025 mm, EL_L 3.24, EL_L2 = EL_L3 = 1.44, DEV_L 3.7, MTX 2 um).
Port 1 at line 1 (y = -0.1025, z = 0); port 2 at line 3 (y = 0.3075, z = 2.7).

Monitors: `field_monitors_ubend.bas`. It creates 60 E-field monitors from 1 to 60 GHz, every 1 GHz. Each one is a
subvolume over x 0..MTX, y -BEND_RADIUS-0.1 .. 3*BEND_RADIUS+0.1, and z 0..DEV_L.

Exports use 3D Export in Volume, ASCII, one common step, with every frequency of monitor `e-field (f=N) [1]`.

| Export | x | y | z | step |
|---|---|---|---|---|
| L1_gap+ / L1_gap- | 0.001 | -0.082925 / -0.122075 | 0 .. 3.7 | 0.005 |
| L2_gap+ / L2_gap- | 0.001 | 0.122075 / 0.082925 | 0 .. 3.7 | 0.005 |
| L3_gap+ / L3_gap- | 0.001 | 0.327075 / 0.287925 | 0 .. 3.7 | 0.005 |
| BEND1 | 0.001 | -0.13 .. 0.13 | 3.50 .. 3.65 | 0.001 |
| BEND2 | 0.001 | 0.075 .. 0.335 | 1.375 .. 1.53 | 0.001 |

The gap centres sit at line centre ± (WS/2 + GAP/2) = ± 0.019575 mm. The bend boxes come from the history list:
- arc start at z = EL_L + 0.05 + TAPER_L ≈ 3.514 for bend 1, and 1.526 for bend 2;
- gap outer radius ≈ 0.1247 mm.

Confirm both boxes against the bounding boxes of the bend mesh helpers (component3:solid4/solid5 and their
component7 copies) before exporting. The 1 um step resolves the 4.8 um bend gaps, where the gap field is radial,
not along y.

## Single straight reference line (line 1 only, z 0..EL_L)
Monitors: `field_monitors_straight.bas`, subvolume x 0..MTX, y -BEND_RADIUS ± 0.1, z 0..EL_L.
Exports: x 0.001, y -0.082925 and y -0.122075 (one line export per gap), z 0 .. 3.24, step 0.005.

## Single U-bend (line 1 + bend + line 2)
Port 1 at line 1 (y = -0.1025, z = 0); port 2 at line 2 (y = 0.1025, z = 1.08).
Monitors: `field_monitors_single_bend.bas`, subvolume x 0..MTX, y -BEND_RADIUS-0.1 .. BEND_RADIUS+0.1, z 0..DEV_L.

| Export | x | y | z | step |
|---|---|---|---|---|
| L1_gap+ / L1_gap- | 0.001 | -0.082925 / -0.122075 | 0 .. 3.7 | 0.005 |
| L2_gap+ / L2_gap- | 0.001 | 0.122075 / 0.082925 | 0 .. 3.7 | 0.005 |
| BEND1 | 0.001 | -0.13 .. 0.13 | 3.50 .. 3.65 | 0.001 |
