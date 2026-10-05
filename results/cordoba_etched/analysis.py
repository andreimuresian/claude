"""Cordoba (non-lifted, flat electrodes) with an etched LN slab vs the filled lifted design
(GOLD_OUT, solid stepped gold), gap 4.2 um, 1575 nm: IL(slab_w) for a slab ending inside the gold."""
import re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
OUT = "/home/user/claude/results/cordoba_etched/"
RES = "/home/user/claude/results/"
K = 20 * np.log10(np.e) * 2 * np.pi / 1.575e-6 / 100        # dB/cm per |Im neff|
GAP = 4.2
C = dict(blue="#2a78d6", orange="#eb6834", grey="#7f8c8d", green="#1baf7a")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def runs(*files):
    d = {}
    for fn in files:
        for l in open(SP + fn):
            m = re.match(r"(\S+)\s+tri=\s*(\d+).*neff=(\S+) Im=(\S+) IL=\S+ VpiL=(\S+)", l)
            if m:
                d[m[1]] = dict(tri=int(m[2]), neff=float(m[3]), IL=K * abs(float(m[4])), VpiL=float(m[5]))
    return d


def airy(p, L):
    I0, r0, a2, P, ph = p
    rho = r0 * np.exp(-a2 * L)
    return I0 * (1 - rho ** 2) / (1 - 2 * rho * np.cos(2 * np.pi * L / P + ph) + rho ** 2)


def fit(L, I):
    best = None
    for P0 in np.linspace(0.85, 0.95, 5):
        for r00 in (0.85, 0.92, 0.95):
            for ph0 in np.linspace(-3.1, 3.1, 13):
                r = least_squares(lambda p: np.log(airy(p, L)) - np.log(I), [0.4, r00, 0.17, P0, ph0],
                                  bounds=([0, 0, 0, 0.5, -20], [5, 0.999, 2, 1.5, 20]))
                if best is None or r.cost < best.cost:
                    best = r
    p = best.x.copy(); p[4] = (p[4] + np.pi) % (2 * np.pi) - np.pi
    return p, float(np.sqrt(np.mean((np.log10(airy(p, L)) - np.log10(I)) ** 2)))


def fitdict(p, r):
    return dict(IL_inf_dB_cm=round(p[0], 4), rho0=round(p[1], 4), two_alpha_per_um=round(p[2], 4),
                period_um=round(p[3], 4), phase_rad=round(p[4], 3), rms_log10=round(r, 4))


# ---- Cordoba etched (this study) ---------------------------------------------
d = runs("c1_out.txt", "c2_out.txt")
cor = np.array(sorted((float(k[2:]), v["IL"], v["VpiL"], v["tri"]) for k, v in d.items()
                      if re.fullmatch(r"C_\d+\.\d+", k)))
noetch = d["C_noetch"]
with open(OUT + "cordoba_etched_slab_w_sweep.csv", "w") as f:
    f.write("slab_w_um,slab_end_beyond_gap_edge_um,IL_dB_per_cm,VpiL_Vcm,triangles\n")
    for w, il, vp, tri in cor:
        f.write(f"{w:.2f},{(w - GAP) / 2:.3f},{il:.5f},{vp:.4f},{int(tri)}\n")
    f.write(f"no_etch,,{noetch['IL']:.5f},{noetch['VpiL']:.4f},{noetch['tri']}\n")

# ---- Filled lifted reference ---------------------------------------------------
# GOLD_OUT (solid stepped gold, no SiO2 in the electrodes): sweep 3
go = np.genfromtxt(RES + "three_sweeps/sweep3_full_etch_gold_at_slab_level.csv", delimiter=",", names=True)
go = np.c_[go["slab_w_um"], go["IL_dB_per_cm"], go["VpiL_Vcm"]]
# lifted etched sweep (SiO2 lift beyond x = 7 um): identical to GOLD_OUT while the slab
# ends inside the gold (median 0.03 %, sweep 3), so it fills in the 0.05-0.2 um grid
lf = np.genfromtxt(RES + "etched_slab/slab_w_sweep.csv", delimiter=",", names=True, dtype=None, encoding=None)
lf = np.c_[lf["slab_w_um"], lf["IL_dB_per_cm"], lf["VpiL_Vcm"]]
lo, hi = cor[:, 0].min() - 1e-9, cor[:, 0].max() + 1e-9
go = go[(go[:, 0] >= lo) & (go[:, 0] <= hi)]
lf = lf[(lf[:, 0] >= lo) & (lf[:, 0] <= min(hi, 13.96))]

summary = dict(n_cordoba=len(cor), no_etch_IL=round(noetch["IL"], 4), no_etch_VpiL=round(noetch["VpiL"], 4))
cmp = {}
for name, ref in (("filled_lifted_GOLD_OUT", go), ("lifted_etched_slab_in_gold", lf)):
    rows = [(w, il, cor[np.isclose(cor[:, 0], w), 1][0], vp, cor[np.isclose(cor[:, 0], w), 2][0])
            for w, il, vp in ref if np.isclose(cor[:, 0], w).any()]
    a = np.array(rows)
    rel = np.abs(a[:, 2] / a[:, 1] - 1)
    cmp[name] = a
    summary[name] = dict(n_shared=len(a), median_rel_dIL=round(float(np.median(rel)), 5),
                         max_rel_dIL=round(float(rel.max()), 5), at_slab_w=float(a[rel.argmax(), 0]),
                         max_rel_dVpiL=round(float(np.max(np.abs(a[:, 4] / a[:, 3] - 1))), 5))

L = (cor[:, 0] - GAP) / 2
m = L > 0.3
p, r = fit(L[m], cor[m, 1])
summary["airy_fit_cordoba"] = fitdict(p, r)
json.dump(summary, open(OUT + "summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))

# ---- Figure --------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.4), sharex=True, gridspec_kw=dict(height_ratios=[2.3, 1]))
ww = np.linspace(cor[m, 0].min(), cor[:, 0].max(), 2000); Lw = (ww - GAP) / 2
rho = p[1] * np.exp(-p[2] * Lw)
a1.fill_between(ww, p[0] * (1 - rho) / (1 + rho), p[0] * (1 + rho) / (1 - rho), color=C["blue"], alpha=0.07, lw=0)
a1.plot(cor[:, 0], cor[:, 1], "-", color=C["blue"], lw=1.6, label="Cordoba (flat electrodes), etched slab — this study")
a1.plot(lf[:, 0], lf[:, 1], "o", ms=5, mfc="none", mec=C["orange"], mew=1.1,
        label="lifted, etched slab (slab ends in the gold; = filled lifted to 0.03 %)")
a1.plot(go[:, 0], go[:, 1], "s", ms=4.5, color=C["orange"], label="filled lifted (no SiO₂ in the electrodes)")
a1.axhline(noetch["IL"], color=C["grey"], ls="--", lw=1)
a1.text(cor[-1, 0], noetch["IL"] * 1.07, f"Cordoba, no etch: {noetch['IL']:.3f} dB/cm", ha="right", color=C["grey"], fontsize=9)
a1.axhline(p[0], color=C["blue"], ls=":", lw=1)
a1.text(cor[-1, 0], p[0] * 0.86, f"fitted IL∞ {p[0]:.3f} dB/cm", ha="right", va="top", color=C["blue"], fontsize=9)
a1.set_yscale("log"); a1.set_ylabel("IL (dB/cm)"); a1.grid(alpha=0.3, which="both", lw=0.4)
a1.legend(loc="upper right", fontsize=8.5)
a1.set_title(f"Etched slab ending inside the gold, gap {GAP} µm, 1575 nm: Cordoba vs filled lifted "
             f"(shaded = Airy envelope, period {p[3]:.3f} µm in L = {2 * p[3]:.2f} µm in slab_w)", fontsize=10)
for name, mk, col in (("lifted_etched_slab_in_gold", "o", C["orange"]), ("filled_lifted_GOLD_OUT", "s", C["orange"])):
    a = cmp[name]
    a2.plot(a[:, 0], 100 * (a[:, 2] / a[:, 1] - 1), mk, ms=4.5, color=col, mfc="none" if mk == "o" else col,
            label=f"vs {name.replace('_', ' ')}: median |Δ| {100 * summary[name]['median_rel_dIL']:.2f} %")
a2.axhline(0, color="k", lw=0.6)
a2.set_ylabel("IL Cordoba / lifted − 1 (%)"); a2.set_xlabel("slab_w (µm)")
a2.grid(alpha=0.3, lw=0.4); a2.legend(fontsize=8.5, loc="lower left")
plt.tight_layout(); fig.savefig(OUT + "cordoba_vs_filled_lifted_IL_vs_slab_w.png", dpi=150); plt.close(fig)
