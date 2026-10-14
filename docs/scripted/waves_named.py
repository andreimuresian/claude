"""Every wave of SRC -> EL_1 -> LOAD, with its name (figure for the far-end derivation)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, ax = plt.subplots(figsize=(13, 5.2)); ax.set_xlim(0, 13); ax.set_ylim(0, 5.2); ax.axis("off")
def box(x, y, w, h, t, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", fc=fc, ec="k", lw=1.4))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=11)
def arr(x0, x1, y, c, lab, above=True):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=18, lw=2.3, color=c))
    ax.text((x0 + x1)/2, y + (0.15 if above else -0.42), lab, ha="center", color=c, fontsize=13, weight="bold")
box(0.1, 2.0, 1.5, 1.4, "Driver\nmatched 50 Ω", "#ddd")
box(2.6, 2.0, 1.9, 1.4, "SRC\nT_f , Γ_s", "#cfe2f3")
box(6.0, 2.0, 2.6, 1.4, "EL_1\nS11, S21\n(line, length L)", "#d9ead3")
box(10.1, 2.0, 1.6, 1.4, "LOAD\nΓ_L", "#f4cccc")
arr(1.6, 2.6, 3.05, "#1565c0", "a_drv")
arr(4.5, 6.0, 3.05, "#1565c0", "a1")
arr(6.0, 4.5, 2.35, "#c62828", "b1", False)
arr(8.6, 10.1, 3.05, "#1565c0", "b2")
arr(10.1, 8.6, 2.35, "#c62828", "a2", False)
for x, n in [(5.25, "junction J1\nV(0) = a1 + b1"), (9.35, "junction J2\nV(L) = a2 + b2")]:
    ax.plot([x, x], [1.55, 3.85], ":", c="gray"); ax.text(x, 4.0, n, ha="center", fontsize=10)
ax.text(6.5, 0.95, "Names are seen from EL_1:  a = wave going INTO EL_1,  b = wave coming OUT of EL_1.   Port 1 = left end (z = 0),  port 2 = right end (z = L).",
        ha="center", fontsize=10)
ax.text(6.5, 0.45, "Blue: travelling towards the load.   Red: travelling back towards the driver.", ha="center", fontsize=10)
plt.savefig("waves_named.png", dpi=140, bbox_inches="tight")
