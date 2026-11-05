"""
End-scattering model fitted to the six-mode amplitudes of the dense -40 dB run.
Model (as ../cordoba_8mm_wide_ebottom_60dB/endmodel.py): a- = R P a+, a+ = s + R P a-, P = diag(exp(-gamma_m L)),
one R for both ends (z-symmetric ends), block-diagonal in even/odd (A <-> B symmetry), R and s polynomials of order
K in t = (f - 30 GHz)/10 GHz; amplitudes normalised by A's forward CPW amplitude; equations in A/B combinations
weighted by their typical size.
Pre-registered tests (stated before running), band 20-40 GHz:
  A: fit on 20, 22, ..., 40; predict 21, 23, ..., 39: success if median EO complex error < 0.3;
  B: fit on 20, 24, ..., 40; predict the other 15: success if < 0.3 and < half the spline error from the same points.
EO here = B/A on the fitted interior samples (as in the six-mode fits).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ["TDDIR"] = os.path.join(HERE, "unpacked")
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/eigen_w2mm_mag_ebottom_sweep"))
import numpy as np
from scipy.interpolate import CubicSpline
import sweepfit as S
REF = {fam: S.pattern_raw(D.files[int(np.where(D.ph == 15)[0][0])]) for fam, D in S.DISP.items()}
_orig = S.pattern_at
def pattern_at(fam, f, mode):
    u, src = _orig(fam, f, mode); u = S.align(u, REF[fam]); return u / np.linalg.norm(u), src
S.pattern_at = pattern_at
E = ("e_cpw", "e_slot", "e_sb"); O = ("o_cpw", "o_slot", "o_AvsB"); MODES = list(E + O)
K = int(os.environ.get("K", "1"))
BAND = np.arange(20, 41).astype(float)


def gamma(m, f):
    D = S.DISP[m]; n = float(D.n_of(f)); a = float(D.alpha(f))
    if m.endswith("cpw"):
        nm = 0.5 * (float(S.DISP["e_cpw"].n_of(f)) + float(S.DISP["o_cpw"].n_of(f)))
        n = nm + (0.5 if m.startswith("e") else -0.5) * float(S.split_cpw(f))
    return a + 1j * 2 * np.pi * f * 1e9 * n / S.C0


TD = {f: S.TDData(int(f)) for f in BAND}
AMP, XD = {}, {}
for f in BAND:
    td = TD[f]; x = S.fit(int(f), td)["x"]; aA = 0.5 * (x["e_cpw+"] + x["o_cpw+"])
    AMP[f] = (np.array([x[m + "+"] for m in MODES]) / aA, np.array([x[m + "-"] for m in MODES]) / aA)
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    XD[f] = np.mean(S.cpw(td.Bp) * w) / np.mean(S.cpw(td.A) * w)
COMB = [("A cpw", {0: .5, 3: .5}), ("B cpw", {0: .5, 3: -.5}), ("A slot", {1: .5, 4: .5}), ("B slot", {1: .5, 4: -.5}),
        ("sb", {2: 1.0}), ("AvsB", {5: 1.0})]
NB = 12; NU = 2 * NB * (K + 1)
def ui(b, kind, i, j, k):
    return (b * NB + ((i * 3 + j) if kind == "R" else 9 + i)) * (K + 1) + k


def rows_at(f):
    ap, am = AMP[f]; P = np.exp(-np.array([gamma(m, f) for m in MODES]) * S.L); t = (f - 30.0) / 10.0; out = {}
    for eq, (lhs, src) in {"E1": (am, ap), "E2": (ap, am)}.items():
        for r in range(6):
            b, i = divmod(r, 3); row = np.zeros(NU, complex)
            for j in range(3):
                for k in range(K + 1):
                    row[ui(b, "R", i, j, k)] -= P[b * 3 + j] * src[b * 3 + j] * t ** k
            if eq == "E2":
                for k in range(K + 1):
                    row[ui(b, "s", i, 0, k)] -= t ** k
            out[(eq, r)] = (row, -lhs[r])
    return out


ROWS = {f: rows_at(f) for f in BAND}
SC = {}
for n, wts in COMB:
    for eq in ("E1", "E2"):
        SC[(n, eq)] = np.median([abs(sum(w * (AMP[f][1] if eq == "E1" else AMP[f][0])[r] for r, w in wts.items())) for f in BAND])


def solve(freqs):
    M, d = [], []
    for f in freqs:
        for eq in ("E1", "E2"):
            for n, wts in COMB:
                M.append(sum(w * ROWS[f][(eq, r)][0] for r, w in wts.items()) / SC[(n, eq)])
                d.append(sum(w * ROWS[f][(eq, r)][1] for r, w in wts.items()) / SC[(n, eq)])
    return np.linalg.lstsq(np.array(M), np.array(d), rcond=None)[0]


def predict(th, f):
    t = (f - 30.0) / 10.0; R = np.zeros((6, 6), complex); s = np.zeros(6, complex)
    for b in (0, 1):
        for i in range(3):
            for j in range(3):
                R[b * 3 + i, b * 3 + j] = sum(th[ui(b, "R", i, j, k)] * t ** k for k in range(K + 1))
            s[b * 3 + i] = sum(th[ui(b, "s", i, 0, k)] * t ** k for k in range(K + 1))
    P = np.diag(np.exp(-np.array([gamma(m, f) for m in MODES]) * S.L))
    ap = np.linalg.solve(np.eye(6) - R @ P @ R @ P, s); return ap, R @ P @ ap


def eo(ap, am, f):
    td = TD[f]; x = {m + "+": ap[i] for i, m in enumerate(MODES)}; x.update({m + "-": am[i] for i, m in enumerate(MODES)})
    ce, le, _ = S.basis(E, f, td); co, lo, _ = S.basis(O, f, td); v = np.array([x[k] for k in le + lo])
    mA = np.array([S.cpw(0.5 * c) for c in ce] + [S.cpw(0.5 * c) for c in co]).T @ v
    mB = np.array([S.cpw(0.5 * c) for c in ce] + [S.cpw(-0.5 * c) for c in co]).T @ v
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(mB * w) / np.mean(mA * w), mB


def evaluate(train, label):
    th = solve(train); test = [f for f in BAND if f not in train]
    em = [abs(eo(*predict(th, f), f)[0] - XD[f]) / abs(XD[f]) for f in test]
    sp = CubicSpline(train, [XD[f] for f in train])
    es = [abs(sp(f) - XD[f]) / abs(XD[f]) for f in test]
    print(f"  {label}: model median {np.median(em):.2f} (max {np.max(em):.2f}) | spline median {np.median(es):.2f} (max {np.max(es):.2f})")
    return th, np.median(em), np.median(es)


if __name__ == "__main__":
    print(f"K = {K}: {NU} complex unknowns; band 20-40 GHz")
    th = solve(BAND)
    print(" f  | EO model vs data (dB, deg) | |dX|/|X| | B CPW field vs data")
    for f in BAND:
        X, mB = eo(*predict(th, f), f); d = S.cpw(TD[f].Bp)
        aA = 0.5 * (S.fit(int(f), TD[f])["x"]["e_cpw+"] + S.fit(int(f), TD[f])["x"]["o_cpw+"]) if False else None
        print(f"{f:3.0f} | {20*np.log10(abs(X/XD[f])):+6.2f} {np.degrees(np.angle(X/XD[f])):+6.1f} | {abs(X-XD[f])/abs(XD[f]):.2f}")
    print("Pre-registered tests:")
    _, ma, sa = evaluate(BAND[::2], "A (train every 2 GHz)")
    _, mb, sb = evaluate(BAND[::4], "B (train every 4 GHz)")
    print(f"  A {'PASS' if ma < 0.3 else 'FAIL'};  B {'PASS' if (mb < 0.3 and mb < 0.5 * sb) else 'FAIL'}")
