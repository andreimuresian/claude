# HELSINKI measured lines: ALD RF impact (wafer 5HK0005)
Same method and figures as `../jerez` and `../ald_cordoba8mm`. 8 chips (LINEA 00-07), one 13 mm line each, measured
before (MTX) and after ALD (source folder ALD_SPUTTER; labelled ALD, user). Collected with `collect_helsinki_files.py`;
placed as `raw/5HK0005/5HK0005_<noALD|ALD>_NN.s2p`. 2-port, 40 MHz-60 GHz, 1601 points, 50 ohm, RI.

Scripts (shared, run from `../ald_cordoba8mm`):
* `wafer_analysis.py 5HK0005 ../helsinki 13 41.5` (L = 13 mm; Z0 band 10-41.5 GHz = 6 periods of the measured 5.25 GHz
  pad ripple) -> `out_5HK0005/`, log `out_5HK0005_log.txt`;
* `figs_v2.py` / `box_both_medians.py --base ../helsinki --wafers 5HK0005 --length 13 --nm 2.20 2.35 0.01
  --z0 40.0 45.0 0.5` (`figs_v2.py` also `--s21min -6`; CORDOBA axes, coworker 2026-11-10; S21 clipped above ~57 GHz) -> `out_5HK0005/v2_*.png`, `v2_box_wafer*.png`, `box_medians.log`;
* deck `deck/build_helsinki_deck.py` -> `ALD_RF_impact_HELSINKI.pptx` (5 slides).

## Results (2026-11-10)
All 16 files pass the checks (reciprocity median 0.8-1.2 %, passivity <= 0.925); no chip excluded.
Median per-chip change ALD - no ALD (chips up / 8): n_m @ 60 GHz +0.0098 (8/8); Re Z0 10-41.5 GHz -0.227 ohm (0/8);
alpha @ 30 GHz -0.122 dB/cm (0/8); alpha @ 60 GHz -0.079 dB/cm (0/8); |S21| @ 30 GHz +0.160 dB (8/8); @ 60 GHz
+0.104 dB (8/8). Z0 pad ripple (std over 10-41.5 GHz, median of chips): 1.76 ohm no ALD -> 0.95 ohm ALD.
Against JEREZ / CORDOBA: smallest n_m rise (+0.010 vs +0.018 / +0.035-0.038); loss decreases as on JEREZ (about 4x
larger at 30 GHz), while CORDOBA increased; the pad ripple shrinks after ALD (CORDOBA: grew).
