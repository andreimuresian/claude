"""FEXT (|S41|, continuous, from the s4p) and EO crosstalk B/A (12 monitor points, from the gap fields,
50 ohm, push-pull) on one dB axis, for CORDOBA and CORDOBA HZ. Both are amplitude ratios (20 log10)."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_s4p as X, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__))
RUNS = [("CORDOBA", os.path.join(HERE, "../cordoba_8mm"), "LINEA_8MM_625UM_PITCH_CORDOBA.s4p", "#2a78d6"),
        ("CORDOBA HZ", HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_NARROW.s4p", "#eb6834")]
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False})
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
fig, a = plt.subplots(figsize=(10, 5.5))
for name, path, s4p, col in RUNS:
    net = skrf.Network(os.path.join(path, s4p))
    a.plot(net.f / 1e9, d(net.s[:, 3, 0]), color=col, lw=2, label=f"{name}: FEXT |S41| (s4p)")
    r = XF.eo_crosstalk_fields(p, XF.load_field_dir(path), X.load_pair(os.path.join(path, s4p), 8.0))
    a.plot(r["f_GHz"], d(r["X"]), "o", color=col, ms=8, mec=SURF, mew=2, label=f"{name}: EO crosstalk B/A (gap fields)")
    a.plot(r["f_GHz"], d(r["X"]), ":", color=col, lw=1.2)
a.set_xlim(0, 60); a.set_ylim(-140, -20)
a.set_xlabel("Frequency (GHz)"); a.set_ylabel("dB (amplitude ratio)")
a.set_title("8 mm pairs, 625 µm pitch: far-end crosstalk and EO crosstalk on one scale\n"
            "(50 Ω; EO: push-pull, optical n_g 2.27, exact at the 12 monitor frequencies, dotted lines only join them)",
            loc="left", color=INK, fontsize=10)
a.legend(frameon=False, loc="lower right", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_vs_fext.png"), dpi=150)
print("ok")
