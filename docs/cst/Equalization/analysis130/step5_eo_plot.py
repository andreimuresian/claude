"""Step 5 figure: EO response of the full equaliser (2.70 + 1.44 + 1.44 mm, + + -) from the CST gap fields (reference)
against the two-mode cascade prediction (lines from L+S, bends from L+B+S; nothing from the full run).
Input: two_mode_cascade.npz. Output: step5_eo.png"""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); d = np.load(os.path.join(HERE, "two_mode_cascade.npz"))
F, ref, mod = d["F"], d["eo_ref"], d["two-mode_smooth_eo"]; diff = mod - ref
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(2, 1, figsize=(9, 6.2), sharex=True, gridspec_kw={"height_ratios": [2.2, 1]})
ax[0].plot(F, ref, "o", ms=4, color="#EB6834", label="full equaliser, CST gap fields (reference)")
ax[0].plot(F, mod, "-", color="#0E2268", lw=1.8, label="model: L+S line + two-mode L+B+S bend")
ax[0].axhline(-3, color="0.4", lw=0.8, ls=":"); ax[0].set_ylim(-3.5, 0); ax[0].set_ylabel("EO response re 1 GHz (dB)")
ax[0].legend(frameon=False, fontsize=10.5, loc="lower left"); ax[0].set_title("2.70 (+) + 1.44 (+) + 1.44 (−) mm, 50 Ω ports, n$_g$ = 2.27", fontsize=11)
ax[1].plot(F, diff, "-", color="#0E2268", lw=1.5); ax[1].axhline(0, color="0.4", lw=0.8); ax[1].axhspan(-0.05, 0.05, color="#F1F3F8", zorder=0)
ax[1].set_ylim(-0.3, 0.3); ax[1].set_ylabel("Model − CST (dB)"); ax[1].set_xlabel("Frequency (GHz)")
m1, m2 = F <= 60, F > 60
ax[1].text(3, 0.2, f"rms {np.sqrt(np.mean(diff[m1]**2)):.2f} dB (1–60 GHz),  {np.sqrt(np.mean(diff[m2]**2)):.2f} dB (62–130 GHz)", fontsize=10)
for a in ax: a.set_xlim(0, 130); a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "step5_eo.png"), dpi=200)
