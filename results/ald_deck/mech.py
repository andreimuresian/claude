import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
LN, OX, AU, AL = "#8b95a1", "#9cc9ef", "#e8b923", "#f472d0"
fig, axs = plt.subplots(1, 2, figsize=(13, 4.6))
def panel(ax, buf, title):
    yb = 0.0; ys = 1.0
    ax.add_patch(Rectangle((0, 0), 6, ys, fc=LN, ec="none"))
    ax.text(0.3, 0.45, "LN slab   ε ≈ 28–44", fontsize=12)
    y0 = ys
    if buf:
        ax.add_patch(Rectangle((0, ys), 6, 0.8, fc=OX, ec="none")); ax.text(0.3, ys + 0.3, "SiO$_2$ buffer   ε = 3.75", fontsize=12); y0 = ys + 0.8
    ax.add_patch(Rectangle((3.5, y0), 2.5, 2.4, fc=AU, ec="none")); ax.text(4.2, y0 + 1.6, "Gold\nelectrode", fontsize=12, weight="bold")
    ax.add_patch(Rectangle((0, y0), 3.5, 0.25, fc=AL, ec="none")); ax.add_patch(Rectangle((3.25, y0 + 0.25), 0.25, 2.15, fc=AL, ec="none"))
    ax.text(0.3, y0 + 0.45, "Al$_2$O$_3$   ε = 9.8", fontsize=12, color="#9d174d", weight="bold")
    ax.text(1.0, y0 + 1.6, "air  ε = 1", fontsize=12, color="0.4")
    ax.set_xlim(0, 6); ax.set_ylim(0, 4.6); ax.axis("off"); ax.set_title(title, fontsize=14, weight="bold")
panel(axs[0], False, "Cordoba: Al$_2$O$_3$ lies on LN")
panel(axs[1], True, "Lisbon: Al$_2$O$_3$ lies on low-ε SiO$_2$")
axs[0].text(0.3, -0.35, "Al$_2$O$_3$ is much weaker than the LN below it → small effect", fontsize=12, transform=axs[0].transData)
axs[1].text(0.3, -0.35, "Al$_2$O$_3$ is the strongest material near the electrode corner → larger effect", fontsize=12)
fig.tight_layout(); fig.savefig("figs/mechanism.png", dpi=180)
