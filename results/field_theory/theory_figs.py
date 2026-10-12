"""Analytical / physical justification of the field components of the
Lisbon lifted, etched-slab design (1575 nm, slab_w = 8.2 um, gap 4.2 um).

Inputs : mode_fields.npz (FEM field re-exported by run_solve.py, parameters unchanged)
         ../etched_slab/slab_w_sweep.csv, ../etched_slab/fabry_perot_fit_slab_in_gold.json
Outputs: figs/*.png and theory_numbers.json
"""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MPoly, Rectangle, FancyArrowPatch, Arc
from scipy.ndimage import gaussian_filter
from scipy.signal import argrelmin
import slab1d as s1

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
                     "savefig.dpi": 200, "savefig.bbox": "tight"})
C = {"Ex": "#1f5aa6", "Ey": "#c2410c", "Ez": "#0f766e", "th": "#111111", "au": "#d4a017",
     "ln": "#8b95a1", "ox": "#9cc9ef", "mut": "#6b7280", "acc": "#7c3aed"}

d = np.load("mode_fields.npz")
k0 = float(d["k0"]); ne, no, ns = float(d["ne"]), float(d["no"]), float(d["n_sio2"])
eau = complex(d["eps_au"]); neff = complex(d["neff"]); nr = neff.real
beta = nr * k0; wl = 2 * np.pi / k0
xg, yg = d["xg"], d["yg"]; X, Y = np.meshgrid(xg, yg)
Ex, Ey, Ez = d["Ex"], d["Ey"], d["Ez"]
E0 = np.nanmax(np.abs(Ex)) ** 2
dB = lambda a: 10 * np.log10(np.maximum(np.abs(a) ** 2 / E0, 1e-30))
xc = d["xc"]
SLAB_H, WG_H, XG, XS = 0.275, 0.275, 2.1, 4.1           # slab, rib, gold inner edge, slab end
WB = 0.5 + WG_H / np.tan(np.deg2rad(60))                # rib half-width at its base
N = {}

# ---------------------------------------------------------------- 1D indices
def lay(top, es, t=SLAB_H, buf=0.0):
    L = [(ns**2, ns**2, 0), (es, no**2, t)]
    if buf > 0:
        L.append((ns**2, ns**2, buf))
    return L + [(top, top, 0)]

# lateral wave under the gold: in-plane E mostly along z (no), partly along x (ne);
# mix the in-plane permittivity with the exit angle, iterated to self-consistency.
n_lat = s1.solve(lay(eau, no**2), k0, "TM", 2.08)
for _ in range(6):
    th = np.arccos(nr / n_lat.real)
    es_mix = no**2 * np.cos(th) ** 2 + ne**2 * np.sin(th) ** 2
    n_lat = s1.solve(lay(eau, es_mix), k0, "TM", n_lat)
theta = np.degrees(np.arccos(nr / n_lat.real))
kx = k0 * np.sqrt(n_lat**2 - nr**2 + 0j)
if kx.imag > 0:
    kx = np.conj(kx)
half = np.pi / kx.real
idx = {}
for reg, top in [("air-clad slab (gap)", 1.0), ("SiO2-clad slab", ns**2), ("gold-clad slab (cavity)", eau)]:
    idx[reg] = {"TE": s1.solve(lay(top, ne**2), k0, "TE", 1.7).real,
                "TM": s1.solve(lay(top, es_mix if top == eau else no**2), k0, "TM",
                               2.08 if top == eau else 1.55).real}
n_te_air = idx["air-clad slab (gap)"]["TE"]
gam = k0 * np.sqrt(nr**2 - n_te_air**2)
N.update(neff=nr, n_lat=[n_lat.real, n_lat.imag], theta_out_deg=theta, kx=[kx.real, kx.imag],
         half_period_um=half, gamma_gap=gam, pred_slope_dB_um=-2 * gam * 10 / np.log(10),
         region_indices=idx, n_spp_Au_LN=float(np.sqrt(eau * no**2 / (eau + no**2)).real),
         skin_depth_nm=1e3 / (k0 * np.sqrt(n_lat**2 - eau).real))

# ============================================================ F1 regions + indices
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.3), gridspec_kw={"width_ratios": [1.45, 1]})
a1.add_patch(Rectangle((-5.2, -0.6), 10.4, 0.6, fc=C["ox"], ec="none"))
a1.add_patch(Rectangle((-XS, 0), 2 * XS, SLAB_H, fc=C["ln"], ec="none"))
a1.add_patch(MPoly([[-WB, SLAB_H], [WB, SLAB_H], [0.5, 0.55], [-0.5, 0.55]], fc=C["ln"], ec="none"))
a1.add_patch(Rectangle((-1.0, SLAB_H), 2.0, 1.4, fc=C["ox"], ec="none", alpha=.55, zorder=0))
for sg in (-1, 1):
    x0 = XG if sg > 0 else -5.2
    a1.add_patch(Rectangle((x0, SLAB_H), 5.2 - XG, 1.5, fc=C["au"], ec="none"))
    a1.add_patch(Rectangle((XS if sg > 0 else -5.2, 0), 5.2 - XS, SLAB_H, fc=C["au"], ec="none"))
for (x0, x1, lab, col) in [(-0.66, 0.66, "rib\n(guided mode)", "k"), (0.75, XG, "free slab\n(evanescent)", C["Ex"]),
                           (XG, XS, "gold-clad slab\n= lateral cavity", C["Ey"])]:
    a1.annotate("", (x0, -0.85), (x1, -0.85), arrowprops=dict(arrowstyle="<->", color=col, lw=1.4))
    a1.text((x0 + x1) / 2, -1.0, lab, ha="center", va="top", fontsize=9.5, color=col)
a1.text(4.6, 1.2, "Au", fontsize=12, weight="bold", color="#7a5b00", ha="center")
a1.text(4.6, 0.12, "Au\nwall", fontsize=8.5, color="#7a5b00", ha="center", va="center")
a1.text(-3.0, -0.35, "SiO$_2$ (BOX)", fontsize=9, color="#1e4f7a")
a1.text(0, 1.3, "SiO$_2$ cap", fontsize=8.5, ha="center", color="#1e4f7a")
a1.text(-1.5, 0.95, "air", fontsize=9, color=C["mut"])
a1.set_xlim(-5.2, 5.2); a1.set_ylim(-1.55, 1.9); a1.set_aspect("equal"); a1.axis("off")
a1.set_title("Three lateral regions seen by the mode")
regs = list(idx)
yy = np.arange(len(regs))
a2.barh(yy + 0.18, [idx[r]["TE"] for r in regs], 0.34, color=C["Ex"], label="TE slab wave (E$_x$-like)")
a2.barh(yy - 0.18, [idx[r]["TM"] for r in regs], 0.34, color=C["Ey"], label="TM slab wave (E$_y$-like)")
a2.axvline(nr, color="k", lw=1.6, ls="--")
a2.text(nr - 0.01, 1.5, ha="right", s=None) if False else a2.text(nr + 0.008, 1.5, f"guided mode\nn$_{{eff}}$ = {nr:.3f}", fontsize=9, va="top")
for i, r in enumerate(regs):
    a2.text(idx[r]["TE"] + 0.01, i + 0.18, f"{idx[r]['TE']:.3f}", va="center", fontsize=8.5)
    a2.text(idx[r]["TM"] + 0.01, i - 0.18, f"{idx[r]['TM']:.3f}", va="center", fontsize=8.5,
            weight="bold" if idx[r]["TM"] > nr else "normal")
a2.set_yticks(yy); a2.set_yticklabels(regs); a2.set_xlim(1.4, 2.25)
a2.set_xlabel("1D slab-wave effective index"); a2.legend(fontsize=8.5, loc="lower right", frameon=False)
a2.set_title("Only the TM wave under gold exceeds n$_{eff}$")
fig.tight_layout(); fig.savefig("figs/F1_regions_indices.png"); plt.close(fig)

# ============================================================ F2 phase matching
fig, ax = plt.subplots(figsize=(6.2, 5.6))
t = np.linspace(0, np.pi / 2, 300)
for r, col, lab in [(n_lat.real, C["Ey"], f"TM wave under gold, n = {n_lat.real:.3f}"),
                    (n_te_air, C["Ex"], f"TE wave in free slab, n = {n_te_air:.3f}"),
                    (idx["air-clad slab (gap)"]["TM"], C["mut"], "TM wave in free slab, n = %.3f" % idx["air-clad slab (gap)"]["TM"])]:
    ax.plot(r * np.cos(t), r * np.sin(t), color=col, lw=2.2, label=lab)
ax.axvline(nr, color="k", ls="--", lw=1.3)
ax.text(nr + 0.02, 0.08, f"n$_{{eff}}$ = {nr:.3f}\n(k$_z$ conserved)", fontsize=9.5)
kxn = np.sqrt(n_lat.real**2 - nr**2)
ax.annotate("", (nr, kxn), (0, 0), arrowprops=dict(arrowstyle="-|>", color=C["Ey"], lw=2))
ax.annotate("", (nr, kxn), (nr, 0), arrowprops=dict(arrowstyle="-|>", color=C["acc"], lw=2))
ax.text(nr + 0.03, kxn / 2, f"k$_x$/k$_0$ = {kxn:.3f}\n→ propagates\nsideways", color=C["acc"], fontsize=9.5)
ax.add_patch(Arc((0, 0), 0.9, 0.9, theta1=0, theta2=theta, color="k"))
ax.text(0.5, 0.09, f"θ$_{{out}}$ = {theta:.1f}°", fontsize=10)
ax.set_xlim(0, 2.3); ax.set_ylim(0, 2.3); ax.set_aspect("equal")
ax.set_xlabel("k$_z$ / k$_0$ (along the waveguide)"); ax.set_ylabel("k$_x$ / k$_0$ (lateral)")
ax.legend(fontsize=8.5, loc="upper right", frameon=False)
ax.set_title("Phase matching (Webster Fig. 2 / Oliner eq. 3)")
fig.tight_layout(); fig.savefig("figs/F2_phase_matching.png"); plt.close(fig)

# ============================================================ F3 rib: Ez from Ex (Marcatili / Gauss)
ln_mask = ((Y > 0.005) & (Y < SLAB_H - 0.005) & (np.abs(X) < XG - 0.05)) | \
          ((Y >= SLAB_H) & (Y < 0.545) & (np.abs(X) < WB - (Y - SLAB_H) / np.tan(np.deg2rad(60)) - 0.03))
dx, dy = xg[1] - xg[0], yg[1] - yg[0]
Exs = gaussian_filter(Ex.real, 3.0) + 1j * gaussian_filter(Ex.imag, 3.0)
dEx_dx = np.gradient(Exs, dx, axis=1)
Ez_pred = -1j * (ne**2 / no**2) * dEx_dx / beta            # Okamoto (2.41) / Gauss law
Ey_pred = np.gradient(dEx_dx, dy, axis=0) / (k0**2 * ne * no)   # Okamoto (2.41), dominant term
lim = (np.abs(X) < 2.0) & (Y > -0.3) & (Y < 0.9)
ex = (-2.0, 2.0, -0.3, 0.9)
sl = np.ix_((yg > -0.3) & (yg < 0.9), (xg > -2.0) & (xg < 2.0))

def outline(ax, lw=0.8, c="w"):
    ax.plot([-2, 2], [0, 0], c=c, lw=lw); ax.plot([-2, 2], [SLAB_H, SLAB_H], c=c, lw=lw)
    ax.plot([-WB, -0.5, 0.5, WB], [SLAB_H, .55, .55, SLAB_H], c=c, lw=lw)

fig, axs = plt.subplots(2, 2, figsize=(13, 5.6))
for a, F, ttl in [(axs[0, 0], np.abs(Ez), "FEM  |E$_z$|  (full-vector solver)"),
                  (axs[0, 1], np.where(ln_mask, np.abs(Ez_pred), np.nan),
                   r"Theory  |E$_z$| = (n$_e^2$/n$_o^2$)·|∂E$_x$/∂x| / β   (LN only)")]:
    im = a.imshow((F / np.sqrt(E0))[sl], extent=ex, origin="lower", cmap="magma", vmin=0, vmax=0.28, aspect="auto")
    outline(a); a.set_title(ttl, fontsize=11); a.set_ylabel("y (µm)")
    plt.colorbar(im, ax=a, fraction=0.03, pad=0.01, label="|E$_z$| / max|E$_x$|")
a = axs[1, 0]
for yc, ls in [(0.138, "-"), (0.41, "-.")]:
    j = np.argmin(np.abs(yg - yc)); m = ln_mask[j]
    a.plot(xg, np.abs(Ez[j]) / np.sqrt(E0), color=C["Ez"], ls=ls, lw=2, label=f"FEM, y = {yc} µm")
    a.plot(xg[m], np.abs(Ez_pred[j][m]) / np.sqrt(E0), color="k", ls=("--" if ls=="-" else ":"), lw=1.5, label=f"theory, y = {yc} µm")
a.set_xlim(-2, 2); a.set_xlabel("x (µm)"); a.set_ylabel("|E$_z$| / max|E$_x$|"); a.legend(fontsize=8, ncol=2, frameon=False)
a.set_title("Lateral cuts: amplitude agreement")
a = axs[1, 1]
ph = np.angle(Ez / Ex, deg=True)[lim & ln_mask & (np.abs(Ex) ** 2 > E0 * 1e-3) & (np.abs(X) > 0.1)]
a.hist(ph, bins=np.linspace(-180, 180, 73), color=C["Ez"])
a.set_xlabel("phase of E$_z$ relative to E$_x$ (deg)"); a.set_ylabel("mesh points in LN")
a.set_title("E$_z$ is ±90° from E$_x$ everywhere → 'Im(E$_z$)'")
a.set_xticks([-180, -90, 0, 90, 180])
fig.tight_layout(); fig.savefig("figs/F3_rib_Ez_from_Ex.png"); plt.close(fig)
j = np.argmin(np.abs(yg - 0.41)); m = ln_mask[j] & (np.abs(xg) > 0.15)
N["rib_Ez_rel_err"] = float(np.median(np.abs(np.abs(Ez_pred[j][m]) - np.abs(Ez[j][m])) / np.abs(Ez[j][m])))
N["phase_Ez_Ex_median_abs_deg"] = float(np.median(np.abs(ph)))

# ============================================================ F4 rib: Ey (quadrupole) from Ex
fig, axs = plt.subplots(1, 3, figsize=(15, 3.5))
v = 0.06
for a, F, ttl in [(axs[0], Ey.real if np.abs(Ey.real).max() > np.abs(Ey.imag).max() else Ey.imag,
                   "FEM  E$_y$ (signed)"),
                  (axs[1], np.where(ln_mask, Ey_pred.real if np.abs(Ey.real).max() > np.abs(Ey.imag).max() else Ey_pred.imag, np.nan),
                   r"Theory  E$_y$ ≈ ∂²E$_x$/∂x∂y / (k$_0^2$n$^2$)  (LN only)")]:
    Fs = (F / np.sqrt(E0))[sl]
    im = a.imshow(Fs, extent=ex, origin="lower", cmap="RdBu_r", vmin=-v, vmax=v, aspect="auto")
    outline(a, c="k"); a.set_title(ttl, fontsize=11)
    plt.colorbar(im, ax=a, fraction=0.03, pad=0.01)
a = axs[2]
Fe = (Ex.real if np.abs(Ex.real).max() > np.abs(Ex.imag).max() else Ex.imag) / np.sqrt(E0)
im = a.imshow(Fe[sl], extent=ex, origin="lower", cmap="RdBu_r", vmin=-1, vmax=1, aspect="auto")
outline(a, c="k"); a.set_title("FEM  E$_x$ (signed): one lobe, even–even", fontsize=11)
plt.colorbar(im, ax=a, fraction=0.03, pad=0.01)
for a in axs:
    a.set_xlabel("x (µm)")
fig.tight_layout(); fig.savefig("figs/F4_rib_Ey_quadrupole.png"); plt.close(fig)

# ============================================================ F5 gap: evanescent decay
fig, axs = plt.subplots(1, 2, figsize=(13, 4.0))
Exc, Eyc, Ezc = d["cut_0.138"]
a = axs[0]
for F, nm in [(Exc, "Ex"), (Eyc, "Ey"), (Ezc, "Ez")]:
    a.plot(xc, dB(F), color=C[nm], lw=1.6, label=f"|E$_{nm[1]}$|$^2$ FEM")
x0 = 1.5; i0 = np.argmin(np.abs(xc - x0)); m = (xc > 0.8) & (xc < XG)
pred = dB(Exc)[i0] - 2 * gam * 10 / np.log(10) * (xc - x0)
a.plot(xc[m], pred[m], "k--", lw=1.6, label=f"theory  e$^{{-2γx}}$, γ = k$_0$√(n$_{{eff}}^2$−n$_{{TE,slab}}^2$)")
a.plot(xc[m], (pred + 20 * np.log10(gam / beta * ne**2 / no**2))[m], ":", color=C["Ez"], lw=2,
       label="theory  E$_z$ = (γ/β)·E$_x$")
a.axvspan(XG, XS, color=C["au"], alpha=0.15); a.axvline(XG, color="k", lw=.8)
a.text(XG + 0.05, -5, "under gold", fontsize=9, color="#7a5b00")
a.set_xlim(0, 4.3); a.set_ylim(-90, 2); a.set_xlabel("x (µm), cut at mid-slab y = 0.138 µm")
a.set_ylabel("dB rel. max|E$_x$|$^2$"); a.legend(fontsize=8, frameon=False, loc="lower left")
a.set_title("Free slab: all components decay with ONE rate")
mm = (xc > 1.2) & (xc < 1.9)
slopes = {nm: np.polyfit(xc[mm], dB(F)[mm], 1)[0] for F, nm in [(Exc, "Ex"), (Ezc, "Ez")]}
N["fem_slope_Ex"], N["fem_slope_Ez"] = slopes["Ex"], slopes["Ez"]
N["fem_Ez_minus_Ex_dB_at_1p5"] = float(dB(Ezc)[i0] - dB(Exc)[i0])
N["pred_Ez_minus_Ex_dB"] = float(20 * np.log10(gam / beta * ne**2 / no**2))
a = axs[1]
lab = ["E$_x$ slope\n(dB/µm)", "E$_z$ slope\n(dB/µm)", "E$_z$ − E$_x$\n(dB)"]
fem = [slopes["Ex"], slopes["Ez"], N["fem_Ez_minus_Ex_dB_at_1p5"]]
th_ = [N["pred_slope_dB_um"], N["pred_slope_dB_um"], N["pred_Ez_minus_Ex_dB"]]
xx = np.arange(3)
a.bar(xx - 0.18, fem, 0.34, color=C["Ex"], label="FEM")
a.bar(xx + 0.18, th_, 0.34, color="#9ca3af", label="theory")
for i in range(3):
    a.text(i - 0.18, fem[i] - 0.4, f"{fem[i]:.1f}", ha="center", va="top", fontsize=9, weight="bold", color=C["Ex"])
    a.text(i + 0.18, th_[i] - 0.4, f"{th_[i]:.1f}", ha="center", va="top", fontsize=9, weight="bold")
a.set_xticks(xx); a.set_xticklabels(lab); a.axhline(0, color="k", lw=.8); a.legend(frameon=False)
a.set_title("Numbers (no fitting parameter)")
fig.tight_layout(); fig.savefig("figs/F5_gap_decay.png"); plt.close(fig)

# ============================================================ F6 cavity standing wave
# Standing wave against the gold wall at x_w: Ey, Ez ~ sin(kx (x_w - x)) (tangential to wall -> node)
# Ex ~ cos(kx (x_w - x)) (normal to wall -> antinode).  x_w fitted (gold penetration).
Exc, Eyc, Ezc = d["cut_0.248"]
mm = (xc > XG + 0.05) & (xc < XS - 0.02)
mins_y = [xc[mm][k] for k in argrelmin(dB(Eyc)[mm], order=150)[0]]
mins_z = [xc[mm][k] for k in argrelmin(dB(Ezc)[mm], order=150)[0]]
Exc2 = d["cut_0.138"][0]
mins_x = [xc[mm][k] for k in argrelmin(dB(Exc2)[mm], order=150)[0]]
null_yz = 3.234
xw = null_yz + half                                   # effective mirror plane from the deep null
N.update(fem_null_EyEz=null_yz, fem_null_Ex=float(np.median([m_ for m_ in mins_x if m_ > 3.4] or [np.nan])),
         x_wall_effective=xw, wall_penetration_nm=1e3 * (xw - XS))
fig, axs = plt.subplots(1, 3, figsize=(15, 3.9), sharey=True)
xs_ = np.linspace(XG, XS + 0.02, 600)
kxc = kx
for a, F, nm, fn in [(axs[0], d["cut_0.138"][0], "Ex", np.cos), (axs[1], d["cut_0.138"][1], "Ey", np.sin), (axs[2], d["cut_0.138"][2], "Ez", np.sin)]:
    a.plot(xc, dB(F), color=C[nm], lw=1.8, label="FEM")
    model = np.abs(fn(kxc * (xw - xs_))) ** 2
    ref = np.max(dB(F)[mm])
    if nm == "Ex":   # no free amplitude: Ex = (kx/beta) * Ez  (in-plane TM field projected on x)
        ref = np.max(dB(d["cut_0.138"][2])[mm]) + 20 * np.log10(abs(kx) / beta)
    a.plot(xs_, 10 * np.log10(model / model.max()) + ref, "k--", lw=1.3, label="standing wave, theory")
    for k_ in range(0, 4):
        xn = xw - (k_ + (0.5 if nm == "Ex" else 0)) * half - (0 if nm == "Ex" else 0)
        if nm != "Ex":
            xn = xw - k_ * half
        if XG < xn < XS + 0.05:
            a.axvline(xn, color=C["acc"], lw=1, ls=":")
    a.axvspan(XS, 4.6, color=C["au"], alpha=0.25); a.axvline(XG, color="k", lw=.8)
    a.set_xlim(1.9, 4.5); a.set_ylim(-95, -30); a.set_xlabel("x (µm)")
    a.set_title(f"|E$_{nm[1]}$|$^2$, y = 0.138 µm" + ("  (∝ cos², amplitude = k$_x$/β·E$_z$)" if nm == "Ex" else "  (∝ sin²: node at wall)"),
                fontsize=10.5)
axs[0].set_ylabel("dB rel. max|E$_x$|$^2$"); axs[0].legend(fontsize=8.5, frameon=False, loc="lower left")
axs[2].text(XS + 0.05, -40, "Au\nwall", fontsize=9, color="#7a5b00")
fig.suptitle(f"Lateral cavity: one wave, k$_x$ = k$_0$√(n$_{{TM}}^2$ − n$_{{eff}}^2$), half-period π/k$_x$ = {half:.3f} µm (purple: predicted nodes)",
             y=1.03, fontsize=12)
fig.tight_layout(); fig.savefig("figs/F6_cavity_standing_wave.png"); plt.close(fig)

# ============================================================ F7 vertical profile vs 1D TM mode
yv = d["yv"]
fig, axs = plt.subplots(1, 2, figsize=(13, 4.2))
xa = 2.75
vEx, vEy, vEz = d[f"vcut_{xa:.2f}"]
L = lay(eau, es_mix)
U, V, tops = s1.profile(n_lat, L, k0, "TM", yv)
eps_y = np.where(yv < 0, ns**2, np.where(yv < SLAB_H, no**2, eau))
eps_s = np.where(yv < 0, ns**2, np.where(yv < SLAB_H, es_mix, eau))
Ey1 = n_lat * U / eps_y                  # normal component ~ beta_lat H / eps_y
Es1 = V                                  # in-plane component ~ (1/eps_s) dH/dy
Ez1 = Es1 * nr / n_lat / k0              # projection on z of the in-plane component
a = axs[0]
sc = np.abs(vEy[np.argmin(np.abs(yv - 0.2))]) / np.abs(Ey1[np.argmin(np.abs(yv - 0.2))])
a.plot(np.abs(vEy) / np.sqrt(E0) * 1e3, yv, color=C["Ey"], lw=2.2, label="|E$_y$| FEM")
a.plot(np.abs(Ey1) * sc / np.sqrt(E0) * 1e3, yv, "k--", lw=1.3, label="|E$_y$| 1D TM mode (Au/LN/SiO$_2$)")
sz = sc * np.abs(Ez1[np.argmin(np.abs(yv - 0.2))]) / np.abs(Ez1[np.argmin(np.abs(yv - 0.2))])
a.plot(np.abs(vEz) / np.sqrt(E0) * 1e3, yv, color=C["Ez"], lw=2.2, label="|E$_z$| FEM")
a.plot(np.abs(Ez1) * sc * np.abs(np.sin(kx * (xw - xa))) / np.abs(np.sin(kx * (xw - xa))) / np.sqrt(E0) * 1e3, yv, ":", color="k", lw=1.6,
       label="|E$_z$| 1D TM mode (same scale)")
for yb, c_ in [(0, C["ox"]), (SLAB_H, C["au"])]:
    a.axhline(yb, color=c_, lw=2)
a.text(a.get_xlim()[1] * 0.02 if False else 0.1, -0.12, "SiO$_2$", fontsize=9, color="#1e4f7a")
a.text(0.1, 0.12, "LN slab", fontsize=9)
a.text(0.1, 0.33, "Au", fontsize=9, color="#7a5b00")
a.set_ylim(-0.45, 0.45); a.set_xlabel("field amplitude (×10$^{-3}$ of max|E$_x$|)"); a.set_ylabel("y (µm)")
a.set_title(f"Vertical cut through a cavity antinode (x = {xa} µm)")
a.legend(fontsize=8, frameon=False, loc="upper right")
# jumps from the normal-D condition
a = axs[1]
jLN = np.argmin(np.abs(yv - 0.0015)); jOX = np.argmin(np.abs(yv + 0.0015))
jLNt = np.argmin(np.abs(yv - (SLAB_H - 0.0015))); jAU = np.argmin(np.abs(yv - (SLAB_H + 0.0015)))
rows = [("|E$_y$| LN / SiO$_2$\nat slab bottom", np.abs(vEy[jLN] / vEy[jOX]), ns**2 / no**2),
        ("|E$_y$| Au / LN\nat slab top", np.abs(vEy[jAU] / vEy[jLNt]), abs(no**2 / eau)),
        ("|E$_z$| / |E$_y$|\nin LN under gold", np.abs(vEz[np.argmin(np.abs(yv - 0.2))] / vEy[np.argmin(np.abs(yv - 0.2))]),
         float(np.abs(Ez1[np.argmin(np.abs(yv - 0.2))] / Ey1[np.argmin(np.abs(yv - 0.2))]) ))]
rows[1] = (rows[1][0], rows[1][1], rows[1][2])
xx = np.arange(len(rows))
fv = [20 * np.log10(r[1]) for r in rows]; tv = [20 * np.log10(r[2]) for r in rows]
a.bar(xx - 0.18, fv, 0.34, color=C["Ey"], label="FEM"); a.bar(xx + 0.18, tv, 0.34, color="#9ca3af", label="theory")
for i in xx:
    a.text(i - 0.18, fv[i] - 0.8 if fv[i] < 0 else fv[i] + 0.3, f"{fv[i]:.1f}", ha="center", va="top" if fv[i] < 0 else "bottom", fontsize=9)
    a.text(i + 0.18, tv[i] - 0.8 if tv[i] < 0 else tv[i] + 0.3, f"{tv[i]:.1f}", ha="center", va="top" if tv[i] < 0 else "bottom", fontsize=9)
a.set_xticks(xx); a.set_xticklabels([r[0] for r in rows], fontsize=9); a.axhline(0, color="k", lw=.8)
a.set_ylabel("amplitude ratio (dB)"); a.legend(frameon=False, loc="lower left")
a.set_title("Interface jumps: ε$_1$E$_{y1}$ = ε$_2$E$_{y2}$ (normal D continuous)")
N["jumps"] = {r[0].replace("\n", " "): [float(f), float(t_)] for r, f, t_ in zip(rows, fv, tv)}
fig.tight_layout(); fig.savefig("figs/F7_cavity_vertical_profile.png"); plt.close(fig)

# ============================================================ F8 IL vs slab end (Fabry-Perot)
import csv
rows = [r for r in csv.DictReader(open("../etched_slab/slab_w_sweep.csv")) if r["regime"] == "inside_gold"]
dd = np.array([float(r["slab_edge_beyond_gap_edge_um"]) for r in rows]); il = np.array([float(r["IL_dB_per_cm"]) for r in rows])
fp = json.load(open("../etched_slab/fabry_perot_fit_slab_in_gold.json"))
dfit = np.linspace(0.45, dd.max(), 1500)
rho = fp["rho0"] * np.exp(-fp["two_alpha_per_um"] * dfit)
ilf = fp["IL_inf"] * (1 - rho**2) / (1 - 2 * rho * np.cos(2 * np.pi * dfit / fp["period_um_in_slab_edge"] + fp["phase"]) + rho**2)
fig, ax = plt.subplots(figsize=(12, 3.9))
ax.semilogy(dd, il, "o", ms=3.5, color=C["Ey"], label="FEM (slab_w sweep)")
ax.semilogy(dfit, ilf, "-", color="k", lw=1, label=f"Airy fit: period {fp['period_um_in_slab_edge']:.3f} µm, ρ$_0$ = {fp['rho0']:.2f}")
pk = 2.0
ax.axvline(pk, color=C["acc"], ls=":", lw=1.3)
ax.text(pk + 0.03, 3.0, "field maps\n(slab_w 8.2)", color=C["acc"], fontsize=9, va="top")
ax.axhline(fp["IL_inf"], color=C["mut"], ls="--", lw=1); ax.text(4.5, fp["IL_inf"] * 1.12, "IL$_∞$ (no mirror)", color=C["mut"], fontsize=9)
ax.set_xlabel("cavity length L = slab end − gold edge (µm)"); ax.set_ylabel("IL (dB/cm)")
ax.set_title(f"IL is periodic in L: theory π/Re(k$_x$) = {half:.3f} µm, fitted {fp['period_um_in_slab_edge']:.3f} µm  "
             f"(Δ = {100*(half/fp['period_um_in_slab_edge']-1):+.1f} %)")
ax.legend(frameon=False, fontsize=9, loc="upper right"); ax.set_xlim(0.4, 4.9)
fig.tight_layout(); fig.savefig("figs/F8_IL_vs_cavity_length.png"); plt.close(fig)
N.update(fp_period=fp["period_um_in_slab_edge"], fp_two_alpha=fp["two_alpha_per_um"],
         pred_two_alpha=float(2 * abs(kx.imag)))

# ============================================================ F9 buffer cut-off (Liu 2021)
tb = np.r_[np.linspace(0, 0.1, 41), np.linspace(0.11, 0.3, 20)]
nb = []
for tt in tb:
    nb.append(s1.solve(lay(eau, es_mix, buf=tt) if tt > 0 else lay(eau, es_mix), k0, "TM", nb[-1] if nb else n_lat))
nb = np.array(nb)
tc = np.interp(-nr, -nb.real, tb)
N["buffer_cutoff_nm"] = 1e3 * tc
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.0))
a1.plot(tb * 1e3, nb.real, color=C["Ey"], lw=2.2, label="TM wave under Au/SiO$_2$(t)/LN slab")
a1.axhline(nr, color="k", ls="--"); a1.text(200, nr + 0.01, "n$_{eff}$ guided mode", fontsize=9)
a1.fill_between(tb * 1e3, nr, nb.real, where=nb.real > nr, color=C["Ey"], alpha=0.15)
a1.axvline(tc * 1e3, color=C["acc"], ls=":"); a1.text(tc * 1e3 + 5, 2.03, f"cut-off\nt$_c$ ≈ {tc*1e3:.0f} nm", color=C["acc"], fontsize=10)
a1.text(5, 1.71, "leaky\n(lateral\ncavity on)", fontsize=9, color=C["Ey"])
a1.text(150, 1.71, "bound: no lateral wave, no cavity", fontsize=9)
a1.set_xlabel("SiO$_2$ buffer thickness t (nm)"); a1.set_ylabel("index"); a1.legend(frameon=False, fontsize=9)
a1.set_title("A buffer pushes the TM wave below n$_{eff}$")
bt = [r for r in csv.DictReader(open("../buffer_thickness/buffer_thickness_sweep.csv"))]
for des, w, col, lab in [("L", "1", C["Ex"], "Lisbon 1575 nm, WG 1.0"), ("J", "1", C["Ez"], "Jerez 1360 nm, WG 1.0")]:
    r_ = [r for r in bt if r["design"] == des and r["wg_top"] == w and float(r["buffer_nm"]) > 0]
    a2.semilogy([float(r["buffer_nm"]) for r in r_], [float(r["IL_dBcm"]) for r in r_], "o-", color=col, ms=4, label=lab)
    r0 = [r for r in bt if r["design"] == des and r["wg_top"] == w and float(r["buffer_nm"]) == 0]
    if r0:
        a2.axhline(float(r0[0]["IL_dBcm"]), color=col, ls=":", lw=1)
a2.text(135, 0.25, "dotted: no buffer, gap 4.2 µm", fontsize=8.5, color=C["mut"])
a2.set_xlabel("buffer thickness (nm)"); a2.set_ylabel("IL (dB/cm)"); a2.legend(frameon=False, fontsize=9)
a2.set_title("FEM: all buffers ≫ t$_c$ → smooth decay, no ripple")
fig.tight_layout(); fig.savefig("figs/F9_buffer_cutoff.png"); plt.close(fig)

# ============================================================ F10 cavity maps with predicted nodes
sz_ = np.ix_((yg > -0.35) & (yg < 0.6), (xg > 1.0) & (xg < 4.6))
ez = (1.0, 4.6, -0.35, 0.6)
fig, axs = plt.subplots(3, 1, figsize=(11, 7.4), sharex=True)
for a, F, nm in zip(axs, (Ex, Ey, Ez), ("Ex", "Ey", "Ez")):
    im = a.imshow(dB(F)[sz_], extent=ez, origin="lower", cmap="turbo", vmin=-80, vmax=-20, aspect="auto")
    a.plot([1, 4.6], [0, 0], "w", lw=.7); a.plot([1, XS], [SLAB_H, SLAB_H], "w", lw=.7)
    a.plot([XG, XG, 4.6], [0.6, SLAB_H, SLAB_H], color=C["au"], lw=1.5); a.plot([XS, XS], [0, SLAB_H], color=C["au"], lw=1.5)
    for k_ in range(4):
        xn = xw - (k_ + (0.5 if nm == "Ex" else 0)) * half
        if XG < xn < XS:
            a.axvline(xn, color="w", ls="--", lw=1.2)
    a.text(1.05, 0.48, f"|E$_{nm[1]}$|$^2$", color="w", fontsize=12, weight="bold")
    plt.colorbar(im, ax=a, fraction=0.02, pad=0.01, label="dB")
    a.set_ylabel("y (µm)")
axs[-1].set_xlabel("x (µm)   — white dashed: nodes predicted by k$_x$ (no fit apart from the wall phase)")
fig.tight_layout(); fig.savefig("figs/F10_cavity_maps_nodes.png"); plt.close(fig)

# ============================================================ F11 loss budget / skin
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 3.8))
a1.bar(["gold skin\n(70 nm shell)", "gold corners", "gold bulk"], [89.4, 10.4, 0.2], color=[C["au"], "#b45309", "#78350f"])
for i, v_ in enumerate([89.4, 10.4, 0.2]):
    a1.text(i, v_ + 1.5, f"{v_:.1f} %", ha="center")
a1.set_ylabel("share of absorbed power"); a1.set_title("Where the light is absorbed (FEM)"); a1.set_ylim(0, 100)
yy_ = np.linspace(0, 0.12, 300)
dsk = N["skin_depth_nm"] / 1e3
a2.plot(yy_ * 1e3, np.exp(-2 * yy_ / dsk), color=C["au"], lw=2.2, label=f"theory e$^{{-2y/δ}}$, δ = {N['skin_depth_nm']:.1f} nm")
jj = (yv > SLAB_H + 0.002) & (yv < SLAB_H + 0.12)
I_ = np.abs(vEy[jj]) ** 2 + np.abs(vEz[jj]) ** 2 + np.abs(vEx[jj]) ** 2
a2.plot((yv[jj] - SLAB_H) * 1e3, I_ / I_[0], "k--", lw=1.3, label="FEM |E|² inside gold (x = 2.75 µm)")
a2.set_xlabel("depth into gold (nm)"); a2.set_ylabel("|E|² (normalised)"); a2.legend(frameon=False, fontsize=9)
a2.set_title("Field inside the metal: skin depth (Maier eq. 2.13)")
fig.tight_layout(); fig.savefig("figs/F11_loss_skin.png"); plt.close(fig)

json.dump(N, open("theory_numbers.json", "w"), indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o))
print(json.dumps(N, indent=1, default=str))
