"""Matrix pencil of line B's gap field (wide run) at every monitor frequency: one sample per 180 um cell
at each non-stem cell position (channels), both gap columns, interior 0.31-7.69 mm. Lists the waves
(index n, sign = direction, loss, relative amplitude) to follow the |n| ~ 2.5 wave in frequency."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np
from mzm_interconnect.xtalk_fields import load_field_dir
C0 = 2.99792458e8
fd = load_field_dir(os.path.dirname(os.path.abspath(__file__))); z = fd["z"] * 1e3
sel = (z >= 0.31 - 1e-9) & (z <= 7.69 + 1e-9); zz = z[sel]
idx = np.round(((zz - 0.04) % 0.18) / 0.005).astype(int) % 36
keep = ~((idx >= 13) & (idx <= 23))
for f in fd["f_GHz"]:
    k0 = 2 * np.pi * f * 1e9 / C0
    ep, em = (v[sel] for v in fd["ports"][f][1]["B"])
    ch = []
    for col in (ep, em):
        for p in sorted(set(idx[keep])):
            ch.append(col[idx == p][:40])
    X = np.array(ch); X = X / abs(X).max(); N = X.shape[1]; Lp = N // 2
    H = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
    _, S, Vh = np.linalg.svd(H, full_matrices=False)
    M = 6
    V = Vh[:M].T; q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(N)[:, None]; A, *_ = np.linalg.lstsq(Z, X.T, rcond=None)
    err = np.linalg.norm(Z @ A - X.T) / np.linalg.norm(X)
    g = -np.log(q) / 0.18e-3; n = g.imag / k0; a = g.real * 8.686 / 100
    am = np.sqrt(np.sum(abs(A) ** 2, axis=1)); o = np.argsort(-am); am = am / am[o[0]]
    print(f"{f:4.0f} GHz resid {err:.2f}: " + "; ".join(f"{n[i]:+.3f} ({a[i]:5.1f} dB/cm, {am[i]:.2f})" for i in o if am[i] > 0.05))
