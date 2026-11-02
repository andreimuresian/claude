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

Odd run (XZ electric), same model and mesh, 15-60 GHz, 4 found:

| mode | f (GHz) | n | Q | file |
|---|---|---|---|---|
| 1 A vs B | 23.2683 | 2.9824 | 9.48 | eig_odd_mode1_AvsB.txt |
| 2 slot | 28.8767 | 2.4032 | 33.86 | eig_odd_mode2_slot.txt |
| 3 CPW | 31.0365 | 2.2360 | 26.27 | eig_odd_mode3_cpw.txt |
| 4 substrate (TM0) wave between the cell walls | 56.7381 | 1.2231 | 9.99 | eig_odd_mode4_unknown.txt |

Open bottom: A vs B 3.096 (Q 4.6), slot odd 2.4040, CPW split 3.4e-5; electric bottom: CPW split 2.5e-5.
A vs B: 78 % of the energy in the Si, gap pattern slot-dominated (CPW/slot 0.23).

Mode 4: 92 % of the energy in the Si (74 % deeper than 100 um), 41 % between the lines, 36 % beyond the outer
ground; gap pattern slot (CPW/slot 0.04). It is the grounded-slab TM0 surface wave of the Si on the bottom
conductor (n 2.50 at 56.7 GHz for 525 um Si), travelling obliquely with a quarter wave across the 0.6 mm
between the electric symmetry plane and the magnetic Ymax: sqrt(2.50^2 - (pi/(2*0.6 mm)/k0)^2) = 1.19
(eigen: 1.22). Its index along z is set by the cell width: in the wide chip the same TM0 wave exists at
every angle. TM0 index: 1.12 at 30 GHz, 1.91 at 45, 2.50 at 56.7, 2.61 at 60 GHz (crosses the CPW index,
2.24, near 50 GHz).
