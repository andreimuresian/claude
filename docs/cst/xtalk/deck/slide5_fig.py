"""Slide 5 (EO crosstalk from fields): sketch of one Istanbul line with its two gaps, the optical arms and the field
sample points. Cross-section (top) and top view along the line (bottom). Not to scale vertically.
Geometry from the runs: signal edge at 4.85 um from the line centre, gap 4.85..9.35 um, samples at y = +-5 um,
every 5 um in z. Output: istanbul_img/eo_sampling.png"""
import os
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "istanbul_img")
NAVY, RED, GREY, ORANGE, BLUE, MUTED = "#0E2268", "#F20013", "#9AA0AC", "#EB6834", "#2A78D6", "#5A606E"
METAL, LN = "#C9A227", "#DCE6F5"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
fig, ax = plt.subplots(2, 1, figsize=(6.4, 5.4), gridspec_kw=dict(height_ratios=[1, 1.25]))
S, G2, GW = 4.85, 9.35, 18.0            # signal half-width, outer gap edge, ground extent (um)

# cross-section: y horizontal, height vertical
a = ax[0]; a.set_xlim(-GW, GW); a.set_ylim(-2.3, 3.4); a.axis("off")
a.add_patch(Rectangle((-GW, -2.3), 2 * GW, 2.3, fc=LN, ec="none"))
a.text(0, -1.95, "LN thin film / substrate", ha="center", fontsize=10, color=MUTED)
for x0, x1, lab in ((-GW, -G2, "G"), (-S, S, "S"), (G2, GW, "G")):
    a.add_patch(Rectangle((x0, 0), x1 - x0, 1.2, fc=METAL, ec="none")); a.text((x0 + x1) / 2, 0.45, lab, ha="center", fontsize=12, weight="bold")
for sgn, lab, arm in ((1, "gap +", "arm 1"), (-1, "gap −", "arm 2")):
    c = sgn * (S + G2) / 2
    a.add_patch(Rectangle((c - 1.3, -0.55), 2.6, 0.55, fc=ORANGE, ec="none", alpha=0.85))
    a.text(c, -0.95, arm, ha="center", fontsize=10, color=ORANGE, weight="bold")
    a.annotate("", xy=(sgn * (G2 - 0.3), 0.75), xytext=(sgn * (S + 0.3), 0.75), arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
    a.text(c, 1.55, lab, ha="center", fontsize=11, color=NAVY, weight="bold")
    a.plot(sgn * 5.0, 0.3, "o", color=RED, ms=6, zorder=5)
a.text(0, 2.45, "E$_y$ and V$_\\pm$: signal → ground, opposite in the two gaps", ha="center", fontsize=10.5, color=BLUE)
a.set_title("Cross-section of one line", fontsize=12, loc="left")

# top view: z horizontal (um), y vertical
b = ax[1]; Z = 120; b.set_xlim(-4, Z + 30); b.set_ylim(-GW, GW + 3); b.axis("off")
for y0, y1 in ((-GW, -G2), (-S, S), (G2, GW)):
    b.add_patch(Rectangle((0, y0), Z, y1 - y0, fc=METAL, ec="none", alpha=0.55))
for sgn in (1, -1):
    c = sgn * (S + G2) / 2
    b.add_patch(Rectangle((0, c - 1.3), Z, 2.6, fc=ORANGE, ec="none", alpha=0.35))
    zz = np.arange(2.5, Z, 5.0); b.plot(zz, np.full_like(zz, sgn * 5.0), "o", color=RED, ms=3.5, zorder=5)
b.text(Z + 1.5, 8.0, "gap + (arm 1)", va="center", fontsize=10, color=NAVY, weight="bold")
b.text(Z + 1.5, -8.0, "gap − (arm 2)", va="center", fontsize=10, color=NAVY, weight="bold")
b.text(Z + 1.5, 0, "S", va="center", fontsize=12, weight="bold"); b.text(Z + 1.5, 13.7, "G", va="center", fontsize=12, weight="bold")
b.text(Z + 1.5, -13.7, "G", va="center", fontsize=12, weight="bold")
b.annotate("", xy=(25, GW + 2.2), xytext=(0, GW + 2.2), arrowprops=dict(arrowstyle="->", color=ORANGE, lw=2))
b.text(27, GW + 2.2, "light, group index n$_g$", va="center", fontsize=10.5, color=ORANGE)
b.annotate("", xy=(Z, GW + 2.2), xytext=(Z - 18, GW + 2.2), arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
b.text(Z - 20, GW + 2.2, "RF wave", va="center", ha="right", fontsize=10.5, color=BLUE)
b.plot([], [], "o", color=RED, ms=5, label="E$_y$ sample points, every 5 µm in z")
b.legend(frameon=False, fontsize=10.5, loc="lower center", bbox_to_anchor=(0.5, -0.17))
b.set_title("Top view along z (first 120 µm of 8.75 mm)", fontsize=12, loc="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "eo_sampling.png"), dpi=200); plt.close(fig)

# equations (mathtext)
EQ = {"eq5_pockels": r"$\dfrac{d\varphi_\pm}{dz} = \pm\,\kappa\,V_\pm(z,t),\qquad \kappa = \dfrac{\pi}{V_\pi\,L}$",
      "eq5_arm": r"$\varphi_\pm(t_0) = \pm\,\kappa \int_0^L V_\pm\!\left(z,\; t_0 + \dfrac{n_g\,z}{c}\right) dz$",
      "eq5_phasor": r"$V(z,t) = \mathrm{Re}\{V(z)\,e^{j\omega t}\}\;\Rightarrow\; \varphi_\pm = \pm\,\kappa L\,\mathrm{Re}\{H[V_\pm]\,e^{j\omega t_0}\}$",
      "eq5_H": r"$H[V] = \dfrac{1}{L}\int_0^L V(z)\,e^{j\beta_o z}\,dz,\qquad \beta_o = \dfrac{\omega\,n_g}{c}$",
      "eq5_X": r"$\varphi_+ - \varphi_- \;\propto\; M = H[V_+] + H[V_-],\qquad X_{EO} = \dfrac{M_B}{M_A}$"}
for k, v in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1)); f.text(0, 0, v, fontsize=22, color="#1A1A1A")
    f.savefig(os.path.join(OUT, k + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(f)
