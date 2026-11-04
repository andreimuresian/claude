"""
Multimode line with end scattering, fitted to the six-mode amplitudes at the 12 monitor frequencies (-44.5 dB run).

Field on the line: sum over the six modes m of a_m+ u_m exp(-gamma_m z) + a_m- u_m exp(-gamma_m (L - z)),
gamma_m(f) from the eigen dispersion (sweepfit.DISP). With P = diag(exp(-gamma_m L)):
    a- = R P a+          (far end: waves arriving at z = L are scattered back)
    a+ = s + R P a-      (near end: source plus scattering of waves arriving at z = 0)
=>  a+ = (I - R P R P)^-1 s.
Assumptions (with reasons): both ends identical (same ports, same 50 ohm, model symmetric under z -> L - z), so one R;
the pair is mirror-symmetric (A <-> B) and so are the ends, so R does not mix even and odd modes:
R = blockdiag(R_e (e_cpw, e_slot, e_sb), R_o (o_cpw, o_slot, o_AvsB)); s = (s_e, s_o). R and s are polynomials in f
of order K (slow end physics); the fast phases are all in P.
Amplitudes are normalised by A's forward CPW amplitude at each f. Equations are written in A/B combinations
((e+o)/2, (e-o)/2) for the CPW and slot pairs and weighted by the typical size of each combination, so B's tiny
differences are not swamped by A.
Outputs: fit residuals, leave-one-out EO at the interior monitors, dense EO prediction (endmodel_eo.png).
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ["TDDIR"] = HERE
exec(open(os.path.join(HERE, "smoothness.py")).read().split("C = {f: coeffs")[0])

def data_X(f, td):
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(S.cpw(td.Bp) * w) / np.mean(S.cpw(td.A) * w)


ME = ["e_cpw", "e_slot", "e_sb"]; MO = ["o_cpw", "o_slot", "o_AvsB"]; MODES = ME + MO
K = int(os.environ.get("K", "1")); F0 = 30.0


def gam(f):
    return np.array([gamma(m, f) for m in MODES])


def amps(f):
    x = fits[f]["x"]; aA = 0.5 * (x["e_cpw+"] + x["o_cpw+"])
    ap = np.array([x[m + "+"] for m in MODES]) / aA; am = np.array([x[m + "-"] for m in MODES]) / aA
    return ap, am


AMP = {f: amps(f) for f in F}
# unknowns: for each block b in (e, o): R_b (3x3) and s_b (3), each times (K+1) polynomial coefficients
NB = 9 + 3; NU = 2 * NB * (K + 1)
def uidx(block, kind, i, j, k):
    base = (0 if block == 0 else NB) * (K + 1)
    off = (i * 3 + j) if kind == "R" else 9 + i
    return base + off * (K + 1) + k

# combination of mode rows (6) into A/B rows: pairs (0,3) cpw, (1,4) slot; sb (2) and AvsB (5) alone
COMB = [("A cpw", {0: .5, 3: .5}), ("B cpw", {0: .5, 3: -.5}), ("A slot", {1: .5, 4: .5}), ("B slot", {1: .5, 4: -.5}),
        ("sb", {2: 1.0}), ("AvsB", {5: 1.0})]


def rows_at(f):
    """Linear equations at f: for each mode row r (0..5) of E1 (a- - R P a+ = 0) and E2 (a+ - R P a- - s = 0),
    the coefficient row in the unknowns and the right-hand side."""
    ap, am = AMP[f]; P = np.exp(-gam(f) * S.L); t = (f - F0) / 30.0
    out = {}
    for eq, (lhs, src) in {"E1": (am, ap), "E2": (ap, am)}.items():
        for r in range(6):
            b = 0 if r < 3 else 1; i = r % 3; row = np.zeros(NU, complex)
            for j in range(3):
                c = (b * 3 + j); val = P[c] * src[c]
                for k in range(K + 1):
                    row[uidx(b, "R", i, j, k)] -= val * t ** k
            if eq == "E2":
                for k in range(K + 1):
                    row[uidx(b, "s", i, 0, k)] -= t ** k
            out[(eq, r)] = (row, -lhs[r])          # row . theta = rhs  <=>  lhs + row.theta = 0
    return out


def scale_of(name, eq):
    v = []
    for f in F:
        ap, am = AMP[f]; vec = am if eq == "E1" else ap
        v.append(abs(sum(w * vec[r] for r, w in dict(COMB)[name].items())))
    return np.median(v)


SC = {(n, eq): scale_of(n, eq) for n, _ in COMB for eq in ("E1", "E2")}


def solve(freqs):
    M, d = [], []
    for f in freqs:
        R = rows_at(f)
        for eq in ("E1", "E2"):
            for n, wts in COMB:
                row = sum(w * R[(eq, r)][0] for r, w in wts.items()); rhs = sum(w * R[(eq, r)][1] for r, w in wts.items())
                M.append(row / SC[(n, eq)]); d.append(rhs / SC[(n, eq)])
    th, *_ = np.linalg.lstsq(np.array(M), np.array(d), rcond=None)
    return th


def RS(th, f):
    t = (f - F0) / 30.0; R = np.zeros((6, 6), complex); s = np.zeros(6, complex)
    for b in (0, 1):
        for i in range(3):
            for j in range(3):
                R[b * 3 + i, b * 3 + j] = sum(th[uidx(b, "R", i, j, k)] * t ** k for k in range(K + 1))
            s[b * 3 + i] = sum(th[uidx(b, "s", i, 0, k)] * t ** k for k in range(K + 1))
    return R, s


def predict(th, f):
    R, s = RS(th, f); P = np.diag(np.exp(-gam(f) * S.L))
    ap = np.linalg.solve(np.eye(6) - R @ P @ R @ P, s); am = R @ P @ ap
    return ap, am


def eo_from(ap, am, f, td):
    x = {m + "+": ap[i] for i, m in enumerate(MODES)}; x.update({m + "-": am[i] for i, m in enumerate(MODES)})
    ce, le, _ = S.basis(E, f, td); co, lo, _ = S.basis(O, f, td)
    v = np.array([x[k] for k in le + lo])
    colsA = [0.5 * c for c in ce] + [0.5 * c for c in co]; colsB = [0.5 * c for c in ce] + [-0.5 * c for c in co]
    mA = np.array([S.cpw(c) for c in colsA]).T @ v; mB = np.array([S.cpw(c) for c in colsB]).T @ v
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(mB * w) / np.mean(mA * w), mB


if __name__ == "__main__":
    Xd = np.array([data_X(f, TD[f]) for f in F])
    th = solve(F)
    print(f"K = {K} (polynomial order of R and s in f), unknowns {NU}, equations {len(F) * 24}")
    print(" f  | B CPW field: end-model vs data | EO end-model / data (dB, deg) | amplitude mismatch per combination (rel.)")
    for i, f in enumerate(F):
        ap, am = predict(th, f); X, mB = eo_from(ap, am, f, TD[f]); d = S.cpw(TD[f].Bp)
        aA = 0.5 * (fits[f]["x"]["e_cpw+"] + fits[f]["x"]["o_cpw+"])
        rb = np.linalg.norm(d - mB * aA) / np.linalg.norm(d)
        ap0, am0 = AMP[f]
        mis = []
        for n, wts in COMB:
            for vec, vec0 in ((ap, ap0), (am, am0)):
                v = sum(w * vec[r] for r, w in wts.items()); v0 = sum(w * vec0[r] for r, w in wts.items())
                mis.append(abs(v - v0) / max(abs(v0), 1e-12))
        print(f"{f:3.0f} | {rb:6.3f} | {20*np.log10(abs(X/Xd[i])):+6.2f} {np.degrees(np.angle(X/Xd[i])):+6.1f} | "
              + " ".join(f"{m:5.2f}" for m in mis))
    print("  (mismatch columns: A cpw +/-, B cpw +/-, A slot +/-, B slot +/-, sb +/-, AvsB +/-)")
    print("\nLeave-one-out (interior monitors): EO error |dX|/|X| and dB")
    lo = []
    for i in range(1, len(F) - 1):
        thi = solve(np.delete(F, i)); ap, am = predict(thi, F[i]); X, _ = eo_from(ap, am, F[i], TD[F[i]])
        e = abs(X - Xd[i]) / abs(Xd[i]); lo.append(e)
        print(f"  {F[i]:3.0f} GHz  {e:5.2f}  {20*np.log10(abs(X/Xd[i])):+6.2f} dB")
    print(f"  median {np.median(lo):.2f}  (coefficient interpolation 0.77, direct spline of X 0.80)")
    # dense prediction on the fitted samples of the nearest monitor geometry (same z sampling)
    fd = np.arange(5, 60.01, 0.25); Xp = []
    for f in fd:
        ap, am = predict(th, f); X, _ = eo_from(ap, am, f, TD[F[np.argmin(abs(F - f))]]); Xp.append(X)
    Xp = np.array(Xp)
    np.savetxt(os.path.join(HERE, f"endmodel_eo_K{K}.csv"), np.c_[fd, Xp.real, Xp.imag], delimiter=",",
               header="f_GHz,ReX,ImX  (EO B/A on the fitted interior samples, end model)")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(fd, 20 * np.log10(abs(Xp)), "-", color="#2a78d6", lw=1.5, label=f"end model (R, s order {K} in f)")
    ax.plot(F, 20 * np.log10(abs(Xd)), "o", color="#eb6834", ms=7, mec="white", mew=1.5, label="TD fields (-44.5 dB run)")
    ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk B/A, interior samples (dB)")
    ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, f"endmodel_eo_K{K}.png"), dpi=150)
