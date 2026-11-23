"""Slide 5 (EO crosstalk from fields): sketch of one Istanbul line, to scale in the cross-section (gap 4.45 um, gap
centre 7.1 um from the line centre, electrodes 2 um), with the field sample points at the gap centre and electrode
mid-height (no optical waveguide in the simulated model). Cross-section (top) and top view along the line (bottom). Not to scale vertically.
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
GAP, YC, MT = 4.45, 7.1, 2.0            # gap width, gap centre from the line centre, electrode height (um)
S, G2, GW = YC - GAP / 2, YC + GAP / 2, 16.0   # signal half-width, ground edge, drawn ground extent (um)

# cross-section to scale: y horizontal, height vertical (no optical waveguide in the simulated model)
a = ax[0]; a.set_xlim(-GW, GW); a.set_ylim(-1.6, 4.6); a.set_aspect("equal"); a.axis("off")
a.add_patch(Rectangle((-GW, -1.6), 2 * GW, 1.6, fc=LN, ec="none"))
a.text(0, -1.0, "substrate", ha="center", fontsize=10, color=MUTED)
for x0, x1, lab in ((-GW, -G2, "G"), (-S, S, "S"), (G2, GW, "G")):
    a.add_patch(Rectangle((x0, 0), x1 - x0, MT, fc=METAL, ec="none")); a.text((x0 + x1) / 2, MT / 2, lab, ha="center", va="center", fontsize=12, weight="bold")
for sgn, lab in ((1, "gap +"), (-1, "gap −")):
    a.annotate("", xy=(sgn * (G2 - 0.15), 1.6), xytext=(sgn * (S + 0.15), 1.6), arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8))
    a.text(sgn * YC, 2.4, lab, ha="center", fontsize=11, color=NAVY, weight="bold")
    a.plot(sgn * YC, MT / 2, "o", color=RED, ms=7, zorder=5)
a.text(0, 3.6, "E$_y$ and V$_\\pm$: signal → ground, opposite in the two gaps", ha="center", fontsize=10.5, color=BLUE)
a.set_title("Cross-section of one line (to scale)", fontsize=12, loc="left")

# top view: z horizontal (um), y vertical
b = ax[1]; Z = 120; b.set_xlim(-4, Z + 30); b.set_ylim(-GW, GW + 3); b.axis("off")
for y0, y1 in ((-GW, -G2), (-S, S), (G2, GW)):
    b.add_patch(Rectangle((0, y0), Z, y1 - y0, fc=METAL, ec="none", alpha=0.55))
for sgn in (1, -1):
    zz = np.arange(2.5, Z, 5.0); b.plot(zz, np.full_like(zz, sgn * YC), "o", color=RED, ms=3.5, zorder=5)
b.text(Z + 1.5, YC, "gap +", va="center", fontsize=10.5, color=NAVY, weight="bold")
b.text(Z + 1.5, -YC, "gap −", va="center", fontsize=10.5, color=NAVY, weight="bold")
b.text(Z + 1.5, 0, "S", va="center", fontsize=12, weight="bold"); b.text(Z + 1.5, 12.5, "G", va="center", fontsize=12, weight="bold")
b.text(Z + 1.5, -12.5, "G", va="center", fontsize=12, weight="bold")
b.annotate("", xy=(25, GW + 2.2), xytext=(0, GW + 2.2), arrowprops=dict(arrowstyle="->", color=ORANGE, lw=2))
b.text(27, GW + 2.2, "light, group index n$_g$", va="center", fontsize=10.5, color=ORANGE)
b.annotate("", xy=(Z, GW + 2.2), xytext=(Z - 18, GW + 2.2), arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
b.text(Z - 20, GW + 2.2, "RF wave", va="center", ha="right", fontsize=10.5, color=BLUE)
b.plot([], [], "o", color=RED, ms=5, label="E$_y$ samples: gap centre, electrode mid-height, every 5 µm in z")
b.legend(frameon=False, fontsize=10.5, loc="lower center", bbox_to_anchor=(0.5, -0.2))
b.set_title("Top view along z (first 120 µm of 8.75 mm)", fontsize=12, loc="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "eo_sampling.png"), dpi=200); plt.close(fig)

# equations (mathtext)
EQ = {"eq5_pockels": r"$\dfrac{d\varphi_\pm}{dz} = \pm\,\kappa\,V_\pm(z,t),\qquad \kappa = \dfrac{\pi}{V_\pi\,L}$",
      "eq5_arm": r"$\varphi_\pm(t_0) = \pm\,\kappa \int_0^L V_\pm\!\left(z,\; t_0 + \dfrac{n_g\,z}{c}\right) dz$",
      "eq5_phasor": r"$V(z,t) = \mathrm{Re}\{V(z)\,e^{j\omega t}\}\;\Rightarrow\; \varphi_\pm = \pm\,\kappa L\,\mathrm{Re}\{H[V_\pm]\,e^{j\omega t_0}\}$",
      "eq5_H": r"$H[V] = \dfrac{1}{L}\int_0^L V(z)\,e^{j\beta_o z}\,dz,\qquad \beta_o = \dfrac{\omega\,n_g}{c}$",
      "eq5_X": r"$\varphi_+ - \varphi_- = \kappa L\,\mathrm{Re}\{M\,e^{j\omega t_0}\},\qquad M = H[V_+] + H[V_-] = 2\,H[V_d]$",
      "eq5_X2": r"$V_d = \dfrac{V_+ + V_-}{2},\quad V_c = \dfrac{V_+ - V_-}{2}\ \mathrm{(cancels)},\qquad X_{EO} = \dfrac{M_B}{M_A}$"}
EQ.update({"eq12_mode": r"$\cosh\gamma_m L = \dfrac{A_m + D_m}{2},\qquad Z_m = \sqrt{B_m/C_m}$",
           "eq12_V": r"$V_m(z) = V_m(0)\cosh\gamma_m z - Z_m I_m(0)\sinh\gamma_m z$",
           "eq12_AB": r"$V_A = V_{even} + V_{odd},\qquad V_B = V_{even} - V_{odd}$"})
for k, v in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1)); f.text(0, 0, v, fontsize=22, color="#1A1A1A")
    f.savefig(os.path.join(OUT, k + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(f)

# slide 13: port sketch and NEXT/FEXT from the fields
fig, a = plt.subplots(figsize=(3.6, 2.0)); a.set_xlim(-1.6, 11.6); a.set_ylim(-0.6, 5.0); a.axis("off")
for y, lab, c in ((3.4, "A", NAVY), (1.0, "B", ORANGE)):
    a.plot([0, 10], [y, y], color=c, lw=3); a.text(5, y + 0.4, f"line {lab}", ha="center", fontsize=10, color=c, weight="bold")
for x, y, t, col in ((0, 3.4, "1", NAVY), (10, 3.4, "2", MUTED), (0, 1.0, "3", MUTED), (10, 1.0, "4", MUTED)):
    a.plot(x, y, "s", color=col, ms=9); a.text(x + (-0.5 if x == 0 else 0.5), y, t, ha="right" if x == 0 else "left", va="center", fontsize=9.5, color=col)
for x, y, t in ((0, 3.4, "V$_A^+$(0)"), (0, 1.0, "V$_B$(0)"), (10, 1.0, "V$_B$(L)")):
    a.plot(x, y, "o", color=RED, ms=6, zorder=5); a.text(x, y - 0.65, t, ha="center", fontsize=10, color=RED)
a.text(5, -0.45, "z = 0 … L", ha="center", fontsize=9, color=MUTED); a.text(-0.6, 4.25, "driven", ha="center", fontsize=9.5, color=NAVY)
fig.savefig(os.path.join(OUT, "ports_sketch.png"), dpi=200, bbox_inches="tight", pad_inches=0.02, transparent=True); plt.close(fig)
EQ2 = {"eq13_next": r"$\mathrm{NEXT} = \left|\dfrac{V_B(0)}{V_A^+(0)}\right|,\qquad \mathrm{FEXT} = \left|\dfrac{V_B(L)}{V_A^+(0)}\right|$",
       "eq13_fit": r"$V_A(z) = V_A^+(0)\,e^{-\gamma z} + V_A^-(0)\,e^{\gamma z}$"}
for k, v in EQ2.items():
    f = plt.figure(figsize=(0.1, 0.1)); f.text(0, 0, v, fontsize=22, color="#1A1A1A")
    f.savefig(os.path.join(OUT, k + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(f)
