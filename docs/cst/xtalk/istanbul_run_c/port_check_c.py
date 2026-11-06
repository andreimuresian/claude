"""Run (c): which of touchstone ports 2/3/4 is which? History: 1 = A near pad, 2 = A far (z 9.05), 3 = B near pad, 4 = B far.
Check at the far end (last field point z = 9.05 = far port plane): V_B/V_A there should match S41/S21 (not S31/S21)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "../istanbul_run_a"))
import numpy as np, skrf as rf
from load_fields import load
fd = load(base=HERE, a_zip="e-field (f=1) [1]_lineA.zip", drop="first", skip_f=(2.0, 15.0)); f = fd["f_GHz"]
n = rf.Network(os.path.join(HERE, "v0_istanbul_rf_lineLaunch.s4p")); fs = n.f / 1e9
S = lambda i: np.interp(f, fs, n.s[:, i, 0].real) + 1j * np.interp(f, fs, n.s[:, i, 0].imag)
V = lambda k, i: np.array([(fd["ports"][x][1][k][0][i] - fd["ports"][x][1][k][1][i]) / 2 for x in f])
Vf = V("B", -1) / V("A", -1)
cc = lambda x, y: abs(np.vdot(x, y)) / np.linalg.norm(x) / np.linalg.norm(y)
for lab, s in (("4 = B far", S(3) / S(1)), ("3 = B far", S(2) / S(1))):
    print(f"{lab}: complex correlation {cc(Vf, s):.3f}, median |field/S| {np.median(abs(Vf / s)):.2f}")
dB = lambda x: 20 * np.log10(abs(x))
for lab, s in (("4 = B far", S(3) / S(1)), ("3 = B far", S(2) / S(1))):
    print(f"{lab}: corr of dB magnitudes {np.corrcoef(dB(Vf), dB(s))[0,1]:.2f}, median dB offset {np.median(dB(Vf)-dB(s)):+.1f}")
for i in (-1, -2, -3):
    Vi = V("B", i) / V("A", i); print(f"field point {i}: corr dB with S41/S21 {np.corrcoef(dB(Vi), dB(S(3)/S(1)))[0,1]:.2f}, complex {cc(Vi, S(3)/S(1)):.2f}")
