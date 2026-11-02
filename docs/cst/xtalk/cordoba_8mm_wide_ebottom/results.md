# Widened CORDOBA, electric Si bottom vs open bottom (`../cordoba_8mm_wide`)

Files: s4p (column 1), 24 gap files (renamed `e-field_f<f>_1_<A|B>.txt`, grids checked: x 0.001, 9 y,
1601 z, 0-8 mm), 30 GHz planes V1, V2 (x -0.528..0.107: grid shifted by 1 um from the open-bottom run;
the row at x = 1.55 um under B's signal is inside the metal), H.

## S-parameters (`compare_open.py`)
* S11, S21 unchanged (0.02 dB); through n_g 2.2292 in both.
* NEXT: +4 dB at 1-2 GHz, +1.5..+3 dB at 5-10 GHz, within 0.5 dB above 20 GHz. Impulse response: still a
  return from A's far end, peak 128.2 ps, 0.55 rms in 100-140 ps (`s31_time.py`).
* FEXT: -5 to -12 dB at 2-15 GHz, +2 to +3 dB at 30-50 GHz. Impulse response: two equal peaks, 61.0 and
  75.3 ps (open bottom: one at 63 ps); 75.3 ps over 8 mm = n_g 2.82, a slower forward wave.
* Group delay ratio FEXT/through 1.07 -> 1.13.

## Gap fields and EO crosstalk
* Line A CPW pattern: changed by <= 0.2 %. Line B: CPW pattern 56-112 %, slot pattern 31-38 %.
* EO crosstalk (50/50 ohm, push-pull, n_g 2.27), electric - open: -5.6, -9.7, -5.2, +0.8, -3.8, +3.6, +2.1,
  +3.0, +4.8, +2.8, +5.0, +2.0 dB at 5..60 GHz. Electric: -96.5, -97.1, -86.2, -83.4, -78.7, -71.6, -69.9,
  -65.8, -65.9, -64.9, -62.9, -66.5 dB.

## Five-mode fit at 30 GHz (open-bottom eigenmodes; `fit30_ebottom.log`, `scan_free_wave.log`)
A CPW pattern 0.014; B' CPW pattern 0.512 (open: 0.517). Free extra wave: best n 2.45, 3 dB/cm, B' CPW
0.26 (open: 0.18 at 2.475): something the basis lacks has been added.

## Planes at 30 GHz (`planes_pencil.py`, `planes_pencil.log`)
* Under line B (V2), every depth: two backward waves of equal size, |n| 2.84-3.04 and |n| 1.94-2.05
  (open bottom: backward 2.5-2.7 leading).
* Surface on B's side and beyond (H, y -0.15 ... -1.0): backward |n| 2.84-3.02 leading, backward ~2.0
  second (open bottom: backward 2.58-2.65). Field +4.7 dB at y = -0.40.
* Midway (V1) near the surface: backward 2.52-2.68, as with the open bottom; deeper, |n| 2.8-2.9 grows.
* A's side: unchanged (A's forward 2.25-2.33 near A; 2.6-2.8 beyond).
Reading: with a conductor under the Si, a wave of index about 2.9 appears under and around B, and a
forward wave with n_g 2.82 appears in FEXT. An index near 2.9 is what a quasi-TEM wave between the
whole electrode set and the bottom conductor (microstrip-like, mostly in Si, eps 11.9 with fringing in
oxide and air) would have; such a wave is bound (above the grounded-slab TM0 index, 1.10 at 30 GHz),
so an eigenmode cell with an electric bottom should find it. Not yet confirmed.
