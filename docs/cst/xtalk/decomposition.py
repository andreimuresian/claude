"""Exciting line A alone = 1/2 (pair even mode) + 1/2 (pair odd mode)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
fig = plt.figure(figsize=(13, 8.2))
ax = fig.add_axes([0, 0.42, 1, 0.58]); ax.set_xlim(0, 13); ax.set_ylim(0, 5); ax.axis("off")
def cpw_pair(x0, va, vb, title):
    # cross-section: G S_A G  G S_B G on a substrate (schematic)
    ax.add_patch(plt.Rectangle((x0, 1.2), 3.4, 0.5, fc="#f3e9d2", ec="none"))
    for xg in (0.0, 1.0, 2.0, 3.0):
        ax.add_patch(plt.Rectangle((x0 + xg, 1.7), 0.4, 0.12, fc="#999", ec="k", lw=0.6))
    for xs, v, n in ((0.6, va, "A"), (2.6, vb, "B")):
        c = "#c62828" if v > 0 else ("#1565c0" if v < 0 else "#bbb")
        ax.add_patch(plt.Rectangle((x0 + xs, 1.7), 0.2, 0.12, fc=c, ec="k", lw=0.6))
        ax.text(x0 + xs + 0.1, 2.0, f"{v:+.1f}" if v else "0", ha="center", fontsize=12, color=c, weight="bold")
        ax.text(x0 + xs + 0.1, 0.95, n, ha="center", fontsize=11)
    ax.text(x0 + 1.7, 2.75, title, ha="center", fontsize=11.5)
cpw_pair(0.2, 1, 0, "drive line A only\n(what CST does: A excited, B victim)")
ax.text(3.95, 1.75, "=", fontsize=26, ha="center")
cpw_pair(4.6, 0.5, 0.5, "½ × pair EVEN mode\nsame voltage on A and B")
ax.text(8.35, 1.75, "+", fontsize=26, ha="center")
cpw_pair(9.0, 0.5, -0.5, "½ × pair ODD mode\nopposite voltages on A and B")
ax.text(6.5, 4.4, "Each line keeps its own CPW (symmetric, quasi-TEM) mode. 'Even/odd' describes the PAIR: the relative sign between line A and line B.",
        ha="center", fontsize=11, weight="bold")
ax.text(6.5, 0.25, "Grey: grounds.  Red/blue: signal conductors at +/− voltage.  Superposition: (1, 0) = ½(1, 1) + ½(1, −1).",
        ha="center", fontsize=10)
# beating along z (exaggerated mode difference, lossless)
bx = fig.add_axes([0.07, 0.07, 0.86, 0.30])
z = np.linspace(0, 1, 600); dphi = 2*np.pi*1.0   # 1 full beat over the plot, illustrative
VA = 0.5*(1 + np.exp(-1j*dphi*z)); VB = 0.5*(1 - np.exp(-1j*dphi*z))
bx.plot(z, abs(VA), lw=2, label="|V on line A|  (aggressor)")
bx.plot(z, abs(VB), lw=2, label="|V on line B|  (victim)")
bx.set_xlabel("position along the lines (illustrative: mode difference exaggerated)")
bx.set_ylabel("amplitude"); bx.legend(loc="center right"); bx.grid(alpha=0.3)
bx.set_title("If the two pair modes travel at different speeds, their sum drifts from (1,0) towards (0,1): far-end crosstalk grows with length", fontsize=10.5)
plt.savefig("decomposition.png", dpi=140)
