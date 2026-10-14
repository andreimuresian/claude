"""Clean drawing of the scripted electrode as built today (straight build)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
fig, ax = plt.subplots(figsize=(12, 5.6)); ax.set_xlim(0, 12); ax.set_ylim(0, 5.6); ax.axis("off")
def box(x, y, w, h, t, fc, fs=10):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec="k", lw=1.2))
    ax.text(x+w/2, y+h/2, t, ha="center", va="center", fontsize=fs)
def wire(p, q, c="k", ls="-"):
    ax.plot([p[0], q[0]], [p[1], q[1]], c=c, lw=1.8, ls=ls)
ax.add_patch(FancyBboxPatch((1.6, 0.55), 6.9, 4.5, boxstyle="round,pad=0.02", fc="#f4f7fb", ec="#1f4e79", lw=2, ls="--"))
ax.text(1.7, 4.8, "Compound 'ELECTRODE'  —  its property 'scattering data analysis' = on", fontsize=10.5, color="#1f4e79", weight="bold")
RF = 3.7
box(0.05, RF-0.4, 1.15, 0.8, "Driver\n(ENA / NRZ)", "#ddd")
box(1.4, RF-0.22, 0.4, 0.44, "R", "#fff2b3", 9)
box(2.3, RF-0.5, 1.2, 1.0, "SRC\nport 1 | port 2\nZs", "#cfe2f3", 9)
box(4.1, RF-0.5, 1.9, 1.0, "EL_1  (TL line)\nport 1 | port 2", "#d9ead3", 9)
box(6.6, RF-0.5, 1.2, 1.0, "LOAD\nport 1\nZt", "#f4cccc", 9)
for a, b in [(1.2, 1.4), (1.8, 2.3), (3.5, 4.1), (6.0, 6.6)]:
    wire((a, RF), (b, RF))
ax.text(5.05, RF+0.75, "bidirectional ports: waves travel both ways", ha="center", fontsize=9, style="italic")
outs = [(4.5, 2.5, "modulation  (arm 1, n_g1)", "#2e7d32", "OM arm 1   φ₁ = π·V_mod1/Vπ"),
        (5.05, 1.75, "modulation 2  (arm 2, n_g2)", "#7b1fa2", "OM arm 2   φ₂ = π·V_mod2/Vπ"),
        (5.6, 1.0, "far end  (V across Zt)", "#c62828", "ENA input 2  or  EYE_2")]
for x0, y, lab, c, dst in outs:
    wire((x0, RF-0.5), (x0, y), c); wire((x0, y), (8.3, y), c)
    ax.text(x0+0.08, y+0.08, lab, color=c, fontsize=9)
    box(8.3, y-0.22, 0.4, 0.44, "R", "#fff2b3", 9)
    wire((8.7, y), (9.2, y), c)
    box(9.2, y-0.3, 2.7, 0.6, dst, "#ffffff", 9)
ax.text(0.05, 0.15, "Output ports (coloured) are one-way probes: they read the line and do not load it.   "
        "R = relay: the inside end of a Compound pin, no physics.\nBent electrode: EL_1 is replaced by one 'TL electrode' element (sections + bends inside), same ports.",
        fontsize=8.5)
plt.savefig("docs/scripted/circuit.png", dpi=150, bbox_inches="tight")
