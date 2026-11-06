# Istanbul run (c): line pair + input launch pads

8.75 mm line pair (pitch 625 um) with launch pads (on oxide) at the near end; 50 ohm discrete ports at both ends.
Touchstone ports: 1 = line A near pad (excited), 2 = A far (z 9.05), 3 = B near pad, 4 = B far.
Far-end assignment checked against the fields (`port_check_c.py`). NEXT = |S31|, FEXT = |S41|.

Files: gap-field exports `e-field (f=1) [1]_lineA.zip` (txt, y -0.005/0/0.005) and `_lineB.zip` (CSV, y -0.63..-0.615),
x 0.001275, z 0.300..9.050, step 0.005; `v0_istanbul_rf_lineLaunch.s4p`.

Data notes: line B exports at 2 GHz (only Ex filled) and 15 GHz (all zero) are corrupted and left out of all three runs'
EO curves. The z = 0.300 point (line A zero there, line/pad boundary) is dropped.

`xtalk_run_c.py` -> `xtalk_run_c.log/.csv`, `xtalk_run_c.png` (NEXT, FEXT, EO), `eo_runs_abc.png`, `next_fext_runs_abc.png`.

| 5-60 GHz | run (a) bare line | run (b) real terminations | run (c) launch pads |
|---|---|---|---|
| NEXT max | -27.0 dB @ 38 GHz | -25.8 @ 30 | -20.8 @ 35 |
| FEXT max | -27.9 @ 46 | n/a | -21.6 @ 48 |
| EO max | -33.1 @ 46 | -31.9 @ 37 | -26.1 @ 48 |
| EO median | -38.4 | -36.7 | -32.8 |
