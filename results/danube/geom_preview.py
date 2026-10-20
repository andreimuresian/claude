"""Geometry-only preview of the 4 Danube cross-sections (no mesh): validity over the whole
sweep + figures.  Usage: geom_preview.py"""
import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Danube.ipynb"))
s = "".join(nb["cells"][0]["source"]); s = s[:s.index("polygons, Y_TOP = build_polygons()")]
CASES = [(False, 0.0, "outside of tee, standard"), (True, 0.0, "inside of tee, standard"),
         (False, 0.7, "outside of tee, over-etched 700 nm"), (True, 0.7, "inside of tee, over-etched 700 nm")]
def build(tee, oe, w):
    src = re.sub(r"\nTEE = \w+", f"\nTEE = {tee}", s); src = re.sub(r"\nOE = [0-9.]+", f"\nOE = {oe}", src)
    src = re.sub(r"\nSLAB_W = [0-9.]+", f"\nSLAB_W = {w}", src)
    g = {}; exec(src, g); P, yt = g["build_polygons"]()
    names = list(P); tot = sum(p.area for p in P.values())
    assert abs(tot - g["DEV_W"] * (g["BOX_H"] + yt)) < 1e-7, ("tiling", tee, oe, w)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert P[names[i]].intersection(P[names[j]]).area < 1e-10, ("overlap", names[i], names[j], tee, oe, w)
    return g, P
W = np.round(np.arange(5.15, 12.1501, 0.1), 2)
for tee, oe, lab in CASES:
    for w in W: build(tee, oe, w)
    print("valid over the sweep:", lab)
COL = {"LN": "#8b95a1", "SiO2": "#5aa9f0", "air": "#ffffff", "Au_sig": "#f6c453", "Au_gnd": "#e5a92e"}
def draw(ax, g, P, xl, yl):
    for n, p in P.items():
        m = g["material_of"](n)
        for part in getattr(p, "geoms", [p]):
            ax.add_patch(plt.Polygon(np.asarray(part.exterior.coords), fc=COL[m], ec="none"))
    from shapely.ops import unary_union
    by = {}
    for n, p in P.items(): by.setdefault(g["material_of"](n), []).append(p)
    for m, v in by.items():
        u = unary_union(v)
        for part in getattr(u, "geoms", [u]):
            for r in [part.exterior, *part.interiors]:
                xy = np.asarray(r.coords); ax.plot(xy[:, 0], xy[:, 1], "k", lw=0.5)
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal")
leg = [mpatches.Patch(color=c, label=l) for l, c in [("LN", COL["LN"]), ("SiO2", COL["SiO2"]), ("Au signal", COL["Au_sig"]), ("Au ground", COL["Au_gnd"])]]
# Fig 1: the 4 cases at nominal, zoom + full width
fig, axs = plt.subplots(4, 1, figsize=(14, 13))
for ax, (tee, oe, lab) in zip(axs, CASES):
    g, P = build(tee, oe, 10.15); draw(ax, g, P, (-8.5, g["X_R"]), (-1.3, 2.7))
    ax.set_title(f"{lab}  |  slab top 10.15 µm, gap 4.15 µm  (right edge = signal centre / symmetry plane)", fontsize=10)
    ax.axvline(0, c="grey", lw=0.4, ls=":")
axs[0].legend(handles=leg, loc="upper left", fontsize=8, ncol=4); axs[-1].set_xlabel("x (µm)")
plt.tight_layout(); plt.savefig("danube_4cases_nominal.png", dpi=120); plt.close()
fig, axs = plt.subplots(4, 1, figsize=(14, 7))
for ax, (tee, oe, lab) in zip(axs, CASES):
    g, P = build(tee, oe, 10.15); draw(ax, g, P, (g["X_L"], g["X_R"]), (-2, 3)); ax.set_title(lab + " (full domain)", fontsize=9)
plt.tight_layout(); plt.savefig("danube_4cases_full_domain.png", dpi=120); plt.close()
# Fig 2: slab-width series per case
WS = [5.15, 7.15, 8.15, 10.15, 12.15]
for k, (tee, oe, lab) in enumerate(CASES):
    fig, axs = plt.subplots(len(WS), 1, figsize=(13, 2.3 * len(WS)))
    for ax, w in zip(axs, WS):
        g, P = build(tee, oe, w); draw(ax, g, P, (-8.5, g["X_R"]), (-1.3, 2.7))
        ax.set_title(f"{lab} | slab top width {w:.2f} µm (edge {(w-4.15)/2:+.2f} µm past each gap edge)", fontsize=9)
    plt.tight_layout(); plt.savefig(f"danube_case{k+1}_slab_series.png", dpi=110); plt.close()
print("figures done")
