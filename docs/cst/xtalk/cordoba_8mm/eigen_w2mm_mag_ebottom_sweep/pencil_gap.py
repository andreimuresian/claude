"""
Model-free wave content of the TD gap fields (electric-bottom widened CORDOBA, port-1 monitors, 5..60 GHz):
multi-snapshot matrix pencil. No eigenmode input.

A Bloch wave u(zc) exp(-gamma z) sampled once per cell (period 0.18 mm) at a fixed cell position zc is a pure
geometric sequence with ratio p = exp(-gamma*0.18 mm), whatever u is. Each of the 36 cell positions (stem
positions excluded: 25 kept) is one snapshot; all snapshots share the poles p. beta*0.18 mm stays below pi
for |n| < 4.4 at 60 GHz, so no aliasing. Forward waves (exp(-j beta z)) have n > 0, backward n < 0.

Data sets: B's CPW pattern (E+ - E-)/2, B's slot pattern, A's CPW pattern; windows: full line 0-8 mm,
0.31-4.0 mm, 4.0-7.69 mm. Model order: singular values above REL * largest (REL = 1e-2 by default),
capped at 12. Amplitudes by least squares with the poles fixed; reported energy share of each wave over the
window and the reconstruction residual.
"""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sweepfit as S

LAMC = 0.18e-3; DZ = 5e-6; REL = float(os.environ.get("REL", "1e-2")); MMAX = 12


def snapshots(v, z, z0, z1):
    """v: complex samples on z (5 um grid). Returns list of sequences, one per kept cell position, and k-grid."""
    out = []
    for j in range(36):
        if 13 <= j <= 23:
            continue                                     # T-stem positions
        zj = 0.04e-3 + j * DZ
        k0 = int(np.ceil((z0 - zj) / LAMC - 1e-9)); k1 = int(np.floor((z1 - zj) / LAMC + 1e-9))
        zs = zj + LAMC * np.arange(k0, k1 + 1)
        idx = np.round((zs - z[0]) / DZ).astype(int)
        ok = (idx >= 0) & (idx < len(z))
        out.append((v[idx[ok]], zs[ok]))
    n = min(len(s[0]) for s in out)
    return [(s[0][:n], s[1][:n]) for s in out]


def pencil(snaps, M=None):
    N = len(snaps[0][0]); L = N // 2
    H = np.vstack([np.array([x[i:i + L + 1] for i in range(N - L)]) for x, _ in snaps])
    U, s, Vh = np.linalg.svd(H, full_matrices=False)
    if M is None:
        M = int(min(MMAX, np.sum(s > REL * s[0])))
    V = Vh[:M].T                                         # row space: [1, p, p^2, ...]
    p = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    return p, s / s[0], M


def amplitudes(snaps, p):
    N = len(snaps[0][0]); k = np.arange(N)
    E = p[None, :] ** k[:, None]
    C = []; res_num = res_den = 0.0
    for x, zs in snaps:
        c, *_ = np.linalg.lstsq(E, x, rcond=None); C.append(c)
        res_num += np.linalg.norm(x - E @ c) ** 2; res_den += np.linalg.norm(x) ** 2
    C = np.array(C)
    energy = np.sum(abs(C) ** 2, 0) * np.sum(abs(E) ** 2, 0)
    return energy / energy.sum(), np.sqrt(res_num / res_den)


def describe(p, f):
    g = -np.log(p) / LAMC                                # alpha + j beta
    n = g.imag * S.C0 / (2 * np.pi * f * 1e9)
    a_db = g.real * 8.686e-3                             # dB/mm (positive: decays toward +z)
    return n, a_db


def expected(f):
    return {k: float(D.n_of(f)) for k, D in S.DISP.items()}


if __name__ == "__main__":
    wins = {"full 0-8": (0.0, 8e-3), "0.31-4.0": (0.31e-3, 4.0e-3), "4.0-7.69": (4.0e-3, 7.69e-3)}
    for f in S.FTD:
        td = S.TDData(f); z = td.z_full
        ex = expected(f)
        print(f"\n===== {f} GHz =====  eigen n: CPW {ex['e_cpw']:.3f}, slot {ex['e_slot']:.3f}/{ex['o_slot']:.3f},"
              f" strips-bottom {ex['e_sb']:.3f}, A vs B {ex['o_AvsB']:.3f}")
        sets = {"B CPW": S.cpw(td.Bp_full), "B slot": S.slot(td.Bp_full), "A CPW": S.cpw(td.A_full)}
        for sn, v in sets.items():
            for wn, (z0, z1) in wins.items():
                if sn == "A CPW" and wn != "full 0-8":
                    continue
                sn_ = snapshots(v, z, z0, z1); p, sv, M = pencil(sn_)
                share, res = amplitudes(sn_, p); n, a = describe(p, f)
                o = np.argsort(-share)
                waves = "  ".join(f"[n {n[i]:+.2f}, {a[i]:+.2f} dB/mm, {share[i]*100:4.1f}%]" for i in o if share[i] > 0.01)
                print(f"  {sn:6s} {wn:9s} N {len(sn_[0][0])} M {M:2d} resid {res:.3f} | {waves}")
