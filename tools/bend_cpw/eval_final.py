import json, sys, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, '.')
from cpw_analytic import bend_cpw, capacitance, BEND_LAYERS, BEND_SIGMA, C0, DB_PER_NEPER as DB
UM = 1e-6
NAVY, RED, ORANGE, TEAL, MUTED, GRID = "#0E2268", "#F20013", "#E07B39", "#1C8C82", "#5A606E", "#D9DCE3"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.grid": True, "grid.color": GRID,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "savefig.dpi": 160})

def stack(h):
    return [(h * UM, 3.9, 3.9), (0.275 * UM, 28.0, 44.0), (4.7 * UM, 3.9, 3.9), (550 * UM, 11.7, 11.7)]

# ---- base geometry vs frequency -------------------------------------------
rows = [json.loads(l) for l in open("results/sweep_eddy.jsonl") if l.startswith("{") and "info" not in l]
f = np.array([r['f_GHz'] for r in rows]); R = np.array([r['R'] for r in rows]); L = np.array([r['L'] for r in rows])
Ce = 1.350833e-10
nr, Zr = C0 * np.sqrt(L * Ce), np.sqrt(L / Ce)
ar = DB * R / (2 * Zr) / 100
an = bend_cpw(f * 1e9, 35 * UM, 4.15 * UM, 50 * UM, 2 * UM, BEND_LAYERS, layer_sigma=BEND_SIGMA)
ibc = {0.05: (1.69051, 42.269, 4.0158), 0.025: (1.69178, 42.327, 4.1861), 0.0125: (1.69277, 42.366, 4.3111)}
fig, axs = plt.subplots(1, 3, figsize=(15, 4))
axs[0].plot(f, ar, color=NAVY, lw=2.6, label="reference: eddy-current R, L + FEM C")
axs[0].plot(f, an["alpha_dB_cm"], "--", color=ORANGE, lw=2, label="analytical model")
for cr, mk in zip(ibc, ("o", "s", "^")):
    axs[0].plot(60, ibc[cr][2], mk, color=RED, ms=7, mfc="none", mew=1.8, label=f"your FEM (IBC), corner mesh {cr} µm")
axs[0].plot(f, 0.3519 * np.sqrt(f) + 0.03419 * f, ":", color=MUTED, lw=1.6, label="BEND200GHZ.csv fit (coworker)")
axs[0].set_xlabel("Frequency (GHz)"); axs[0].set_ylabel("α (dB/cm)"); axs[0].set_title("Attenuation"); axs[0].legend(fontsize=8.5, loc="upper left")
axs[1].plot(f, nr, color=NAVY, lw=2.6, label="reference"); axs[1].plot(f, an["n_m"], "--", color=ORANGE, lw=2, label="analytical")
axs[1].plot(60, ibc[0.05][0], "o", color=RED, mfc="none", mew=1.8, label="your FEM (IBC)")
axs[1].set_xscale("log"); axs[1].set_xlabel("Frequency (GHz)"); axs[1].set_title("Microwave index n_m"); axs[1].legend(fontsize=9)
axs[2].plot(f, Zr, color=NAVY, lw=2.6, label="reference"); axs[2].plot(f, an["Z0"], "--", color=ORANGE, lw=2, label="analytical")
axs[2].plot(60, ibc[0.05][1], "o", color=RED, mfc="none", mew=1.8, label="your FEM (IBC)")
axs[2].set_xscale("log"); axs[2].set_xlabel("Frequency (GHz)"); axs[2].set_ylabel("Ω"); axs[2].set_title("Z0"); axs[2].legend(fontsize=9)
fig.suptitle("Bend CPW (signal 35, gaps 4.15, grounds 50, Au 2 µm, on 3.6 µm SiO2 / 0.275 µm LN / 4.7 µm SiO2 / Si)", y=1.03)
fig.subplots_adjust(wspace=0.28)
fig.savefig("results/fig_bend_vs_f.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
print("base: alpha err %:", np.round((an['alpha_dB_cm'] / ar - 1) * 100, 1))
print("base: n err %:", np.round((an['n_m'] / nr - 1) * 100, 2))
print("base: Z err %:", np.round((an['Z0'] / Zr - 1) * 100, 2))

# ---- validation set ------------------------------------------------------
doe = [json.loads(l) for l in open("results/doe_eddy.jsonl")]
E = {"n": [], "Z": [], "a": [], "pcm_n": []}
tab = []
for r in doe:
    S, W, t, h = r['S'] * UM, r['W'] * UM, r['t'] * UM, r['h']
    fr = np.array(r['f']) * 1e9
    a = bend_cpw(fr, S, W, 50 * UM, t, stack(h), layer_sigma=BEND_SIGMA)
    Ln = np.array(r['L']); Rn = np.array(r['R'])
    n_ref = C0 * np.sqrt(Ln * r['C_eps']); Z_ref = np.sqrt(Ln / r['C_eps']); a_ref = DB * Rn / (2 * Z_ref) / 100
    E["n"].append((a['n_m'] / n_ref - 1) * 100); E["Z"].append((a['Z0'] / Z_ref - 1) * 100)
    E["a"].append((a['alpha_dB_cm'] / a_ref - 1) * 100)
    tab.append((r['S'], r['W'], r['t'], h, n_ref[1], a['n_m'][1], Z_ref[1], a['Z0'][1], a_ref[1], a['alpha_dB_cm'][1]))
for k in ("n", "Z", "a"):
    E[k] = np.array(E[k])
print(f"{len(doe)} geometries")
for k, lab in (("n", "n_m"), ("Z", "Z0"), ("a", "alpha")):
    print(f"{lab:6s} error % at 20/60/150 GHz: mean {np.round(E[k].mean(0), 2)}  rms {np.round(np.sqrt((E[k]**2).mean(0)), 2)}  max|.| {np.round(np.abs(E[k]).max(0), 2)}")
thick = np.array([r['t'] for r in doe]) >= 1.0
print("alpha, metal >= 1 um:", "mean", np.round(E['a'][thick].mean(0), 2), "max|.|", np.round(np.abs(E['a'][thick]).max(0), 2))
fig, axs = plt.subplots(1, 3, figsize=(15, 4.2))
for ax, k, lab in zip(axs, ("n", "Z", "a"), ("n_m", "Z0", "α")):
    tt = np.array([r['t'] for r in doe])
    for j, (fq, col) in enumerate(zip((20, 60, 150), (TEAL, NAVY, ORANGE))):
        ax.scatter(tt, E[k][:, j], color=col, s=28, label=f"{fq} GHz")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xlabel("Metal thickness t (µm)"); ax.set_ylabel("analytical − reference (%)")
    ax.set_title(f"{lab}: error over {len(doe)} geometries")
axs[0].legend(fontsize=9)
fig.subplots_adjust(wspace=0.3)
fig.savefig("results/fig_validation.png", bbox_inches="tight", facecolor="white"); plt.close(fig)
json.dump(dict(tab=tab), open("results/eval_final.json", "w"))
