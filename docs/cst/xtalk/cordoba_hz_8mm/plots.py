"""Comparison plots: CORDOBA (35 / 49.85 um) vs CORDOBA HZ (10 / 25 um), 8 mm. Model-free S-parameters
from the s4p files; EO crosstalk from the CST gap fields at the 12 monitor frequencies (50 ohm, push-pull)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_s4p as X, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = {"CORDOBA (signal 35 µm, grounds 49.85 µm)": (os.path.join(HERE, "../cordoba_8mm"), "LINEA_8MM_625UM_PITCH_CORDOBA.s4p"),
        "CORDOBA HZ (signal 10 µm, grounds 25 µm)": (HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_NARROW.s4p")}
COL = ["#2a78d6", "#eb6834"]; INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#e4e3de"; SURF = "#fcfcfb"
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False})
nets = {k: skrf.Network(os.path.join(v[0], v[1])) for k, v in RUNS.items()}
fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
panels = [((0, 0), "S11 (dB)", 0, 0), ((0, 1), "S21 (dB)", 1, 0), ((1, 0), "NEXT = S31 (dB)", 2, 0), ((1, 1), "FEXT = S41 (dB)", 3, 0)]
for (r, c), title, i, j in panels:
    a = axs[r, c]
    for n, (k, net) in enumerate(nets.items()):
        a.plot(net.f / 1e9, d(net.s[:, i, j]), color=COL[n], lw=2, label=k)
    a.set_title(title, loc="left", color=INK, fontsize=11)
    a.set_xlim(0, 60)
for a in axs[1]: a.set_xlabel("Frequency (GHz)")
axs[1, 1].set_ylim(-140, -20); axs[1, 0].set_ylim(-100, -20)
axs[0, 0].legend(frameon=False, loc="lower right")
fig.suptitle("8 mm pairs, 625 µm pitch: S-parameters (ports 1 A near, 2 A far, 3 B near, 4 B far; 50 Ω)", color=INK, x=0.01, ha="left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "compare_sparams.png"), dpi=150)

p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
fig, a = plt.subplots(figsize=(9, 5))
for n, (k, (path, s4p)) in enumerate(RUNS.items()):
    r = XF.eo_crosstalk_fields(p, XF.load_field_dir(path), X.load_pair(os.path.join(path, s4p), 8.0))
    y = d(r["X"])
    a.plot(r["f_GHz"], y, "-o", color=COL[n], lw=2, ms=8, mec=SURF, mew=2, label=k)
    a.annotate(f"{y[-1]:.1f} dB", (r["f_GHz"][-1], y[-1]), xytext=(8, 0), textcoords="offset points", va="center", color=INK, fontsize=9)
a.set_xlim(0, 66); a.set_xlabel("Frequency (GHz)"); a.set_ylabel("EO crosstalk B/A (dB)")
a.set_title("EO crosstalk from the CST gap fields, 12 monitor frequencies\n(50 Ω source and load, push-pull, optical n_g 2.27; points are exact for the TD models, lines only join them)",
            loc="left", color=INK, fontsize=10)
a.legend(frameon=False, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "compare_eo_xtalk.png"), dpi=150)
print("ok")
