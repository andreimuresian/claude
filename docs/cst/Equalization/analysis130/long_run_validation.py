"""Validation of the models on the long equaliser run (L1 10.08 mm +, L2 5.04 mm +, L3 5.04 mm -), 0-130 GHz.
Reference (CST): electrical S21/S11 from the touchstone; EO response from the gap fields (as full_eq_eo_130.py:
V_k = GAP/2 (Ey+ - Ey-) on each buried line, light delay in each bend = RF delay of that bend from the field waves,
n_g 2.27, + + -); parasitic content rms |v_p|/|v_c| on each line (cell-averaged; v_p = (v_left - v_right)/2).
Predictions with no information from this run (lines from L+S, bends from L+B+S): two-mode bend, two-mode with no
conversion (kap = 0), two-port cubic bend. Outputs: long_run_validation.npz, long_run_validation.png, printed table."""
import os, io, contextlib, runpy, numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); C0, GAP, NG = 299792458.0, 4.45e-6, 2.27
D = os.path.join(HERE, "..", "full equalizer 10+5+5"); L1, L2, L3 = 10.08e-3, 5.04e-3, 5.04e-3
LINES = {"L1": (0.0, L1, +1), "L2": (L1 - L2, L1, -1), "L3": (L1 - L3, L1, +1)}
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
data, raw = {}, {}
for ln in LINES:
    F, z, Ep = load(f"{ln}_gap+.txt"); _, _, Em = load(f"{ln}_gap-.txt"); data[ln] = (z, GAP / 2 * (Ep - Em)); raw[ln] = (z, Ep, Em)
w = 2 * np.pi * F * 1e9; LS = np.load(os.path.join(HERE, "ls_extraction_130.npz"))
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
fitp = {}
for ln, (z0, z1, _) in LINES.items():
    z, V = data[ln]; ker = np.ones(36) / 36; zs = np.convolve(z, ker, "valid"); m = (zs >= z0 + 0.18e-3) & (zs <= z1 - 0.18e-3); G, Cc = [], []
    for i in range(len(F)):
        vs = np.convolve(V[i], ker, "valid")[m]; g0 = [np.interp(F[i], LS["F"], LS["aF"]) * 100 / 8.686, np.interp(F[i], LS["F"], LS["nF"]) * w[i] / C0]
        r = lambda p: np.r_[(e := two(p[0] + 1j * p[1], zs[m], vs)[1]).real, e.imag]
        p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]; G.append(g); Cc.append(two(g, zs[m], vs)[0])
    fitp[ln] = (np.array(G), np.array(Cc))
an = {ln: (fitp[ln][0].real * 8.686 / 100, fitp[ln][0].imag * C0 / w) for ln in LINES}
def bend(lin, lout, zp):
    g1, c1 = fitp[lin]; g2, c2 = fitp[lout]
    f1, r1 = c1[:, 0] * np.exp(-g1 * zp), c1[:, 1] * np.exp(g1 * zp); f2, r2 = c2[:, 0] * np.exp(-g2 * zp), c2[:, 1] * np.exp(g2 * zp)
    a1, b1 = (f1, r1) if LINES[lin][2] > 0 else (r1, f1); a2, b2 = (r2, f2) if LINES[lout][2] > 0 else (f2, r2)
    return (b1 * a1 - b2 * a2) / (a1**2 - a2**2), (b2 * a1 - b1 * a2) / (a1**2 - a2**2)
tau = {}
for nm, (S11, S21) in (("b1", bend("L1", "L2", L1)), ("b2", bend("L2", "L3", L1 - L2))):
    mm = F >= 20; tau[nm] = -np.polyfit(w[mm], np.unwrap(np.angle(S21))[mm], 1)[0]
def eo(p):
    H = np.zeros(len(F), complex); t0 = np.zeros(len(F))
    for ln in ("L1", "L2", "L3"):
        z, V = data[ln]; z0, z1, d = LINES[ln]; mm = (z >= z0 - 1e-9) & (z <= z1 + 1e-9); s = (z[mm] - z0) if d > 0 else (z1 - z[mm]); o = np.argsort(s)
        H += p[ln] * np.trapezoid((V[:, mm] * np.exp(1j * w[:, None] * (t0[:, None] + NG * s[None, :] / C0)))[:, o], s[o], axis=1)
        t0 = t0 + NG * (z1 - z0) / C0 + (tau["b1"] if ln == "L1" else tau["b2"] if ln == "L2" else 0)
    return H
db0 = lambda h: 20 * np.log10(abs(h) / abs(h[0])); dB = lambda x: 20 * np.log10(abs(x))
eo_ref = db0(eo({"L1": 1, "L2": 1, "L3": -1}))
# parasitic content per line (left/right with respect to travel: L1, L3 along +z: left = gap+; L2 along -z: left = gap-)
cell = lambda X: np.array([np.convolve(x, np.ones(36) / 36, "valid") for x in X]); rms = lambda x: np.sqrt((abs(x) ** 2).mean(1))
RPcst = []
for ln in ("L1", "L2", "L3"):
    z, Ep, Em = raw[ln]; vup, vdn = GAP * Ep, -GAP * Em; vl, vr = (vup, vdn) if LINES[ln][2] > 0 else (vdn, vup)
    RPcst.append(rms(cell((vl - vr) / 2)) / rms(cell((vl + vr) / 2)))
RPcst = np.array(RPcst).T
net = rf.Network(os.path.join(D, "BASELINE - FULL EQUALIZER - 10 mm.s2p")); fS = net.f / 1e9
cplx = lambda x: np.interp(F, fS, abs(x)) * np.exp(1j * np.interp(F, fS, np.unwrap(np.angle(x))))
S21r, S11r = cplx(net.s[:, 1, 0]), cplx(net.s[:, 0, 0])
# predictions
with contextlib.redirect_stdout(io.StringIO()):
    tm = runpy.run_path(os.path.join(HERE, "two_mode_cascade.py")); ca = runpy.run_path(os.path.join(HERE, "cascade_130.py"))
assert np.allclose(tm["F"], F)
SM = tm["SM"]; NOK = dict(SM); NOK["kap"] = 0 * SM["kap"]; LEN = [L1, L2, L3]
P = {}
S21, S11, H, RP = tm["solve"](SM, tm["RHO"], LEN=LEN); P["two-mode bend"] = (S21, S11, db0(H), RP)
S21, S11, H, RP = tm["solve"](NOK, tm["RHO"], LEN=LEN); P["no conversion"] = (S21, S11, db0(H), RP)
ca["cascade"].__globals__["SECT"] = [(L1, +1), (L2, +1), (L3, -1)]; S2p, H2p, _ = ca["cascade"]("smoothed"); P["two-port bend"] = (S2p[:, 1, 0], S2p[:, 0, 0], db0(H2p), None)
print(f"run: line fits per fold vs L+S (mean over 4-130 GHz): " + " | ".join(f"{ln}: alpha {np.mean((an[ln][0]-LS['aF'])[F>=4]):+.3f} dB/cm, n_m {np.mean((an[ln][1]-LS['nF'])[F>=4]):+.4f}" for ln in LINES))
print(f"bend delays (fields): {tau['b1']*1e12:.3f} / {tau['b2']*1e12:.3f} ps")
for lab, (s21, s11, e, rp) in P.items():
    for lo, hi in ((1, 60), (62, 130)):
        mm = (F >= lo) & (F <= hi); de, d2 = (e - eo_ref)[mm], (dB(s21) - dB(S21r))[mm]
        print(f"{lab:14s} {lo:3d}-{hi:3d} GHz: EO rms {np.sqrt(np.mean(de**2)):.3f} max {abs(de).max():.3f} dB | |S21| rms {np.sqrt(np.mean(d2**2)):.3f} max {abs(d2).max():.3f} dB | |S11| max diff {abs(abs(s11)-abs(S11r))[mm].max():.3f}")
print(" f GHz | EO re 1 GHz: CST / two-mode / two-port | |S21| dB: CST / two-mode | v_p/v_c dB L1/L2/L3: CST | two-mode")
for q in (10, 20, 40, 60, 80, 100, 120, 130):
    i = np.argmin(abs(F - q)); rp = P["two-mode bend"][3]
    print(f"{q:5d} | {eo_ref[i]:+.2f} / {P['two-mode bend'][2][i]:+.2f} / {P['two-port bend'][2][i]:+.2f} | {dB(S21r[i]):+.2f} / {dB(P['two-mode bend'][0][i]):+.2f} | "
          + " / ".join(f"{20*np.log10(RPcst[i,k]):5.1f}" for k in range(3)) + " | " + " / ".join(f"{20*np.log10(rp[i,k]):5.1f}" for k in range(3)))
np.savez(os.path.join(HERE, "long_run_validation.npz"), F=F, eo_ref=eo_ref, S21r=S21r, S11r=S11r, RPcst=RPcst, tau=np.array([tau["b1"], tau["b2"]]),
         **{f"{k.replace(' ', '_')}_{q}": v for k, val in P.items() for q, v in zip(("S21", "S11", "eo", "RP"), val) if v is not None})
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 3, figsize=(14, 4.3)); col = {"two-mode bend": ("-", "#0E2268"), "no conversion": ("--", "#2A78D6"), "two-port bend": (":", "#9AA0AC")}
ax[0].plot(F, eo_ref, "o", ms=3, color="#EB6834", label="10 + 5 + 5 run (CST fields)"); ax[1].plot(F, dB(S21r), "o", ms=3, color="#EB6834", label="10 + 5 + 5 run (CST)")
for lab, (ls, c) in col.items():
    ax[0].plot(F, P[lab][2], ls, color=c, lw=1.6, label=f"prediction, {lab}"); ax[1].plot(F, dB(P[lab][0]), ls, color=c, lw=1.6, label=f"prediction, {lab}")
ax[0].set_ylim(-3, 0.5); ax[0].set_ylabel("EO re 1 GHz (dB)"); ax[1].set_ylim(-14, 0); ax[1].set_ylabel("|S$_{21}$| (dB)")
for k, (c, ln) in enumerate(zip(("#0E2268", "#EB6834", "#2A78D6"), ("L1", "L2", "L3"))):
    ax[2].plot(F, 20 * np.log10(RPcst[:, k]), "o", ms=2.5, color=c, label=f"{ln} CST"); ax[2].plot(F, 20 * np.log10(P["two-mode bend"][3][:, k]), "-", color=c, lw=1.4, label=f"{ln} two-mode")
ax[2].set_ylim(-75, 0); ax[2].set_ylabel("|v$_p$| / |v$_c$| (dB)")
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=8.5, loc="lower right" if a is ax[2] else "lower left", ncol=2 if a is ax[2] else 1)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "long_run_validation.png"), dpi=200)
