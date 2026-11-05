# Istanbul TD run (b): bare lines + real far-end terminations
Same model as `../istanbul_run_a` with, on each line, the far-end termination (pads on Si through a 300 x 200 um LN/SiO2
trench; RS = 25 ohm, RG = 50 ohm lumped elements; intended network: RS in series, then 2 x RG to ground = 50 ohm).
Ports only at the near end: CST port 1 = line A (y = 0, excited), CST port 3 = line B (y = -0.625), z = 0.3; in the s2p
they are ports 1 and 2. Accuracy -40 dB, 0-60 GHz. LN_THICKNESS 0.000275, SILICON_THICKNESS 0.55.

Files: `e-field (f=1) [1]_lineA.zip` (txt, y -0.005/0/0.005), `e-field (f=1) [1]_lineB.zip` (CSV, y -0.63..-0.615),
z 0.3025..9.0525 step 0.005, 60 frequencies: the same grids as the matched run (a) exports. `v0_istanbul_rf_lineZload.s2p`.

## Results (`xtalk_run_b.py`, `.log`, `.csv`; `xtalk_run_b.png`, `eo_run_a_vs_b.png`)
Termination check: S11 at DC +0.0134, input resistance 51.4 ohm (load + line DC resistance, estimated ~11 ohm from the
gold cross-sections), i.e. a load of roughly 40 ohm; 25 ohm (both RG only) would give S11 ~ -0.16, 8 ohm ~ -0.44.
|S11| 1-60 GHz median -17.3 dB (run a, 50 ohm port at the far end: -18.2 dB).
NEXT max -25.8 dB (30 GHz); EO max -31.9 dB (37 GHz). EO b - EO a: median +1.8 dB, 5-95 % -7.7 .. +9.7 dB,
correlation 0.66. EO dips every ~6.5-7 GHz above 30 GHz (34, 41, 47 GHz).
| f (GHz) | NEXT b | EO b | EO a |
|---|---|---|---|
| 5 | -45.2 | -48.4 | -52.5 |
| 10 | -40.5 | -46.2 | -51.5 |
| 20 | -35.9 | -40.2 | -40.3 |
| 30 | -25.8 | -32.4 | -41.7 |
| 40 | -26.7 | -40.9 | -33.5 |
| 50 | -32.6 | -32.5 | -41.8 |
| 60 | -43.8 | -34.4 | -35.1 |
