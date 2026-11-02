# Eigenmode cell, 1.2 mm (Ymax magnetic, 221 um beyond the outer ground), electric Si bottom (Si 525 um)
Even run (XZ magnetic), 15 deg, General (Lossy), losses on, 8 modes requested in 15-60 GHz, 3 found:

| mode | f (GHz) | n = 69.396/f | Q | file |
|---|---|---|---|---|
| 1 strips vs bottom (new) | 21.7364 | 3.1926 | 172.8 | eig_even_mode1_stripsvsbottom.txt |
| 2 slot | 28.6810 | 2.4196 | 29.86 | eig_even_mode2_slot.txt |
| 3 CPW | 31.0361 | 2.2360 | 26.27 | eig_even_mode3_cpw.txt |

Open bottom, same cell: slot 2.4209 (Q 29.1), CPW 2.2364 (Q 26.3). `*_xsec.txt`: cell-centre cross-section
(x -0.527..0.103, y 0..0.6, z 0.09, step 0.005). `summarize.py` -> `summarize.log`: energy shares and gap
patterns. Mode 1: 90 % of the energy in the Si (62 % deeper than 100 um), 40 % under the line, 31 % between
the lines, 27 % beyond the outer ground (so the 221 um wall may still shift it); gap pattern CPW-like
(CPW/slot 6.2) but weak per unit energy (4.2e-3 vs 0.30 for the CPW mode, -37 dB).
