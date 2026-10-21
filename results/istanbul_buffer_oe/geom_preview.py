import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from shapely.ops import unary_union
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_buffer_overetch.ipynb"))
s = "".join(nb["cells"][0]["source"]); s = s[:s.index("polygons, Y_TOP = build_polygons()")]
def build(oe, L):
    src = re.sub(r"\nOE = [0-9.]+", f"\nOE = {oe}", s); src = re.sub(r"\nBUFFER_L = [0-9.]+", f"\nBUFFER_L = {L}", src)
    g = {}; exec(src, g); P, yt = g["build_polygons"]()
    names = list(P); assert abs(sum(p.area for p in P.values()) - g["DEV_W"] * (g["BOX_H"] + yt)) < 1e-7, ("tiling", oe, L)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            assert P[names[i]].intersection(P[names[j]]).area < 1e-10, ("overlap", names[i], names[j], oe, L)
    pts = np.array([c for v in P.values() for part in getattr(v, "geoms", [v]) for r in [part.exterior, *part.interiors] for c in r.coords])
    from scipy.spatial import cKDTree
    d, _ = cKDTree(pts).query(pts, k=2); nd = int(((d[:, 1] > 0) & (d[:, 1] < 1e-6)).sum())
    assert nd == 0, ("near-duplicate vertices", oe, L, nd)
    return g, P
COL = {"LN": "#8b95a1", "SiO2": "#5aa9f0", "air": "#ffffff", "Au_sig": "#f6c453", "Au_gnd": "#e5a92e"}
def draw(ax, g, P, xl, yl):
    by = {}
    for n, p in P.items(): by.setdefault(g["material_of"](n), []).append(p)
    for m in sorted(by, key=lambda k: k == "LN"):
        u = unary_union(by[m])
        for part in getattr(u, "geoms", [u]):
            ax.add_patch(plt.Polygon(np.asarray(part.exterior.coords), fc=COL[m], ec="k", lw=0.6))
            for r in part.interiors: ax.add_patch(plt.Polygon(np.asarray(r.coords), fc="none", ec="k", lw=0.6))
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axhline(0, c="k", lw=0.4, ls=":")
OES = np.round(np.arange(0, 0.9001, 0.05), 3); LS = np.round(np.arange(0, 0.4001, 0.02), 3)
for oe in OES: build(oe, 0.2)
for L in LS: build(0.7, L)
print("all sweep geometries valid, no near-duplicate vertices")
for tag, vals, fixed in (("overetch", [0.0, 0.1, 0.2, 0.3, 0.5, 0.7, 0.9], "L"), ("lateral", [0.0, 0.04, 0.1, 0.2, 0.3, 0.4], "OE")):
    fig, axs = plt.subplots(2, (len(vals) + 1) // 2, figsize=(4.2 * ((len(vals) + 1) // 2), 7.2))
    for ax, v in zip(axs.flat, vals):
        g, P = build(v, 0.2) if tag == "overetch" else build(0.7, v)
        draw(ax, g, P, (4.3, 6.4), (-1.15, 0.85))
        ax.set_title(f"over-etch {v*1e3:.0f} nm (lateral buffer 200 nm)" if tag == "overetch" else f"lateral buffer {v*1e3:.0f} nm (over-etch 700 nm)", fontsize=10)
    for ax in list(axs.flat)[len(vals):]: ax.axis("off")
    fig.suptitle(f"Istanbul + buffer, gap 3.65 µm, slab 10.15 µm: {'over-etch sweep 0–900 nm' if tag == 'overetch' else 'lateral buffer sweep 0–400 nm'} (zoom on the signal-side slab end)")
    plt.tight_layout(); plt.savefig(f"preview_{tag}_sweep.png", dpi=120); plt.close()
g, P = build(0.7, 0.2); fig, ax = plt.subplots(figsize=(13, 3.6)); draw(ax, g, P, (-12, 12), (-1.3, 3.0))
ax.set_title("Nominal: gap 3.65 µm, slab 10.15 µm (top), buffer 200 nm top/floor and 200 nm lateral, over-etch 700 nm, 60° slab ends, 1575 nm")
plt.tight_layout(); plt.savefig("preview_nominal.png", dpi=120); plt.close(); print("figures ok")
