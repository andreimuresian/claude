"""Slide 10: where the victim signal is created. Top: module chain (driver carrier traces, bond wires, launch pads,
8.75 mm line pair) with the two coupling paths. Bottom: idealised victim voltage along the line for each path and what
the light averages. Output: istanbul_img/coupling_paths.png"""
import os
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "istanbul_img")
NAVY, RED, GREY, TEAL, ORANGE, BLUE, PURPLE, MUTED = "#0E2268", "#F20013", "#9AA0AC", "#1BAA7D", "#EB6834", "#2A78D6", "#7A4BD1", "#5A606E"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11.5})
fig = plt.figure(figsize=(7.0, 5.4)); gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1], hspace=0.45, wspace=0.3)

# module chain
a = fig.add_subplot(gs[0, :]); a.set_xlim(0, 100); a.set_ylim(0, 42); a.axis("off")
def blk(x, w, t, fc):
    a.add_patch(FancyBboxPatch((x, 8), w, 24, boxstyle="round,pad=0.4", fc=fc, ec="none")); a.text(x + w / 2, 4.5, t, ha="center", fontsize=10, color=MUTED)
blk(1, 15, "driver carrier\ntraces", "#ECEFF5"); blk(18, 9, "bond\nwires", "#ECEFF5"); blk(29, 7, "launch\npads", "#ECEFF5"); blk(38, 60, "line pair, 8.75 mm", "#ECEFF5")
for y, lab, c in ((26, "A (aggressor)", NAVY), (14, "B (victim)", ORANGE)):
    a.plot([2, 97], [y, y], color=c, lw=2.5); a.text(97.5, y, lab, va="center", fontsize=10, color=c, weight="bold")
for x in np.arange(42, 96, 6):
    a.annotate("", xy=(x, 15.5), xytext=(x, 24.5), arrowprops=dict(arrowstyle="->", color=TEAL, lw=1.3))
a.text(68, 35.5, "(1) coupling along the line: all runs", ha="center", fontsize=10.5, color=TEAL, weight="bold")
a.annotate("", xy=(17, 15.5), xytext=(17, 24.5), arrowprops=dict(arrowstyle="->", color=PURPLE, lw=3.5))
a.annotate("", xy=(23, 15.5), xytext=(23, 24.5), arrowprops=dict(arrowstyle="->", color=PURPLE, lw=3.5))
a.text(14, 37, "(2) coupling before\nthe line: run (d)", ha="center", va="center", fontsize=10.5, color=PURPLE, weight="bold")

# idealised victim profiles
z = np.linspace(0, 1, 200)
for k, (v, c, t, msg) in enumerate(((z, TEAL, "(1) victim builds up along z", "light average ≈ ½ end value\nEO ≈ FEXT − 6 dB"),
                                    (np.ones_like(z), PURPLE, "(2) victim present from the input", "light average ≈ end value\nEO ≈ FEXT"))):
    b = fig.add_subplot(gs[1, k]); b.plot(z, v, color=c, lw=2.5); b.axhline(np.mean(v), color=c, ls=":", lw=1.5)
    b.set_xlim(0, 1); b.set_ylim(0, 1.35); b.set_xticks([0, 1]); b.set_xticklabels(["input", "far end"]); b.set_yticks([])
    b.set_ylabel("|V$_B$(z)|"); b.set_title(t, fontsize=11, color=c, weight="bold"); b.spines[["top", "right"]].set_visible(False)
    b.text(0.03 if k == 0 else 0.5, 1.17, msg, fontsize=10, color="#1A1A1A", ha="left" if k == 0 else "center", va="center")
fig.savefig(os.path.join(OUT, "coupling_paths.png"), dpi=200, bbox_inches="tight", pad_inches=0.05); plt.close(fig)
