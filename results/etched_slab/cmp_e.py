import re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares
OUT = "/home/user/claude/results/etched_slab/"
XG = 2.1
K = 20*np.log10(np.e)*2*np.pi/1.575e-6/100
# A: slab facet (inside the gold) as mirror, cavity length L = slab edge - gold inner edge
a = np.genfromtxt(OUT + "slab_w_sweep.csv", delimiter=",", names=True, dtype=None, encoding=None)
mA = (a["regime"] == "inside_gold") & (a["slab_edge_beyond_gap_edge_um"] >= 0.5)
LA, IA = a["slab_edge_beyond_gap_edge_um"][mA], a["IL_dB_per_cm"][mA]
# B: gold/SiO2 interface as mirror (slab_w = 24, past it), L = x_lift - gold inner edge
rows = []
for l in open("xl_out.txt"):
    m = re.match(r"X_(\S+)\s+tri=.*Im=(\S+) IL=\S+ VpiL=(\S+)", l)
    if m: rows.append((float(m[1]), K*abs(float(m[2])), float(m[3])))
B = np.array(sorted(rows)); LB, IB, VB = B[:, 0] - XG, B[:, 1], B[:, 2]
with open(OUT + "xlift_sweep_slab_past_interface.csv", "w") as f:
    f.write("x_lift_um,cavity_length_um,slab_w_um,IL_dB_per_cm,VpiL_Vcm\n")
    for (x, il, vp) in B: f.write(f"{x:.2f},{x-XG:.2f},24.0,{il:.5f},{vp:.4f}\n")
old = np.genfromtxt("/home/user/claude/results/lift_sweep.csv", delimiter=",", names=True)
def model(p, L):
    I0, r0, a2, P, ph = p
    rho = r0*np.exp(-a2*L)
    return I0*(1-rho**2)/(1-2*rho*np.cos(2*np.pi*L/P+ph)+rho**2)
def fit(L, I):
    best = None
    for P0 in np.linspace(0.85, 0.95, 5):
      for r00 in (0.85, 0.92, 0.95):
        for ph0 in np.linspace(-3.1, 3.1, 13):
            r = least_squares(lambda p: model(p, L)-I, [0.4, r00, 0.17, P0, ph0],
                              bounds=([0, 0, 0, 0.5, -20], [5, 0.999, 2, 1.5, 20]))
            if best is None or r.cost < best.cost: best = r
    p = best.x; p[4] = (p[4] + np.pi) % (2*np.pi) - np.pi
    return p, np.sqrt(np.mean((model(p, L)-I)**2))
pA, rA = fit(LA, IA); pB, rB = fit(LB, IB)
res = {}
for k, p, r in [("slab_facet_in_gold", pA, rA), ("gold_SiO2_interface", pB, rB)]:
    res[k] = dict(IL_inf=p[0], rho0=p[1], two_alpha_per_um=p[2], period_um=p[3], phase_rad=p[4],
                  rms_dB_cm=r)
json.dump(res, open(OUT + "ripple_comparison_facet_vs_interface.json", "w"), indent=1)
for k, v in res.items(): print(k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})
np.save("cmp_fits.npy", np.array([pA, pB]))
fig, ax = plt.subplots(figsize=(11, 5))
L = np.linspace(0.3, 9.2, 1500)
for p, Ld, Id, c, lab in [(pA, LA, IA, "#c0392b", "mirror = slab end wrapped in gold (sweep slab_w, x_lift = 7)"),
                          (pB, LB, IB, "#1f4e79", "mirror = gold / SiO$_2$ interface (sweep x_lift, slab_w = 24)")]:
    Lm = L[(L >= Ld.min()-0.05) & (L <= Ld.max()+0.05)]
    ax.plot(Lm, model(p, Lm), color=c, lw=0.9, alpha=0.7)
    rho = p[1]*np.exp(-p[2]*Lm)
    ax.plot(Lm, p[0]*(1+rho)/(1-rho), color=c, lw=0.8, ls=":"); ax.plot(Lm, p[0]*(1-rho)/(1+rho), color=c, lw=0.8, ls=":")
    ax.plot(Ld, Id, "o", color=c, ms=3, label=lab + f"\n   fit: period {p[3]:.3f} um, IL$_\\infty$ {p[0]:.3f} dB/cm, $\\rho_0$ {p[1]:.3f}, 2$\\alpha$ {p[2]:.3f}/um")
ax.plot(old["x_lift_um"]-XG, old["IL_dB_per_cm"], "-", color="#7f8c8d", lw=0.8, alpha=0.8,
        label="previous unetched x_lift sweep (old SiO$_2$/Au constants)")
ax.axhline(pB[0], color="#1f4e79", lw=0.6, ls="--"); ax.axhline(pA[0], color="#c0392b", lw=0.6, ls="--")
ax.set_yscale("log"); ax.set_xlabel(r"cavity length L = mirror position $-$ gold inner edge ($\mu$m)")
ax.set_ylabel("IL (dB/cm)"); ax.grid(alpha=0.3); ax.set_xlim(0.3, 9.2); ax.set_ylim(0.02, 5)
ax.legend(fontsize=8, loc="upper right")
ax.set_title("Same cavity, two different mirrors: IL vs cavity length (1575 nm, gap 4.2 um)")
plt.tight_layout(); fig.savefig(OUT + "ripple_facet_vs_interface.png", dpi=150)
print("saved")
