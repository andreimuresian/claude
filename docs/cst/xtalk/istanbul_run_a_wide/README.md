# Istanbul run (a, wide): bare line pair, 625 um lateral padding

Same as run (a) (8.75 mm line pair, pitch 625 um, 50 ohm ports at both ends, port 1 excited) except the substrate
layers widened to 625 um lateral padding on both sides (run a: 391 / 474 um). Open boundaries still on the substrate edges.
Ports: 1 = A near, 2 = A far, 3 = B near, 4 = B far; NEXT = |S31|, FEXT = |S41|.

Files: `e-field (f=1) [1]_lineA.zip` (txt, y -0.005/0/0.005), `_lineB.zip` (CSV, y -0.63..-0.615), x 0.001275,
z 0.3025..9.0525 (same grid as run a), step 0.005; `v0_istanbul_rf_line_625.s4p`. The uploaded zips had swapped names;
renamed by content (y range) on placement.

`xtalk_run_a_wide.py` -> `.log`, `.csv`, `padding_a_vs_wide.png`.

| 5-60 GHz, wide - run (a) | median | 5-95 % | max abs | corr |
|---|---|---|---|---|
| EO | +0.7 dB | -2.3 .. +2.5 | 5.2 | 0.98 |
| NEXT | -0.4 | -2.9 .. +2.1 | 7.2 | 0.99 |
| FEXT | +0.2 | -3.0 .. +2.4 | 5.2 | 0.98 |
| S11 | 0.0 | -0.3 .. +0.3 | 0.5 | 1.00 |
