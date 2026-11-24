import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.tri as mtri
from matplotlib.patches import Rectangle, Polygon
D = {k: np.load(k + ".npz") for k in ("notrench", "trench")}
G = 3.5; SL = 0.275; yb = SL + 0.13; RT = 1.4; bt = 0.275 / np.tan(np.radians(60)); ytop = yb + 2.0; yfl = 0.55 + 0.1
X0, X1, Y0, Y1 = -2.6, 2.6, -0.3, 2.7
def outline(ax, tr):
    kw = dict(fill=False, ec="k", lw=.7)
    ax.add_patch(Polygon([(-RT/2-bt, SL), (RT/2+bt, SL), (RT/2, 0.55), (-RT/2, 0.55)], **kw)); ax.axhline(SL, c="k", lw=.5); ax.axhline(0, c="k", lw=.4, ls=":")
    ax.add_patch(Rectangle((G/2, yb), 3, 5, fc="#f2c14e", ec="k", lw=.7)); ax.add_patch(Rectangle((-G/2-3, yb), 3, 1.0, fc="#f2c14e", ec="k", lw=.7))
    ax.add_patch(Rectangle((-G/2, SL), G, ytop-SL, **kw))
    if tr: ax.add_patch(Rectangle((-0.5, yfl), 1.0, ytop-yfl, fill=False, ec="#c0392b", lw=1.4, ls="--"))
f = plt.figure(figsize=(15, 12)); gs = f.add_gridspec(3, 2, height_ratios=[1.15, 1.15, 0.9])
vmax = 2.2
for j, (k, tit) in enumerate((("notrench", "No trench (oxide fills the gap)"), ("trench", "U-slot: 1.0 µm air trench, floor 100 nm above rib"))):
    d = D[k]; p, t = d["p"], d["t"]; tri = mtri.Triangulation(p[0], p[1], t.T); E = -d["Ex"] * G      # Ex·G/V (V = 1)
    ax = f.add_subplot(gs[0, j]); mesh = ax.tripcolor(tri, facecolors=E, cmap="inferno", vmin=0, vmax=vmax, shading="flat")
    ax.tricontour(tri, d["pot"], levels=np.linspace(0.05, 0.95, 19), colors="w", linewidths=.6)
    I = d["Iopt"]; In = I / I.max()
    ax.tricontour(mtri.Triangulation(d["cent"][0], d["cent"][1]), In, levels=[0.1, 0.5], colors=["#5fd3ff", "#5fd3ff"], linewidths=[1.0, 1.6], linestyles=["--", "-"])
    outline(ax, k == "trench"); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect("equal")
    ax.set_title(f"{tit}\nVπ·L {float(d['VpiL']):.3f} V·cm · IL {float(d['IL']):.3f} dB/cm · Γ {float(d['gamma']):.3f}", fontsize=10.5)
    ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)")
    if j == 1: f.colorbar(mesh, ax=ax, label="horizontal DC field  E$_x$·G/V")
# difference map
d0, d1 = D["notrench"], D["trench"]
from scipy.interpolate import griddata
xs, ys = np.meshgrid(np.linspace(X0, X1, 420), np.linspace(Y0, Y1, 260))
E0 = griddata(d0["cent"].T, -d0["Ex"] * G, (xs, ys), method="nearest"); E1 = griddata(d1["cent"].T, -d1["Ex"] * G, (xs, ys), method="nearest")
ax = f.add_subplot(gs[1, 0]); im = ax.imshow(np.clip(E1 / E0 - 1, -1, 1) * 100, extent=(X0, X1, Y0, Y1), origin="lower", cmap="RdBu_r", vmin=-60, vmax=60, aspect="equal")
I1 = d1["Iopt"] / d1["Iopt"].max(); ax.tricontour(mtri.Triangulation(d1["cent"][0], d1["cent"][1]), I1, levels=[0.1, 0.5], colors="k", linewidths=[0.8, 1.3], linestyles=["--", "-"])
outline(ax, True); ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); f.colorbar(im, ax=ax, label="ΔE$_x$ trench vs no trench (%)")
ax.set_title("Change of E$_x$ caused by the trench (red = stronger)\nblack: optical mode 50 % / 10 % intensity", fontsize=10.5); ax.set_xlabel("x (µm)"); ax.set_ylabel("y (µm)")
# line cuts
ax = f.add_subplot(gs[1, 1]); xx = np.linspace(-2.3, 2.3, 400)
for k, c in (("notrench", "k"), ("trench", "#c0392b")):
    d = D[k]
    for yv, ls in ((0.41, "-"), (0.20, "--")):
        Ev = griddata(d["cent"].T, -d["Ex"] * G, np.c_[xx, np.full_like(xx, yv)], method="linear")
        ax.plot(xx, Ev, ls, c=c, lw=1.6, label=f"{'trench' if k=='trench' else 'no trench'}, y = {yv} µm ({'rib centre' if yv>0.3 else 'slab'})")
ax.axvspan(-0.86, 0.86, color="#6b7b8c", alpha=.12); ax.text(0, 0.15, "rib", ha="center", fontsize=9); ax.axvspan(-0.5, 0.5, ymin=0.9, color="#c0392b", alpha=.15)
ax.set_xlabel("x (µm)"); ax.set_ylabel("E$_x$·G/V"); ax.set_ylim(0, 2.3); ax.grid(alpha=.3); ax.legend(fontsize=8.5); ax.set_title("Horizontal cuts: field inside the LN", fontsize=10.5)
ax = f.add_subplot(gs[2, :]); yy = np.linspace(0.01, 2.6, 500)
for k, c in (("notrench", "k"), ("trench", "#c0392b")):
    d = D[k]; Ev = griddata(d["cent"].T, -d["Ex"] * G, np.c_[np.zeros_like(yy), yy], method="linear"); ax.plot(yy, Ev, c=c, lw=1.8, label="trench" if k == "trench" else "no trench")
    Iv = griddata(d["cent"].T, d["Iopt"] / d["Iopt"].max(), np.c_[np.zeros_like(yy), yy], method="linear"); ax.fill_between(yy, 0, Iv * 0.6, color=c, alpha=.12)
for y0_, lab in ((SL, "slab top"), (0.55, "rib top"), (yfl, "trench floor")): ax.axvline(y0_, c="gray", lw=.8, ls=":"); ax.text(y0_ + 0.01, 2.05, lab, fontsize=8.5, rotation=90, va="top")
ax.set_xlabel("y (µm) at x = 0 (vertical cut through the rib centre)"); ax.set_ylabel("E$_x$·G/V"); ax.set_ylim(0, 2.1); ax.grid(alpha=.3); ax.legend(fontsize=9)
ax.set_title("Vertical cut at x = 0 · shaded: optical intensity (scaled)", fontsize=10.5)
f.suptitle("Madrid 1, gap 3.5 µm, buffer 130 nm, fill 2.0 µm, λ = 1625 nm · DC field E$_x$·G/V (white: equipotentials every 0.05 V; blue: optical mode 50 % / 10 %)", fontsize=11.5)
f.tight_layout(); f.savefig("trench_field_comparison.png", dpi=140)
# numbers: optical-power-weighted Ex in LN
for k in D:
    d = D[k]; ln = np.char.startswith(d["mat"], "LN"); w = d["Iopt"]; print(k, "<Ex G/V>_opt in LN:", round(float(np.sum(-d["Ex"][ln] * G * w[ln]) / np.sum(w[ln])), 4))
