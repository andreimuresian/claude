import io, contextlib, matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.show = lambda *a, **k: plt.close("all")
src0 = open("/home/user/claude/cells/cell0_etched.py").read().replace("SLAB_W = 3.2 ", "SLAB_W = 20.0 ")
G = {}
for flag in (False, True):
    g = {"__name__": "__main__"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(src0.replace("GOLD_OUT = False", f"GOLD_OUT = {flag}"), g)
    G[flag] = g
fig, axs = plt.subplots(2, 1, figsize=(15, 7.6))
for ax, flag in zip(axs, (False, True)):
    g = G[flag]; g["_draw_materials"](ax)
    ax.set_xlim(-37.5, 37.5); ax.set_ylim(-1.6, 8.2); ax.set_aspect("equal")
    ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)")
    ax.annotate("", (-10, -0.9), (10, -0.9), arrowprops=dict(arrowstyle="<->", lw=1))
    ax.text(-4, -1.0, "slab_w = 20 µm (example)", ha="center", va="top", fontsize=9)
axs[0].set_title("Previous etched-slab geometry: SiO₂ lift reaches down to the BOX beyond x_lift = 7 µm → gold/SiO₂ edge on top of the slab", fontsize=10.5)
axs[1].set_title("GOLD_OUT = True (sweep 3): gold at slab level out to the pad end (x = 32.1 µm); SiO₂ lift kept only between block and pad", fontsize=10.5)
for ax in axs:
    ax.annotate("x_lift = 7 µm (column outer edge)", (7, 0.14), (12.5, -1.3), fontsize=9, color="#1f4e79", arrowprops=dict(arrowstyle="->", color="#1f4e79", lw=0.8))
axs[0].annotate("gold / SiO₂ edge\non the slab", (7, 0.28), (13, 1.2), fontsize=9, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
axs[1].annotate("slab end wrapped in gold\n(the only mirror)", (10, 0.14), (14, 1.0), fontsize=9, color="#c0392b",
                arrowprops=dict(arrowstyle="->", color="#c0392b", lw=0.9))
axs[1].annotate("lower gold runs to x = 32.1", (32.1, 1.0), (22, 1.0), fontsize=9, va="center",
                arrowprops=dict(arrowstyle="->", lw=0.8))
axs[1].text(20, 3.07, "SiO₂ lift (kept)", ha="center", va="center", fontsize=9, color="white")
plt.tight_layout(); fig.savefig("/home/user/claude/results/three_sweeps/sweep3_cross_section_gold_at_slab_level.png", dpi=140)
