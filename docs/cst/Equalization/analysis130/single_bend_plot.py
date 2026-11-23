"""Figure of the single-bend analysis (single_bend_analysis.npz): loss split from the net power, paired over the two mirror
sides (cancels the plane-type calibration), and the single-bend |S21| with the trapped-mode dip. Output: single_bend_130.png"""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); d = np.load(os.path.join(HERE, "single_bend_analysis.npz")); F, P = d["F"], d["P"]
r = lambda a, b: 10 * np.log10(P[b] / P[a])
trans, straight, arc, total = r(0, 1) + r(7, 8), r(1, 3) + r(5, 7), r(3, 4) + r(4, 5), r(0, 8)
qs = [10, 20, 40, 60, 100, 120]; ii = [int(np.argmin(abs(F - q))) for q in qs]
for q, i in zip(qs, ii): print(f"{q} GHz: transitions {trans[i]:+.3f}, raised straights {straight[i]:+.3f}, arc {arc[i]:+.3f}, total {total[i]:+.3f} dB")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(13, 4.2)); x = np.arange(len(qs)); w = 0.2
ax[0].bar(x - 1.5 * w, [trans[i] for i in ii], w, color="#2A78D6", label="2 transitions (step + 50 µm gap taper)")
ax[0].bar(x - 0.5 * w, [straight[i] for i in ii], w, color="#EB6834", label="2 raised straights (0.41 mm)")
ax[0].bar(x + 0.5 * w, [arc[i] for i in ii], w, color="#9AA0AC", label="U-bend arc (0.32 mm)")
ax[0].bar(x + 1.5 * w, [total[i] for i in ii], w, color="#0E2268", label="whole bend")
ax[0].set_xticks(x); ax[0].set_xticklabels([f"{q} GHz" for q in qs]); ax[0].axhline(0, color="0.4", lw=0.8); ax[0].set_ylim(-0.7, 0.05)
ax[0].set_ylabel("Change of net power (dB)"); ax[0].grid(alpha=0.3, axis="y"); ax[0].legend(frameon=False, fontsize=9, loc="lower left")
fS, s21 = d["fS"], 20 * np.log10(abs(d["s21"]))
ax[1].plot(fS, s21, "-", color="#0E2268", lw=1.4, label="single-bend run |S$_{21}$| (touchstone)")
ax[1].axvline(79.3, color="#EB6834", ls="--", lw=1.2, label="trapped-mode dip 79.3 GHz (n ≈ 2.08 over 0.91 mm)")
ax[1].set_ylim(-3, 0); ax[1].set_xlim(0, 130); ax[1].set_xlabel("Frequency (GHz)"); ax[1].set_ylabel("|S$_{21}$| (dB)"); ax[1].grid(alpha=0.3); ax[1].legend(frameon=False, fontsize=9.5, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "single_bend_130.png"), dpi=200)
