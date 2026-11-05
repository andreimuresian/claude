# Istanbul TD run (a): bare lines (no termination, no pads); both lines A and B

Upload here the zipped exports of run (a).

Exports (3D Export in Volume, ASCII; monitor `e-field (f=1) [1]`, sweep all, excitation [1]); one step for x, y, z:
- A_ : x 0.001275 (min = max), y -0.0075..0.0075, z 0.3..9.05, step 0.005
- B_ : x 0.001275 (min = max), y -0.6325..-0.6175, z 0.3..9.05, step 0.005

Grid points in y per line: +-2.5 um (inside the signal, unused) and +-7.5 um (in the gaps, 0.4 um from the gap centre
at +-7.1 um). Excited line A at y = 0 (port 1 at z = 0.3); line B at y = -0.625.
Please also add the S-parameter touchstone and say which of ports 3/4 is at z = 0.3.

## Received (2026-11-05)
Two zips (A: txt, B: CST CSV; 60 frequencies 1-60 GHz each) and `v0_istanbul_rf_line.s4p` (port 1 excited;
LN_THICKNESS 0.000275, SILICON_THICKNESS 0.55). Grid as exported:
* A: y -0.0075, -0.0025, 0.0025, 0.0075 (gaps at +-7.5 um, as planned);
* B: y -0.63, -0.625, -0.62, -0.615, not the planned -0.6325..-0.6175: gaps sampled at 5 um from the line centre
  (0.15 um from the signal edge), -0.615 mostly inside the ground;
* z 0.3025..9.0525 step 0.005 (last point beyond the far port, zero, dropped).
`load_fields.py` reads the zips directly (no unpacking).

## Port assignment (`port_check.py`)
Complex correlation of the B/A gap-voltage ratio at the line ends with the S-parameters: port 3 near / port 4 far
0.79 / 0.73, swapped 0.02 / 0.02. So NEXT = S31, FEXT = S41 (as in CORDOBA).

## NEXT, FEXT, EO (`xtalk_run_a.py`, `xtalk_run_a.png`, `xtalk_run_a.csv`, `xtalk_run_a.log`)
50/50 ohm, push-pull, n_g 2.27 (same settings as the CORDOBA dense run). Maxima 5-60 GHz: NEXT -27.0 dB (38 GHz),
FEXT -27.9 dB (46 GHz), EO -30.9 dB (46 GHz). EO - FEXT median -2.6 dB (5-95 % -6.6 .. +1.5), correlation of the dB
curves with FEXT 0.91, with NEXT 0.74. CORDOBA dense run EO: median -66.7 dB, max -63.2 dB, i.e. about 30 dB lower.
Caveat: B sampled at 5 um, A at 7.5 um from the line centre; the EO level may carry a bias of unknown size. Re-export
of B with y -0.6325..-0.6175 (export only, no new run) removes it.

## Line B re-exported as txt (2026-11-05, `e-field (f=1) [1]_lineB_txt.zip`)
Export dialog (user's screenshot): x 0.001275, y -0.6325..-0.6175, z 0.3..9.05, step 0.005, uniform sampling. The txt
file has the same grid as the CSV (y -0.63..-0.615, z 0.3025..9.0525) and identical values (difference 0 at 5, 30,
60 GHz): the format is not the cause; CST places the grid differently from the dialog values. Next: pointlist export
(`pointlist_B_gaps.txt`).

## Line A re-exported at y -0.005..0.005 (`e-field (f=1) [1]_lineA_5um.zip`): matched sampling
Grid as requested: y -0.005, 0, 0.005 (gaps at +-5 um, 0.15 um from the signal edge, as line B), z 0.3025..9.0525.
`xtalk_run_a.py` now uses it. Sampling bias of the first EO (A at 7.5 um, B at 5 um): +2.2 dB, constant with
frequency (+2.16 .. +2.24 dB). Results with matched sampling: NEXT max -27.0 dB (38 GHz), FEXT max -27.9 dB (46 GHz),
EO max -33.1 dB (46 GHz); EO - FEXT median -4.8 dB (5-95 % -8.9 .. -0.7), correlation with FEXT 0.91, with NEXT 0.74.
EO at 5/10/20/30/40/50/60 GHz: -52.5, -51.5, -40.3, -41.7, -33.5, -41.8, -35.1 dB.
