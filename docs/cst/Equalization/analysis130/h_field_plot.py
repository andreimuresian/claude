"""Figure of the H-field line impedance (h_field_analysis.npz). Output: h_field_zc.png"""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); d = np.load(os.path.join(HERE, "h_field_analysis.npz")); F = d["F"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(12, 4.0))
for l, c in zip(("L1", "L2", "L3"), ("#0E2268", "#EB6834", "#2A78D6")):
    ax[0].plot(F, d[f"{l}_Zc"].real, "o", ms=2.8, color=c, label=f"{l}: V (outside apertures) / I (H loop)"); ax[1].plot(F, d[f"{l}_Zc"].imag, "o", ms=2.8, color=c, label=l)
ax[0].plot(F, d["L1_Zc_avg"].real, "^", ms=2.8, color="#9AA0AC", label="L1: cell-averaged V / I")
ax[0].plot(F, d["Zts"].real, "k-", lw=1.5, label="L+S touchstone (with port blocks)"); ax[1].plot(F, d["Zts"].imag, "k-", lw=1.5, label="L+S touchstone")
ax[0].set_ylim(34, 46); ax[0].set_ylabel("Re Z$_c$ (Ω)"); ax[1].set_ylim(-4, 4); ax[1].set_ylabel("Im Z$_c$ (Ω)")
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=9, loc="upper right")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "h_field_zc.png"), dpi=200)
