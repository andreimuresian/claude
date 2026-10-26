import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
nb = json.load(open("/home/user/claude/VPI_RF_Cordoba_buffer_ALD.ipynb")); s0 = "".join(nb["cells"][0]["source"])
s0 = s0[:s0.index("# ---- cross-section (materials, from the mesh)")]
cases = [(0, 0, "baseline"), (0.2, 0, "200 nm SiO₂ buffer"), (0, 0.04, "40 nm ALD"), (0.2, 0.04, "buffer + ALD")]
fig, axs = plt.subplots(2, 4, figsize=(20, 7))
for j, (b, t, lab) in enumerate(cases):
    s = re.sub(r"\nBUFFER_H  = [0-9.]+", f"\nBUFFER_H  = {b}", s0); s = re.sub(r"\nT_ALD     = [0-9.]+", f"\nT_ALD     = {t}", s)
    g = {}; exec(s, g); m = g["mesh"]; mk = list(g["MATERIALS"]); mi = np.array([mk.index(q) for q in g["mat_of_el"]], float)
    cm = ListedColormap([g["MATERIALS"][q]["color"] for q in mk])
    for i, (xl, yl) in enumerate((((g["x_sig"] - 1.5, g["x_gi"] + 1.5), (-0.6, g["y_el"] + 1.2)),
                                  ((g["x_gi"] - 0.45, g["x_gi"] + 0.45), (g["y_b"] - 0.35, g["y_b"] + 0.4)))):
        ax = axs[i, j]; ax.tripcolor(m.p[0], m.p[1], m.t.T, facecolors=mi, cmap=cm, vmin=-0.5, vmax=len(mk) - 0.5)
        if i == 1: m.draw(ax=ax, color="k", lw=0.12)
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal")
    axs[0, j].set_title(f"{lab}  ({m.nelements} triangles)")
axs[1, 0].set_ylabel("zoom: ground inner corner (with mesh)")
fig.suptitle("Cordoba RF cross-sections (right gap; one of the two arms), 60 GHz: gold orange, LN green, SiO₂ cyan, ALD pink")
plt.tight_layout(); plt.savefig("rf_cross_sections.png", dpi=110); print("ok")
