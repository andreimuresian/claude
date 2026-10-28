"""Istanbul 3 mm: coarse vs refined TD mesh, same model. CPW index (equivalent line, both
sectors), S21 phase index, Z, S11/S21, NEXT/FEXT. Eigenmode CPW pair-even 2.355 at 26.5 GHz."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np
from mzm_interconnect import xtalk_s4p as X
here = os.path.dirname(os.path.abspath(__file__))
d = lambda x: 20 * np.log10(np.abs(x))
runs = {"coarse": "TEST0_XTALK_SW__3p00mm.s4p", "refined": "TEST0_XTALK_SW_3mm - mesh refined.s4p"}
P = {k: X.load_pair(os.path.join(here, v), 3.0) for k, v in runs.items()}
for k, pr in P.items():
    f = pr["f_Hz"]; w = 2 * np.pi * f; s = pr["s"]
    gd = -np.gradient(np.unwrap(np.angle(s[:, 1, 0])), w)
    sel = (f > 5e9) & (f < 50e9)
    print(f"{k}: A/B asym {pr['sym_ab']:.1e}, end asym {pr['sym_end']:.1e}, n_g(5-50 GHz, S21 delay) {np.median(gd[sel])*X.C0/3e-3:.4f}")
print(" f GHz | n_e coarse  refined  change | n_o coarse refined | Z_e coarse refined | S11 c/r | S21 c/r | NEXT c/r | FEXT c/r")
for g in (5, 10, 20, 26.5, 30, 40, 45, 50, 60, 70, 80):
    row = f"{g:6.1f}|"
    i = {k: np.argmin(abs(pr["f_Hz"] - g * 1e9)) for k, pr in P.items()}
    c, r = P["coarse"], P["refined"]
    ec, er = c["even"]["table"][1][i["coarse"]], r["even"]["table"][1][i["refined"]]
    oc, orr = c["odd"]["table"][1][i["coarse"]], r["odd"]["table"][1][i["refined"]]
    sc, sr = c["s"][i["coarse"]], r["s"][i["refined"]]
    row += f" {ec:.4f}  {er:.4f}  {er-ec:+.4f} | {oc:.4f} {orr:.4f} | {c['even']['Z'][i['coarse']].real:5.1f} {r['even']['Z'][i['refined']].real:5.1f} |"
    row += f" {d(sc[0,0]):5.1f} {d(sr[0,0]):5.1f} | {d(sc[1,0]):5.2f} {d(sr[1,0]):5.2f} | {d(sc[2,0]):5.1f} {d(sr[2,0]):5.1f} | {d(sc[3,0]):5.1f} {d(sr[3,0]):5.1f}"
    print(row)
