"""Legacy lifted design (no buffer, 1575 nm): IL vs bottom gap at fixed x_lift = 7.0 / 7.1 / 7.2 um.
No new simulations: points are taken from sweep 1 (gaps 3.9 / 5.0) and lift_sweep (gap 4.2).
Dotted lines are a model between the simulated gaps: IL = IL_inf(gap) * f(L), L = x_lift - gap/2,
with IL_inf(gap) an exponential fit of the three fitted IL_inf and f the common Airy cavity factor
(gap-averaged rho0, 2alpha, period, phase from the per-gap fits in summary.json)."""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/home/user/claude/results/three_sweeps/"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
COL = {7.0: "#2a78d6", 7.1: "#1baf7a", 7.2: "#eb6834"}
GAPS = (3.9, 4.2, 5.0)
XL = (7.0, 7.1, 7.2)

a = np.genfromtxt(OUT + "sweep1_legacy_gap_xlift.csv", delimiter=",", names=True)
sim = {(g, x): (il, vp) for g, x, il, vp in zip(a["gap_um"], np.round(a["x_lift_um"], 2), a["IL_dB_per_cm"], a["VpiL_Vcm"])}
S = json.load(open(OUT + "summary.json"))
fp = {g: S[f"sweep1_gap{g}"] for g in GAPS}
ILinf = np.array([fp[g]["IL_inf_dB_cm"] for g in GAPS])
slope, icpt = np.polyfit(GAPS, np.log(ILinf), 1)                 # IL_inf = exp(icpt + slope*gap)
r0, a2, P, ph = (np.mean([fp[g][k] for g in GAPS]) for k in ("rho0", "two_alpha_per_um", "period_um", "phase_rad"))


def f_cav(L):
    rho = r0 * np.exp(-a2 * L)
    return (1 - rho ** 2) / (1 - 2 * rho * np.cos(2 * np.pi * L / P + ph) + rho ** 2)


def model(g, x):
    return np.exp(icpt + slope * g) * f_cav(x - g / 2)


rows = []
for x in XL:
    for g in GAPS:
        il, vp = sim[(g, x)]
        rows.append((x, g, round(x - g / 2, 3), il, fp[g]["IL_inf_dB_cm"], il / fp[g]["IL_inf_dB_cm"], vp, model(g, x)))
with open(OUT + "sweep1_IL_vs_gap_fixed_xlift.csv", "w") as f:
    f.write("x_lift_um,gap_um,cavity_length_um,IL_dB_per_cm,IL_inf_dB_per_cm,IL_over_IL_inf,VpiL_Vcm,model_IL_dB_per_cm\n")
    for r in rows:
        f.write("{:.2f},{:.1f},{:.2f},{:.5f},{:.4f},{:.3f},{:.4f},{:.5f}\n".format(*r))

gg = np.linspace(3.8, 5.1, 400)
fig, (a1, a2_) = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw=dict(width_ratios=[1.35, 1]))
a1.plot(gg, np.exp(icpt + slope * gg), "--", color="#7f8c8d", lw=1.1,
        label=f"IL∞ (no cavity): ∝ e^({slope:.2f}·gap)")
for x in XL:
    a1.plot(gg, model(gg, x), ":", color=COL[x], lw=1.1)
    a1.plot(GAPS, [sim[(g, x)][0] for g in GAPS], "o", color=COL[x], ms=7, label=f"x_lift = {x:.1f} µm")
TL = [f"{g}\nVπ·L {sim[(g, 7.0)][1]:.2f} V·cm" for g in GAPS]
a1.set_yscale("log"); a1.set_ylim(0.008, 4); a1.set_xlim(3.8, 5.1)
a1.set_xticks(GAPS, TL); a1.grid(alpha=0.3, which="both", lw=0.4)
a1.set_xlabel("bottom gap (µm)"); a1.set_ylabel("IL (dB/cm)")
a1.set_title("IL vs gap at fixed x_lift (dots = simulated, dotted = model)")
a1.plot([], [], ":", color="#555", label="model between simulated gaps")
a1.legend(loc="upper right", fontsize=8.5)

for x in XL:
    a2_.plot(gg, f_cav(x - gg / 2), ":", color=COL[x], lw=1.1)
    a2_.plot(GAPS, [sim[(g, x)][0] / fp[g]["IL_inf_dB_cm"] for g in GAPS], "o", color=COL[x], ms=7,
             label=f"x_lift = {x:.1f} µm")
a2_.axhline(1, color="#7f8c8d", lw=0.8, ls="--")
a2_.set_xticks(GAPS); a2_.set_xlim(3.8, 5.1); a2_.grid(alpha=0.3, lw=0.4)
a2_.set_xlabel("bottom gap (µm)"); a2_.set_ylabel("IL / IL∞  (cavity factor)")
a2_.set_title("Cavity factor: the gap also shifts L = x_lift − gap/2")
a2_.legend(loc="upper right", fontsize=8.5)
plt.tight_layout(); fig.savefig(OUT + "sweep1_IL_vs_gap_fixed_xlift.png", dpi=150); plt.close(fig)

print(f"IL_inf slope {slope:.3f}/um; avg rho0 {r0:.3f} 2a {a2:.4f} P {P:.4f} ph {ph:.3f}")
for r in rows:
    print("x={:.1f} g={:.1f} L={:.2f} IL={:.4f} ILinf={:.4f} ratio={:.2f} VpiL={:.3f} model={:.4f}".format(*r))
