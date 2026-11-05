"""Which of CST ports 3, 4 is line B's near end (z = 0.3)? Compare the line B / line A gap-voltage ratio at the two
ends of the line with |S31|, |S41| (matched 50 ohm ports: port voltage = incident + reflected wave at the port)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, skrf as rf
from load_fields import load
fd = load(); f = fd["f_GHz"]
n = rf.Network(os.path.join(HERE, "v0_istanbul_rf_line.s4p")); fs = n.f / 1e9
S = lambda i: np.interp(f, fs, n.s[:, i, 0].real) + 1j * np.interp(f, fs, n.s[:, i, 0].imag)
V = lambda k, i: np.array([(fd["ports"][x][1][k][0][i] - fd["ports"][x][1][k][1][i]) / 2 for x in f])
near = abs(V("B", 0) / V("A", 0)); far = abs(V("B", -1) / V("A", -1))
nearS = abs(S(2) / (1 + S(0))) ; farS = abs(S(3) / S(1))   # if port 3 near, 4 far
dB = lambda x: 20 * np.log10(x)
for lab, a, b in (("3 near, 4 far", nearS, farS), ("4 near, 3 far", abs(S(3) / (1 + S(0))), abs(S(2) / S(1)))):
    print(f"{lab}: corr(dB) near {np.corrcoef(dB(near), dB(a))[0,1]:.2f}, far {np.corrcoef(dB(far), dB(b))[0,1]:.2f}; "
          f"median offset field-S (dB) near {np.median(dB(near)-dB(a)):+.1f}, far {np.median(dB(far)-dB(b)):+.1f}")
cc = lambda x, y: abs(np.vdot(x, y)) / np.linalg.norm(x) / np.linalg.norm(y)
Vn = V("B", 0) / V("A", 0); Vf = V("B", -1) / V("A", -1)
for lab, a, b in (("3 near, 4 far", S(2) / (1 + S(0)), S(3) / S(1)), ("4 near, 3 far", S(3) / (1 + S(0)), S(2) / S(1))):
    print(f"{lab}: complex correlation near {cc(Vn, a):.3f}, far {cc(Vf, b):.3f}")
