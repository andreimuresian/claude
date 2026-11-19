"""Full equaliser run, 0-130 GHz (L1 2.70 mm +, bend 1, L2 1.44 mm +, bend 2, L3 1.44 mm -), simulated lengths, no model.
1. Electrical S21: directly from the touchstone (50 ohm ports).
2. EO response from the gap fields: V_k(z) = (GAP/2)(Ey(gap+) - Ey(gap-)) on the buried metal of each line
   (L1 z 0..2.70 along +z; L2 z 2.70..1.26 along -z; L3 z 1.26..2.70 along +z), field read at the gap centre (the
   field the light sees). H = sum_k p_k int V_k(s) exp(j w t_opt(s)) ds, t_opt = t0_k + n_g s / c, n_g = 2.27.
   Light delay in each bend = RF delay of that bend (assumption: optical path matched to the RF in the bends);
   RF bend delay = slope of the bend S21 phase over 20-130 GHz, bend S21 from the forward/backward waves on the two
   lines next to it (symmetric reciprocal block, as for L+B+S).
   (a) L1 only: p = (+1, 0, 0)    (b) equaliser: p = (+1, +1, -1)    both in the same simulation (same RF).
   Normalised to |H_L1(1 GHz)| (common reference) and each to its own 1 GHz value.
Outputs: full_eq_eo_130.png, full_eq_eo_130.csv, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
C0 = 299792458.0; D = os.path.join(HERE, "..", "full equalizer", "130 GHz"); GAP, NG = 4.45e-6, 2.27
LINES = {"L1": (0.0, 2.70e-3, +1), "L2": (1.26e-3, 2.70e-3, -1), "L3": (1.26e-3, 2.70e-3, +1)}
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
data = {}
for ln in LINES:
    F, z, Ep = load(f"{ln}_gap+.txt"); _, _, Em = load(f"{ln}_gap-.txt"); data[ln] = (z, GAP / 2 * (Ep - Em))
w = 2 * np.pi * F * 1e9
# forward/backward fits per line (gamma free, pitch average, 0.18 mm cut)
LSn = np.load(os.path.join(HERE, "ls_extraction_130.npz"))
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
fitp = {}
for ln, (z0, z1, _) in LINES.items():
    z, V = data[ln]; ker = np.ones(36) / 36; zs = np.convolve(z, ker, "valid"); m = (zs >= z0 + 0.18e-3) & (zs <= z1 - 0.18e-3); G, Cc = [], []
    for i in range(len(F)):
        vs = np.convolve(V[i], ker, "valid")[m]; g0 = [np.interp(F[i], LSn["F"], LSn["aF"]) * 100 / 8.686, np.interp(F[i], LSn["F"], LSn["nF"]) * w[i] / C0]
        r = lambda p: np.r_[(e := two(p[0] + 1j * p[1], zs[m], vs)[1]).real, e.imag]
        p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]; G.append(g); Cc.append(two(g, zs[m], vs)[0])
    fitp[ln] = (np.array(G), np.array(Cc))
def bend(lin, lout, zp):
    g1, c1 = fitp[lin]; g2, c2 = fitp[lout]
    f1, r1 = c1[:, 0] * np.exp(-g1 * zp), c1[:, 1] * np.exp(g1 * zp); f2, r2 = c2[:, 0] * np.exp(-g2 * zp), c2[:, 1] * np.exp(g2 * zp)
    a1, b1 = (f1, r1) if LINES[lin][2] > 0 else (r1, f1); a2, b2 = (r2, f2) if LINES[lout][2] > 0 else (f2, r2)
    return (b1 * a1 - b2 * a2) / (a1**2 - a2**2), (b2 * a1 - b1 * a2) / (a1**2 - a2**2)
tau = {}
for nm, (S11, S21) in (("b1", bend("L1", "L2", 2.70e-3)), ("b2", bend("L2", "L3", 1.26e-3))):
    m = F >= 20; c = np.polyfit(w[m], np.unwrap(np.angle(S21))[m], 1); tau[nm] = -c[0]
    print(f"{nm}: RF delay from the phase slope 20-130 GHz {tau[nm]*1e12:.3f} ps; |S21| at 60 / 120 GHz {20*np.log10(abs(S21[np.argmin(abs(F-60))])):+.2f} / {20*np.log10(abs(S21[np.argmin(abs(F-120))])):+.2f} dB")
def eo(p):
    H = np.zeros(len(F), complex); t0 = np.zeros(len(F))
    for ln in ("L1", "L2", "L3"):
        z, V = data[ln]; z0, z1, d = LINES[ln]; mm = (z >= z0 - 1e-9) & (z <= z1 + 1e-9); s = (z[mm] - z0) if d > 0 else (z1 - z[mm]); o = np.argsort(s)
        if p[ln]: H += p[ln] * np.trapezoid((V[:, mm] * np.exp(1j * w[:, None] * (t0[:, None] + NG * s[None, :] / C0)))[:, o], s[o], axis=1)
        t0 = t0 + NG * (z1 - z0) / C0 + (tau["b1"] if ln == "L1" else tau["b2"] if ln == "L2" else 0)
    return H
H1, He = eo({"L1": 1, "L2": 0, "L3": 0}), eo({"L1": 1, "L2": 1, "L3": -1})
ref = abs(H1[0]); dB = lambda h, r: 20 * np.log10(abs(h) / r)
e1, ee, e1o, eeo = dB(H1, ref), dB(He, ref), dB(H1, abs(H1[0])), dB(He, abs(He[0]))
net = rf.Network(os.path.join(D, "BASELINE - FULL EQUALIZER_130 GHz.s2p")); fS = net.f / 1e9; s21 = 20 * np.log10(abs(net.s[:, 1, 0])); s11 = 20 * np.log10(abs(net.s[:, 0, 0]))
def cross(ff, y, lev=-3.0):
    k = np.where(y[ff >= 1] <= lev)[0]
    if not len(k): return "> 130"
    fa, ya = ff[ff >= 1], y[ff >= 1]; i = k[0]; return f"{fa[i-1] + (lev - ya[i-1]) * (fa[i] - fa[i-1]) / (ya[i] - ya[i-1]):.1f}"
print(f"|H_eq| / |H_L1| at 1 GHz: {abs(He[0])/abs(H1[0]):.3f}")
print(" f GHz | S21 el. dB | EO L1 only (re L1 1 GHz) | EO equaliser (re L1 1 GHz) | EO equaliser (re own 1 GHz)")
for q in (1, 10, 20, 30, 40, 60, 80, 100, 120, 130):
    i = np.argmin(abs(F - q)); j = np.argmin(abs(fS - q))
    print(f"{q:5d}  | {s21[j]:+.2f} | {e1[i]:+.2f} | {ee[i]:+.2f} | {eeo[i]:+.2f}")
print(f"-3 dB: S21 electrical {cross(fS, s21)} GHz | EO L1 only {cross(F, e1o)} GHz | EO equaliser re own 1 GHz {cross(F, eeo)} GHz, re L1 at 1 GHz {cross(F, ee)} GHz")
np.savetxt(os.path.join(HERE, "full_eq_eo_130.csv"), np.column_stack([F, np.interp(F, fS, s21), e1, ee, eeo]), delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,S21_electrical_dB,EO_L1_only_dB_re_L1_1GHz,EO_equaliser_dB_re_L1_1GHz,EO_equaliser_dB_re_own_1GHz")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(13, 4.4))
ax[0].plot(fS, s21, "-", color="#0E2268", lw=1.5, label="|S$_{21}$|, full equaliser (touchstone)"); ax[0].set_ylim(-6, 0)
ax[0].set_ylabel("Electrical |S$_{21}$| (dB)"); ax[0].set_title("Electrical S$_{21}$: 2.70 + 1.44 + 1.44 mm, 50 Ω ports", fontsize=11)
ax[1].plot(F, e1, "o-", ms=3, lw=1, color="#9AA0AC", label="EO, L1 only (2.70 mm)")
ax[1].plot(F, ee, "o-", ms=3, lw=1, color="#EB6834", label="EO, equaliser (+ + −)"); ax[1].axhline(-3, color="0.4", lw=0.8, ls=":")
ax[1].set_ylim(-6, 0); ax[1].set_ylabel("EO response (dB, re L1 at 1 GHz)"); ax[1].set_title("EO response from the gap fields, n$_g$ = 2.27", fontsize=11)
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=10.5, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "full_eq_eo_130.png"), dpi=200)
