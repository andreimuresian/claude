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

# ===================== bend block (L+B+S) =====================
A = os.path.join(HERE, "..", "analysis130")
b = np.load(os.path.join(A, "lbs_bend_130.npz")); P = np.load(os.path.join(A, "parasitic_mode_130.npz")); C = np.load(os.path.join(A, "bend_compare_130.npz"))
Lo = np.load(os.path.join(A, "bend_loss_130.npz")); Pa = np.load(os.path.join(A, "bend_path_130.npz"))
f, SA, Fb, SB = b["f"], b["SA"], b["F"], b["SB"]; dB = lambda s: 20 * np.log10(abs(s))
# equations
eq("eq_chain", r"$T_{L+B+S}=P_1\,T_{line}(2.16)\;T_{bend}\;T_{line}(1.08)\,P_2\ \Rightarrow\ T_{bend}=T_{line}(2.16)^{-1}P_1^{-1}\,T_{L+B+S}\,P_2^{-1}\,T_{line}(1.08)^{-1}$", 17)
eq("eq_a2s", r"$S_{21}=\dfrac{2}{A+B/Z_c+C\,Z_c+D},\qquad S_{11}=\dfrac{A+B/Z_c-C\,Z_c-D}{A+B/Z_c+C\,Z_c+D}$", 17)
eq("eq_w1", r"$V_1(z)=V_1^{+}e^{-\gamma z}+V_1^{-}e^{+\gamma z},\qquad V_2(s)=V_2^{+}e^{-\gamma s}+V_2^{-}e^{+\gamma s}$", 17)
eq("eq_w2", r"$a_1=V_1^{+}e^{-\gamma L_1},\quad b_1=V_1^{-}e^{+\gamma L_1},\quad a_2=V_2^{-},\quad b_2=V_2^{+}\qquad (L_1=2.16\ \mathrm{mm})$", 17)
eq("eq_w3", r"$b_1=S_{11}a_1+S_{12}a_2,\qquad b_2=S_{21}a_1+S_{22}a_2,\qquad S_{12}=S_{21},\ S_{22}=S_{11}$", 17)
eq("eq_delay", r"$\varphi_{21}(f)=\arg S_{21}=\varphi_0-\omega\,\tau\ \Rightarrow\ \tau=-\dfrac{d\varphi_{21}}{d\omega}\ \ (\mathrm{fit\ 20-130\ GHz}),\qquad \mathrm{phase\ delay}=-\dfrac{\varphi_{21}}{\omega}=\tau-\dfrac{\varphi_0}{\omega}$", 17)
eq("eq_vp", r"$v_c=\dfrac{v_{in}+v_{out}}{2},\qquad v_p=\dfrac{v_{in}-v_{out}}{2}$")
eq("eq_comb", r"$f_m=m\,\dfrac{c}{2\,n_p\,L_{path}}$")

# routes
tauA, tauB = 5.025, 4.996
fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
ax[0].plot(f, dB(SA[:, 1, 0]), "-", color=NAVY, lw=1.3, label="touchstone"); ax[0].plot(Fb, dB(SB[:, 1, 0]), "o", ms=3, color=ORANGE, label="fields")
ax[0].set_ylim(-1.4, 0); ax[0].set_ylabel("|S$_{21}$| (dB)")
ax[1].plot(f, b["tpA"], "-", color=NAVY, lw=1.3, label="phase delay"); ax[1].plot(Fb, b["tpB"], "o", ms=3, color=ORANGE)
ax[1].axhline(tauA, color=NAVY, ls="--", lw=1); ax[1].axhline(tauB, color=ORANGE, ls="--", lw=1)
ax[1].text(128, 4.62, f"slope delay: touchstone {tauA:.2f} ps, fields {tauB:.2f} ps", ha="right", fontsize=10)
ax[1].set_ylim(4.5, 5.5); ax[1].set_ylabel("Delay (ps)")
ax[2].plot(f, abs(SA[:, 0, 0]), "-", color=NAVY, lw=1.3); ax[2].plot(Fb, abs(SB[:, 0, 0]), "o", ms=3, color=ORANGE); ax[2].set_ylim(0, 0.2); ax[2].set_ylabel("|S$_{11}$|")
for a in ax:
    a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3)
    for x in P["dips"]: a.axvline(x, color=GREY, lw=0.7, ls=":")
ax[0].legend(frameon=False, fontsize=11, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "bend_routes.png"), dpi=200); plt.close(fig)

# parasitic: spectrum on the lines + profile along the path
S_, VC, VP, SEG = Pa["S"], Pa["VC"], Pa["VP"], Pa["SEG"]
cell = lambda x: np.convolve(x, np.ones(36) / 36, "same")
fig, ax = plt.subplots(1, 2, figsize=(13.2, 4.2), gridspec_kw={"width_ratios": [1.25, 1]})
ax[0].plot(P["F"], 20 * np.log10(P["r1"]), "o-", ms=3, lw=1, color=NAVY, label="line 1")
ax[0].plot(P["F"], 20 * np.log10(P["r2"]), "s-", ms=3, lw=1, color=ORANGE, label="line 2")
for j, x in enumerate(P["dips"]): ax[0].axvline(x, color=GREY, lw=0.8, ls=":", label="dips of the bend |S$_{21}$|" if j == 0 else None)
ax[0].plot(P["comb"], np.full(len(P["comb"]), -3), "v", color=RED, ms=8, label=f"$m\\,c/(2n_pL)$, $n_p$ = {float(P['npm']):.2f}, L = 4.11 mm")
ax[0].set_ylim(-50, 0); ax[0].set_xlim(0, 130); ax[0].set_xlabel("Frequency (GHz)"); ax[0].set_ylabel("|v$_p$| / |v$_c$| (dB)"); ax[0].grid(alpha=0.3)
ax[0].legend(frameon=False, fontsize=9.5, loc="lower right")
for lo, hi in ((2.16, 2.434), (2.756, 3.03)): ax[1].axvspan(lo, hi, color="#FBE3D6", zorder=0)
ax[1].axvspan(2.434, 2.756, color="#F6C7AE", zorder=0)
for q, col in ((20, GREY), (40, BLUE), (78, ORANGE), (108, NAVY)):
    i = np.argmin(abs(Pa["F"] - q)); vc, vp = VC[i].copy(), VP[i].copy()
    for k in (0, 4): m = SEG == k; vc[m], vp[m] = cell(VC[i][m]), cell(VP[i][m])
    ok = np.ones(len(S_), bool)
    for k in (0, 4): idx = np.where(SEG == k)[0]; ok[idx[:18]] = False; ok[idx[-18:]] = False
    ax[1].plot(S_[ok], abs(vp[ok]) / abs(vc[ok]), ".", ms=2.2, color=col, label=f"{Pa['F'][i]:.0f} GHz")
ax[1].text(2.595, 0.62, "U-bend", ha="center", fontsize=10); ax[1].text(1.0, 0.62, "line 1", ha="center", fontsize=10); ax[1].text(3.6, 0.62, "line 2", ha="center", fontsize=10)
ax[1].set_xlim(0, 4.11); ax[1].set_ylim(0, 0.68); ax[1].set_xlabel("Path from port 1 (mm)"); ax[1].set_ylabel("|v$_p$| / |v$_c$|"); ax[1].grid(alpha=0.3)
ax[1].legend(frameon=False, fontsize=9.5, loc="upper left", ncol=2)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "bend_parasitic.png"), dpi=200); plt.close(fig)

# loss: smooth part vs line, and loss per section (field route, 10-60 GHz)
fig, ax = plt.subplots(1, 2, figsize=(13.2, 4.1))
ax[0].plot(f, dB(SA[:, 1, 0]), "-", color=NAVY, lw=1.2, label="bend block (touchstone)")
ax[0].plot(f, C["trend"], "--", color=ORANGE, lw=1.8, label="cubic fit outside the dips (±2.5 GHz)")
ax[0].plot(f, C["line_eq"], ":", color=GREY, lw=2.2, label="0.87 mm of straight buried line")
ax[0].set_ylim(-1.4, 0); ax[0].set_xlim(0, 130); ax[0].set_xlabel("Frequency (GHz)"); ax[0].set_ylabel("|S$_{21}$| (dB)"); ax[0].grid(alpha=0.3)
ax[0].legend(frameon=False, fontsize=10, loc="lower left")
FF = Lo["F"]; qs = [10, 20, 40, 50, 60]; ii = [int(np.argmin(abs(FF - q))) for q in qs]; xx = np.arange(len(qs)); wdt = 0.26
ax[1].bar(xx - wdt, [Lo["rise1"][i] + Lo["rise2"][i] for i in ii], wdt, color=BLUE, label="the two transitions (vertical step + 50 µm gap taper)")
ax[1].bar(xx, [Lo["raised"][i] for i in ii], wdt, color=ORANGE, label="raised straights + U-bend (0.76 mm)")
ax[1].bar(xx + wdt, [Lo["total"][i] for i in ii], wdt, color=NAVY, label="whole block (plane 1 → plane 2)")
ax[1].set_xticks(xx); ax[1].set_xticklabels([f"{q} GHz" for q in qs]); ax[1].axhline(0, color="#5A606E", lw=0.8)
ax[1].set_ylim(-0.5, 0.05); ax[1].set_ylabel("Change of the forward wave (dB)"); ax[1].grid(alpha=0.3, axis="y")
ax[1].legend(frameon=False, fontsize=10, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "bend_loss.png"), dpi=200); plt.close(fig)
print("bend figures saved")

# ===================== full equaliser: steps 1-2 =====================
Q = np.load(os.path.join(A, "full_eq_analysis_130.npz")); FP = np.load(os.path.join(A, "full_eq_path_130.npz")); LS_ = np.load(os.path.join(A, "ls_extraction_130.npz"))
FF = Q["F"]; cols = {"L1": NAVY, "L2": ORANGE, "L3": BLUE}
fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
for k, ln in enumerate(("L1", "L2", "L3")):
    ax[0].plot(FF, Q["a"][k], "o", ms=2.5, color=cols[ln], label=ln); ax[1].plot(FF, Q["n"][k], "o", ms=2.5, color=cols[ln], label=ln)
ax[0].plot(LS_["F"], LS_["aF"], "k-", lw=1.2, label="L+S"); ax[1].plot(LS_["F"], LS_["nF"], "k-", lw=1.2, label="L+S")
ax[0].set_ylabel("α (dB/cm)"); ax[1].set_ylabel("$n_m$"); ax[1].set_ylim(2.2, 2.4)
trB = np.interp(FF, f, C["trend"]); pair = dB(Q["B1"][1]) + dB(Q["B2"][1])
ax[2].plot(FF, pair, "o-", ms=3, lw=1, color=ORANGE, label="bend 1 + bend 2 (full run)")
ax[2].plot(FF, 2 * trB, "--", color=NAVY, lw=1.8, label="2 × smoothed L+B+S bend")
ax[2].plot(FF, 2 * dB(SB[:, 1, 0]), ":", color=GREY, lw=1.6, label="2 × L+B+S bend, dips kept")
ax[2].set_ylim(-2.2, 0); ax[2].set_ylabel("|S$_{21}$| of the two bends (dB)")
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=9.5, loc="lower left" if a is not ax[1] else "upper right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "full_blocks.png"), dpi=200); plt.close(fig)

fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9), gridspec_kw={"width_ratios": [1, 1.15, 1]})
ax[0].plot(P["F"], 20 * np.log10(P["r2"]), "-", color=GREY, lw=1.6, label="L+B+S, after one bend")
ax[0].plot(FF, 20 * np.log10(Q["r"][1]), "o-", ms=2.5, lw=1, color=ORANGE, label="full run, L2 (between the bends)")
ax[0].plot(FF, 20 * np.log10(Q["r"][2]), "o-", ms=2.5, lw=1, color=BLUE, label="full run, L3 (after both bends)")
ax[0].set_ylim(-60, 0); ax[0].set_ylabel("|v$_p$| / |v$_c$| (dB)"); ax[0].legend(frameon=False, fontsize=9, loc="lower right")
Sx, VCx, VPx, SGx, nm = FP["S"], FP["VC"], FP["VP"], FP["SEG"], list(FP["names"])
for nme in ("arc 1", "arc 2"): ss = Sx[SGx == nm.index(nme)]; ax[1].axvspan(ss[0], ss[-1], color="#F6C7AE", zorder=0)
for q, col in ((30, GREY), (70, ORANGE), (110, NAVY)):
    i = np.argmin(abs(FP["F"] - q)); vc, vp = VCx[i].copy(), VPx[i].copy()
    for ln in ("L1", "L2", "L3"): mm = SGx == nm.index(ln); vc[mm] = np.convolve(VCx[i][mm], np.ones(36) / 36, "same"); vp[mm] = np.convolve(VPx[i][mm], np.ones(36) / 36, "same")
    ok = np.ones(len(Sx), bool)
    for ln in ("L1", "L2", "L3"): ii = np.where(SGx == nm.index(ln))[0]; ok[ii[:18]] = False; ok[ii[-18:]] = False
    ax[1].plot(Sx[ok], abs(vp[ok]) / abs(vc[ok]), ".", ms=2, color=col, label=f"{FP['F'][i]:.0f} GHz")
for x, t in ((1.35, "L1"), (4.29, "L2"), (6.6, "L3")): ax[1].text(x, 0.36, t, ha="center", fontsize=10.5, fontweight="bold")
ax[1].set_xlim(0, 7.32); ax[1].set_ylim(0, 0.5); ax[1].set_xlabel("Path from port 1 (mm)"); ax[1].set_ylabel("|v$_p$| / |v$_c$|"); ax[1].legend(frameon=False, fontsize=9.5, loc="upper center", ncol=3)
dev = Q["s21"] - Q["trend"]; ax[2].plot(Q["fS"], dev, "-", color=NAVY, lw=1.2, label="|S$_{21}$| − smooth trend")
for j, x in enumerate([14.3, 23.9, 34.1, 43.8, 53.2, 63.0, 73.2, 82.8, 91.6, 101.9, 112.4, 120.2]): ax[2].plot(x, 0.13, "v", color=GREY, ms=6, label="|S$_{11}$| peaks (coplanar ripple)" if j == 0 else None)
for j, x in enumerate([36, 45, 53, 64, 72, 82, 90, 98, 108, 116]): ax[2].plot(x, -0.5, "^", color=ORANGE, ms=6, label="v$_p$ peaks on L1/L3" if j == 0 else None)
ax[2].set_ylim(-0.95, 0.2); ax[2].set_ylabel("dB"); ax[2].legend(frameon=False, fontsize=9, loc="lower left", ncol=1)
for a in (ax[0], ax[2]): a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)")
for a in ax: a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "full_parasitic.png"), dpi=200); plt.close(fig)
print("full-run figures saved")

# ===================== two-mode bend =====================
TMB = np.load(os.path.join(A, "two_mode_bend.npz")); Ft = TMB["F"]; mm = Ft >= 10
eq("eq_tm1", r"$b_{1c}=r_c\,a_{1c}+t_c\,a_{2c}+\rho\,\kappa\,a_{2p},\qquad b_{2c}=t_c\,a_{1c}+r_c\,a_{2c}+\rho\,\kappa\,a_{1p}$", 17)
eq("eq_tm2", r"$b_{1p}=t_p\,a_{2p}+\kappa\,a_{2c},\qquad b_{2p}=t_p\,a_{1p}+\kappa\,a_{1c},\qquad \rho=Z_c/Z_p$", 17)
fig, ax = plt.subplots(1, 3, figsize=(13.5, 3.9))
ax[0].plot(Fb, dB(SB[:, 1, 0]), ":", color=GREY, lw=1.6, label="two-port (dips included)")
ax[0].plot(Ft, dB(TMB["tc"]), "o-", ms=3, lw=1, color=NAVY, label="two-mode: coplanar t$_c$")
ax[0].set_ylim(-1.4, 0); ax[0].set_ylabel("Bend transmission (dB)"); ax[0].legend(frameon=False, fontsize=10, loc="lower left")
ax[1].plot(Ft[mm], abs(TMB["kap"][mm]), "o", ms=3, color=ORANGE, label="|κ| from the L+B+S fields")
ax[1].plot(Ft, 1.99e-3 * Ft - 4.11e-6 * Ft ** 2, "-", color=NAVY, lw=1.5, label="smooth: 0.002 f (GHz)")
ax[1].set_ylim(0, 0.25); ax[1].set_ylabel("Conversion |κ| (coplanar → parasitic)"); ax[1].legend(frameon=False, fontsize=10, loc="upper left")
ax[2].plot(TMB["rhos"][1:], TMB["rough"][1:], "-", color=NAVY, lw=1.5); ax[2].axvline(float(TMB["rho"]), color=ORANGE, ls="--", lw=1.2)
ax[2].set_xscale("log"); ax[2].set_xlabel("ρ = Z$_c$ / Z$_p$"); ax[2].set_ylabel("Roughness of |t$_c$| (dB rms)"); ax[2].text(float(TMB["rho"]) * 1.1, 0.08, f"ρ = {float(TMB['rho']):.2f}", color=ORANGE)
for a in ax[:2]: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)")
for a in ax: a.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "two_mode_coeffs.png"), dpi=200); plt.close(fig)
print("two-mode figures saved")
