import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
plt.rcParams.update({"font.size": 13, "axes.spines.top": False, "axes.spines.right": False})
cases = [("air32", "slab_w 3.2: slab ends in the gap", "#1baf7a"),
         ("pk675", "slab_w 6.75: slab ends in the gold (peak)", "#eb6834"),
         ("dip76", "slab_w 7.6: slab ends in the gold (dip)", "#2a78d6"),
         ("past20", "slab_w 20: slab past the gold/SiO$_2$ edge", "#4a3aa7")]
fig, axs = plt.subplots(2, 2, figsize=(13.5, 6.2), sharex=True, sharey=True, gridspec_kw=dict(hspace=0.45, wspace=0.06))
for ax, (tag, lab, c) in zip(axs.flat, cases):
    d = np.load(f"{SP}fcut_{tag}.npz"); x = d["x"]
    ax.axvspan(2.1, 7.0, color="#f2c14e", alpha=0.28, lw=0)
    ax.plot(x, 10 * np.log10(np.maximum(d["mid"], 1e-16)), color=c, lw=2)
    xs = float(d["slab_w"]) / 2
    if xs < 14: ax.axvline(xs, color="#222", lw=1.3, ls=":")
    ax.set_title(f"{lab}\nIL = {float(d['IL']):.3g} dB/cm", fontsize=13, loc="left")
    ax.set_ylim(-100, 3); ax.set_xlim(0, 12); ax.grid(alpha=0.25)
for ax in axs[1]: ax.set_xlabel(r"x ($\mu$m)")
for ax in axs[:, 0]: ax.set_ylabel(r"$|E|^2$ (dB)")
axs[0, 0].text(4.55, -95, "gold on the slab region", ha="center", fontsize=11.5, color="#8a6d00")
axs[0, 0].text(7.15, -12, "x_lift", fontsize=11.5, color="#555")
fig.savefig("/tmp/deck4/fig/fieldcuts.png", dpi=170, bbox_inches="tight")
