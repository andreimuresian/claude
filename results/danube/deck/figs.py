import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.ops import unary_union
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Danube.ipynb"))
s = "".join(nb["cells"][0]["source"]); s = s[:s.index("polygons, Y_TOP = build_polygons()")]
def build(tee, oe, w):
    src = re.sub(r"\nTEE = \w+", f"\nTEE = {tee}", s); src = re.sub(r"\nOE = [0-9.]+", f"\nOE = {oe}", src)
    src = re.sub(r"\nSLAB_W = [0-9.]+", f"\nSLAB_W = {w}", src); g = {}; exec(src, g); return g, g["build_polygons"]()[0]
COL = {"LN": "#8b95a1", "SiO2": "#a9cdf2", "air": "#ffffff", "Au_sig": "#f2c14e", "Au_gnd": "#e0a52b"}
def draw(ax, tee, oe, w, xl=(-8.5, 7.075), yl=(-1.2, 2.6)):
    g, P = build(tee, oe, w); by = {}
    for n, p in P.items(): by.setdefault(g["material_of"](n), []).append(p)
    for m, v in by.items():
        u = unary_union(v)
        for part in getattr(u, "geoms", [u]):
            ax.add_patch(plt.Polygon(np.asarray(part.exterior.coords), fc=COL[m], ec="#333", lw=0.6))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values(): sp.set_visible(False)
    for x, y, t in ((4.5, 1.1, "signal"), (-3.075 if tee else -6.5, 1.0 if tee else 1.1, "ground")):
        if xl[0] + 0.5 < x < xl[1] - 0.5: ax.text(x, y, t, fontsize=10, ha="center")
T = [((False, 0.0), "1  Outside of tee · standard"), ((True, 0.0), "2  Inside of tee · standard"),
     ((False, 0.7), "3  Outside of tee · over-etched"), ((True, 0.7), "4  Inside of tee · over-etched")]
fig, axs = plt.subplots(2, 2, figsize=(14, 5.6))
for ax, ((tee, oe), lab) in zip(axs.flat, T):
    draw(ax, tee, oe, 10.15); ax.set_title(lab, fontsize=13, loc="left", color="#1f4e79", fontweight="bold")
plt.tight_layout(); plt.savefig("xs_2x2.png", dpi=170, bbox_inches="tight"); plt.close()
# inside of tee: slab end under the stub vs beyond the stub
fig, axs = plt.subplots(1, 2, figsize=(14, 3.0))
for ax, w, lab in ((axs[0], 7.15, "slab 7.15 µm: slab end wrapped by the stub"), (axs[1], 9.15, "slab 9.15 µm: slab continues past the stub")):
    draw(ax, True, 0.0, w, xl=(-6.5, 1.5), yl=(-0.6, 1.8)); ax.set_title(lab, fontsize=12, loc="left")
plt.tight_layout(); plt.savefig("tee_transition.png", dpi=170, bbox_inches="tight"); plt.close()
# over-etch at narrow vs nominal slab
fig, axs = plt.subplots(1, 2, figsize=(14, 3.0))
for ax, w, lab in ((axs[0], 5.15, "slab 5.15 µm: recess gold 0.6 µm from the gap edge"), (axs[1], 10.15, "slab 10.15 µm: recess gold 3.1 µm from the gap edge")):
    draw(ax, False, 0.7, w, xl=(-1.5, 7.075), yl=(-1.2, 2.6)); ax.set_title(lab, fontsize=12, loc="left")
plt.tight_layout(); plt.savefig("oe_narrow_vs_nominal.png", dpi=170, bbox_inches="tight"); plt.close()
print("ok")
