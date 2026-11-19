"""Propagation constant of the parasitic (ground-to-ground) mode, global fit on the L+B+S lines.
gamma_p(f) = k * alpha_c(f) + j n_p w / c   (alpha_c: coplanar attenuation of the line model, lbs_bend_130.py)
Two real constants (k, n_p) fitted to the cell-averaged v_p on line 1 and line 2 at all frequencies where v_p is above
-30 dB of v_c (forward + backward amplitudes solved linearly at each frequency, 0.18 mm cut at the ports).
Outputs: two_mode_gamma_p.npz (k, n_p), printed fit quality."""
import os, sys, io, contextlib, runpy, numpy as np
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../.."))); from mzm_interconnect.physics import fit_alpha_scaled
d = np.load(os.path.join(HERE, "bend_path_130.npz")); F, S, VC, VP, SEG = d["F"], d["S"] * 1e-3, d["VC"], d["VP"], d["SEG"]
b = np.load(os.path.join(HERE, "lbs_bend_130.npz")); ac = fit_alpha_scaled(F, *b["pa"]) * 100 / 8.686; w = 2 * np.pi * F * 1e9
ker = np.ones(36) / 36; cav = lambda x: np.convolve(x, ker, "valid")
def line_data(seg, flip):
    s = S[SEG == seg]; s = (s - s[0]) if not flip else s; o = np.argsort(s); s = s[o]
    ss = cav(s); m = (ss >= ss.min() + 0.18e-3) & (ss <= ss.max() - 0.18e-3)
    return ss[m], np.array([cav(v[SEG == seg][o])[m] for v in VP]), np.array([cav(v[SEG == seg][o])[m] for v in VC])
s1, P1, C1 = line_data(0, True); s2, P2, C2 = line_data(4, False)
strong = np.sqrt((abs(P1) ** 2).mean(1) / (abs(C1) ** 2).mean(1)) > 10 ** (-30 / 20)
def resid(p, ret=False):
    k, n = p; out, rel = [], []
    for i in np.where(strong)[0]:
        g = k * ac[i] + 1j * n * w[i] / C0
        for s, V in ((s1, P1[i]), (s2, P2[i])):
            M = np.stack([np.exp(-g * s), np.exp(g * s)], 1); c = np.linalg.lstsq(M, V, rcond=None)[0]; e = (M @ c - V) / np.linalg.norm(V)
            out.append(np.r_[e.real, e.imag]); rel.append(np.linalg.norm(e))
    return (np.concatenate(out), np.array(rel)) if ret else np.concatenate(out)
best = min((least_squares(resid, [k0, 2.39], bounds=([0, 1.5], [10, 3.5])) for k0 in (0.5, 1, 2, 4)), key=lambda r: r.cost)
k, n = best.x; _, rel = resid(best.x, True)
print(f"parasitic mode: k = {k:.2f} (alpha_p = k alpha_c), n_p = {n:.3f}; {strong.sum()} frequencies; fit residual median {100*np.median(rel):.1f} %, 90th pct {100*np.percentile(rel,90):.1f} %")
for kk in (0.5, 1.0, 2.0):
    print(f"   residual median with k fixed at {kk}: {100*np.median(resid([kk, n], True)[1]):.1f} %")
np.savez(os.path.join(HERE, "two_mode_gamma_p.npz"), k=k, n_p=n)
