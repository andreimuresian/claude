# Next steps (recorded 2026-10-30)

1. **Done 2026-10-30 (`cordoba_8mm_wide/results.md`): wave still present, hypothesis 1 rejected.** Widened CORDOBA standard run (substrate 625 um beyond each outer ground). Does the
   extra victim wave (n ~ 2.45-2.50) disappear? Exports and folder: `cordoba_8mm_wide/README.md`.
   Analyses: field EO, S-parameters vs the narrow run, five-mode fit, free-index scan, remainder.
2. CORDOBA high impedance (`cordoba_hz_8mm`): same -27 dB energy level but much higher
   crosstalk, so a cleaner test of the mode model.
3. Field export at rib height (x = 0.1 um): a check of the sample-point height, low priority.
4. Finite silicon with an electric (conducting) boundary at its bottom: later.

Theory reports (`docs/reports`): 1 done (field-based EO crosstalk); 2 TD vs eigenmode comparison;
3 how the eigenmode solver finds modes; 4 the two-mode model (Ze = Zo).

## 2026-11-03: TD accuracy check (pending)
Open- and electric-bottom widened TD runs used accuracy -27 dB; B's gap fields lie 55-72 dB below A's, and the
matrix pencil finds 65-99 % of B's energy in waves that change amplitude the wrong way for their phase direction
(`cordoba_8mm/eigen_w2mm_mag_ebottom_sweep/pencil_sign.log`). Hypothesis: truncation error of the -27 dB runs.
Rerun launched by the user: electric bottom, widened, one port, accuracy -60 dB (the -27 dB run took 4 h).
To do on arrival: check in the log which criterion ended the run (accuracy or time limit); compare B at the 12
monitor frequencies with the -27 dB run; repeat `pencil_sign.py`; if B changes, redo the TD crosstalk results.

## 2026-11-04: dense run launched (pending)
Widened electric-bottom CORDOBA, one port, accuracy -40 dB; E-field 2D-plane monitors at x = 0.001, 1-60 GHz every
1 GHz (broadband field monitor tool; no subvolume option there). Exports via result template, sweep all, two
templates (A_, B_ prefixes, standard gap boxes, step 0.005), excitation [1].
On arrival: (1) check grid and which x plane the 2D monitor used; (2) dense EO 1-60 GHz; (3) third accuracy level at
5, 10, ... 60 GHz vs the -27 and -44.5 dB runs: test of the error-scales-with-amplitude assumption; (4) six-mode fits
with index corrections at 60 frequencies, end-model test; (5) EO ripple period vs c/((n_opt + n_wave) L).

## 2026-11-05: Istanbul TD runs (a: line only; b: + real termination; c: + input pads; d: full module)
Geometry (user): pitch 625 um; line A centred at y = 0, line B at y = -0.625 mm; signal 9.7 um, gaps 4.5 um, outer gap
edges +-0.00935 mm (B: -0.63435, -0.61565); electrodes from x = slab_h = 0.000275 mm, 2 um thick (to 0.002275);
line length 8.75 mm. Gap centres: A y = +-0.0071; B y = -0.6321, -0.6179.
Line runs z = 0.3..9.05 (ports at z = 0.3 and 9.05).
Monitors: 60 E-field subvolume monitors 1-60 GHz, x 0..0.002, y -0.645..0.015, z 0.3..9.05 (as built, run a).
Exports: one line per gap (y min = max = gap centre), x 0.001275, z 0.3..9.05, step 0.005 (1751 points): the 4.5 um gaps
cannot be hit by a common-step box spanning both gaps of a line (0.0142 mm is not a multiple of 0.005).

### 2026-11-05: run (a) finished; history list checked against the last CORDOBA run
Same as CORDOBA: materials (LN 43/28/43, SiO2 3.9, Si 11.9 with 2.5e-4 S/m, Au 4.561e7 S/m), Xmin electric + open
elsewhere, background XmaxSpace 0.1, TD-S, excitation port 1 only, -40 dB, 0-60 GHz, 50 ohm discrete face ports with
5 um port + 10 um PEC bridge, E-field monitors 1-60 GHz every 1 GHz. Line B made as a copy of line A shifted -0.625 mm.
Differences: substrate y -1.0595..0.5175 is not centred on the line pair (outer ground edge to substrate edge
0.474 mm on the A side, 0.391 mm on the B side; CORDOBA symmetric); gap mesh group 6 steps (CORDOBA 15), global 60
(CORDOBA 50), no LN mesh group (CORDOBA 8 steps); substrate z faces offset (-8.865, +9.5), so the substrate may extend
past the line ends (CORDOBA ports sit on the substrate end faces): to be confirmed in the GUI; SUBSTRATE:solid5_1 (Si
copy) never deleted in the history.
Exports (user's choice, two templates as in CORDOBA): A_ y -0.0075..0.0075, B_ y -0.6325..-0.6175; x 0.001275,
z 0.3..9.05, step 0.005 (gap samples at +-7.5 um, 0.4 um from the gap centre). Upload folder: istanbul_run_a/.
