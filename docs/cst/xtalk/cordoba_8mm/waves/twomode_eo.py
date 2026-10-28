"""
How much of the victim field (and of the EO crosstalk) does the CPW two-mode model carry?
Port-1 fields with 50 ohm ports = the device case with 50 ohm source and load (no re-termination).
Push-pull reads the CPW pattern c = (Ey+ - Ey-)/2 of each line (V+ + V- = 2c).
Model on B (A's coordinates, B' = mirror of B): CPW pair modes, forward and backward,
|dbeta| L << 1:  B'_c = a q^k + b k q^k + c q^-k + d k q^-k per Bloch channel (cell position),
q = A's forward per-cell factor. Interior z = 0.31-7.69 mm (port regions excluded from both).
X = H[B_c] / H[A_c], H[v] = int v exp(j beta_o z) dz, beta_o = k0 n_g (n_g 2.27).
"""
import numpy as np
from sector_pencil import fd, channels, pencil, n_alpha, STEP, C0, LAM, DZ
from split_slope import fit
NG = 2.27
z0, nc = 0.31, 41
i0 = int(round(z0 / DZ)); N = STEP * nc
zz = (i0 + np.arange(N)) * DZ * 1e-3
def unchan(X):                       # channels (p, k) -> samples i0 + p + STEP k
    out = np.empty(N, complex)
    for p in range(STEP):
        out[p::STEP] = X[p]
    return out
print(" f  | resid B_c two-mode | X fields (int.) | X two-mode | X fwd-only | diff dB")
for f in fd["f_GHz"]:
    F = fd["ports"][f][1]
    Ac = (F["A"][0] - F["A"][1]) / 2
    Bp = (-F["B"][1], -F["B"][0]); Bc = (Bp[0] - Bp[1]) / 2
    XA = channels(Ac, z0, nc); XB = channels(Bc, z0, nc); k = np.arange(nc)
    q, Am, _ = pencil(XA / np.abs(XA).max(), 4)
    n, a = n_alpha(q, f)
    qf = q[np.argmax(np.where(n > 0, np.abs(Am).mean(axis=1), 0))]
    cB, rB = fit(XB, qf, 1.16, False, k)
    cols = np.array([qf ** k, k * qf ** k, qf ** -k, k * qf ** -k])
    Bm = unchan((cB.T @ cols)); Bf = unchan((cB[:2].T @ cols[:2]))
    bo = 2 * np.pi * f * 1e9 * NG / C0
    H = lambda v: np.trapezoid(v * np.exp(1j * bo * zz), zz)
    a_ = H(Ac[i0:i0 + N]); xf = H(Bc[i0:i0 + N]) / a_; xm = H(Bm) / a_; xw = H(Bf) / a_
    d = lambda x: 20 * np.log10(abs(x))
    print(f"{f:4.0f}| {rB:.2f}               | {d(xf):6.1f}          | {d(xm):6.1f}     | {d(xw):6.1f}     | {d(xm)-d(xf):+5.1f}")
