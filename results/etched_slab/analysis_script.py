import re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
OUT = "/home/user/claude/results/etched_slab/"
import os; os.makedirs(OUT, exist_ok=True)
GAP, XL = 4.2, 7.0
rows, refs = [], {}
import itertools
for l in itertools.chain(*(open(f) for f in ("e_out.txt","e_ref_out.txt","e_ref2_out.txt") if os.path.exists(f))):
    m = re.match(r"(\S+)\s+tri=\s*(\d+).*neff=([\d.]+) Im=(\S+) IL=([\d.]+) VpiL=([\d.]+)", l)
    if not m: continue
    tag, tri, nr, ni, il, vp = m.groups()
    if tag.startswith("S_"):
        rows.append((float(tag[2:]), int(tri), float(nr), float(ni), 20*np.log10(np.e)*2*np.pi/1.575e-6*abs(float(ni))/100, float(vp)))
    else:
        refs[float(tag[4:])] = (int(tri), 20*np.log10(np.e)*2*np.pi/1.575e-6*abs(float(ni))/100, float(vp))
rows.sort(); A = np.array(rows)
sw, IL, VP = A[:, 0], A[:, 4], A[:, 5]
d = (sw - GAP) / 2
with open(OUT + "slab_w_sweep.csv", "w") as f:
    f.write("slab_w_um,slab_edge_beyond_gap_edge_um,regime,triangles,neff_re,neff_im,IL_dB_per_cm,VpiL_Vcm\n")
    for r in rows:
        dd = (r[0] - GAP) / 2
        reg = "air_gap" if dd < 0 else ("inside_gold" if r[0] / 2 < XL - 1e-9 else ("at_interface" if abs(r[0] / 2 - XL) < 1e-9 else "past_interface"))
        f.write(f"{r[0]:.2f},{dd:.2f},{reg},{r[1]},{r[2]:.6f},{r[3]:.4e},{r[4]:.4e},{r[5]:.4f}\n")
# mesh check
mc = []
for s, (tri, il, vp) in sorted(refs.items()):
    k = np.argmin(abs(sw - s)); mc.append((s, A[k, 1], tri, IL[k], il, VP[k], vp))
with open(OUT + "mesh_check.csv", "w") as f:
    f.write("slab_w_um,tri_prod,tri_ref,IL_prod,IL_ref,dIL_pct,VpiL_prod,VpiL_ref,dVpiL_pct\n")
    for s, tp, tr, ip, ir, vp, vr in mc:
        f.write(f"{s},{int(tp)},{tr},{ip:.4e},{ir:.4e},{100*(ip-ir)/ir if ir else 0:+.2f},{vp:.4f},{vr:.4f},{100*(vp-vr)/vr:+.3f}\n")
print(open(OUT + "mesh_check.csv").read())
# Airy fit, slab end inside gold: cavity = rib-side gap edge -> slab facet, L = d
m2 = (d >= 0.5) & (sw / 2 < XL - 1e-9)
def model(p, L):
    I0, r0, a2, P, ph = p
    rho = r0 * np.exp(-a2 * L)
    return I0 * (1 - rho**2) / (1 - 2 * rho * np.cos(2 * np.pi * L / P + ph) + rho**2)
best = None
for P0 in np.linspace(0.8, 1.0, 5):
    for ph0 in np.linspace(-3, 3, 7):
        r = least_squares(lambda p: model(p, d[m2]) - IL[m2], [0.4, 0.9, 0.17, P0, ph0],
                          bounds=([0, 0, 0, 0.5, -10], [5, 0.999, 2, 1.5, 10]))
        if best is None or r.cost < best.cost: best = r
p = best.x; rms = np.sqrt(np.mean((model(p, d[m2]) - IL[m2])**2))
fit = dict(IL_inf=p[0], rho0=p[1], two_alpha_per_um=p[2], period_um_in_slab_edge=p[3], phase=p[4], rms_dB_cm=rms,
           note="IL(d)=IL_inf(1-rho^2)/(1-2 rho cos(2 pi d/P+phi)+rho^2), rho=rho0 exp(-2alpha d); d = slab edge beyond gap edge")
json.dump(fit, open(OUT + "fabry_perot_fit_slab_in_gold.json", "w"), indent=1)
print(fit)
# --- plots
inf_ref = 0.2295
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[1.6, 1]))
for a in (a1, a2):
    a.axvspan(0, GAP, color="#ecf0f1", zorder=0); a.axvspan(GAP, 2 * XL, color="#fdf2d0", zorder=0); a.axvspan(2 * XL, 25, color="#dbeaf7", zorder=0)
    a.axvline(GAP, color="k", lw=0.8, ls="--"); a.axvline(2 * XL, color="k", lw=0.8, ls="--"); a.grid(alpha=0.3)
L = np.linspace(0.5, XL - GAP / 2, 600)
a1.plot(GAP + 2 * L, model(p, L), color="#e67e22", lw=1, alpha=0.8, label=f"Fabry-Perot fit (cavity rib to slab facet), period {2*p[3]:.2f} um in slab_w")
rho = p[1] * np.exp(-p[2] * L)
a1.plot(GAP + 2 * L, p[0] * (1 + rho) / (1 - rho), color="#e67e22", lw=0.8, ls=":")
a1.plot(GAP + 2 * L, p[0] * (1 - rho) / (1 + rho), color="#e67e22", lw=0.8, ls=":")
g1, g2 = d < 0, d > 0
a1.plot(sw[g1], IL[g1], "o-", color="#1f4e79", ms=3.2, lw=1, label="2D FEM")
a1.plot(sw[g2], IL[g2], "o-", color="#1f4e79", ms=3.2, lw=1)
a1.axhline(inf_ref, color="#c0392b", lw=1, ls="-.", label=f"unetched slab (x_lift = 7 um): {inf_ref:.3f} dB/cm")
a1.set_yscale("log"); a1.set_ylabel("IL (dB/cm)")
a1.set_ylim(1e-5, 30)
a1.text(GAP / 2 + 1.0, 18, "slab ends\nin the air gap", ha="center", va="top", fontsize=9)
a1.text((GAP + 2 * XL) / 2, 18, "slab ends inside the gold", ha="center", va="top", fontsize=9)
a1.text((2 * XL + 25) / 2, 18, "slab runs past the gold / SiO$_2$ interface", ha="center", va="top", fontsize=9)
a1.legend(loc="center right", fontsize=8, framealpha=0.95)
a1.text(GAP + 0.15, 2e-5, "slab_w = gap\n(not fabricable,\nnot simulated)", fontsize=7.5, color="#555")
a1.set_title("Etched LN slab, 1575 nm, gap 4.2 um, x_lift 7 um: IL and V$_\\pi$L vs slab width")
a2.plot(sw[g1], VP[g1], "o-", color="#1f4e79", ms=3.2, lw=1); a2.plot(sw[g2], VP[g2], "o-", color="#1f4e79", ms=3.2, lw=1)
for x_, v_ in [(2.4, VP[0]), (3.2, VP[np.argmin(abs(sw-3.2))]), (4.0, VP[np.argmin(abs(sw-4.0))])]:
    a2.annotate(f"{v_:.2f}", (x_, v_), textcoords="offset points", xytext=(6, 2), fontsize=8)
a2.annotate(f"{VP[-1]:.3f} V$\\cdot$cm whenever the slab reaches under the gold", (18, VP[-1]), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8)
a2.set_ylabel(r"V$_\pi$L (V$\cdot$cm)"); a2.set_xlabel(r"slab_w ($\mu$m)   [slab edge at $\pm$slab_w/2; gap edge at $\pm$2.1, gold/SiO$_2$ interface at $\pm$7.0]")
a2.set_xlim(2.0, 24.5)
sec = a1.secondary_xaxis("top", functions=(lambda x: (x - GAP) / 2, lambda d_: GAP + 2 * d_))
sec.set_xlabel(r"slab edge beyond the gold inner edge, d ($\mu$m)")
plt.tight_layout(); fig.savefig(OUT + "IL_VpiL_vs_slab_w.png", dpi=150)
print("saved")
