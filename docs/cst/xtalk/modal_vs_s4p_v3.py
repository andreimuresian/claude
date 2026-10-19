"""Hybrid crosstalk model vs coworker's 3-D CST .s4p (200 um pitch).
 - average line (speed, loss, impedance): 3-D single-line fit, cascade/three_lengths_results.npz
   (includes gold loss / internal inductance, which the hexahedral port solver ignores: it treats metal as PEC)
 - even/odd SPLIT: 2-D port modes 5/6 -> dn(f) from beta (portmode_betas.txt),
   Ze/Zo - 1 = +0.30...+0.45 % from field integration (port_voltages_sweep.py)."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from first_look_lib import load4
c = 299792458
R = np.load("../cascade/three_lengths_results.npz"); fR, gR, ZR = R["f"], R["g"], R["Zfit"]
B = np.loadtxt("portmode_betas.txt"); fb = B[:, 0]*1e9; dbeta_over_f = (B[:, 1]-B[:, 2])/fb
def line2(gam, Z, L, z0=50.0):
    t = np.exp(-gam*L); r = (Z-z0)/(Z+z0); d = 1 - r**2*t**2
    return r*(1-t**2)/d, (1-r**2)*t/d
def xtalk(f, L, dz):
    g = np.interp(f, fR, gR.real) + 1j*np.interp(f, fR, gR.imag)
    Z = np.interp(f, fR, ZR.real) + 1j*np.interp(f, fR, ZR.imag)
    db_ = np.interp(f, fb, dbeta_over_f)*f            # beta_even - beta_odd
    s11e, s21e = line2(g + 0.5j*db_, Z*(1+dz/2), L); s11o, s21o = line2(g - 0.5j*db_, Z*(1-dz/2), L)
    return 0.5*(s11e-s11o), 0.5*(s21e-s21o)
db = lambda x: 20*np.log10(np.abs(x)+1e-30)
fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True); rows = []
for j, (fn, L) in enumerate([("LINEA0_1MM_200UM_PITCH.s4p", 1e-3), ("LINEA0_5MM_200UM_PITCH.s4p", 5e-3)]):
    f, S = load4(fn); f, S = f[1:], S[1:]
    lo, hi = xtalk(f, L, 0.0030), xtalk(f, L, 0.0045)
    for i, (k, name) in enumerate([(2, "NEXT  |S31|"), (3, "FEXT  |S41|")]):
        a = axs[i, j]; cst = db(S[:, k, 0]); m1, m2 = db(lo[i]), db(hi[i])
        a.fill_between(f/1e9, np.minimum(m1, m2), np.maximum(m1, m2), color="C3", alpha=.35,
                       label="cross-section model (3-D line + 2-D even/odd split)")
        a.plot(f/1e9, cst, "k", lw=2, label="coworker's 3-D CST (.s4p)")
        a.set_title(f"{name},  L = {L*1e3:.0f} mm,  pitch 200 µm"); a.set_ylim(-110, -30); a.grid(alpha=.3)
        for gq in (6, 18, 30, 42, 60):
            q = np.argmin(abs(f-gq*1e9)); rows.append((L*1e3, name[:4], gq, cst[q], m1[q], m2[q]))
axs[0, 0].legend(fontsize=8, loc="lower right"); [a.set_xlabel("frequency (GHz)") for a in axs[1]]
[a.set_ylabel("dB") for a in axs[:, 0]]
fig.tight_layout(); fig.savefig("modal_vs_s4p_v3.png", dpi=110)
for r in rows: print("%.0fmm %s %2d GHz  CST %6.1f  model %6.1f .. %6.1f" % r)
