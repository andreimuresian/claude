import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.ops import unary_union
nb = json.load(open("/home/user/claude/VPI_RF_Cordoba_buffer_ALD.ipynb")); s = "".join(nb["cells"][0]["source"])
s = s[:s.index("BASE_RES = {")]
s = re.sub(r"\nBUFFER_H  = [0-9.]+", "\nBUFFER_H  = 0.0", s); s = re.sub(r"\nT_ALD     = [0-9.]+", "\nT_ALD     = 0.04", s)
g = {}; exec(s, g); P = g["build_polygons"]()
COL = {"Au": "#f2c14e", "LN": "#8b95a1", "SiO2": "#a9cdf2", "Al2O3": "#e0218a", "Si": "#bdbdbd", "air": "#ffffff"}
by = {}
for n, p in P.items(): by.setdefault(g["mat_of_region"](n), []).append(p)
U = {m: unary_union(v) for m, v in by.items()}
def draw(ax, xl, yl):
    for m in ("Si", "SiO2", "LN", "air", "Au", "Al2O3"):
        if m not in U or m == "air": continue
        for q in getattr(U[m], "geoms", [U[m]]):
            ax.add_patch(plt.Polygon(np.asarray(q.exterior.coords), fc=COL[m], ec="#333" if m != "Al2O3" else "none", lw=0.5))
            for r in q.interiors: ax.add_patch(plt.Polygon(np.asarray(r.coords), fc="white", ec="#333", lw=0.5))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.set_xlabel("x (µm)")
xs, xgi, xgo, yel = g["x_sig"], g["x_gi"], g["x_go"], g["y_el"]
fig = plt.figure(figsize=(16, 8.2)); gs = fig.add_gridspec(2, 2, height_ratios=[0.55, 1.25])
a = fig.add_subplot(gs[0, :]); draw(a, (-xgo - 6, xgo + 6), (-4.7, 5))
a.set_title("True 1:1 scale — Cordoba push-pull (GSG), full electrodes: signal 35 µm, gaps 4.15 µm, grounds 49.85 µm, gold 2 µm")
for x0, x1, t in ((-xs, xs, "signal"), (xgi, xgo, "ground"), (-xgo, -xgi, "ground")): a.text((x0 + x1) / 2, yel + 0.8, t, ha="center")
b = fig.add_subplot(gs[1, 0]); draw(b, (xs - 1.0, xgi + 1.0), (-0.6, yel + 0.8))
b.set_title("One gap: rib 1.0 µm (540/270 nm LN), SiO₂ cap 2.0 × 1.4 µm, 40 nm ALD (pink)")
for x0, t in ((xs - 0.9, "signal"), (xgi + 0.1, "ground")): b.text(x0, 1.3, t)
b.annotate("", (xs, yel + 0.45), (xgi, yel + 0.45), arrowprops=dict(arrowstyle="<->")); b.text((xs + xgi) / 2, yel + 0.55, "gap 4.15 µm", ha="center")
c = fig.add_subplot(gs[1, 1]); draw(c, (xgi - 0.45, xgi + 0.25), (g["slab_h"] - 0.12, g["slab_h"] + 0.4))
c.set_title("Zoom: ground inner corner — ALD on the gold wall and on the LN slab")
c.annotate("40 nm ALD", (xgi - 0.02, g["slab_h"] + 0.25), (xgi - 0.4, g["slab_h"] + 0.33), arrowprops=dict(arrowstyle="->"), fontsize=10)
c.text(xgi + 0.05, g["slab_h"] + 0.15, "gold"); c.text(xgi - 0.4, g["slab_h"] - 0.08, "LN slab")
from matplotlib.patches import Patch
a.legend(handles=[Patch(color=COL[m], label=l) for m, l in (("Au", "gold"), ("LN", "LN"), ("SiO₂" and "SiO2", "SiO₂"), ("Al2O3", "ALD Al₂O₃ 40 nm"))], loc="upper center", bbox_to_anchor=(0.5, -0.35), ncol=4, fontsize=9)
plt.tight_layout(); plt.savefig("cordoba_ALD40_sketch.png", dpi=150); print("ok")
