"""Plot the polygons exactly as handed to the mesher (no meshing)."""
import json, os, re, sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb")); src = "".join(nb["cells"][0]["source"])
src = re.sub(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1); src = re.sub(r"\nwl = [0-9.]+", "\nwl = 1.625", src, count=1); src = re.sub(r"\nT_ALD = [0-9.]+", "\nT_ALD = 0.0", src, count=1)
cut = src.index("\npolygons, Y_TOP = build_polygons()")
par = "M1_GAP=3.5; M1_BUF=0.13; M1_CW=3.5; M1_CH=1.0; MTX_SMALL=1.0; MTX_BIG=10.0; W_S=10.0; W_T=10.0; W_G=10.0\n"
code = src[:cut] + "\n" + par + open("/home/user/claude/results/madrid/m1/m1_geom.py").read() + "\npolygons, Y_TOP = build_polygons()\n"
col = {"LN": "#6b7b8c", "SiO2": "#9ccaf2", "air": "#ffffff", "Au_sig": "#f2c14e", "Au_gnd": "#e5a92e"}
cases = [("0.1", "0.1", "Aligned: 0.1 µm tongues"), ("0", "0.2", "Misaligned → signal tongue 0.2 µm"), ("0.2", "0", "Misaligned → ground tongue 0.2 µm")]
f, axs = plt.subplots(2, 3, figsize=(17, 9), gridspec_kw=dict(height_ratios=[1, 1]))
for j, (l, r, t) in enumerate(cases):
    os.environ.update(TGL=l, TGR=r, TRW="1.0", TRF="0.1", BELLY="0.2"); g = {}
    exec(compile("import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: None\n" + code, "geo", "exec"), g)
    for row, (xl, yl) in enumerate((((-3.2, 3.2), (-0.2, 3.0)), ((-2.35, -1.25), (1.0, 2.6)))):
        ax = axs[row, j]
        for name, poly in g["polygons"].items():
            m = g["material_of"](name); geoms = poly.geoms if hasattr(poly, "geoms") else [poly]
            for p in geoms:
                x, y = p.exterior.xy; ax.fill(x, y, fc=col.get(m, "#ccc"), ec="k", lw=0.25)
        ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.set_xlabel("x (µm)")
        if row == 0: ax.set_title(t, fontsize=11)
        else: ax.set_title("zoom: ground tongue and 200 nm belly", fontsize=10)
f.suptitle("Madrid 1 U-slot with gold tongues: polygons exactly as simulated (oxide 3.5 × 1.0 µm, trench 1.0 µm, floor 100 nm, buffer 130 nm)", fontsize=11.5)
f.tight_layout(); f.savefig("tongue_as_simulated.png", dpi=140)
