import json, re, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Jerez_lifted_buffer.ipynb")); s = "".join(nb["cells"][0]["source"])
s = s[:s.index("# ============================================================\n# 3. MESH")]
fig, axs = plt.subplots(1, 2, figsize=(15, 4.2))
for ax, (b, gap, lab) in zip(axs, ((0.0, 4.2, "No buffer, bottom gap 4.2 µm"), (0.2, 3.2, "200 nm SiO₂ buffer, bottom gap 3.2 µm"))):
    src = re.sub(r"\nBUFFER_H = [0-9.]+", f"\nBUFFER_H = {b}", s); src = re.sub(r"\nGAP_BOT = [0-9.]+", f"\nGAP_BOT = {gap}", src)
    g = {}; exec(src + "\n_res = build_polygons()\n", g); P = g["_res"][0] if isinstance(g["_res"], tuple) else g["_res"]
    for n, p in P.items():
        col = g["MATERIALS"][g["material_of"](n)]["color"]
        for q in getattr(p, "geoms", [p]):
            if q.geom_type == "Polygon": x, y = q.exterior.xy; ax.fill(x, y, color=col, ec="none")
    ax.set_xlim(-12, 12); ax.set_ylim(-0.8, 6.8); ax.set_aspect("equal"); ax.set_title(lab, fontsize=13); ax.set_xlabel("x (µm)")
    xl = g["GAP_BOT"] / 2 + g.get("LOW_W", 0)
    ax.annotate("", (g["X_LIFT"], 0.15), (g["X_LIFT"], 2.6), arrowprops=dict(arrowstyle="-", ls="--", color="k"))
    ax.text(g["X_LIFT"] + 0.15, 2.5, "x_lift", fontsize=11)
axs[0].set_ylabel("y (µm)")
plt.tight_layout(); plt.savefig("xs_jerez_lifted.png", dpi=150); print("ok")
