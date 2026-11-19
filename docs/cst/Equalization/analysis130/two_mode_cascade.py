"""Step 4-5: full equaliser predicted with the two-mode bend (from L+B+S only), against the full run and the two-port cascade.

Smooth two-mode bend (from two_mode_bend.py, L+B+S fields; no information from the full run):
  t_c  : |t_c| dB = cubic in f, phase = -w tau_c (slope fit)        r_c : c1 f + c2 f^2 + c3 f^3 (complex; zero at DC)
  kap  : j (k1 f + k2 f^2) exp(-j w tau_k)   (conversion grows with f; +90 deg = path-difference mechanism)
  t_p  : |t_p| dB = k |t_c| dB (same loss ratio k as on the lines), phase = -w tau_p
  rho  : Zc/Zp from two_mode_bend.py;   Gamma_p at both ports = -|G| exp(-j w tau_G) (median fit of both ports)
Lines: coplanar from the L+S model (gamma_c, Zc), parasitic gamma_p = k alpha_c + j n_p w/c. Ports: coplanar port block
(L+S) with 50 ohm source/load; parasitic reflected with Gamma_p.
Global linear system per frequency: 12 unknowns (forward/backward, c/p, 3 lines), 12 equations (2 per port, 4 per bend).
Bend 1 turns left, bend 2 right: with v_p = (v_left - v_right)/2 along the path, kap enters with + at bend 1, - at bend 2.
EO: H = sum p_k int v_c(s) exp(j w t_opt) ds, p = (+1, +1, -1), n_g 2.27, light delay per bend = tau_c.
Outputs: two_mode_cascade.npz, two_mode_cascade.png, printed table."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
C0, NG = 299792458.0, 2.27
with contextlib.redirect_stdout(io.StringIO()):
    lb = runpy.run_path(os.path.join(HERE, "lbs_bend_130.py"))
line, ports, pp = lb["line"], lb["ports"], lb["pp"]
TM = np.load(os.path.join(HERE, "two_mode_bend.npz")); GPm = np.load(os.path.join(HERE, "two_mode_gamma_p.npz"))
F = TM["F"]; w = 2 * np.pi * F * 1e9; K, NP, RHO = float(GPm["k"]), float(GPm["n_p"]), float(TM["rho"]); m = F >= 10
# ---- smooth bend coefficients
def slope(x):
    ph = np.unwrap(np.angle(x)); c = np.polyfit(w[F >= 25], ph[F >= 25], 1); return -c[0], c[1]
tauc, _ = slope(TM["tc"]); taup, _ = slope(TM["tp"]); tauk, ph0k = slope(TM["kap"])
tc_dB = np.polyval(np.polyfit(F[m], 20 * np.log10(abs(TM["tc"][m])), 3), F)
SM = {}
SM["tc"] = 10 ** (tc_dB / 20) * np.exp(-1j * w * tauc)
Mr = np.stack([F, F ** 2, F ** 3], 1)                                           # r_c -> 0 at DC: polynomial without constant term
SM["rc"] = Mr @ np.linalg.lstsq(Mr, TM["rc"], rcond=None)[0]
kk = np.linalg.lstsq(np.stack([F[m], F[m] ** 2], 1), abs(TM["kap"][m]), rcond=None)[0]
SM["kap"] = 1j * (kk[0] * F + kk[1] * F ** 2) * np.exp(-1j * w * tauk)
SM["tp"] = 10 ** (K * tc_dB / 20) * np.exp(-1j * w * taup)
G = np.r_[TM["G1"][F >= 25], TM["G2"][F >= 25]]; FF = np.r_[F[F >= 25], F[F >= 25]]
Gmag = np.median(abs(G)); tg = -np.polyfit(2 * np.pi * FF * 1e9, np.unwrap(np.angle(-G)), 1)[0]
SM["G"] = -Gmag * np.exp(-1j * w * tg)
print(f"smooth bend: tau_c {tauc*1e12:.3f} ps, tau_p {taup*1e12:.3f} ps, kap = j({kk[0]:.2e} f + {kk[1]:.2e} f^2) exp(-j w {tauk*1e12:.2f} ps) "
      f"[raw phase at 0 Hz {np.degrees(ph0k):+.0f} deg]; rho {RHO:.2f}; Gamma_p = -{Gmag:.3f} exp(-j w {tg*1e12:.2f} ps); k {K:.2f}, n_p {NP:.3f}")
RAW = {"tc": TM["tc"], "rc": TM["rc"], "kap": TM["kap"], "tp": TM["tp"], "G": SM["G"]}
gc, Zc = line(F); gp = K * gc.real + 1j * NP * w / C0
P1, P2 = ports(F, pp[0] * 1e-12, pp[1] * 1e-15); P2i = np.linalg.inv(P2)
LEN = [2.70e-3, 1.44e-3, 1.44e-3]; POL = [+1, +1, -1]; SIG = [+1, -1]
def solve(B, rho=RHO, ds=5e-6):
    S21, S11, H = np.zeros(len(F), complex), np.zeros(len(F), complex), np.zeros(len(F), complex); RP = np.zeros((len(F), 3))
    for i in range(len(F)):
        A = np.zeros((12, 12), complex); y = np.zeros(12, complex); g, Z, q = gc[i], Zc[i], gp[i]
        ix = lambda k, mode, d: 4 * k + 2 * mode + d                     # mode 0 = c, 1 = p; d 0 = fwd (A), 1 = bwd (B)
        r0 = P1[i][0] + 50 * P1[i][1]; A[0, ix(0, 0, 0)] = r0[0] + r0[1] / Z; A[0, ix(0, 0, 1)] = r0[0] - r0[1] / Z; y[0] = 1
        A[1, ix(0, 1, 0)] = 1; A[1, ix(0, 1, 1)] = -B["G"][i]
        row = 2
        for j in range(2):
            Lj, sg = LEN[j], SIG[j]; ec, ep = np.exp(-g * Lj), np.exp(-q * Lj); kap = sg * B["kap"][i]
            a1c, a1p = (ix(j, 0, 0), ec), (ix(j, 1, 0), ep); b1c, b1p = (ix(j, 0, 1), 1 / ec), (ix(j, 1, 1), 1 / ep)
            a2c, a2p = (ix(j + 1, 0, 1), 1.0), (ix(j + 1, 1, 1), 1.0); b2c, b2p = (ix(j + 1, 0, 0), 1.0), (ix(j + 1, 1, 0), 1.0)
            for (out, terms) in ((b1c, [(a1c, B["rc"][i]), (a2c, B["tc"][i]), (a2p, rho * kap)]), (b2c, [(a1c, B["tc"][i]), (a2c, B["rc"][i]), (a1p, rho * kap)]),
                                 (b1p, [(a2p, B["tp"][i]), (a2c, kap)]), (b2p, [(a1p, B["tp"][i]), (a1c, kap)])):
                A[row, out[0]] += out[1]
                for (col, f_), coef in terms: A[row, col] -= coef * f_
                row += 1
        L3 = LEN[2]; ec, ep = np.exp(-g * L3), np.exp(-q * L3); r2 = P2i[i][0] - 50 * P2i[i][1]
        A[10, ix(2, 0, 0)] = (r2[0] + r2[1] / Z) * ec; A[10, ix(2, 0, 1)] = (r2[0] - r2[1] / Z) / ec
        A[11, ix(2, 1, 1)] = 1 / ep; A[11, ix(2, 1, 0)] = -B["G"][i] * ep
        x = np.linalg.solve(A, y)
        V0, I0 = x[0] + x[1], (x[0] - x[1]) / Z; Vs = P1[i][0] @ np.array([V0, I0]); S11[i] = 2 * Vs - 1
        VL, IL = x[ix(2, 0, 0)] * ec + x[ix(2, 0, 1)] / ec, (x[ix(2, 0, 0)] * ec - x[ix(2, 0, 1)] / ec) / Z; S21[i] = 2 * (P2i[i][0] @ np.array([VL, IL]))
        t0 = 0.0
        for k in range(3):
            s = np.arange(0, LEN[k] + ds / 2, ds); vc = x[ix(k, 0, 0)] * np.exp(-g * s) + x[ix(k, 0, 1)] * np.exp(g * s)
            vp = x[ix(k, 1, 0)] * np.exp(-q * s) + x[ix(k, 1, 1)] * np.exp(q * s); RP[i, k] = np.sqrt(np.mean(abs(vp) ** 2) / np.mean(abs(vc) ** 2))
            H[i] += POL[k] * np.trapezoid(vc * np.exp(1j * w[i] * (t0 + NG * s / C0)), s); t0 += NG * LEN[k] / C0 + (tauc if k < 2 else 0)
    return S21, S11, H, RP
full = rf.Network(os.path.join(HERE, "..", "full equalizer", "130 GHz", "BASELINE - FULL EQUALIZER_130 GHz.s2p")); fS = full.f / 1e9
cplx = lambda x: np.interp(F, fS, abs(x)) * np.exp(1j * np.interp(F, fS, np.unwrap(np.angle(x))))
S21r, S11r = cplx(full.s[:, 1, 0]), cplx(full.s[:, 0, 0]); EQ = np.loadtxt(os.path.join(HERE, "full_eq_eo_130.csv"), delimiter=",", skiprows=1); eo_ref = EQ[:, 4]
FA = np.load(os.path.join(HERE, "full_eq_analysis_130.npz")); CA = np.load(os.path.join(HERE, "cascade_130.npz"))
dB = lambda x: 20 * np.log10(abs(x)); db0 = lambda h: 20 * np.log10(abs(h) / abs(h[0])); OUT = {}
for lab, B, rho in (("two-mode, smooth", SM, RHO), ("two-mode, raw coefficients", RAW, RHO), ("two-mode, smooth, rho = 1", SM, 1.0), ("two-mode, smooth, no p->c (rho = 0)", SM, 0.0)):
    S21, S11, H, RP = solve(B, rho); eo = db0(H); OUT[lab] = dict(S21=S21, S11=S11, eo=eo, RP=RP)
    for lo, hi in ((1, 60), (62, 130)):
        mm = (F >= lo) & (F <= hi); de, d2 = (eo - eo_ref)[mm], (dB(S21) - dB(S21r))[mm]
        print(f"{lab:38s} {lo:3d}-{hi:3d} GHz: EO rms {np.sqrt(np.mean(de**2)):.3f} max {abs(de).max():.3f} dB | |S21| rms {np.sqrt(np.mean(d2**2)):.3f} max {abs(d2).max():.3f} dB | |S11| max diff {abs(abs(S11)-abs(S11r))[mm].max():.3f}")
for lo, hi in ((1, 60), (62, 130)):
    mm = (F >= lo) & (F <= hi); de = CA["smoothed_d_eo"][mm]; d2 = CA["smoothed_d21"][mm]
    print(f"{'two-port, cubic (step 3)':38s} {lo:3d}-{hi:3d} GHz: EO rms {np.sqrt(np.mean(de**2)):.3f} max {abs(de).max():.3f} dB | |S21| rms {np.sqrt(np.mean(d2**2)):.3f} max {abs(d2).max():.3f} dB")
R = OUT["two-mode, smooth"]
print(" f GHz | |v_p|/|v_c| dB on L1 / L2 / L3: full run | two-mode smooth")
for q in (20, 31, 40, 60, 70, 80, 90, 100, 110, 120):
    i = np.argmin(abs(F - q)); print(f"{q:5d}  | " + " / ".join(f"{20*np.log10(FA['r'][k][i]):5.1f}" for k in range(3)) + " | " + " / ".join(f"{20*np.log10(R['RP'][i,k]):5.1f}" for k in range(3)))
np.savez(os.path.join(HERE, "two_mode_cascade.npz"), F=F, eo_ref=eo_ref, S21r=S21r, S11r=S11r, **{f"{k.replace(' ', '_').replace(',', '').replace('>', '').replace('=', '')}_{q}": OUT[k][q] for k in OUT for q in OUT[k]})
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].plot(F, eo_ref, "o", ms=3, color="#EB6834", label="full run (fields)"); ax[0].plot(F, R["eo"], "-", color="#0E2268", lw=1.6, label="two-mode bend (L+B+S)")
ax[0].plot(F, CA["smoothed_eo"], ":", color="#9AA0AC", lw=1.6, label="two-port bend, cubic"); ax[0].set_ylim(-2.5, 0); ax[0].set_ylabel("EO re 1 GHz (dB)")
ax[1].plot(F, dB(S21r), "o", ms=3, color="#EB6834", label="full run (CST)"); ax[1].plot(F, dB(R["S21"]), "-", color="#0E2268", lw=1.6, label="two-mode bend (L+B+S)")
ax[1].plot(F, dB(CA["smoothed_S"][:, 1, 0]), ":", color="#9AA0AC", lw=1.6, label="two-port bend, cubic"); ax[1].set_ylim(-6, 0); ax[1].set_ylabel("|S$_{21}$| (dB)")
for k, (c, ln) in enumerate(zip(("#0E2268", "#EB6834", "#2A78D6"), ("L1", "L2", "L3"))):
    ax[2].plot(F, 20 * np.log10(FA["r"][k]), "o", ms=2.5, color=c, label=f"{ln} full run"); ax[2].plot(F, 20 * np.log10(R["RP"][:, k]), "-", color=c, lw=1.4, label=f"{ln} two-mode")
ax[2].set_ylim(-75, 0); ax[2].set_ylabel("|v$_p$| / |v$_c$| (dB)")
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=8.5, loc="lower right" if a is ax[2] else "lower left", ncol=2 if a is ax[2] else 1)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "two_mode_cascade.png"), dpi=200)
