"""Check of the coupled-electrode twin (mzm_interconnect/coupled_line.py):
 1. S-matrix vs the hybrid model already compared with CST (modal_vs_s4p_v3.xtalk)
 2. full block (S, light-integrated voltages, far-end voltages) vs a brute-force
    solution of the coupled telegrapher equations
 3. writes the even/odd tables and prints the 14 mm electrical and EO crosstalk."""
import sys, os; sys.path.insert(0, os.path.abspath("../../.."))
import numpy as np
from mzm_interconnect.coupled_line import (coupled_sparams, hybrid_mode_tables, brute_force,
                                           write_mode_tables, coupled_sparams_from_tables)
from modal_vs_s4p_v3 import xtalk, fR, gR, ZR, fb, dbeta_over_f, db
NG = 2.27                                    # optical group index used in the single-line block
f = fR[1:]                                   # 3-D grid, 0 excluded
db_ = np.interp(f, fb, dbeta_over_f) * f
worst = lambda a, b: np.max(np.abs(a - b))
for dz in (0.0030, 0.0045):
    ev, od = hybrid_mode_tables(f, gR[1:], ZR[1:], db_, dz)
    for L in (1e-3, 5e-3, 14e-3):
        B = coupled_sparams(f, ev, od, L, ng=NG)
        nx, fx = xtalk(f, L, dz)
        print(f"dz={dz:.4f} L={L*1e3:4.0f} mm  |NEXT-v3| {worst(B['S'][2][0], nx):.1e}  |FEXT-v3| {worst(B['S'][3][0], fx):.1e}")
# brute force on a few frequencies, 14 mm, both drive ends of A
dz, L = 0.0045, 14e-3
idx = [np.argmin(abs(f - g*1e9)) for g in (1, 10, 30, 60)]
ev, od = hybrid_mode_tables(f, gR[1:], ZR[1:], db_, dz)
sub = lambda m: tuple(np.asarray(x)[idx] for x in m)
B = coupled_sparams(f[idx], sub(ev), sub(od), L, ng=NG)
for j in (0, 1):
    R = brute_force(f[idx], sub(ev), sub(od), L, NG, nz=20001, drive=j)
    eS = max(worst(B["S"][i][j], R["S"][:, i]) for i in range(4))
    eT = max(worst(B["T"][k][j], R["T"][:, k]) / np.max(abs(R["T"][:, k])) for k in range(2))
    eF = max(worst(B["FE"][k][j], R["FE"][:, k]) for k in range(2))
    print(f"brute force, drive {['A1','A2'][j]}:  S {eS:.1e}   modulation (rel.) {eT:.1e}   far end {eF:.1e}")
# tables + 14 mm results
for dz in (0.0030, 0.0045):
    ev, od = hybrid_mode_tables(f, gR[1:], ZR[1:], db_, dz)
    pe, po = write_mode_tables(f"coupled_tables/xtalk200_dz{dz*1e4:.0f}", f, ev, od,
        notes=["200 um pitch: 3-D cascade line + 2-D even/odd split", f"Ze/Zo-1 = {dz}"])
    B = coupled_sparams_from_tables(pe, po, 14e-3, ng=NG)
    for g in (10, 30, 60):
        q = np.argmin(abs(B["f_Hz"] - g*1e9))
        print(f"dz={dz:.4f} 14 mm {g:2d} GHz  NEXT {db(B['S'][2][0][q]):6.1f}  FEXT {db(B['S'][3][0][q]):6.1f} dB"
              f"   EO victim/aggressor {db(B['T'][1][0][q]/B['T'][0][0][q]):6.1f} dB")
