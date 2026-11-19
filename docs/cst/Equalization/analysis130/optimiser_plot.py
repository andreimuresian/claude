"""Figures of the L1 = 10 mm optimiser (optimiser_L1_10mm.npz): map of the absolute worst EO level 10-130 GHz over (L2, L3)
with peaking contours; EO curves of selected designs re the standalone 10 mm line at 1 GHz. Output: optimiser_L1_10mm.png"""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); d = np.load(os.path.join(HERE, "optimiser_L1_10mm.npz"))
L2, L3, F = d["L2s"], d["L3s"], d["F"]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(13.5, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
im = ax[0].pcolormesh(L3, L2, d["absworst"], shading="nearest", cmap="viridis", vmin=-4, vmax=-1); cb = plt.colorbar(im, ax=ax[0]); cb.set_label("Worst EO level 10–130 GHz (dB)")
cs = ax[0].contour(L3, L2, d["peak"], levels=[0.5, 1.0, 2.0], colors=["w", "#EB6834", "#F20013"], linewidths=1.3); ax[0].clabel(cs, fmt="peaking %.1f dB", fontsize=8.5)
ax[0].plot(L3, L3, ":", color="w", lw=1); ax[0].set_xlabel("L3, polarity − (mm)"); ax[0].set_ylabel("L2, polarity + (mm)")
ax[0].set_title("L1 = 10 mm: absolute EO, re the 10 mm line at 1 GHz", fontsize=10.5)
DES = [((None, None), "10 mm line alone", "#9AA0AC", "-"), ((5.0, 5.0), "10 + 5 + 5", "#2A78D6", "-"), ((8.5, 8.0), "10 + 8.5 + 8 (best, peaking ≤ 0.25 dB)", "#0E2268", "-"),
       ((9.0, 9.0), "10 + 9 + 9 (best, peaking ≤ 1 dB)", "#0E2268", "--"), ((5.5, 7.0), "10 + 5.5 + 7 (flattest normalised)", "#EB6834", "-")]
for (a, b), lab, c, ls in DES:
    if a is None: y = d["e10"]
    else: y = d["EO_abs"][np.argmin(abs(L2 - a)), np.argmin(abs(L3 - b))]
    ax[1].plot(F, y, ls, color=c, lw=1.7, label=lab); 
    if a is not None: ax[0].plot(b, a, "o", ms=7, mfc="none", mec=c if c != "#0E2268" else "w", mew=1.8)
ax[1].axhline(-3, color="0.4", lw=0.8, ls=":"); ax[1].set_ylim(-6, 1); ax[1].set_xlim(0, 130); ax[1].set_xlabel("Frequency (GHz)")
ax[1].set_ylabel("EO re the 10 mm line at 1 GHz (dB)"); ax[1].grid(alpha=0.3); ax[1].legend(frameon=False, fontsize=9.5, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "optimiser_L1_10mm.png"), dpi=200)
