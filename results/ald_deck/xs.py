import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
def load(nbp, call):
    nb = json.load(open(nbp)); s = "".join(nb["cells"][0]["source"]); s = s[:s.index("# ============================================================\n# 3. MESH")]
    g = {}; exec(s + "\n_res = " + call + "\n", g); return g, g["_res"][0]
for nbp, call, fn, xl, yl, zx, zy in [
    ("/home/user/claude/VPI_interface_optimized_Cordoba_alumina.ipynb", "build_polygons()", "xs_cordoba_clean.png", (-6, 6), (-0.6, 2.7), (1.7, 2.5), (0.15, 0.55)),
    ("/home/user/claude/VPI_interface_optimized_Lisbona_lifted_buffer_alumina.ipynb", "build_polygons()", "xs_lisbon_clean.png", (-8.5, 8.5), (-0.6, 6.5), (1.3, 2.1), (0.2, 0.75))]:
    g, polys = load(nbp, call)
    fig, (a, b) = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [2.3, 1]})
    for ax in (a, b):
        for n, p in polys.items():
            col = g["MATERIALS"][g["material_of"](n)]["color"]
            for q in (p.geoms if hasattr(p, "geoms") else [p]):
                if q.geom_type != "Polygon": continue
                x, y = q.exterior.xy; ax.fill(x, y, color=col, ec="none")
        ax.set_aspect("equal"); ax.set_xlabel("x (µm)", fontsize=11)
    a.set_xlim(*xl); a.set_ylim(*yl); a.set_ylabel("y (µm)", fontsize=11)
    b.set_xlim(*zx); b.set_ylim(*zy); b.set_title("zoom: electrode corner", fontsize=11)
    a.add_patch(plt.Rectangle((zx[0], zy[0]), zx[1] - zx[0], zy[1] - zy[0], fill=False, ec="red", lw=1.2))
    fig.tight_layout(); fig.savefig("figs/" + fn, dpi=200); plt.close(fig)
