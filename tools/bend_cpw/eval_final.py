"""Figures and error tables: analytical model vs references (results/)."""
import json
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, ".")
from cpw_analytic import bend_cpw, BEND_LAYERS, BEND_SIGMA, C0, DB_PER_NEPER as DB
import bem_pec

UM = 1e-6
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.grid": True, "grid.color": GRID,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "savefig.dpi": 160, "lines.linewidth": 2})


def stack(h):
    return [(h * UM, 3.9, 3.9), (0.275 * UM, 28.0, 44.0), (4.7 * UM, 3.9, 3.9), (550 * UM, 11.7, 11.7)]


def ref_line(R, L, C, f):
    w = 2 * np.pi * f
    g = np.sqrt((R + 1j * w * L) * (1j * w * C))
    return DB * g.real / 100, (g.imag / w) * C0, np.abs(np.sqrt((R + 1j * w * L) / (1j * w * C)))


Ce = 1.350833e-10                                       # FEM quasi-static C of the bend
rows = [json.loads(l) for l in open("results/sweep_eddy.jsonl") if '"R"' in l]
f = np.array([r["f_GHz"] for r in rows]); R = np.array([r["R"] for r in rows]); L = np.array([r["L"] for r in rows])
ar, nr, Zr = ref_line(R, L, Ce, f * 1e9)

# ---- 1. why the reference can be trusted ------------------------------------
peec = json.load(open("results/peec_bend.json"))[-1]["res"]
fp = np.array([x["f_GHz"] for x in peec]); Rp = np.array([x["R"] for x in peec])
coax = [r for r in json.load(open("results/verify_coax.json")) if r["h_um"] == min(q["h_um"] for q in json.load(open("results/verify_coax.json")))]
Z0r = float(np.interp(60, f, Zr))
ibc_fem = {0.05: 4.0158, 0.025: 4.1861, 0.0125: 4.3111}            # bend_fem.py (your notebook), 60 GHz
hb = np.array([1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7])
Rs60 = np.sqrt(np.pi * 60e9 * 4e-7 * np.pi / 4.56e7)
a_bem = np.array([DB * Rs60 * bem_pec.solve(35 * UM, 4.15 * UM, 50 * UM, 2 * UM, h_min_rel=h)["G_pec"] / (2 * Z0r) / 100
                  for h in hb])
fw = {10: 1.74202, 60: 4.594989, 160: 7.70554}                       # fullwave_metal.py (metal meshed)

fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
ax = axs[0]
ax.loglog(f, R, color=BLUE, label="current inside the gold, FEM (reference)")
ax.loglog(fp, Rp, "o", color=ORANGE, ms=8, mfc="none", mew=2, label="PEEC integral equation (independent)")
ax.axhline(R[0] * 0 + 1 / (4.56e7 * 35e-6 * 2e-6) + 0.5 / (4.56e7 * 50e-6 * 2e-6), color=MUTED, ls="--", lw=1.4,
           label="exact DC resistance")
dmax = np.max(np.abs(Rp / np.interp(fp, f, R) - 1)) * 100
ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("R' (Ω/m)")
ax.set_title(f"Bend R': two methods, max difference {dmax:.2f} %")
ax.legend(fontsize=8.5, loc="upper left")
ax = axs[1]
fc = np.array([r["f_GHz"] for r in coax])
ax.semilogx(fc[fc >= 1], [r["dR_pct"] for r in coax if r["f_GHz"] >= 1], "o-", color=BLUE, ms=8, label="R'")
ax.semilogx(fc[fc >= 1], [r["dL_pct"] for r in coax if r["f_GHz"] >= 1], "s-", color=ORANGE, ms=8, label="L'")
ax.axhline(0, color=MUTED, lw=1)
ax.set_ylim(-0.05, 0.05)
ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("FEM − exact (%)")
ax.set_title("Same solver on a gold coax vs Bessel solution")
ax.legend(fontsize=9)
ax = axs[2]
ax.semilogx(hb * 2.0, a_bem, "-", color=VIOLET, marker="D", ms=6, label="IBC, boundary elements (converged)")
ax.semilogx(list(ibc_fem), list(ibc_fem.values()), "o", color=ORANGE, ms=9, mfc="none", mew=2,
            label="IBC, your FEM notebook")
ax.axhline(float(np.interp(60, f, ar)), color=BLUE, label="current inside the gold (reference)")
ax.axhline(fw[60], color=AQUA, ls="--", label="your mode solver, gold meshed (full-wave)")
ax.set_xlabel("Smallest element at the corner (µm)"); ax.set_ylabel("α at 60 GHz (dB/cm)")
ax.set_title("IBC: slow corner convergence, limit too high")
ax.legend(fontsize=8.5, loc="lower right")
ax.invert_xaxis()
fig.subplots_adjust(wspace=0.3)
fig.savefig("results/fig_reference_checks.png", bbox_inches="tight", facecolor="white"); plt.close(fig)

# ---- 2. bend vs frequency -------------------------------------------------
an = bend_cpw(f * 1e9, 35 * UM, 4.15 * UM, 50 * UM, 2 * UM, BEND_LAYERS, layer_sigma=BEND_SIGMA)
gh = bend_cpw(f * 1e9, 35 * UM, 4.15 * UM, 50 * UM, 2 * UM, BEND_LAYERS, layer_sigma=BEND_SIGMA, conductor="ghione")
fig, axs = plt.subplots(1, 3, figsize=(16, 4.3))
ax = axs[0]
ax.plot(f, ar, color=BLUE, lw=2.6, label="reference")
ax.plot(list(fw), list(fw.values()), "s", color=AQUA, ms=9, mfc="none", mew=2, label="full-wave, gold meshed")
ax.plot(f, an["alpha_dB_cm"], "--", color=ORANGE, label="analytical (thick conductors)")
ax.plot(f, gh["alpha_dB_cm"], ":", color=MUTED, lw=1.6, label="analytical, Ghione (previous)")
ax.plot(list(ibc_fem.keys()) and [60, 60, 60], list(ibc_fem.values()), "o", color=VIOLET, ms=7, mfc="none", mew=1.8,
        label="your FEM (IBC), corner 0.05 / 0.025 / 0.0125 µm")
ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("α (dB/cm)"); ax.set_title("Attenuation")
ax.legend(fontsize=8.5, loc="upper left")
ax = axs[1]
ax.semilogx(f, nr, color=BLUE, lw=2.6, label="reference"); ax.semilogx(f, an["n_m"], "--", color=ORANGE, label="analytical")
ax.set_xlabel("Frequency (GHz)"); ax.set_title("Microwave index n_m"); ax.legend(fontsize=9)
ax = axs[2]
ax.semilogx(f, Zr, color=BLUE, lw=2.6, label="reference"); ax.semilogx(f, an["Z0"], "--", color=ORANGE, label="analytical")
ax.set_xlabel("Frequency (GHz)"); ax.set_ylabel("Ω"); ax.set_title("Z0"); ax.legend(fontsize=9)
fig.suptitle("Bend CPW: signal 35, gaps 4.15, grounds 50, Au 2 µm, on 3.6 µm SiO2 / 0.275 µm LN / 4.7 µm SiO2 / Si",
             y=1.03)
fig.subplots_adjust(wspace=0.28)
fig.savefig("results/fig_bend_vs_f.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
print("full-wave vs reference alpha %:", {k: round((v / float(np.interp(k, f, ar)) - 1) * 100, 2) for k, v in fw.items()})
print("base: alpha err %:", np.round((an["alpha_dB_cm"] / ar - 1) * 100, 1))
print("base: Ghione alpha err %:", np.round((gh["alpha_dB_cm"] / ar - 1) * 100, 1))
print("base: n err %:", np.round((an["n_m"] / nr - 1) * 100, 2))
print("base: Z err %:", np.round((an["Z0"] / Zr - 1) * 100, 2))

# ---- 3. validation set ------------------------------------------------------
doe = [json.loads(l) for l in open("results/doe_eddy.jsonl")]
E = {c: {"n": [], "Z": [], "a": []} for c in ("thick", "ghione")}
tab = []
for r in doe:
    S, W, t, h = r["S"] * UM, r["W"] * UM, r["t"] * UM, r["h"]
    fr = np.array(r["f"]) * 1e9
    a_ref, n_ref, Z_ref = ref_line(np.array(r["R"]), np.array(r["L"]), r["C_eps"], fr)
    for c in E:
        a = bend_cpw(fr, S, W, 50 * UM, t, stack(h), layer_sigma=BEND_SIGMA, conductor=c)
        E[c]["n"].append((a["n_m"] / n_ref - 1) * 100); E[c]["Z"].append((a["Z0"] / Z_ref - 1) * 100)
        E[c]["a"].append((a["alpha_dB_cm"] / a_ref - 1) * 100)
        if c == "thick":
            tab.append((r["S"], r["W"], r["t"], h, n_ref[1], a["n_m"][1], Z_ref[1], a["Z0"][1], a_ref[1],
                        a["alpha_dB_cm"][1]))
summary = {}
for c in E:
    for k in E[c]:
        E[c][k] = np.array(E[c][k])
    print(f"== {c}: {len(doe)} geometries")
    for k, lab in (("n", "n_m"), ("Z", "Z0"), ("a", "alpha")):
        e = E[c][k]
        print(f"   {lab:6s} error % at 20/60/150 GHz: mean {np.round(e.mean(0), 2)}  rms "
              f"{np.round(np.sqrt((e ** 2).mean(0)), 2)}  max|.| {np.round(np.abs(e).max(0), 2)}")
        summary[f"{c}_{k}"] = dict(mean=e.mean(0).tolist(), rms=np.sqrt((e ** 2).mean(0)).tolist(),
                                   maxabs=np.abs(e).max(0).tolist())
tt = np.array([r["t"] for r in doe])
fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
for ax, k, lab in zip(axs, ("n", "Z", "a"), ("n_m", "Z0", "α")):
    for j, (fq, col, mk) in enumerate(zip((20, 60, 150), (AQUA, BLUE, ORANGE), ("^", "o", "s"))):
        ax.scatter(tt, E["thick"][k][:, j], color=col, marker=mk, s=34, label=f"{fq} GHz", zorder=3,
                   edgecolors="white", linewidths=0.8)
    if k == "a":
        ax.scatter(tt, E["ghione"][k][:, 1], facecolors="none", edgecolors=MUTED, s=40, marker="o",
                   label="Ghione (previous), 60 GHz", zorder=2)
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xlabel("Metal thickness t (µm)"); ax.set_ylabel("analytical − reference (%)")
    ax.set_title(f"{lab}: error over {len(doe)} geometries")
    ax.legend(fontsize=8.5)
fig.subplots_adjust(wspace=0.3)
fig.savefig("results/fig_validation.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
json.dump(dict(tab=tab, summary=summary), open("results/eval_final.json", "w"), indent=1)
