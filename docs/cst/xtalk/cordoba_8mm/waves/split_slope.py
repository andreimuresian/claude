"""
Pair split from the linear growth of the victim's forward CPW field.
Sector modes on line A's coordinates: S+ = A + B' (pair-even), S- = A - B' (pair-odd),
B' = B mirrored onto A (same CPW pattern sign). With dbeta = beta_e - beta_o and
|dbeta| L << 1 (here k0 dn L ~ 1e-3 rad), B'_c = (A/2)(-j dbeta z) e^{-gamma z} + (launch term)
+ backward terms. Fit per Bloch channel (36 cell positions, 41 cells):
  B'_c(k) = a q^k + b k q^k + c q^-k + d k q^-k [+ artefact poles q e^{+-j kappa k}]
q = forward per-cell factor of A (pencil), A's forward amplitude from the same basis.
dn = Re(2j b / (A_fwd Lambda)) / k0. Robustness: windows, basis variants.
"""
import numpy as np
from sector_pencil import fd, channels, pencil, n_alpha, STEP, C0, LAM, DZ
import sys
s4p = {}
try:
    import os; sys.path.insert(0, os.path.abspath("../../../../.."))
    from mzm_interconnect import xtalk_s4p as X
    pr = X.load_pair("../LINEA_8MM_625UM_PITCH_CORDOBA.s4p", 8.0)
    for g in fd["f_GHz"]:
        i = np.argmin(abs(pr["f_Hz"] - g * 1e9)); s4p[g] = pr["even"]["table"][1][i] - pr["odd"]["table"][1][i]
except Exception as e:
    print("s4p not loaded", e)

def fit(Xc, q, kappa, extra, k):
    cols = [q ** k, k * q ** k, q ** -k, k * q ** -k]
    if extra:
        cols += [(q * np.exp(1j * kappa)) ** k, (q * np.exp(-1j * kappa)) ** k]
    Bm = np.array(cols).T
    coef, *_ = np.linalg.lstsq(Bm, Xc.T, rcond=None)
    res = np.linalg.norm(Bm @ coef - Xc.T) / np.linalg.norm(Xc)
    return coef, res

print(" f   | n_A(fwd)  | dn from slope: full, 1st 2/3, last 2/3, no-artefact-poles | resid B | dn s4p eq.line | |launch|/|growth over L|")
for f in fd["f_GHz"]:
    F = fd["ports"][f][1]
    Ac = (F["A"][0] - F["A"][1]) / 2
    Bp = (-F["B"][1], -F["B"][0]); Bc = (Bp[0] - Bp[1]) / 2
    k0 = 2 * np.pi * f * 1e9 / C0
    out = []
    for (z0, nc) in ((0.31, 41), (0.31, 27), (2.83, 27)):
        XA = channels(Ac, z0, nc); XB = channels(Bc, z0, nc); k = np.arange(nc)
        q, Am, _ = pencil(XA / np.abs(XA).max(), 4)
        n, a = n_alpha(q, f)
        qf = q[np.argmax(np.where(n > 0, np.abs(Am).mean(axis=1), 0))]
        # artefact kappa: pole nearest qf * e^{j 1.16}
        kap = 1.16
        for extra in ((True, False) if (z0, nc) == (0.31, 41) else (True,)):
            cA, _ = fit(XA, qf, kap, extra, k)
            cB, rB = fit(XB, qf, kap, extra, k)
            Af = cA[0]; b = cB[1]
            dbeta = 2j * np.sum(b * np.conj(Af)) / np.sum(abs(Af) ** 2) / (LAM * 1e-3)
            launch = np.sqrt(np.mean(abs(cB[0]) ** 2)); grow = np.sqrt(np.mean(abs(cB[1]) ** 2)) * nc
            out.append((dbeta.real / k0, rB, launch / grow))
        if (z0, nc) == (0.31, 41):
            nA = n_alpha(np.array([qf]), f)[0][0]
    dns = [o[0] for o in out]
    print(f"{f:4.0f} | {nA:.4f}   | " + " ".join(f"{d:+.5f}" for d in [dns[0], dns[2], dns[3], dns[1]])
          + f" | {out[0][1]:.2f}    | {s4p.get(f, np.nan):+.5f}       | {out[0][2]:.2f}")
