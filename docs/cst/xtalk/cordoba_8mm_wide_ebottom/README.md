# CORDOBA 8 mm standard, widened, electric bottom (coworker's run)

Identical to `../cordoba_8mm_wide` (substrate 625 um beyond each outer ground, port 1 driven, ports 2-4
50 ohm, -27 dB) except the Si bottom boundary: Xmin electric instead of open (conductive glue under the
chip). Purpose: does the chip-wide |n| ~ 2.55 wave survive with a conducting bottom, and how do the
victim field and the EO crosstalk change? One variable changed, so every difference is due to it.

## Files to place here
1. The Touchstone export (`.s4p`, any name): column 1 only.
2. 24 gap-field files, port 1, 5-60 GHz every 5 GHz, same settings as `../cordoba_8mm_wide`
   (x 0.001; A: y 0.2925-0.3325; B: y -0.3325 to -0.2925; z 0-8; step 0.005). CST default names are fine.
3. The three 30 GHz planes, same settings as the open-bottom run (zipped is fine):
   V1: x -0.53..0.103, y = 0, z 0-8, step 0.005; V2: same at y = -0.3125; H: x = 0.001, y -1.03..1.03,
   z 0-8, step 0.01.
4. If the dense subvolume monitors were added: their gap columns (same x, y, z, step as item 2), in a
   subfolder `dense/`.
