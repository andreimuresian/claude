"""Slides 4a/4b (field extraction): gap voltage along the L+S line at 30 GHz (raw 5 um samples, average over one
0.18 mm cell, two-wave fit) and a zoom on the cell pattern; rendered equations. Output: img/field_fit_30GHz.png, img/eq4_*.png"""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img"); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
from mzm_interconnect.physics import C0
D = os.path.join(HERE, "..", "L+S", "130 GHz"); GAP, PITCH, CUT, L = 4.45e-6, 0.18e-3, 0.18e-3, 3.24e-3
NAVY, RED, GREY, ORANGE, BLUE, MUTED = "#0E2268", "#F20013", "#9AA0AC", "#EB6834", "#2A78D6", "#5A606E"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); f = np.unique(d[:, 0]); z = d[d[:, 0] == f[0], 3] * 1e-3
    return f, z, (d[:, 6] + 1j * d[:, 7]).reshape(len(f), len(z))
F, z, Ep = load("L1_gap+.txt"); _, _, Em = load("L1_gap-.txt"); i = int(np.argmin(abs(F - 30))); w = 2 * np.pi * F[i] * 1e9
V = GAP / 2 * (Ep[i] - Em[i]); k = int(round(PITCH / (z[1] - z[0]))); zs = np.convolve(z, np.ones(k) / k, "valid"); Vs = np.convolve(V, np.ones(k) / k, "valid")
m = (zs >= CUT) & (zs <= L - CUT)
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
r = lambda p: np.concatenate([(e := two(p[0] + 1j * p[1], zs[m], Vs[m])[1]).real, e.imag])
p = least_squares(r, [0.5, w * 2.2 / C0]).x; g = p[0] + 1j * p[1]; c, _ = two(g, zs[m], Vs[m])
fit = lambda zz: c[0] * np.exp(-g * zz) + c[1] * np.exp(g * zz)
nrm = abs(c[0])
fig, ax = plt.subplots(2, 1, figsize=(6.6, 5.4), gridspec_kw=dict(height_ratios=[1.25, 1]))
for a, (z0, z1) in zip(ax, ((0, L), (1.0e-3, 1.6e-3))):
    s = (z >= z0) & (z <= z1); ss = (zs >= z0) & (zs <= z1)
    a.plot(z[s] * 1e3, abs(V[s]) / nrm, "o", ms=2.2 if a is ax[0] else 4, color=GREY, label="E$_y$ samples, every 5 µm")
    a.plot(zs[ss] * 1e3, abs(Vs[ss]) / nrm, "-", color=NAVY, lw=1.6, label="average over one 0.18 mm cell")
    zz = np.linspace(z0, z1, 400); a.plot(zz * 1e3, abs(fit(zz)) / nrm, "--", color=RED, lw=1.6, label="two-wave fit")
    a.set_xlim(z0 * 1e3, z1 * 1e3); a.grid(alpha=0.3); a.set_ylabel("|V(z)| / |V$^+$|")
ax[0].set_ylim(0, 1.25); ax[1].set_ylim(0, 1.25); ax[1].set_xlabel("Position along the line z (mm)")
ax[0].set_title("Straight line (L+S run, 3.24 mm), 30 GHz", fontsize=12, loc="left"); ax[1].set_title("Zoom: field dip at each tee aperture (every 0.18 mm)", fontsize=12, loc="left")
h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, frameon=False, fontsize=10, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.0))
fig.tight_layout(rect=(0, 0, 1, 0.94)); fig.savefig(os.path.join(OUT, "field_fit_30GHz.png"), dpi=200); plt.close(fig)
print("30 GHz: n %.4f, alpha %.3f dB/cm, |V-/V+| %.3f" % (p[1] * C0 / w, p[0] * 8.686 / 100, abs(c[1] / c[0])))
EQ = {"eq4_v": r"$V(z_k) = \dfrac{\mathrm{GAP}}{2}\left[E_y^{(+)}(z_k) - E_y^{(-)}(z_k)\right],\qquad k = 1\ldots649$",
      "eq4_model": r"$V(z) = V^+e^{-\gamma z} + V^-e^{+\gamma z},\qquad \gamma = \alpha + j\beta$",
      "eq4_fit": r"$\min_{\gamma}\ \sum_k \left|V(z_k) - V^+e^{-\gamma z_k} - V^-e^{+\gamma z_k}\right|^2$",
      "eq4_an": r"$\alpha = \mathrm{Re}\,\gamma,\qquad n_m = \dfrac{c}{\omega}\,\mathrm{Im}\,\gamma$",
      "eq4_zc": r"$\Gamma_L = \dfrac{V^-e^{+\gamma L}}{V^+e^{-\gamma L}},\qquad Z_c = 50\,\Omega\;\dfrac{1-\Gamma_L}{1+\Gamma_L}$"}
for k_, v in EQ.items():
    f = plt.figure(figsize=(0.1, 0.1)); f.text(0, 0, v, fontsize=22, color="#1A1A1A")
    f.savefig(os.path.join(OUT, k_ + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.05, transparent=True); plt.close(f)
