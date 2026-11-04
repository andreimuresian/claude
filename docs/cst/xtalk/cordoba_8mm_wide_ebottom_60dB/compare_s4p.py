"""S-parameters, -27 dB run vs the run stopped at -44.5 dB: |S| in dB at the monitor frequencies and the change.
Ports (CST): 1 A near, 2 A far, 3 B near, 4 B far -> S21 through, S31 NEXT, S41 FEXT."""
import os, numpy as np, skrf as rf
HERE = os.path.dirname(os.path.abspath(__file__))
old = rf.Network(os.path.join(HERE, "../cordoba_8mm_wide_ebottom/LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port_E-fondo.s4p"))
new = rf.Network(os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port_E-fondo_-minus_60_dB.s4p"))
fs = np.arange(5, 61, 5) * 1e9
def at(n, i, j):
    return np.interp(fs, n.f, n.s[:, i, j].real) + 1j * np.interp(fs, n.f, n.s[:, i, j].imag)
for lab, (i, j) in {"S11": (0, 0), "S21": (1, 0), "S31 NEXT": (2, 0), "S41 FEXT": (3, 0)}.items():
    a, b = at(old, i, j), at(new, i, j)
    print(f"{lab:9s} old " + " ".join(f"{20*np.log10(abs(v)):6.1f}" for v in a))
    print(f"{'':9s} new " + " ".join(f"{20*np.log10(abs(v)):6.1f}" for v in b))
    print(f"{'':9s} |new-old|/|new| " + " ".join(f"{abs(b[k]-a[k])/abs(b[k]):.2f}" for k in range(len(fs))))
