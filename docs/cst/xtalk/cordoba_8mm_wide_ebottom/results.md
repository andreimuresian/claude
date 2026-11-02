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

## Fit with the electric-bottom eigenmodes (`fit30_ebottom_modes.py`, `eo_decomp_ebottom.py`)
Six modes (even cpw, slot, strips vs bottom; odd cpw, slot, A vs B; same model and mesh), 30 GHz:

| model | A CPW | B' all | B' CPW | B' slot |
|---|---|---|---|---|
| CPW pair | 0.225 | 0.771 | 0.565 | 0.853 |
| + slot pairs | 0.014 | 0.343 | 0.573 | 0.127 |
| + A vs B | 0.014 | 0.286 | 0.441 | 0.165 |
| + strips vs bottom (all six) | 0.014 | 0.123 | **0.168** | 0.094 |

The strips-vs-bottom mode (n 3.19, CPW-like gap pattern) carries most of what B's CPW pattern lacked:
0.44 -> 0.17. A free extra wave on top only reaches 0.098, with a flat minimum over n 2.40-2.55 (and
3.0-3.1): no sharply defined extra wave is needed in the gaps any more. (Open bottom, open-bottom
modes: 0.52, and 0.18 only with the free n = 2.475 wave.)
EO weight on B (|H| relative to the data): CPW pair forward 2.07 (-21 deg), CPW pair backward 0.39,
slot pairs 0.42, strips vs bottom forward 0.44 (+118 deg), backward 0.03, A vs B 0.08; model 0.979,
residual 0.026. The CPW pair and the strips-vs-bottom wave differ by 0.96 in index (4.5 rad over the
fitted length), so here the split is well conditioned, unlike CPW vs n 2.475 (1.1 rad).

## Fit with the 2 mm electric-bottom eigenmodes (`fit30_ebottom_2mm.py`)
| model (2 mm modes) | A CPW | B' all | B' CPW | B' slot |
|---|---|---|---|---|
| CPW pair | 0.242 | 0.767 | 0.565 | 0.847 |
| + slot pairs | 0.014 | 0.346 | 0.577 | 0.129 |
| + A vs B | 0.015 | 0.246 | 0.347 | 0.179 |
| + strips vs bottom (all six) | 0.015 | 0.117 | **0.143** | 0.101 |
1.2 mm modes: 0.168 on B' CPW. Free extra wave on top: 0.103, flat in n. B' CPW remainder along z:
0.13-0.18 at 0.5-3.5 mm, 0.04 at 4.5 and 6.5 mm, 0.30 at 7.5 mm (1.2 mm modes: 0.40). Spurious slot field
on A unchanged (0.083 of A's CPW pattern; data 0.004), so it is not caused by the slot split of the cell.
