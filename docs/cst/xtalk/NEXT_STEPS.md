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
