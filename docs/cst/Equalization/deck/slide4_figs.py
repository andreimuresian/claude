"""Field-extraction slides (4a-4d): cross-section sketch with the voltage paths, |V(z)| along the L+S line at 30 GHz
with the two-wave fit, zoom on the cell pattern, rendered equations. Outputs in img/."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img"); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
from mzm_interconnect.physics import C0
D = os.path.join(HERE, "..", "L+S", "130 GHz"); GAP, PITCH, CUT, L = 4.45e-6, 0.18e-3, 0.18e-3, 3.24e-3
NAVY, RED, GREY, ORANGE, BLUE, MUTED, METAL = "#0E2268", "#F20013", "#9AA0AC", "#EB6834", "#2A78D6", "#5A606E", "#C9A227"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})

# (a) cross-section sketch, looking along +z (from port 1 to port 2): y to the right, x up. Not to scale.
fig, a = plt.subplots(figsize=(6.4, 3.3)); a.set_xlim(-14, 14); a.set_ylim(-3.2, 5.2); a.axis("off")
a.add_patch(Rectangle((-14, -2.2), 28, 2.2, fc="#DCE6F5", ec="none")); a.text(0, -1.3, "substrate", ha="center", fontsize=10, color=MUTED)
for x0, x1, lab in ((-14, -6.5, "G"), (-3.5, 3.5, "S"), (6.5, 14, "G")):
    a.add_patch(Rectangle((x0, 0), x1 - x0, 2.2, fc=METAL, ec="none")); a.text((x0 + x1) / 2, 1.1, lab, ha="center", va="center", fontsize=13, weight="bold")
for s_, lab, vl in ((1, "right gap", "V$_R$ = GAP·E$_{y,R}$"), (-1, "left gap", "V$_L$ = −GAP·E$_{y,L}$")):
    a.annotate("", xy=(s_ * 6.4, 1.1), xytext=(s_ * 3.6, 1.1), arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
    a.plot(s_ * 5.0, 1.1, "o", color=RED, ms=7, zorder=5)
    a.text(s_ * 5.0, 2.75, lab, ha="center", fontsize=11, color=NAVY, weight="bold"); a.text(s_ * 5.0, 3.55, vl, ha="center", fontsize=11, color=BLUE)
a.annotate("", xy=(13.2, 4.6), xytext=(10.2, 4.6), arrowprops=dict(arrowstyle="->", color=MUTED)); a.text(13.4, 4.6, "y", va="center", color=MUTED)
a.text(-13.8, 4.6, "view along +z (port 1 → port 2)", fontsize=10, color=MUTED, va="center")
a.text(0, -2.85, "● sample point: gap centre, electrode mid-height (x = 1 µm)    → field and integration path", ha="center", fontsize=9.5, color=MUTED)
fig.savefig(os.path.join(OUT, "xs_voltage.png"), dpi=200, bbox_inches="tight", pad_inches=0.03); plt.close(fig)

# data at 30 GHz
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); f = np.unique(d[:, 0]); z = d[d[:, 0] == f[0], 3] * 1e-3
    return f, z, (d[:, 6] + 1j * d[:, 7]).reshape(len(f), len(z))
F, z, Ep, = load("L1_gap+.txt"); _, _, Em = load("L1_gap-.txt"); i = int(np.argmin(abs(F - 30))); w = 2 * np.pi * F[i] * 1e9
V = GAP / 2 * (Ep[i] - Em[i]); k = int(round(PITCH / (z[1] - z[0]))); zs = np.convolve(z, np.ones(k) / k, "valid"); Vs = np.convolve(V, np.ones(k) / k, "valid")
m = (zs >= CUT) & (zs <= L - CUT)
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
r = lambda p: np.concatenate([(e := two(p[0] + 1j * p[1], zs[m], Vs[m])[1]).real, e.imag])
p = least_squares(r, [0.5, w * 2.2 / C0]).x; g = p[0] + 1j * p[1]; c, _ = two(g, zs[m], Vs[m])
fit = lambda zz: c[0] * np.exp(-g * zz) + c[1] * np.exp(g * zz)
fw = lambda zz: abs(c[0] * np.exp(-g * zz))

# (b) |V(z)| along the whole line with the fit and the forward wave alone
fig, a = plt.subplots(figsize=(6.4, 3.6))
a.plot(zs[m] * 1e3, abs(Vs[m]), "-", color=NAVY, lw=2.2, label="field data (cell average)")
zz = np.linspace(CUT, L - CUT, 400); a.plot(zz * 1e3, abs(fit(zz)), "--", color=RED, lw=1.8, label="two-wave fit")
a.plot(zz * 1e3, fw(zz), ":", color=MUTED, lw=1.6, label="forward wave alone")
a.set_xlim(0, L * 1e3); a.set_ylim(0, 1.25 * abs(Vs).max()); a.grid(alpha=0.3)
a.set_xlabel("Position along the line z (mm)"); a.set_ylabel("|V(z)| (V)")
a.legend(frameon=False, fontsize=10, loc="lower center", ncol=3, bbox_to_anchor=(0.5, -0.02))
a.set_title("Straight line 3.24 mm, 30 GHz: decay + ripple of the reflected wave", fontsize=11.5, loc="left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "vz_fit_30GHz.png"), dpi=200); plt.close(fig)

# (c) zoom: raw samples vs cell average
fig, a = plt.subplots(figsize=(6.4, 3.4)); s = (z >= 1.0e-3) & (z <= 1.6e-3); ss = (zs >= 1.0e-3) & (zs <= 1.6e-3)
a.plot(z[s] * 1e3, abs(V[s]), "o", ms=3.5, color=GREY, label="E$_y$·GAP at each 5 µm sample")
a.plot(zs[ss] * 1e3, abs(Vs[ss]), "-", color=NAVY, lw=2, label="average over one 0.18 mm cell")
a.set_xlim(1.0, 1.6); a.set_ylim(0, 1.3 * abs(V[s]).max()); a.grid(alpha=0.3); a.set_xlabel("Position along the line z (mm)"); a.set_ylabel("|V(z)| (V)")
for zc in (1.17, 1.35, 1.53): a.annotate("tee aperture", (zc, 0.3 * abs(V[s]).max()), ha="center", fontsize=9.5, color=MUTED)
a.legend(frameon=False, fontsize=10, loc="upper center", ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "cell_pattern_30GHz.png"), dpi=200); plt.close(fig)

EQ = {"eqA_int": r"$V = \int_{S}^{G}\mathbf{E}\cdot d\mathbf{l}\;\approx\; E_y\cdot\mathrm{GAP}$",
      "eqA_avg": r"$V(z_k) = \dfrac{V_R + V_L}{2} = \dfrac{\mathrm{GAP}}{2}\left[E_{y,R}(z_k) - E_{y,L}(z_k)\right]$",
      "eqA_zk": r"$z_k = (k-1)\cdot 5\,\mu\mathrm{m},\qquad k = 1\ldots 649\quad(3.24\,\mathrm{mm}/5\,\mu\mathrm{m} + 1)$",
      "eqB_tl": r"$\dfrac{d^2V}{dz^2} = \gamma^2 V\;\;\Rightarrow\;\; V(z) = V^+e^{-\gamma z} + V^-e^{+\gamma z},\qquad \gamma = \alpha + j\beta$",
      "eqB_t": r"$\dfrac{\partial^2 V}{\partial z^2} = LC\,\dfrac{\partial^2 V}{\partial t^2} + (RC + LG)\,\dfrac{\partial V}{\partial t} + RG\,V$",
      "eqB_w": r"$V(z,t) = \mathrm{Re}\{V(z)\,e^{j\omega t}\}:\;\; \dfrac{\partial}{\partial t}\rightarrow j\omega\;\;\Rightarrow\;\; \dfrac{d^2V}{dz^2} = (R + j\omega L)(G + j\omega C)\,V = \gamma^2 V$",
      "eqB_sol": r"$V(z) = V^+e^{-\gamma z} + V^-e^{+\gamma z},\qquad \gamma = \sqrt{(R + j\omega L)(G + j\omega C)} = \alpha + j\beta$",
      "eqB_res": r"$\mathrm{misfit} = \sqrt{\dfrac{\sum_k |V(z_k) - V_{fit}(z_k)|^2}{\sum_k |V(z_k)|^2}}$",
      "eqB_fit": r"$\min_{\gamma}\ \sum_{k}\left|V(z_k) - V^+e^{-\gamma z_k} - V^-e^{+\gamma z_k}\right|^2$",
      "eqC_fl": r"$V(z + p) = V(z)\,e^{-\gamma p}\qquad (p = 0.18\,\mathrm{mm})$",
      "eqD_an": r"$\alpha = \mathrm{Re}\,\gamma,\qquad n_m = \dfrac{c}{\omega}\,\mathrm{Im}\,\gamma$",
      "eqD_gl": r"$\Gamma_L = \dfrac{V^-e^{+\gamma L}}{V^+e^{-\gamma L}} = \dfrac{Z_L - Z_c}{Z_L + Z_c}\;\;\Rightarrow\;\; Z_c = Z_L\,\dfrac{1-\Gamma_L}{1+\Gamma_L},\quad Z_L = 50\,\Omega$"}
for k_, v in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1)); f.text(0, 0, v, fontsize=22, color="#1A1A1A")
    f.savefig(os.path.join(OUT, k_ + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(f)
print("30 GHz n %.4f alpha %.3f dB/cm |V-/V+| %.3f" % (p[1] * C0 / w, p[0] * 8.686 / 100, abs(c[1] / c[0])))
