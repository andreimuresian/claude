import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
BLUE, ORANGE, AQUA, GREY, INK = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a", "#222222"
AU, LN, OX = "#f2c14e", "#8b95a1", "#a9cff2"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
NR, NSW, N_NOLN, N_NOAU = 1.884, 2.073, 1.456, 1.606
XG, XM, XE = 2.1, 6.0, 10.0
fig, axs = plt.subplots(2, 2, figsize=(13, 6.4), gridspec_kw=dict(height_ratios=[1, 1.25], hspace=0.12, wspace=0.12), sharex=True)
cases = [("A", "Mirror = slab end inside the gold", N_NOLN, "gold on BOX, no LN\nn = 1.46"),
         ("B", "Mirror = gold edge, slab continues under SiO$_2$", N_NOAU, "LN slab under SiO$_2$, no gold\nn = 1.61")]
kx = 2 * np.pi / 1.79
for j, (tag, ttl, nout, lab) in enumerate(cases):
    a = axs[0, j]
    # BOX
    a.add_patch(Rectangle((0, -0.5), XE, 0.5, color=OX, lw=0))
    # slab (drawn 0.35 thick for visibility)
    t = 0.35
    xs_end = XM if tag == "A" else XE
    a.add_patch(Rectangle((0, 0), xs_end, t, color=LN, lw=0))
    # gold block
    xau_end = XE if tag == "A" else XM
    a.add_patch(Rectangle((XG, t), xau_end - XG, 1.2, color=AU, lw=0))
    if tag == "A":
        a.add_patch(Rectangle((XM, 0), XE - XM, t, color=AU, lw=0))
    else:
        a.add_patch(Rectangle((XM, t), XE - XM, 1.2, color=OX, lw=0))
    # rib hint
    a.add_patch(Rectangle((0, t), 0.6, 0.3, color=LN, lw=0))
    # overlap region outline
    a.add_patch(Rectangle((XG, 0), XM - XG, t, fill=False, ec=ORANGE, lw=2.2))
    # field sketch along the slab
    x = np.linspace(XG, XM, 400)
    f = np.abs(np.sin(kx * (XM - x) + (0 if tag == "A" else 0.9)))
    a.plot(x, t + 0.05 + 0.5 * f * np.exp(-0.04 * (x - XG)), color="#c0392b", lw=1.6)
    if tag == "B":
        xe = np.linspace(XM, XM + 1.4, 100); f0 = np.abs(np.sin(0.9))
        a.plot(xe, t + 0.05 + 0.5 * f0 * np.exp(-3.0 * (xe - XM)), color="#c0392b", lw=1.6)
    a.plot([XM, XM], [-0.5, 1.75], color=INK, lw=1.2, ls="--")
    a.text(XM, 1.8, "mirror", ha="center", va="bottom", fontsize=11, color=INK)
    a.text(XG + 0.1, 1.42, "|E|$^2$ along the slab", fontsize=9.5, color="#c0392b")
    a.text(0.0, 2.25, f"{tag}. {ttl}", fontsize=13.5, color=INK, va="bottom")
    a.text((XG + XM) / 2, 0.95, "gold + LN overlap", ha="center", color=ORANGE, fontsize=11.5, weight="bold")
    a.text(1.0, -0.3, "BOX", fontsize=10, color="#333", va="center")
    a.set_ylim(-0.55, 2.6); a.set_yticks([]); a.spines["left"].set_visible(False); a.spines["bottom"].set_visible(False)
    a.tick_params(bottom=False)
    # index profile
    b = axs[1, j]
    b.axvspan(0, XG, color="#f2f2f2", lw=0)
    b.text(XG / 2, 1.42, "rib + gap\n(source)", ha="center", va="bottom", fontsize=10, color="#666")
    b.plot([XG, XM], [NSW, NSW], color=ORANGE, lw=3)
    b.plot([XM, XE], [nout, nout], color=BLUE if tag == "A" else AQUA, lw=3)
    b.plot([XM, XM], [nout, NSW], color=INK, lw=1, ls=":")
    b.axhline(NR, color=GREY, lw=1.4, ls="--")
    b.text(XE - 0.05, NR + 0.015, "rib mode 1.884", ha="right", va="bottom", fontsize=10.5, color="#555")
    b.text((XG + XM) / 2, NSW + 0.02, "n = 2.07 > n$_{rib}$: propagates\n(standing wave, period 0.9 µm)", ha="center", va="bottom", fontsize=10.5, color=ORANGE)
    b.text((XM + XE) / 2 + 0.15, nout + 0.02, lab + " < n$_{rib}$: evanescent", ha="center", va="bottom", fontsize=10.5,
           color=BLUE if tag == "A" else "#0f7a55")
    b.set_ylim(1.38, 2.25); b.set_xlim(0, XE)
    b.set_xlabel("x from the rib centre (µm, schematic)")
    if j == 0: b.set_ylabel("index of the stack's\nlateral wave")
    else: b.set_yticklabels([])
    b.grid(alpha=0.2)
fig.savefig("fig/mech_two_mirrors.png", dpi=170, bbox_inches="tight"); plt.close(fig)
print("ok")
