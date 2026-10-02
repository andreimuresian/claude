"""Three sweeps (1575 nm): (1) legacy lifted, x_lift sweep at gap 3.9 / 5.0 vs 4.2;
(2) buffered 200 nm, gap 3.4: slab thickness 275 -> 150 nm (over-etch);
(3) full etch, gold instead of the SiO2 lift at slab level (GOLD_OUT): slab_w sweep."""
import re, json, csv, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
OUT = "/home/user/claude/results/three_sweeps/"
RES = "/home/user/claude/results/"
K = 20 * np.log10(np.e) * 2 * np.pi / 1.575e-6 / 100        # dB/cm per |Im neff|
C = dict(blue="#2a78d6", orange="#eb6834", green="#1baf7a", yel="#eda100", pink="#e87ba4", grey="#7f8c8d")
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})


def runs(*files):
    d = {}
    for fn in files:
        try:
            for l in open(SP + fn):
                m = re.match(r"(\S+)\s+tri=\s*(\d+).*neff=(\S+) Im=(\S+) IL=\S+ VpiL=(\S+)", l)
                if m:
                    d[m[1]] = dict(tri=int(m[2]), neff=float(m[3]), IL=K * abs(float(m[4])), VpiL=float(m[5]))
        except FileNotFoundError:
            pass
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


summary = {}

# ============ Sweep 1: legacy lifted, gap 3.9 / 4.2 / 5.0 =====================
d1 = runs("s8_out.txt", "s8a_out.txt")
old = np.genfromtxt(RES + "lift_sweep.csv", delimiter=",", names=True)
S1 = {4.2: np.c_[old["x_lift_um"], old["IL_dB_per_cm"], old["VpiL_Vcm"]]}
for g in (3.9, 5.0):
    rows = sorted((float(k.split("_x")[1]), v["IL"], v["VpiL"]) for k, v in d1.items()
                  if k.startswith(f"G{g}_x") or (k == f"G{str(g).replace('.', '')}_x7.0" and False))
    if rows:
        S1[g] = np.array(rows)
if len(S1) > 1:
    with open(OUT + "sweep1_legacy_gap_xlift.csv", "w") as f:
        f.write("gap_um,x_lift_um,cavity_length_um,IL_dB_per_cm,VpiL_Vcm\n")
        for g, a in sorted(S1.items()):
            for x, il, vp in a:
                f.write(f"{g},{x:.2f},{x - g / 2:.2f},{il:.5f},{vp:.4f}\n")
    fits1 = {}
    for g, a in S1.items():
        m = (a[:, 0] <= 11.05)
        if m.sum() > 30:
            p, r = fit(a[m, 0] - g / 2, a[m, 1]); fits1[g] = p
            summary[f"sweep1_gap{g}"] = dict(fitdict(p, r), VpiL_Vcm=round(float(np.median(a[:, 2])), 4),
                                             IL_min=round(float(a[m, 1].min()), 4), IL_max=round(float(a[m, 1].max()), 4),
                                             IL_far_xlift=round(float(a[~m, 1][-1]), 4) if (~m).any() else None)
    cols = {3.9: C["orange"], 4.2: C["grey"], 5.0: C["blue"]}
    fig, axs = plt.subplots(2, 1, figsize=(11, 8.2))
    for ax, xkey in zip(axs, ("x", "L")):
        for g, a in sorted(S1.items()):
            m = a[:, 0] <= 11.05
            xx = a[m, 0] - (g / 2 if xkey == "L" else 0)
            yy = a[m, 1] / (fits1[g][0] if xkey == "L" else 1.0)
            ax.plot(xx, yy, "o-", ms=4 if g == 4.2 else 2.5, lw=0.9, color=cols[g], zorder=4 if g == 4.2 else 2,
                    mfc="none" if g == 4.2 else cols[g],
                    label=(f"gap {g} µm  (Vπ·L {np.median(a[:, 2]):.2f} V·cm)" if xkey == "x" else
                           f"gap {g} µm: IL∞ {fits1[g][0]:.3f} dB/cm, period {fits1[g][3]:.3f} µm, 2α {fits1[g][2]:.3f}/µm"))
            if xkey == "x":
                ax.axhline(fits1[g][0], color=cols[g], lw=0.7, ls="--")
        ax.set_yscale("log"); ax.grid(alpha=0.3, which="both", lw=0.4)
        ax.set_ylabel("IL (dB/cm)" if xkey == "x" else "IL / IL∞")
    axs[0].set_xlabel("x_lift (µm)"); axs[0].legend(loc="upper right", fontsize=9)
    axs[0].set_title("Legacy lifted design: IL vs x_lift for three bottom gaps (dashed = fitted IL∞)")
    axs[1].set_xlabel("cavity length L = x_lift − gap/2 (µm)")
    axs[1].legend(loc="upper right", fontsize=8.5)
    axs[1].set_title("Normalised to IL∞ and plotted vs cavity length: the three curves collapse onto one")
    plt.tight_layout(); fig.savefig(OUT + "sweep1_IL_vs_xlift_gaps.png", dpi=150); plt.close(fig)

# ============ Sweep 2: buffered, slab thickness ===============================
d2 = runs("s8_out.txt", "s8b_out.txt")
rows = sorted(((int(k[1:4]), v) for k, v in d2.items() if re.fullmatch(r"T\d{3}_g3\.4", k)), reverse=True)
if rows:
    with open(OUT + "sweep2_buffered_slab_thickness.csv", "w") as f:
        f.write("slab_nm,etch_depth_nm,neff_re,IL_dB_per_cm,VpiL_Vcm,triangles\n")
        for t, v in rows:
            f.write(f"{t},{550 - t},{v['neff']:.6f},{v['IL']:.5f},{v['VpiL']:.4f},{v['tri']}\n")
    flat = {k: v for k, v in d2.items() if k.startswith("T150_g3.4_x")}
    summary["sweep2"] = {str(t): dict(IL=round(v["IL"], 5), VpiL=round(v["VpiL"], 4)) for t, v in rows}
    summary["sweep2_flatness_150nm"] = {k: dict(IL=round(v["IL"], 5), VpiL=round(v["VpiL"], 4)) for k, v in flat.items()}
    t = np.array([r[0] for r in rows]); il = np.array([r[1]["IL"] for r in rows]); vp = np.array([r[1]["VpiL"] for r in rows])
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.2))
    a1.plot(t, vp, "o-", color=C["blue"]); a1.set_ylabel("Vπ·L (V·cm)")
    a2.plot(t, il, "o-", color=C["orange"]); a2.set_ylabel("IL (dB/cm)"); a2.set_yscale("log")
    for a in (a1, a2):
        a.set_xlabel("LN slab thickness (nm)   [etch depth = 550 − slab]"); a.invert_xaxis(); a.grid(alpha=0.3, which="both", lw=0.4)
        a.axvline(275, color=C["grey"], lw=0.7, ls=":")
    a1.set_title("Vπ·L vs slab thickness"); a2.set_title("IL vs slab thickness")
    fig.suptitle("Buffered lifted design (200 nm SiO₂, gap 3.4 µm, x_lift 7): over-etch robustness", fontsize=11)
    plt.tight_layout(); fig.savefig(OUT + "sweep2_buffered_overetch.png", dpi=150); plt.close(fig)

# ============ Sweep 3: full etch, gold at slab level ===========================
d3 = runs("s8_out.txt", "s9_out.txt")
new = sorted((float(k[3:]), v["IL"], v["VpiL"]) for k, v in d3.items() if k.startswith("GO_"))
if new:
    new = np.array(new)
    prev = np.genfromtxt(RES + "etched_slab/slab_w_sweep.csv", delimiter=",", names=True, dtype=None, encoding=None)
    pw = list(zip(prev["slab_w_um"], prev["IL_dB_per_cm"], prev["VpiL_Vcm"]))
    for r in csv.DictReader(open(RES + "etched_slab/followup_runs.csv")):
        if re.fullmatch(r"S_[\d.]+", r["tag"]):
            pw.append((float(r["tag"][2:]), float(r["IL_dB_per_cm"]), float(r["VpiL_Vcm"])))
    pw = np.array(sorted(pw))
    l11 = runs("l11_out.txt")
    l11 = np.array(sorted((float(k[4:]), v["IL"]) for k, v in l11.items() if k.startswith("L11_")))
    with open(OUT + "sweep3_full_etch_gold_at_slab_level.csv", "w") as f:
        f.write("slab_w_um,slab_end_beyond_gap_edge_um,IL_dB_per_cm,VpiL_Vcm\n")
        for w, il, vp in new:
            f.write(f"{w:.2f},{(w - 4.2) / 2:.3f},{il:.5f},{vp:.4f}\n")
    # identical where both end in the gold?
    com = [(w, il, pw[np.argmin(abs(pw[:, 0] - w)), 1]) for w, il, _ in new
           if w <= 13.95 and abs(pw[np.argmin(abs(pw[:, 0] - w)), 0] - w) < 1e-6]
    if com:
        com = np.array(com); rel = np.abs(com[:, 1] / com[:, 2] - 1)
        summary["sweep3_vs_previous_slab_in_gold"] = dict(n=len(com), max_rel_dev=round(float(rel[com[:, 0] > 4.2].max()), 4)
                                                          if (com[:, 0] > 4.2).any() else None,
                                                          median_rel_dev=round(float(np.median(rel)), 5))
    m = new[:, 0] >= 5.2
    if m.sum() > 40:
        L = (new[m, 0] - 4.2) / 2
        p3, r3 = fit(L, new[m, 1]); summary["sweep3_fit_slab_end_in_gold"] = fitdict(p3, r3)
    fig, axs = plt.subplots(2, 1, figsize=(12, 8.4), gridspec_kw=dict(height_ratios=[1.35, 1]))
    for ax, xl in zip(axs, ((2.2, 50.5), (2.2, 25))):
        ax.axvspan(2.2, 4.2, color="#eaf2fb", lw=0)
        ax.plot(pw[:, 0], pw[:, 1], "-", color=C["grey"], lw=1.0, label="previous: SiO₂ lift at slab level (gold/SiO₂ edge at slab_w = 14)")
        ax.plot(new[:, 0], new[:, 1], "o-", ms=2.2, lw=0.9, color=C["orange"], label="gold at slab level (no gold/SiO₂ edge)")
        if m.sum() > 40:
            ww = np.linspace(5.0, 50, 4000); Lw = (ww - 4.2) / 2
            rho = p3[1] * np.exp(-p3[2] * Lw)
            ax.plot(ww, p3[0] * (1 + rho) / (1 - rho), ":", color=C["orange"], lw=0.8)
            ax.plot(ww, p3[0] * (1 - rho) / (1 + rho), ":", color=C["orange"], lw=0.8)
            ax.axhline(p3[0], color=C["orange"], ls="--", lw=0.8, label=f"fitted asymptote IL∞ = {p3[0]:.3f} dB/cm")
        ax.axvline(14.0, color=C["blue"], lw=0.8, ls="--")
        ax.set_yscale("log"); ax.set_xlim(*xl); ax.grid(alpha=0.3, which="both", lw=0.4); ax.set_ylabel("IL (dB/cm)")
    axs[0].text(14.2, 0.0006, "old gold/SiO₂ edge", color=C["blue"], fontsize=8.5)
    axs[0].text(2.35, 0.0006, "slab ends\nin the gap", color="#555", fontsize=8.5)
    axs[0].legend(loc="lower right", fontsize=8.5); axs[0].set_ylim(1e-4, 12)
    axs[1].set_ylim(0.02, 12); axs[1].set_xlabel("slab_w (µm)   [gap 4.2 µm, x_lift 7 µm]")
    axs[0].set_title("Full etch: removing the gold/SiO₂ edge at slab level (dotted = Airy envelope)")
    plt.tight_layout(); fig.savefig(OUT + "sweep3_IL_vs_slab_w_gold_at_slab_level.png", dpi=150); plt.close(fig)

json.dump(summary, open(OUT + "summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
