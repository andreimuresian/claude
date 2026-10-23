"""Figures and equation images for the meeting deck (crosstalk_meeting.pptx)."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, ROOT)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import coupled_line as CL
OUT = os.path.join(HERE, "meeting_img"); os.makedirs(OUT, exist_ok=True)
NAVY = "#0E2268"; RED = "#F20013"
db = lambda x: 20*np.log10(np.abs(x)+1e-30)
def rd(fn):
    toks = []
    for l in open(fn):
        l = l.split('!')[0].strip()
        if not l or l.startswith('#'): continue
        toks += l.split()
    v = np.array(toks, float).reshape(-1, 33)
    return v[:, 0], (v[:, 1::2]*np.exp(1j*np.radians(v[:, 2::2]))).reshape(-1, 4, 4)
ds = CL.load_dataset()
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.grid": True, "grid.alpha": .3})
# validation: model (gold dn, band) vs 3-D at 1 and 5 mm, 50 ohm ports
fig, axs = plt.subplots(2, 2, figsize=(11, 6.2), sharex=True)
for j, (L, fn) in enumerate(((1, "LINEA0_1MM_200UM_PITCH.s4p"), (5, "LINEA0_5MM_200UM_PITCH.s4p"))):
    f, S = rd(os.path.join(HERE, "..", fn)); m = (f > 0.2) & (f <= 60)
    p = dict(f_max_GHz=60, xt_L_mm=L, ng=2.27, Zs_R=50, Zs_L_pH=0, Zs_C_fF=0, Rt_R=50, Rt_L_pH=0, Rt_C_fF=0)
    lo = CL.device_crosstalk(p, ds["dz_lo"], f[m]); hi = CL.device_crosstalk(p, ds["dz_hi"], f[m])
    fit = CL.device_crosstalk(p, 0.0023, f[m])
    for i, (k, nm) in enumerate(((2, "NEXT |S31|"), (3, "FEXT |S41|"))):
        ax = axs[i, j]; a, b = db(lo["block"]["S"][k][0]), db(hi["block"]["S"][k][0])
        ax.fill_between(f[m], np.minimum(a, b), np.maximum(a, b), color=RED, alpha=.25, lw=0, label="model, δ = 0.21–0.61 %")
        if k == 2: ax.plot(f[m], db(fit["block"]["S"][k][0]), color=RED, lw=1.2, label="model, δ = 0.23 % (fit to 1 mm)")
        ax.plot(f[m], db(S[m, k, 0]), color="k", lw=1.6, label="3-D CST (coworker)")
        ax.set_title(f"{nm}, L = {L} mm", fontsize=11); ax.set_ylim(-110, -30)
        if j == 0: ax.set_ylabel("dB")
        if i == 1: ax.set_xlabel("frequency (GHz)")
axs[0, 0].legend(fontsize=9, loc="lower right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "validation.png"), dpi=150)
# equations
EQ = {
 "eq_modes": r"$\gamma_{e,o}=\gamma_{3D}\pm\frac{j}{2}\Delta\beta,\qquad Z_{e,o}=Z_{3D}\left(1\pm\frac{\delta}{2}\right)$",
 "eq_coupling": r"$\delta=\frac{Z_e}{Z_o}-1\approx k_L+k_C,\qquad \frac{\Delta n}{n}=\frac{n_e-n_o}{n}\approx k_L-k_C$",
 "eq_single": r"$S_{11}=\frac{\Gamma\,(1-t^2)}{1-\Gamma^2t^2},\quad S_{21}=\frac{(1-\Gamma^2)\,t}{1-\Gamma^2t^2},\quad \Gamma=\frac{Z-z_0}{Z+z_0},\ t=e^{-\gamma L}$",
 "eq_xt": r"$\mathrm{NEXT}=\frac{1}{2}\left(S_{11}^{e}-S_{11}^{o}\right),\qquad \mathrm{FEXT}=\frac{1}{2}\left(S_{21}^{e}-S_{21}^{o}\right)$",
 "eq_next": r"$\mathrm{NEXT}\approx\frac{\delta}{4}\,(1-t^2)\;+\;\mathcal{O}(\Gamma\,\Delta\beta L)$",
 "eq_fext": r"$|\mathrm{FEXT}|\approx e^{-\alpha L}\,\frac{\pi f L\,\Delta n}{c}\;+\;\mathcal{O}(\Gamma\,\delta)$",
 "eq_nulls": r"$f_m=\frac{m\,c}{2nL}$",
 "eq_H": r"$H_k(f)=\frac{1}{L}\int_0^L V_k(z)\,e^{\,j\beta_o(z-L)}\,dz,\quad \beta_o=\frac{2\pi f n_g}{c}$",
 "eq_EO": r"$\mathrm{EO\ crosstalk}=\left|\frac{H_B(f)}{H_A(f)}\right|$",
 "eq_Vm": r"$V_m(z)=V_m^{+}\left[e^{-\gamma_m z}+\Gamma_{t,m}\,e^{-2\gamma_m L}\,e^{+\gamma_m z}\right],\qquad m=e,o$",
 "eq_Vplus": r"$V_m^{+}=\frac{E}{2}\,\frac{Z_m}{Z_m+Z_s}\,\frac{1}{1-\Gamma_{s,m}\Gamma_{t,m}e^{-2\gamma_m L}},\quad \Gamma_{s,m}=\frac{Z_s-Z_m}{Z_s+Z_m},\ \Gamma_{t,m}=\frac{R_t-Z_m}{R_t+Z_m}$",
 "eq_Hm": r"$H_m=\frac{e^{-j\beta_o L}}{L}\left[V_m^{+}\,F(-\gamma_m+j\beta_o)+V_m^{-}\,F(+\gamma_m+j\beta_o)\right],\qquad F(q)=\int_0^L e^{qz}dz=\frac{e^{qL}-1}{q}$",
 "eq_HAB": r"$H_A=\frac{1}{2}\left(H_e+H_o\right),\qquad H_B=\frac{1}{2}\left(H_e-H_o\right),\qquad \mathrm{EO\ crosstalk}=\left|\frac{H_B}{H_A}\right|$",
 "eq_ratio": r"$\frac{H_B}{H_A}\approx\frac{\delta}{4}\;-\;\frac{j\Delta\beta}{2}\left[\frac{L\,e^{qL}}{e^{qL}-1}-\frac{1}{q}\right],\qquad q=-\gamma+j\beta_o$",
 "eq_limit": r"$\frac{H_B}{H_A}\approx\frac{\delta}{4}-\frac{j\Delta\beta L}{4}=\frac{\delta}{4}+\frac{\mathrm{FEXT}}{2}$",
 "eq_back": r"$\frac{|F(\gamma+j\beta_o)|}{L}\approx\frac{1}{(\beta+\beta_o)L}$",
 "eq_VAB": r"$V_{A,B}(z)=\frac{1}{2}\left[V_e(z)\pm V_o(z)\right]$",
}
for k, t in EQ.items():
    fg = plt.figure(figsize=(0.1, 0.1)); fg.text(0, 0, t, fontsize=22, color=NAVY)
    fg.savefig(os.path.join(OUT, k + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.04, transparent=True); plt.close(fg)
print("ok")
