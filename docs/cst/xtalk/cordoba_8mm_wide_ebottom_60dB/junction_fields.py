"""
B's gap fields and the EO crosstalk predicted from the S-parameter junction model (sparam_endmodel.py, K = 0 fitted on
the S-parameters at the 12 monitor frequencies; parameters in sparam_endmodel_K0_params.npy).

The junction model gives, per even/odd block and unit drive of that block, the modal amplitudes a+ (at z = 0) and
a- (at z = L) of the three modes. Port-1 drive = half even + half odd drive. The field of mode m per unit port wave is
c_m u_m (u_m: eigen gap pattern aligned to the family's 15 deg pattern), with c_m a complex constant per mode (6
unknowns: the port-wave to field scale, assumed frequency independent), and the monitor's overall scale g(f) per
frequency (excitation normalisation; cancels in the EO ratio). Fitted on the 12 monitors by alternating least
squares (line weights, A slot x10, as in the six-mode fits). Index corrections dn from the junction fit are applied.
Outputs: per-monitor B residual and EO vs data; leave-one-out with c refitted on 11 monitors (the junction model
stays the one fitted to the S-parameters at all 12 frequencies: the held-out FIELD data are not used); dense EO.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ["TDDIR"] = HERE
exec(open(os.path.join(HERE, "smoothness.py")).read().split("C = {f: coeffs")[0])
import sparam_endmodel as J

KJ = int(os.environ.get("KJ", "0")); J.K = KJ
J.NPB = (1 + 3 + 6) * (KJ + 1); J.NP = 2 * 2 * J.NPB + 6
pj = np.load(os.path.join(HERE, f"sparam_endmodel_K{KJ}_params.npy"))
MODES = J.BLK["e"] + J.BLK["o"]; DN = dict(zip(MODES, pj[-6:]))
for m, dn in DN.items():
    S.DISP[m].cn = S.DISP[m].cn.copy(); S.DISP[m].cn[0] += dn          # index correction from the junction fit


def junction_amps(f):
    """Modal amplitudes for port-1 drive at frequency f (GHz): dict m -> (a+, a-)."""
    J.fG = np.array([f], float)
    J.GAM0 = {m: np.array([S.DISP[m].alpha(f) - 0j + 1j * 2 * np.pi * f * 1e9 * (S.DISP[m].n_of(f) - DN[m]) / S.C0])
              for m in MODES}
    blocks, dn = J.unpack(pj, np.array([0])); out = {}; i = 0
    for b, modes in J.BLK.items():
        rho, tv, R = blocks[b]
        g = np.array([J.GAM0[m][0] + 1j * 2 * np.pi * f * 1e9 * dn[i + j] / S.C0 for j, m in enumerate(modes)]); i += 3
        P = np.exp(-g * S.L); PR = np.diag(P)
        ap = np.linalg.solve(np.eye(3) - R[0] @ PR @ R[0] @ PR, tv[0]); am = R[0] @ (P * ap)
        for j, m in enumerate(modes):
            out[m] = (0.5 * ap[j], 0.5 * am[j])
    return out


def columns(f, td):
    """Per mode: field columns (A CPW, A slot, B CPW, B slot patterns) of a+ u e^{-gz} + a- u e^{-g(L-z)}."""
    A = junction_amps(f); cols = {}
    ce, le, _ = S.basis(tuple(J.BLK["e"]), f, td, use_split=False); co, lo, _ = S.basis(tuple(J.BLK["o"]), f, td, use_split=False)   # junction indices, incl. its own CPW split
    for sgn, cc, ll in ((1, ce, le), (-1, co, lo)):
        for k in range(0, len(ll), 2):
            m = ll[k][:-1]; ap, am = A[m]
            fld = ap * cc[k] + am * cc[k + 1]
            cols[m] = {"A CPW": S.cpw(0.5 * fld), "A slot": S.slot(0.5 * fld),
                       "B CPW": S.cpw(0.5 * sgn * fld), "B slot": S.slot(0.5 * sgn * fld)}
    return cols


def data_X(f, td):
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(S.cpw(td.Bp) * w) / np.mean(S.cpw(td.A) * w)


PAT = ("A CPW", "A slot", "B CPW", "B slot")
COLS = {f: columns(f, TD[f]) for f in F}
DATA = {f: {"A CPW": S.cpw(TD[f].A), "A slot": S.slot(TD[f].A), "B CPW": S.cpw(TD[f].Bp), "B slot": S.slot(TD[f].Bp)}
        for f in F}


def weights(f):
    wA = 1 / np.sqrt(np.mean(abs(TD[f].A) ** 2)); wB = 1 / np.sqrt(np.mean(abs(TD[f].Bp) ** 2))
    return {"A CPW": wA, "A slot": 10 * wA, "B CPW": wB, "B slot": wB}


def fit_c(freqs, iters=60):
    c = np.ones(len(MODES), complex); g = {}
    for _ in range(iters):
        for f in freqs:                                           # g(f): scalar LS
            w = weights(f); mdl = np.concatenate([w[p] * sum(c[i] * COLS[f][m][p] for i, m in enumerate(MODES)) for p in PAT])
            d = np.concatenate([w[p] * DATA[f][p] for p in PAT]); g[f] = np.vdot(mdl, d) / np.vdot(mdl, mdl)
        Mrows, d = [], []                                         # c: linear LS given g
        for f in freqs:
            w = weights(f)
            Mrows.append(np.concatenate([np.stack([w[p] * g[f] * COLS[f][m][p] for m in MODES], 1) for p in PAT], 0))
            d.append(np.concatenate([w[p] * DATA[f][p] for p in PAT]))
        c, *_ = np.linalg.lstsq(np.concatenate(Mrows), np.concatenate(d), rcond=None)
        c = c / c[0]
    return c, g


def eo(f, td, c, pat_data=None):
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    cl = COLS[f] if f in COLS else columns(f, td)
    mB = sum(c[i] * cl[m]["B CPW"] for i, m in enumerate(MODES)); mA = sum(c[i] * cl[m]["A CPW"] for i, m in enumerate(MODES))
    return np.mean(mB * w) / np.mean(mA * w), mA, mB


if __name__ == "__main__":
    c, g = fit_c(F)
    print("field scale per mode c_m / c_e_cpw: " + ", ".join(f"{m} {abs(v):.3g}({np.degrees(np.angle(v)):+.0f})" for m, v in zip(MODES, c)))
    print(" f  | A CPW resid | B CPW resid | EO junction model vs data (dB, deg) | data EO (dB)")
    Xd = []
    for f in F:
        X, mA, mB = eo(f, TD[f], c); xd = data_X(f, TD[f]); Xd.append(xd)
        rA = np.linalg.norm(DATA[f]["A CPW"] - g[f] * mA) / np.linalg.norm(DATA[f]["A CPW"])
        rB = np.linalg.norm(DATA[f]["B CPW"] - g[f] * mB) / np.linalg.norm(DATA[f]["B CPW"])
        print(f"{f:3.0f} | {rA:.3f} | {rB:.3f} | {20*np.log10(abs(X/xd)):+6.2f} {np.degrees(np.angle(X/xd)):+6.1f} | {20*np.log10(abs(xd)):6.1f}")
    print("\nLeave-one-out (c refitted without the monitor's fields; junction from the S-parameters):")
    lo = []
    for i, f in enumerate(F):
        ci, _ = fit_c(np.delete(F, i)); X, _, _ = eo(f, TD[f], ci); xd = Xd[i]
        e = abs(X - xd) / abs(xd); lo.append(e)
        print(f"  {f:3.0f} GHz  |dX|/|X| {e:5.2f}  {20*np.log10(abs(X/xd)):+6.2f} dB")
    print(f"  median {np.median(lo):.2f} (six-mode coefficient interpolation 0.77, direct spline 0.80, field end model 0.61-1.07)")
    fd = np.arange(1.0, 60.01, 0.25); Xp = []
    for f in fd:
        td = TD[F[np.argmin(abs(F - f))]]; X, _, _ = eo(f, td, c); Xp.append(X)
    Xp = np.array(Xp)
    np.savetxt(os.path.join(HERE, "junction_eo_dense.csv"), np.c_[fd, Xp.real, Xp.imag], delimiter=",",
               header="f_GHz,ReX,ImX  EO B/A on the interior samples, junction model (K=0) + field scales")
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    ax.plot(fd, 20 * np.log10(abs(Xp)), "-", color="#2a78d6", lw=1.4, label="junction model (S-parameters at 12 points + 6 field scales)")
    ax.plot(F, 20 * np.log10(abs(np.array(Xd))), "o", color="#eb6834", ms=7, mec="white", mew=1.5, label="TD gap fields (-44.5 dB run)")
    ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk B/A, interior samples (dB)"); ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(HERE, "junction_eo_dense.png"), dpi=150)
