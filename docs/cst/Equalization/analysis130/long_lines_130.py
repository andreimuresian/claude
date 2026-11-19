"""Step 6: equalisers with longer sections, predicted with the two-mode bend (L+B+S) and the L+S line, 0-130 GHz.
Cases: (A) L1 = 2.70 mm with L2 = L3 = 1.44 (simulated), 3, 5, 8 mm: test of the cancellation (L2, L3 > L1/2 over-equalise);
(B) scaled designs, L2 = L3 about L1/2: 5.40 + 2.88 + 2.88, 8 + 4 + 4, 10 + 5 + 5 mm (run in progress).
Polarities + + -, 50 ohm ports, n_g 2.27, light matched to the RF in the bends.
For each case three bend models: two-mode (conversion and reconversion), no conversion (kap = 0: parasitic mode never
excited, i.e. perfect cancellation and no conversion loss), two-port cubic (step 3, average parasitic loss inside the bend).
Outputs: long_lines_130.npz, long_lines_130.png, printed table."""
import os, io, contextlib, runpy, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    tm = runpy.run_path(os.path.join(HERE, "two_mode_cascade.py")); ca = runpy.run_path(os.path.join(HERE, "cascade_130.py"))
solve, SM, F, RHO = tm["solve"], tm["SM"], tm["F"], tm["RHO"]; casc = ca["cascade"]
NOK = dict(SM); NOK["kap"] = 0 * SM["kap"]
db0 = lambda h: 20 * np.log10(abs(h) / abs(h[0])); dB = lambda x: 20 * np.log10(abs(x))
def cross(y, lev=-3.0):
    k = np.where(y[1:] <= lev)[0]
    if not len(k): return np.inf
    i = k[0] + 1; return F[i - 1] + (lev - y[i - 1]) * (F[i] - F[i - 1]) / (y[i] - y[i - 1])
CASES = [(2.70, 1.44, 1.44), (2.70, 3.0, 3.0), (2.70, 5.0, 5.0), (2.70, 8.0, 8.0), (5.40, 2.88, 2.88), (8.0, 4.0, 4.0), (10.0, 5.0, 5.0)]
out = {}
print(" L1/L2/L3 mm | EO -3 dB GHz: two-mode / no conv. / two-port | EO at 60 / 100 / 130 GHz (two-mode) | max |two-mode - no conv.| | max |two-mode - two-port| | v_p/v_c on L3 at 60 / 100 GHz (dB)")
for L in CASES:
    LEN = [x * 1e-3 for x in L]
    S21, S11, H, RP = solve(SM, RHO, LEN=LEN); S21n, _, Hn, _ = solve(NOK, RHO, LEN=LEN)
    casc.__globals__["SECT"] = [(LEN[0], +1), (LEN[1], +1), (LEN[2], -1)]; S2p, H2p, _ = casc("smoothed")
    e, en, e2 = db0(H), db0(Hn), db0(H2p); i60, i100, i130 = (np.argmin(abs(F - q)) for q in (60, 100, 130))
    out[L] = dict(eo=e, eo_noconv=en, eo_2port=e2, S21=S21, S21_noconv=S21n, S21_2port=S2p[:, 1, 0], RP=RP)
    fmt = lambda x: "> 130" if np.isinf(x) else f"{x:.0f}"
    print(f" {L[0]:.2f}/{L[1]:.2f}/{L[2]:.2f} | {fmt(cross(e))} / {fmt(cross(en))} / {fmt(cross(e2))} | {e[i60]:+.2f} / {e[i100]:+.2f} / {e[i130]:+.2f} | "
          f"{abs(e-en).max():.2f} dB at {F[np.argmax(abs(e-en))]:.0f} GHz | {abs(e-e2).max():.2f} dB | {20*np.log10(RP[i60,2]):.1f} / {20*np.log10(RP[i100,2]):.1f}")
np.savez(os.path.join(HERE, "long_lines_130.npz"), F=F, cases=np.array(CASES), **{f"{'_'.join(f'{x:g}' for x in L)}_{k}": v for L in out for k, v in out[L].items()})
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2)); R = out[(10.0, 5.0, 5.0)]
ax[0].plot(F, R["eo"], "-", color="#0E2268", lw=1.8, label="two-mode bend"); ax[0].plot(F, R["eo_noconv"], "--", color="#2A78D6", lw=1.5, label="no conversion (ideal cancellation)")
ax[0].plot(F, R["eo_2port"], ":", color="#9AA0AC", lw=1.8, label="two-port bend, cubic"); ax[0].set_ylim(-6, 0); ax[0].set_ylabel("EO re 1 GHz (dB)"); ax[0].set_title("10 + 5 + 5 mm: EO response", fontsize=11)
ax[1].plot(F, dB(R["S21"]), "-", color="#0E2268", lw=1.8, label="two-mode bend"); ax[1].plot(F, dB(R["S21_noconv"]), "--", color="#2A78D6", lw=1.5, label="no conversion")
ax[1].plot(F, dB(R["S21_2port"]), ":", color="#9AA0AC", lw=1.8, label="two-port bend, cubic"); ax[1].set_ylim(-16, 0); ax[1].set_ylabel("|S$_{21}$| (dB)"); ax[1].set_title("10 + 5 + 5 mm: electrical S$_{21}$", fontsize=11)
for L, c, ls in zip(CASES, ("#9AA0AC", "#2A78D6", "#EB6834", "#0E2268", "#2A78D6", "#EB6834", "#0E2268"), ("-", "-", "-", "-", ":", ":", ":")):
    ax[2].plot(F, out[L]["eo"] - out[L]["eo_noconv"], ls, color=c, lw=1.5, label=f"{L[0]:g} + {L[1]:g} + {L[2]:g} mm")
ax[2].axhline(0, color="0.4", lw=0.8); ax[2].set_ylim(-0.5, 0.3); ax[2].set_ylabel("EO: two-mode − no conversion (dB)"); ax[2].set_title("Effect of the parasitic mode on the EO response", fontsize=11)
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=8.5 if a is ax[2] else 9, loc="lower left", ncol=2 if a is ax[2] else 1)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "long_lines_130.png"), dpi=200)
