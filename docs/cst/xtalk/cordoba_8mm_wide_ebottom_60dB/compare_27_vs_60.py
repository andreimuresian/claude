"""-27 dB vs -60 dB-target run (stopped at about -44.5 dB energy) of the widened electric-bottom CORDOBA:
change of each gap pattern (A CPW, A slot, B CPW, B slot) per monitor frequency, and the EO crosstalk
(50/50 ohm, push-pull, n_g 2.27) of both runs."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np
from mzm_interconnect import parameters as P, xtalk_fields as XF
OLD = os.path.join(HERE, "../cordoba_8mm_wide_ebottom")
o, n = XF.load_field_dir(OLD), XF.load_field_dir(HERE)
cpw = lambda v: (v[0] - v[1]) / 2; slot = lambda v: (v[0] + v[1]) / 2
rms = lambda v: np.sqrt(np.mean(abs(v) ** 2))
def pats(fd, f):
    F = fd["ports"][f][1]; A = np.stack(F["A"]); Bp = np.stack([-F["B"][1], -F["B"][0]])
    return {"A CPW": cpw(A), "A slot": slot(A), "B CPW": cpw(Bp), "B slot": slot(Bp)}
print(" f  | rel. change |new-old|/|new|: A CPW  A slot  B CPW  B slot | level re A CPW (new, dB): A slot B CPW B slot")
for f in o["f_GHz"]:
    po, pn = pats(o, f), pats(n, f)
    ch = {k: np.linalg.norm(pn[k] - po[k]) / np.linalg.norm(pn[k]) for k in pn}
    lv = {k: 20 * np.log10(rms(pn[k]) / rms(pn["A CPW"])) for k in pn}
    print(f"{f:3.0f} | {ch['A CPW']:.4f}  {ch['A slot']:.3f}  {ch['B CPW']:.3f}  {ch['B slot']:.3f} |"
          f" {lv['A slot']:6.1f} {lv['B CPW']:6.1f} {lv['B slot']:6.1f}")
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
Xo = XF.eo_crosstalk_fields(p, o)["X"]; Xn = XF.eo_crosstalk_fields(p, n)["X"]
print("\nEO crosstalk (dB)   f: " + " ".join(f"{f:6.0f}" for f in o["f_GHz"]))
print("  -27 dB run        : " + " ".join(f"{20*np.log10(abs(x)):6.1f}" for x in Xo))
print("  new run (-44.5 dB): " + " ".join(f"{20*np.log10(abs(x)):6.1f}" for x in Xn))
print("  difference        : " + " ".join(f"{20*np.log10(abs(b/a)):+6.1f}" for a, b in zip(Xo, Xn)))
