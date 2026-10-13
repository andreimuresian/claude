import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Lisbona_lifted_buffer_alumina.ipynb"))
s = "".join(nb["cells"][0]["source"]); s = s[:s.index("# ============================================================\n# 3. MESH")]
g = {}; exec(s + "\npolygons, DEV_W, CLAD_H = build_polygons()\n", g)
fig, axs = plt.subplots(2, 1, figsize=(12, 8))
for ax, (xl, yl) in zip(axs, [((-9, 9), (-0.6, 6.6)), ((1.0, 2.4), (0.15, 0.75))]):
    for n, p in g["polygons"].items():
        col = g["MATERIALS"][g["material_of"](n)]["color"]
        for q in (p.geoms if hasattr(p, "geoms") else [p]):
            if q.geom_type != "Polygon": continue
            x, y = q.exterior.xy; ax.fill(x, y, color=col, ec="k", lw=0.3)
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal")
axs[0].set_title("Lisbon lifted, 200 nm SiO$_2$ buffer, gap 3.4 µm + 40 nm conformal ALD Al$_2$O$_3$ (pink)")
axs[1].set_title("zoom: lower-block inner corner on the buffer")
plt.tight_layout(); plt.savefig("geometry_alumina40.png", dpi=150)
