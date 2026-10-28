"""
CORDOBA 8 mm: wave content of the gap fields, per exact pair sector and per line pattern.

Pair sectors (exact, y-mirror symmetry of the pair): port-1 field F1 and its mirror image
mir(F1) (= the port-3 field). Sector s = +1: F1 + mir(F1) (A and B driven alike), s = -1:
F1 - mir(F1). On line A each sector has two gap fields Ey(+side), Ey(-side).
Line patterns (not exact: the neighbour breaks the line's own mirror symmetry weakly):
CPW c = (Ey+ - Ey-)/2 (opposite directions, V+ = V-), slot s = (Ey+ + Ey-)/2.

Bloch sampling: one sample per 180 um cell at a fixed cell position; all 36 positions are
channels sharing the same q_m = exp(-gamma_m Lambda). Interior z = 0.31-7.69 mm (41 cells).
Hankel SVD -> number of exponentials; matrix pencil -> gamma_m; least squares -> amplitudes.
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../..")))
import numpy as np
from mzm_interconnect.xtalk_fields import load_field_dir
C0 = 2.99792458e8
DZ, LAM = 0.005, 0.18
STEP = int(round(LAM / DZ))
HERE = os.path.dirname(os.path.abspath(__file__))
fd = load_field_dir(os.path.join(HERE, ".."))
z = fd["z"] * 1e3

def sectors(f):
    F = fd["ports"][f][1]
    mir = {"A": (-F["B"][1], -F["B"][0])}
    out = {}
    for s in (+1, -1):
        ep = F["A"][0] + s * mir["A"][0]; em = F["A"][1] + s * mir["A"][1]
        out[s] = dict(c=(ep - em) / 2, s=(ep + em) / 2)
    return out

def channels(sig, z0=0.31, ncell=41, phases=range(STEP)):
    i0 = int(round(z0 / DZ))
    return np.array([sig[i0 + p + STEP * np.arange(ncell)] for p in phases])

def hankel_sv(X, Lp=None):
    N = X.shape[1]; Lp = Lp or N // 2
    Hk = np.vstack([np.array([v[i:i + Lp + 1] for i in range(N - Lp)]) for v in X])
    U, Sv, Vh = np.linalg.svd(Hk, full_matrices=False)
    return Sv / Sv[0], Vh

def pencil(X, M, Lp=None):
    N = X.shape[1]; Lp = Lp or N // 2
    Sv, Vh = hankel_sv(X, Lp)
    V = Vh[:M].T
    q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Zm = q[None, :] ** np.arange(N)[:, None]
    A, *_ = np.linalg.lstsq(Zm, X.T, rcond=None)
    err = np.linalg.norm(Zm @ A - X.T) / np.linalg.norm(X)
    return q, A, err

def n_alpha(q, f):
    g = -np.log(q) / (LAM * 1e-3)                      # gamma = alpha + j beta
    k0 = 2 * np.pi * f * 1e9 / C0
    return g.imag / k0, g.real * 8.686 / 100           # n (sign = direction), dB/cm

if __name__ == "__main__":
    for f in fd["f_GHz"]:
        S = sectors(f)
        print(f"\n===== {f:.0f} GHz   2pi-resolution |dn| ~ lambda0/L = {C0/(f*1e9)/(41*LAM*1e-3):.2f}")
        for s in (+1, -1):
            rc = np.sqrt(np.mean(abs(S[s]["c"]) ** 2)); rs = np.sqrt(np.mean(abs(S[s]["s"]) ** 2))
            X = np.vstack([channels(S[s]["c"]), channels(S[s]["s"])])
            nrm = np.sqrt(np.mean(abs(X) ** 2, axis=1)); Xn = X / nrm.max()
            sv, _ = hankel_sv(Xn)
            print(f" sector {s:+d}: rms slot/CPW = {rs/rc:.3e}   SV: " + " ".join(f"{v:.1e}" for v in sv[:7]))
            for M in (1, 2, 3, 4):
                q, A, err = pencil(Xn, M)
                n, a = n_alpha(q, f)
                amp_c = np.sqrt(np.mean(abs(A[:, :STEP]) ** 2, axis=1)); amp_s = np.sqrt(np.mean(abs(A[:, STEP:]) ** 2, axis=1))
                o = np.argsort(-(amp_c + amp_s))
                print(f"   M={M} resid {err:.1e}: " + "; ".join(f"n {n[i]:+.4f} a {a[i]:5.2f} dB/cm cpw {amp_c[i]:.1e} slot {amp_s[i]:.1e}" for i in o))
