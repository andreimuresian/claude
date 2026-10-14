"""Why near-end crosstalk adds kC and kL while far-end crosstalk subtracts them."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
fig, ax = plt.subplots(figsize=(13, 6.4)); ax.set_xlim(0, 13); ax.set_ylim(0, 6.4); ax.axis("off")
def arr(p, q, c, lw=2.4, ms=18):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, lw=lw, color=c))
yA, yB = 4.6, 2.4
ax.plot([1, 12], [yA, yA], "k", lw=3); ax.plot([1, 12], [yB, yB], "k", lw=3)
ax.text(0.9, yA, "aggressor A", ha="right", va="center", fontsize=11)
ax.text(0.9, yB, "victim B", ha="right", va="center", fontsize=11)
ax.text(1, 1.55, "NEAR END\n(source side)", ha="center", fontsize=10.5, weight="bold")
ax.text(12, 1.55, "FAR END", ha="center", fontsize=10.5, weight="bold")
# wavefront on A
ax.add_patch(plt.Rectangle((6.0, yA - 0.15), 0.9, 0.3, color="#ffb300"))
arr((6.9, yA + 0.45), (8.4, yA + 0.45), "k"); ax.text(7.6, yA + 0.65, "signal edge travelling →", ha="center", fontsize=10)
ax.text(6.45, yA - 0.55, "dV/dt, dI/dt", ha="center", fontsize=9.5)
# capacitive: current into B, splits both ways, same sign
arr((6.45, yA - 0.85), (6.45, yB + 0.25), "#c62828")
ax.text(6.6, 3.2, "C_m·dV/dt: injected current\nsplits both ways, + at each end", color="#c62828", fontsize=10.5)
arr((6.3, yB - 0.25), (4.3, yB - 0.25), "#c62828"); arr((6.6, yB - 0.25), (8.6, yB - 0.25), "#c62828")
ax.text(5.3, yB - 0.6, "+½", color="#c62828", ha="center", fontsize=12, weight="bold")
ax.text(7.6, yB - 0.6, "+½", color="#c62828", ha="center", fontsize=12, weight="bold")
# inductive: induced current flows backwards (Lenz)
arr((8.6, yB + 0.3), (4.3, yB + 0.3), "#1565c0")
ax.text(8.9, yB + 0.45, "L_m·dI/dt: induced current opposes A's (Lenz),\nso it flows backwards: + at near end, − at far end", color="#1565c0", ha="left", fontsize=9.5)
ax.text(4.0, yB - 0.6, "+½", color="#1565c0", ha="center", fontsize=12, weight="bold")
ax.text(9.0, yB - 0.6, "−½", color="#1565c0", ha="center", fontsize=12, weight="bold")
ax.text(3.2, 0.55, "near end:  capacitive + inductive ADD\nNEXT ∝ (k_C + k_L)", ha="center", fontsize=11.5,
        bbox=dict(fc="#e8f5e9", ec="#2e7d32"))
ax.text(9.8, 0.55, "far end:  capacitive − inductive SUBTRACT\nFEXT ∝ (k_C − k_L) × length", ha="center", fontsize=11.5,
        bbox=dict(fc="#fdecea", ec="#c62828"))
ax.text(6.5, 6.05, "Each slice of the aggressor's edge couples into the victim through C_m (electric field) and L_m (magnetic field)",
        ha="center", fontsize=11.5, weight="bold")
ax.text(6.5, 5.65, "k_C = C_m/(C_g + C_m),  k_L = L_m/L_s.  In a homogeneous dielectric k_C = k_L, so far-end crosstalk vanishes.",
        ha="center", fontsize=10.5)
plt.savefig("mechanism.png", dpi=140, bbox_inches="tight")
