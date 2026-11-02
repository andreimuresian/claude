"""EO crosstalk B/A from the gap fields (50/50 ohm, push-pull, n_g 2.27): widened CORDOBA with open vs
electric Si bottom. Points: the 12 monitor frequencies (exact for each TD model). Dashed: shape-preserving
cubic (PCHIP) through the points, a guide for the eye only: the fields say nothing between monitors."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from mzm_interconnect import parameters as P, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__))
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
runs = (("open bottom", os.path.join(HERE, "../cordoba_8mm_wide"), "#2a78d6"),
        ("electric bottom", HERE, "#eb6834"))
fig, ax = plt.subplots(figsize=(7.5, 4.2))
for lab, d, c in runs:
    r = XF.eo_crosstalk_fields(p, XF.load_field_dir(d)); f = r["f_GHz"]; y = 20 * np.log10(abs(r["X"]))
    ff = np.linspace(f[0], f[-1], 400)
    ax.plot(ff, PchipInterpolator(f, y)(ff), "--", color=c, lw=1.3)
    ax.plot(f, y, "o", color=c, ms=7, mec="white", mew=1.5, label=lab)
    print(lab, " ".join(f"{v:.1f}" for v in y))
ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk B/A (dB)")
ax.set_xlim(0, 62); ax.grid(alpha=0.3)
ax.set_title("CORDOBA 8 mm, widened (625 um): EO crosstalk from the fields", fontsize=10)
ax.legend(frameon=False, loc="lower right")
ax.text(0.01, 0.02, "dashed: interpolation through the points (guide only)", transform=ax.transAxes, fontsize=8, color="0.4")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_open_vs_electric.png"), dpi=150)
