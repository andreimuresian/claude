"""Cross-section (2-D port mode) prediction of NEXT/FEXT vs the 3-D CST .s4p,
200 um pitch. Inputs from the CST port-mode runs:
  n_even = 1.8878, n_odd = 1.8863   (modes 5/6 at 30 GHz; held constant)
  Z_even/Z_odd - 1 = +0.30 ... +0.45 %  (field integration, 6-60 GHz, ~flat)
  mean per-line Z = 34.6 ohm.  Lossless, ports 50 ohm, lines identical."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from first_look_lib import load4
c = 299792458; k30 = 2*np.pi*30e9/c
ne, no = 1186.97/k30, 1186.02/k30; Zm = (2*17.3801 + 2*17.1815)/2
def line2(f, n, Z, L, z0=50.0):
    t = np.exp(-2j*np.pi*f*n*L/c); r = (Z-z0)/(Z+z0); d = 1 - r**2*t**2
    return r*(1-t**2)/d, (1-r**2)*t/d
def xtalk(f, L, dz):
    s11e, s21e = line2(f, ne, Zm*(1+dz/2), L); s11o, s21o = line2(f, no, Zm*(1-dz/2), L)
    return 0.5*(s11e-s11o), 0.5*(s21e-s21o)
db = lambda x: 20*np.log10(np.abs(x)+1e-30)
fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
rows = []
for j, (fn, L) in enumerate([("LINEA0_1MM_200UM_PITCH.s4p", 1e-3), ("LINEA0_5MM_200UM_PITCH.s4p", 5e-3)]):
    f, S = load4(fn); f, S = f[1:], S[1:]
    lo, hi = xtalk(f, L, 0.0030), xtalk(f, L, 0.0045)
    for i, (k, name) in enumerate([(2, "NEXT  |S31|"), (3, "FEXT  |S41|")]):
        a = axs[i, j]; cst = db(S[:, k, 0]); m1, m2 = db(lo[i]), db(hi[i])
        a.fill_between(f/1e9, np.minimum(m1, m2), np.maximum(m1, m2), color="C3", alpha=.3,
                       label="cross-section model (Ze/Zo +0.30…0.45 %)")
        a.plot(f/1e9, cst, "k", lw=2, label="coworker's 3-D CST (.s4p)")
        a.set_title(f"{name},  L = {L*1e3:.0f} mm,  pitch 200 µm"); a.set_ylim(-110, -30); a.grid(alpha=.3)
        for g in (6, 18, 30, 42, 60):
            q = np.argmin(abs(f-g*1e9)); rows.append((L*1e3, name[:4], g, cst[q], m1[q], m2[q]))
axs[0, 0].legend(fontsize=8, loc="lower right"); [a.set_xlabel("frequency (GHz)") for a in axs[1]]
[a.set_ylabel("dB") for a in axs[:, 0]]
fig.tight_layout(); fig.savefig("modal_vs_s4p_v2.png", dpi=110)
for r in rows: print("%.0fmm %s %2d GHz  CST %6.1f  model %6.1f .. %6.1f" % r)
