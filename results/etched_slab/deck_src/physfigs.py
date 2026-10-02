import numpy as np, matplotlib, json
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
BLUE, ORANGE, AQUA, YEL, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#8a8a8a", "#222222"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fit = json.load(open("/home/user/claude/results/etched_slab/ripple_comparison_facet_vs_interface.json"))
F = fit["slab_facet_in_gold"]
P = F["period_um"]; lamx = 2 * P; kx = 2 * np.pi / lamx
def IL(L, f=F):
    rho = f["rho0"] * np.exp(-f["two_alpha_per_um"] * L)
    return f["IL_inf"] * (1 - rho**2) / (1 - 2 * rho * np.cos(2 * np.pi * L / f["period_um"] + f["phase_rad"]) + rho**2)
# ---------------- Q1 -------------------------------------------------------
Lpk = (2 * np.pi * 2 - F["phase_rad"]) * P / (2 * np.pi)          # a peak (m = 2)
Ls = [(Lpk, "resonance (peak)", ORANGE), (Lpk + P / 2, "off resonance (dip)", BLUE), (Lpk + P, "next resonance (peak)", ORANGE)]
fig = plt.figure(figsize=(13, 5.2))
gs = fig.add_gridspec(3, 2, width_ratios=[1.25, 1], hspace=0.55, wspace=0.18)
a_il = fig.add_subplot(gs[:, 1])
kxc = kx - 1j * 0.09                                                # field decay under the gold
r1, r2 = 0.5, -0.95
Imax = None
for i, (L, lab, c) in enumerate(Ls):
    ax = fig.add_subplot(gs[i, 0])
    x = np.linspace(0, L, 800)
    E = (np.exp(-1j * kxc * x) + r2 * np.exp(-1j * kxc * (2 * L - x))) / (1 - r1 * r2 * np.exp(-2j * kxc * L))
    I = np.abs(E) ** 2
    if Imax is None: Imax = I.max()
    ax.fill_between(x, 0, I / Imax, color=c, alpha=0.25, lw=0); ax.plot(x, I / Imax, color=c, lw=2)
    ax.add_patch(Rectangle((L, 0), 0.25, 1.1, color="#f2c14e", lw=0))
    ax.axvline(0, color=GREY, lw=1.5)
    ax.set_xlim(-0.1, Ls[-1][0] + 0.35); ax.set_ylim(0, 1.1); ax.set_yticks([])
    ax.text(0.04, 1.0, f"L = {L:.2f} $\\mu$m: {lab}", transform=ax.transAxes, va="top", fontsize=11.5, color=INK, bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
    for xn in np.arange(L, -0.01, -P):                                  # node grid from the mirror
        ax.plot([xn, xn], [0, 0.08], color=INK, lw=1)
    if i < 2: ax.set_xticklabels([])
    else: ax.set_xlabel(r"x from the gold inner edge ($\mu$m)")
    a_il.plot(L, IL(L), "o", ms=11, color=c, zorder=5)
Lg = np.linspace(0.4, 4.9, 900)
a_il.plot(Lg, IL(Lg), color=INK, lw=1.6)
a_il.set_yscale("log"); a_il.set_xlabel(r"cavity length L ($\mu$m)"); a_il.set_ylabel("IL (dB/cm)")
a_il.annotate("", (Ls[2][0], 3.6), (Ls[0][0], 3.6), arrowprops=dict(arrowstyle="<->", lw=1.4, color=INK))
a_il.text((Ls[0][0] + Ls[2][0]) / 2, 4.3, r"$\Delta L = \lambda_x/2$ = %.3f $\mu$m" % P, ha="center", fontsize=12)
a_il.set_ylim(0.025, 6.5); a_il.grid(alpha=0.25)
fig.text(0.02, 0.965, r"Same lateral wavelength $\lambda_x$ = %.2f $\mu$m in every cavity; ticks = nodes every $\lambda_x$/2" % lamx,
         fontsize=12, color=INK)
fig.savefig("fig/q1_cavity.png", dpi=170, bbox_inches="tight"); plt.close(fig)
# ---------------- Q2 -------------------------------------------------------
nr, nsw = 1.884, 2.081
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw=dict(width_ratios=[1, 1.05], wspace=0.3))
kxn = np.sqrt(nsw**2 - nr**2)
a1.add_patch(FancyArrowPatch((0, 0), (nr, 0), arrowstyle="-|>", mutation_scale=18, lw=2.4, color=BLUE))
a1.add_patch(FancyArrowPatch((0, 0), (nr, kxn), arrowstyle="-|>", mutation_scale=18, lw=2.4, color=ORANGE))
a1.add_patch(FancyArrowPatch((nr, 0), (nr, kxn), arrowstyle="-|>", mutation_scale=18, lw=2.4, color=AQUA))
a1.text(nr / 2, -0.13, r"$\beta = n_{rib}k_0$  (rib mode, 1.884)", ha="center", va="top", color=BLUE, fontsize=12)
a1.text(nr * 0.30, kxn * 0.30 + 0.42, r"$n_{sw}k_0$" + "\n(wave under the gold, 2.08)", ha="center", color=ORANGE, fontsize=12)
a1.text(nr + 0.05, kxn / 2, r"$k_x$" + "\n" + r"$\lambda_x = \lambda/\sqrt{n_{sw}^2-n_{rib}^2}$" + "\n" + r"$\approx$ 1.8 $\mu$m", va="center", color="#0f7a55", fontsize=12)
a1.set_xlim(-0.1, 2.9); a1.set_ylim(-0.45, 1.25); a1.set_aspect("equal"); a1.axis("off")
a1.set_title("Phase matching fixes the lateral wavelength", fontsize=13, loc="left", pad=18)
d = np.load(SP + "sw_profile.npz"); y, h = d["y"], d["h"]
a2.add_patch(Rectangle((0, 0.275), 1.15, 0.35, color="#f2c14e", lw=0)); a2.text(1.02, 0.45, "Au", fontsize=12)
a2.add_patch(Rectangle((0, 0), 1.15, 0.275, color="#c9ced4", lw=0)); a2.text(1.02, 0.12, "LN slab", fontsize=12)
a2.add_patch(Rectangle((0, -0.8), 1.15, 0.8, color="#d6e8f8", lw=0)); a2.text(1.02, -0.45, "BOX", fontsize=12)
m = y <= 0.275
a2.plot(h[m] ** 2, y[m], color=ORANGE, lw=2.4)
a2.annotate("field maximum at the\nAu / LN interface", (0.99, 0.27), (0.3, -0.3), fontsize=11.5,
            arrowprops=dict(arrowstyle="->", lw=1.2))
a2.set_xlim(0, 1.45); a2.set_ylim(-0.8, 0.63); a2.set_xlabel(r"$|H|^2$ of the wave under the gold (norm.)"); a2.set_ylabel(r"y ($\mu$m)")
a2.set_title("Where that wave lives: the top of the slab", fontsize=13, loc="left")
fig.savefig("fig/q2_phase_matching.png", dpi=170, bbox_inches="tight"); plt.close(fig)
# ---------------- Q4 -------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(13, 3.9), sharey=True, gridspec_kw=dict(wspace=0.08))
for ax, (tag, xm, c, ttl, note) in zip(axs, [("long120", 6.0, ORANGE, "Slab end wrapped in gold: hard mirror", "node AT the wall"),
                                               ("past20", 7.0, BLUE, "Gold ends on top of the slab: soft mirror", "antinode at the edge,\nevanescent tail beyond")]):
    dd = np.load(SP + f"fcut_{tag}.npz"); x = dd["x"] - xm; I = dd["mid"]
    sel = (x > -2.7) & (x < 1.2)
    In = I[sel] / I[(x > -2.7) & (x < 0.05)].max()
    ax.plot(x[sel], In, color=c, lw=2.2)
    ax.axvspan(0, 1.2, color="#f2c14e" if tag == "long120" else "#d6e8f8", alpha=0.6, lw=0)
    ax.axvline(0, color=INK, lw=1.2)
    nodes = [0.0 - k * P for k in range(4)] if tag == "long120" else [-0.30 - k * P for k in range(3)]
    for xn in nodes: ax.axvline(xn, color=GREY, lw=0.9, ls=":")
    ax.set_xlim(-2.7, 1.2); ax.set_ylim(0, 1.15)
    ax.set_title(ttl, fontsize=13, loc="left"); ax.set_xlabel(r"x $-$ mirror position ($\mu$m)")
    ax.text(0.05, 0.85 if tag == "long120" else 0.62, note, fontsize=11.5, transform=ax.transData if False else ax.transAxes, color=INK) if False else None
    ax.annotate(note, (0.0, 0.03 if tag == "long120" else 0.5), (0.18, 0.75 if tag == "long120" else 0.55),
                fontsize=11.5, arrowprops=dict(arrowstyle="->", lw=1.1))
    ax.text(0.03, 1.08, "gold" if tag == "long120" else "SiO$_2$ over the slab", transform=ax.get_xaxis_transform(), fontsize=10.5, color=INK) if False else None
axs[0].set_ylabel(r"$|E|^2$ in the slab (norm.)")
axs[1].annotate("", (-0.30, 0.25), (0.0, 0.25), arrowprops=dict(arrowstyle="<->", lw=1.3))
axs[1].text(-0.15, 0.29, "0.30 $\\mu$m", ha="center", fontsize=11)
fig.savefig("fig/q4_mirrors.png", dpi=170, bbox_inches="tight"); plt.close(fig)
print("ok", Lpk)
