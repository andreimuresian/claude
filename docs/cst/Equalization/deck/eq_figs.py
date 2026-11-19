"""Figures for the equalisation deck (build_equalisation.py). Source: ../analysis130/ls_extraction_130.npz."""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": "#5A606E", "axes.labelcolor": "#1A1A1A",
                     "xtick.color": "#5A606E", "ytick.color": "#5A606E", "axes.spines.top": False, "axes.spines.right": False})
NAVY, RED, GREY, ORANGE, BLUE = "#0E2268", "#F20013", "#9AA0AC", "#EB6834", "#2A78D6"
d = np.load(os.path.join(HERE, "..", "analysis130", "ls_extraction_130.npz"))
fT, F = d["fT"], d["F"]

# line: touchstone vs fields (2 x 2)
fig, ax = plt.subplots(2, 2, figsize=(8.6, 6.0), sharex=True)
P = [(d["aT"], d["aF"], "α (dB/cm)", None), (d["nT"], d["nF"], "$n_m$", (2.20, 2.40)),
     (d["ZT"].real, d["ZF"].real, "Re $Z_c$ (Ω)", (40, 46)), (d["ZT"].imag, d["ZF"].imag, "Im $Z_c$ (Ω)", (-4, 4))]
for a, (yt, yf, lab, yl) in zip(ax.flat, P):
    a.plot(fT, yt, "-", color=NAVY, lw=1.4, label="touchstone"); a.plot(F, yf, "o", ms=3.2, color=ORANGE, label="fields")
    a.set_ylabel(lab); a.grid(alpha=0.3); a.set_xlim(0, 130)
    if yl: a.set_ylim(*yl)
for a in ax[1]: a.set_xlabel("Frequency (GHz)")
ax[0, 0].legend(frameon=False, fontsize=11.5, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "line_ts_vs_fields.png"), dpi=200); plt.close(fig)

# extrapolation of the old-data fits (1 x 3), field route as the smooth reference
fig, ax = plt.subplots(1, 3, figsize=(12.6, 4.0))
P = [(d["aT"], d["aF"], 0, "α (dB/cm)", None), (d["nT"], d["nF"], 1, "$n_m$", (2.20, 2.40)), (d["ZT"].real, d["ZF"].real, 2, "Re $Z_c$ (Ω)", (40, 46))]
for a, (yt, yf, j, lab, yl) in zip(ax, P):
    a.axvspan(60, 130, color="#F1F3F8", zorder=0)
    a.plot(fT, yt, "-", color=GREY, lw=1.2, label="new touchstone")
    a.plot(F, yf, "o", ms=2.8, color=ORANGE, label="new fields")
    a.plot(fT, d["ext60"][j].real, "--", color=NAVY, lw=1.8, label="fit of 0.5–60 GHz data")
    a.plot(fT, d["ext80"][j].real, ":", color=BLUE, lw=2.0, label="fit of 0.5–80 GHz data")
    a.set_xlabel("Frequency (GHz)"); a.set_ylabel(lab); a.grid(alpha=0.3); a.set_xlim(0, 130)
    if yl: a.set_ylim(*yl)
ax[0].legend(frameon=False, fontsize=10.5, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "line_extrapolation.png"), dpi=200); plt.close(fig)
print("figures saved")
