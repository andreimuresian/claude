"""Figure for the double-infinitesimal discussion: (left) rectangle k0 n L grown by dn and dL: two strips + corner;
(right) phase = k0 x area under Delta n(z): strips + triangles, for 4 and 8 steps (triangles shrink)."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon
S1, S2, CO, BASE = "#2a78d6", "#1baa7d", "#eb6834", "#d9d9d9"
fig, ax = plt.subplots(1, 3, figsize=(15, 5), gridspec_kw=dict(width_ratios=[1.1, 1, 1]))

a = ax[0]; L, n, dL, dn = 3.0, 2.0, 0.6, 0.45
a.add_patch(Rectangle((0, 0), L, n, fc=BASE, ec="k"))
a.add_patch(Rectangle((0, n), L, dn, fc=S1, ec="k", alpha=0.8))
a.add_patch(Rectangle((L, 0), dL, n, fc=S2, ec="k", alpha=0.8))
a.add_patch(Rectangle((L, n), dL, dn, fc=CO, ec="k"))
a.text(L / 2, n / 2, r"$n\,L$", ha="center", va="center", fontsize=15)
a.text(L / 2, n + dn / 2, r"strip 1: $L\,dn$", ha="center", va="center", color="w", fontsize=12)
a.text(L + dL / 2, n / 2, r"strip 2: $n\,dL$", ha="center", va="center", color="w", fontsize=12, rotation=90)
a.annotate(r"corner: $dn\,dL$", (L + dL / 2, n + dn / 2), (L + dL + 0.15, n + dn + 0.45), fontsize=12, color=CO,
           arrowprops=dict(arrowstyle="->", color=CO))
a.annotate("", (0, -0.15), (L, -0.15), arrowprops=dict(arrowstyle="<->")); a.text(L / 2, -0.35, r"$L$", ha="center", fontsize=13)
a.annotate("", (L, -0.15), (L + dL, -0.15), arrowprops=dict(arrowstyle="<->")); a.text(L + dL / 2, -0.35, r"$dL$", ha="center", fontsize=13)
a.annotate("", (-0.15, 0), (-0.15, n), arrowprops=dict(arrowstyle="<->")); a.text(-0.35, n / 2, r"$n$", va="center", fontsize=13)
a.annotate("", (-0.15, n), (-0.15, n + dn), arrowprops=dict(arrowstyle="<->")); a.text(-0.45, n + dn / 2, r"$dn$", va="center", fontsize=13)
a.set_xlim(-0.7, L + dL + 1.6); a.set_ylim(-0.6, n + dn + 0.9); a.set_aspect("equal"); a.axis("off")
a.set_title("1. Index and length both change:\n" r"$d\phi = k_0\,(L\,dn + n\,dL)$ + corner $k_0\,dn\,dL$ (dropped)", fontsize=11)

def area(a, N):
    f = lambda z: 0.25 + 0.75 * z ** 1.6          # an index change that grows along z (any smooth curve)
    zz = np.linspace(0, 1, 400); a.plot(zz, f(zz), "k", lw=1.6, zorder=5)
    dz = 1 / N; tri = 0.0
    for i in range(N):
        z0, z1 = i * dz, (i + 1) * dz
        a.add_patch(Rectangle((z0, 0), dz, f(z0), fc=S2, ec="k", lw=0.6, alpha=0.8))
        top = [(z0, f(z0))] + [(z, f(z)) for z in np.linspace(z0, z1, 30)] + [(z1, f(z0))]
        a.add_patch(Polygon(top, fc=CO, ec="k", lw=0.6)); tri += np.trapezoid(f(np.linspace(z0, z1, 200)) - f(z0), np.linspace(z0, z1, 200))
    tot = np.trapezoid(f(zz), zz)
    a.set_xlim(0, 1); a.set_ylim(0, 1.08); a.set_xlabel(r"$z$ (along the line)"); a.set_ylabel(r"$\Delta n(z)$")
    a.set_title(f"{2 if N == 4 else 3}. Phase = $k_0\\times$ area under $\\Delta n(z)$, {N} steps\n"
                f"strips (green) + corners (orange); corners = {tri / tot * 100:.0f} % of the area", fontsize=11)
    if N == 4:
        z0, z1 = 0.5, 0.75
        a.annotate(r"strip $\Delta n(z)\,dz$", (0.625, f(0.5) / 2), (0.08, 0.85), fontsize=11, color=S2,
                   arrowprops=dict(arrowstyle="->", color=S2))
        a.annotate(r"corner $\approx \frac{1}{2}\,\frac{\partial\Delta n}{\partial z}\,dz^2$", (0.7, (f(0.5) + f(0.75)) / 2 - 0.02),
                   (0.3, 1.0), fontsize=11, color=CO, arrowprops=dict(arrowstyle="->", color=CO))
area(ax[1], 4); area(ax[2], 8)
fig.tight_layout(); fig.savefig("infinitesimals.png", dpi=150)
