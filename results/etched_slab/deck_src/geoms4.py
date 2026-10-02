import io, contextlib, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
C = "/home/user/claude/cells/"
COL = {"LN": "#8b95a1", "SiO2": "#a9cff2", "air": "#ffffff", "Au_sig": "#f2c14e", "Au_gnd": "#f2c14e"}
def polys(path, reps={}):
    src = open(path).read()
    src = src[:src.index("raw_mesh = mesh_from_OrderedDict(")]
    for a, b in reps.items():
        assert a in src, a; src = src.replace(a, b)
    g = {"__name__": "__main__"}
    with contextlib.redirect_stdout(io.StringIO()):
        exec(src, g)
    return g["polygons"], g["material_of"]
def draw(ax, P, mat, ttl, xl=8.6):
    from shapely.ops import unary_union
    by = {}
    for n, p in P.items(): by.setdefault(mat(n), []).append(p)
    for m, ps in by.items():
        u = unary_union(ps)
        for q in (u.geoms if hasattr(u, "geoms") else [u]):
            x, y = q.exterior.xy; ax.fill(x, y, color=COL[m], lw=0)
            for r in q.interiors:
                x, y = r.xy; ax.fill(x, y, color="white", lw=0)
    for m, ps in by.items():
        u = unary_union(ps)
        for q in (u.geoms if hasattr(u, "geoms") else [u]):
            for r in [q.exterior, *q.interiors]:
                x, y = r.xy; ax.plot(x, y, color="#333", lw=0.5)
    ax.set_xlim(-xl, xl); ax.set_ylim(-0.6, 2.7); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(ttl, fontsize=15, loc="left")
if __name__ == "__main__":
    cases = [
        (C + "cell0_lifted.py", {}, "Standard lifted (no buffer)"),
        (C + "cell0_lifted_buffer.py", {}, "Buffered: 200 nm SiO$_2$, gap 3.2 $\\mu$m"),
        (C + "cell0_etched.py", {"SLAB_W = 3.2 ": "SLAB_W = 3.2 "}, "Etched: slab ends in the air gap"),
        (C + "cell0_etched.py", {"SLAB_W = 3.2 ": "SLAB_W = 9.0 "}, "Etched: slab ends inside the gold"),
        (C + "cell0_etched.py", {"SLAB_W = 3.2 ": "SLAB_W = 17.0 "}, "Etched: slab past the gold/SiO$_2$ edge"),
        (C + "cell0_etched.py", {"SLAB_W = 3.2 ": "SLAB_W = 9.0 ", "SPACER_W = 0.0 ": "SPACER_W = 0.3 "}, "Etched + SiO$_2$ spacer at the slab end"),
    ]
    fig, axs = plt.subplots(3, 2, figsize=(13, 6.3))
    for ax, (p, r, t) in zip(axs.flat, cases):
        P, m = polys(p, r); draw(ax, P, m, t)
    plt.tight_layout(h_pad=0.6, w_pad=1.5); fig.savefig("fig/geoms6.png", dpi=170, bbox_inches="tight")
    # single crops for later slides
    for nm, (p, r, t) in zip(["std", "buf", "gap", "gold", "past", "spacer"], cases):
        f, a = plt.subplots(figsize=(5.2, 1.35)); P, m = polys(p, r); draw(a, P, m, ""); a.set_title("")
        f.savefig(f"fig/geom_{nm}.png", dpi=170, bbox_inches="tight", pad_inches=0.02); plt.close(f)
