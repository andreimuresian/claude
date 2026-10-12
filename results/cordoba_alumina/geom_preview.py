import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Cordoba_alumina.ipynb"))
s = "".join(nb["cells"][0]["source"]); s = s[:s.index("# ============================================================\n# 3. MESH")]
g = {}; exec(s + "\npolygons, Y_TOP = build_polygons()\n", g)
fig, axs = plt.subplots(2, 1, figsize=(12, 7))
for ax, (xl, yl) in zip(axs, [((-6, 6), (-0.6, 2.8)), ((1.6, 2.6), (0.1, 0.6))]):
    for n, p in g["polygons"].items():
        col = g["MATERIALS"][g["material_of"](n)]["color"]
        for q in (p.geoms if hasattr(p, "geoms") else [p]):
            x, y = q.exterior.xy; ax.fill(x, y, color=col, ec="k", lw=0.3)
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal")
axs[0].set_title("Cordoba + 40 nm conformal ALD Al$_2$O$_3$ (pink), WG_TOP 1.4 µm, unetched slab")
axs[1].set_title("zoom: gold inner corner on the LN slab")
plt.tight_layout(); plt.savefig("geometry_alumina40.png", dpi=150)
