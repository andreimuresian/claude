import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = "/home/user/claude/results/etched_slab/"
cases = [("air32", "slab_w 3.2: slab ends in the air gap", "#7f8c8d"),
         ("dip76", "slab_w 7.6: slab ends in gold (ripple dip)", "#27ae60"),
         ("pk675", "slab_w 6.75: slab ends in gold (ripple peak)", "#c0392b"),
         ("past20", "slab_w 20: slab past the gold/SiO$_2$ interface", "#1f4e79")]
fig, axs = plt.subplots(len(cases), 1, figsize=(11, 9), sharex=True)
for ax, (tag, lab, c) in zip(axs, cases):
    d = np.load(f"fcut_{tag}.npz")
    x, I = d["x"], d["mid"]
    ax.plot(x, 10*np.log10(np.maximum(I, 1e-16)), color=c, lw=1.1)
    ax.axvspan(2.1, 7.0, color="#f6c453", alpha=0.25, lw=0)
    ax.axvline(2.1, color="#b9770e", lw=0.8, ls="--"); ax.axvline(7.0, color="#1f618d", lw=0.8, ls="--")
    xs = float(d["slab_w"]) / 2
    if xs < 14: ax.axvline(xs, color="#8e44ad", lw=1.2, ls=":")
    ax.set_ylim(-110, 3); ax.grid(alpha=0.3); ax.set_ylabel(r"$|E|^2$ (dB)")
    ax.text(0.01, 0.06, f"{lab}  |  IL = {float(d['IL']):.4g} dB/cm", transform=ax.transAxes, fontsize=9,
            bbox=dict(fc="white", ec="none", alpha=0.85))
axs[0].text(2.15, -8, "gold inner edge", fontsize=8, color="#b9770e")
axs[0].text(7.05, -8, "gold/SiO$_2$ interface (x_lift)", fontsize=8, color="#1f618d")
axs[1].text(3.85, -8, "slab end", fontsize=8, color="#8e44ad")
axs[-1].set_xlabel(r"$x$ ($\mu$m), cut through the slab mid-height (shaded: slab under gold)")
axs[-1].set_xlim(0, 14)
axs[0].set_title("Fundamental-mode intensity along the slab: where the leaked wave travels and where it is reflected")
plt.tight_layout(); fig.savefig(OUT + "field_cuts_along_slab.png", dpi=140); print("ok")
