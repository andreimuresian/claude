"""One graph: electrical |S21| of the full equaliser (touchstone), EO response of the full equaliser (+ + -, fields),
EO response of a standalone 2.70 mm line (alpha, n_m from the L+S fields, Zc from the L+S touchstone, L+S port blocks).
EO curves normalised to their own 1 GHz value. Inputs: full_eq_eo_130.csv, standalone_line_eo_130.csv. Output: equaliser_summary_130.png"""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
a = np.loadtxt(os.path.join(HERE, "full_eq_eo_130.csv"), delimiter=",", skiprows=1)
b = np.loadtxt(os.path.join(HERE, "standalone_line_eo_130.csv"), delimiter=",", skiprows=1)
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(a[:, 0], a[:, 1], "-", color="#0E2268", lw=1.8, label="Full equaliser, electrical |S$_{21}$| (touchstone)")
ax.plot(a[:, 0], a[:, 4], "o-", ms=3, lw=1.2, color="#EB6834", label="Full equaliser, EO (2.70 + 1.44 + 1.44 mm, + + −)")
ax.plot(b[:, 0], b[:, 1], "-", color="#2A78D6", lw=1.8, label="Standalone 2.70 mm line, EO (L+S line model)")
ax.axhline(-3, color="0.4", lw=0.8, ls=":")
ax.set_xlim(0, 130); ax.set_ylim(-5, 0); ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("dB (EO re 1 GHz)"); ax.grid(alpha=0.3)
ax.legend(frameon=False, fontsize=10.5, loc="lower left")
ax.set_title("50 Ω ports, n$_g$ = 2.27, light matched to the RF in the bends", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "equaliser_summary_130.png"), dpi=200)
