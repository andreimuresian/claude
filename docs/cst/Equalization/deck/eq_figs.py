"""Figures and equation images for the equalisation deck (build_equalisation.py).
Sources: ../analysis130/ls_extraction_130.npz, ../analysis130/port_block_test.npz."""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": "#5A606E", "axes.labelcolor": "#1A1A1A",
                     "xtick.color": "#5A606E", "ytick.color": "#5A606E", "axes.spines.top": False, "axes.spines.right": False,
                     "mathtext.fontset": "dejavusans"})
NAVY, RED, GREY, ORANGE, BLUE = "#0E2268", "#F20013", "#9AA0AC", "#EB6834", "#2A78D6"
d = np.load(os.path.join(HERE, "..", "analysis130", "ls_extraction_130.npz")); fT, F = d["fT"], d["F"]

def eq(name, tex, size=20):
    fig = plt.figure(figsize=(0.1, 0.1)); fig.text(0, 0, tex, fontsize=size, color="#1A1A1A")
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=300, bbox_inches="tight", pad_inches=0.03, transparent=True); plt.close(fig)

# --- equations
eq("eq_waves", r"$V(z)=V^{+}e^{-\gamma z}+V^{-}e^{+\gamma z},\quad I(z)=\dfrac{V^{+}e^{-\gamma z}-V^{-}e^{+\gamma z}}{Z_c},\quad \gamma=\alpha+j\beta,\quad n_m=\dfrac{c\,\beta}{\omega}$")
eq("eq_abcd_line", r"$V(0)=\cosh(\gamma L)\,V(L)+Z_c\sinh(\gamma L)\,I(L),\qquad I(0)=\dfrac{\sinh(\gamma L)}{Z_c}\,V(L)+\cosh(\gamma L)\,I(L)$")
eq("eq_s2a", r"$A=\dfrac{(1+S_{11})(1-S_{22})+S_{12}S_{21}}{2S_{21}},\quad B=Z_0\dfrac{(1+S_{11})(1+S_{22})-S_{12}S_{21}}{2S_{21}},\quad C=\dfrac{1}{Z_0}\dfrac{(1-S_{11})(1-S_{22})-S_{12}S_{21}}{2S_{21}}$", 17)
eq("eq_ts_zc", r"$Z_c=\sqrt{B/C}$")
eq("eq_ts_g", r"$e^{\gamma L}=\cosh\gamma L+\sinh\gamma L=A+B/Z_c$")
eq("eq_ts_an", r"$\alpha=\dfrac{\ln|A+B/Z_c|}{L},\qquad n_m=\dfrac{c}{\omega L}\,\arg\left(A+B/Z_c\right)$")
eq("eq_f_v", r"$V(z)=\dfrac{\mathrm{GAP}}{2}\left[E_y^{(+)}(z)-E_y^{(-)}(z)\right]$, averaged over one pitch (0.18 mm)")
eq("eq_f_fit", r"$\min_{\gamma}\ \sum_{z}\left|V(z)-V^{+}e^{-\gamma z}-V^{-}e^{+\gamma z}\right|^2,\quad z\in[0.18,\,3.06]$ mm")
eq("eq_f_an", r"$\alpha=\mathrm{Re}\,\gamma,\qquad n_m=\dfrac{c}{\omega}\,\mathrm{Im}\,\gamma$")
eq("eq_f_zc", r"$\Gamma_L=\dfrac{V^{-}e^{+\gamma L}}{V^{+}e^{-\gamma L}}=\dfrac{Z_L-Z_c}{Z_L+Z_c}\ \Rightarrow\ Z_c=Z_L\,\dfrac{1-\Gamma_L}{1+\Gamma_L},\quad Z_L=50\ \Omega$")
eq("eq_fits", r"$\alpha=a\sqrt{f}+b\,f+c\qquad n_m=n_0+\Delta n\,\dfrac{f}{f_c+f}\qquad \mathrm{Re}\,Z_c=Z_\infty+\dfrac{k_1}{\sqrt{f}}+\dfrac{k_2}{f}\qquad \mathrm{Im}\,Z_c=\dfrac{k_3}{\sqrt{f}}+\dfrac{k_4}{f}$", 18)

# --- touchstone vs fields (2 x 2)
fig, ax = plt.subplots(2, 2, figsize=(8.6, 6.0), sharex=True)
P = [(d["aT"], d["aF"], "α (dB/cm)", None), (d["nT"], d["nF"], "$n_m$", (2.20, 2.40)),
     (d["ZT"].real, d["ZF"].real, "Re $Z_c$ (Ω)", (40, 46)), (d["ZT"].imag, d["ZF"].imag, "Im $Z_c$ (Ω)", (-4, 4))]
for a, (yt, yf, lab, yl) in zip(ax.flat, P):
    a.plot(fT, yt, "-", color=NAVY, lw=1.4, label="touchstone"); a.plot(F, yf, "o", ms=3.2, color=ORANGE, label="fields")
    a.set_ylabel(lab); a.grid(alpha=0.3); a.set_xlim(0, 130)
    if yl: a.set_ylim(*yl)
for a in ax[1]: a.set_xlabel("Frequency (GHz)")
ax[0, 0].legend(frameon=False, fontsize=11.5, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "line_ts_vs_fields.png"), dpi=200); plt.close(fig)

# --- extrapolation, field route only (1 x 4)
import sys; sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
from mzm_interconnect.physics import fit_alpha_scaled, fit_nm_saturating, fit_impedance_physical, fit_impedance_imag
ff = np.linspace(1, 130, 400)
ex = [fit_alpha_scaled(ff, *d["pa"]), fit_nm_saturating(ff, *d["pn"]), fit_impedance_physical(ff, *d["pz"]), fit_impedance_imag(ff, *d["pzi"])]
fig, ax = plt.subplots(1, 4, figsize=(15.5, 3.9))
P = [(d["aFo"], d["aF"], "α (dB/cm)", None), (d["nFo"], d["nF"], "$n_m$", (2.20, 2.40)),
     (d["ZFo"].real, d["ZF"].real, "Re $Z_c$ (Ω)", (40, 46)), (d["ZFo"].imag, d["ZF"].imag, "Im $Z_c$ (Ω)", (-4, 4))]
for a, y, (yo, yn, lab, yl) in zip(ax, ex, P):
    a.axvspan(60, 130, color="#F1F3F8", zorder=0)
    a.plot(d["Fo"], yo, "o", ms=3, color=GREY, label="previous run, 1–60 GHz (fitted)")
    a.plot(F[F > 60], yn[F > 60], "o", ms=3, color=ORANGE, label="new run, 62–130 GHz")
    a.plot(ff, y, "-", color=NAVY, lw=1.6, label="fit, extrapolated")
    a.set_xlabel("Frequency (GHz)"); a.set_ylabel(lab); a.grid(alpha=0.3); a.set_xlim(0, 130)
    if yl: a.set_ylim(*yl)
ax[0].legend(frameon=False, fontsize=10.5, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "line_extrapolation.png"), dpi=200); plt.close(fig)
print("figures saved")
