# Istanbul run (d): full module

Geometry (history and screenshot from the user, 2026-11-09): driver carrier (alumina, to be confirmed with the
back-end engineer) with the driver's GS output traces, 8 bond wires (spline, PEC, 17 um diameter, loop height
`h_looP` = 0.09 mm), launch pads on oxide, line pair 8.75 mm (z 0.3..9.05) on the chip.
Ports: 1 = waveguide port at the start of the driver trace of line A (aggressor, y = 0, the only excited port);
5 = the same for line B (not excited); 2, 4 = far-end discrete ports (assumed 2 = A, 4 = B; not visible in the history).
The driver is not modelled as a circuit: port 1 is a matched source at the trace impedance. Line and driver are both
about 60 ohm (user), so the missing driver mismatch should be small.

Files: `e-field (f=1) [1]_lineA.zip` (txt, y -0.005/0/0.005) and `_lineB.zip` (CSV, y -0.63..-0.615), x 0.001275,
z 0.300..9.050, step 0.005, 1..60 GHz, all frequencies valid. `v0_istanbul_rf_module_allS.txt`: CST ASCII export
(the touchstone export failed), magnitudes in dB only (no phase) of S11, S21, S41, S51.
NEXT = |S51| (at the driver port of B), FEXT = |S41|.

`xtalk_run_d.py` -> `xtalk_run_d.log`, `.csv`, `xtalk_run_d.png`, `eo_runs_abcd.png`, `next_fext_runs_acd.png`.
Same EO method as runs (a)-(c); the comparison leaves out 2 and 15 GHz (corrupted in run c).

## Result (5-60 GHz)
| | Highest | Median | Run (d) - run (c), median |
|---|---|---|---|
| EO | -20.1 dB at 29 GHz | -27.3 dB | +6.4 dB |
| NEXT | -18.0 dB at 28 GHz | -24.3 dB | +2.4 dB |
| FEXT | -21.0 dB at 28 GHz | -27.9 dB | +3.4 dB |

EO is 12.5 dB above run (a) (median). Below 20 GHz the change is largest: EO, NEXT and FEXT reach -20 to -21 dB
already at 3 and 9 GHz, where runs (a)-(c) are at -45 to -70 dB.
All three curves ripple together with a period of about 6 GHz (corr(EO, FEXT) 0.80, corr(EO, NEXT) 0.67), and NEXT
and FEXT are at the same level. This points to a resonant coupling path added by the driver side (carrier, wires or
the substrate below), not to the distributed coupling along the line; the path is not identified yet.
|S11| at port 1 rises to -5 to -8 dB above 30 GHz (run c: about -23 dB); the bond wires are a likely cause, unverified.
The EO-from-fields result does not depend on the S-parameter normalization.

## Comparison with the measurement (`compare_lab.py` -> `sim_vs_lab.png`, `compare_lab.log`)
Measured curve: MZ3toMZ4 of module K00626 (SN 6A077700), the worst of the measured pairs, digitized by the user from
the lab plot (`lab_extracted_EO_xtalk.xlsx`, copied to `lab_MZ3toMZ4_extracted.csv`; digitizer accuracy about 1 dB).
5-60 GHz: median measured -19.3 dB vs simulated -27.3 dB; maximum -14.3 vs -20.1 dB; ripple period about 5 GHz
measured vs about 6.5-7 GHz simulated (the estimate depends on the method: 6.4 from the raw spectrum, 6.9 here).
Below about 25 GHz the two agree within a few dB; above about 27 GHz the measured curve is 5-8 dB higher.
The simulation reproduces the order of magnitude and the rippled shape, but it underestimates this pair. The other
measured pairs are lower (about -30 to -20 dB), so part of the gap is pair-to-pair spread.
