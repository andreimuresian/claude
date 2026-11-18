"""Sensitivity of the field-extracted line parameters (L+S run) to the length excluded at each end of the line
(port transition regions). Same two-wave fit as ls_extraction.py, with end cuts of 0 to 0.72 mm."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np
from scipy.optimize import least_squares
from mzm_interconnect.physics import C0
D = os.path.join(HERE, "..", "L+S"); L = 3.24e-3; GAP = 4.45e-6; PITCH = 0.18e-3
def load_gap(fn):
    a = np.loadtxt(os.path.join(D, fn), comments="#", skiprows=2); out = {}
    for f in np.unique(a[:, 0]):
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3]); out[f] = (b[o, 3] * 1e-3, b[o, 6] + 1j * b[o, 7])
    return out
Gp, Gm = load_gap("L1_gap+.txt"), load_gap("L1_gap-.txt"); F = np.array(sorted(Gp)); z = Gp[F[0]][0]
V = np.array([0.5 * GAP * (Gp[f][1] - Gm[f][1]) for f in F]); k = int(round(PITCH / (z[1] - z[0]))); ker = np.ones(k) / k
zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in V])
def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
print("end cut (mm) | n_m at 10 / 30 / 60 GHz | alpha (dB/cm) at 10 / 30 / 60 GHz | max fit residual")
for cut in (0.0, 0.09e-3, 0.18e-3, 0.36e-3, 0.54e-3, 0.72e-3):
    m = (zs >= cut) & (zs <= L - cut); n, a, r = [], [], []
    for q in (10, 30, 60):
        i = np.argmin(abs(F - q)); w = 2 * np.pi * F[i] * 1e9
        res = lambda p: np.concatenate([(e := two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m])[1]).real, e.imag])
        p = least_squares(res, [20.0, 2.23 * w / C0], x_scale=[20, 2.23 * w / C0]).x
        n.append(p[1] * C0 / w); a.append(p[0] * 8.686 / 100)
        r.append(np.linalg.norm(two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m])[1]) / np.linalg.norm(Vs[i][m]))
    print(f"  {cut*1e3:4.2f}       | {n[0]:.4f} / {n[1]:.4f} / {n[2]:.4f} | {a[0]:.3f} / {a[1]:.3f} / {a[2]:.3f} | {100*max(r):.2f} %")
