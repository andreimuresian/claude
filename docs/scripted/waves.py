"""Waves vs voltages at a port (figure for the scripted TL note)."""
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
fig, ax = plt.subplots(figsize=(13, 9.6)); ax.set_xlim(0, 13); ax.set_ylim(0, 9.6); ax.axis("off")
def box(x, y, w, h, t, fc="#eef", fs=10.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03", fc=fc, ec="k", lw=1.3))
    ax.text(x + w/2, y + h/2, t, ha="center", va="center", fontsize=fs)
def arr(x0, y0, x1, y1, c, lab=None, dy=0.2):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=18, lw=2.2, color=c))
    if lab: ax.text((x0 + x1)/2, y0 + dy, lab, ha="center", color=c, fontsize=12)
# ---- (1) one port, two descriptions
ax.text(0.1, 9.25, "(1) The same port, described two ways", fontsize=13, weight="bold")
box(0.3, 7.0, 2.2, 1.6, "element X", "#ddd")
box(5.2, 7.0, 2.2, 1.6, "element Y", "#ddd")
ax.plot([2.5, 5.2], [8.2, 8.2], "k", lw=1.5); ax.plot([2.5, 5.2], [7.4, 7.4], "k", lw=1.5)
ax.text(3.85, 7.75, "V,  I →", ha="center", fontsize=12)
ax.text(3.85, 6.55, "voltages: one number V (and one I)\nshared by both sides at the same instant", ha="center", fontsize=9.5)
box(7.9, 7.0, 2.0, 1.6, "element X", "#ddd"); box(11.0, 7.0, 1.9, 1.6, "element Y", "#ddd")
arr(9.9, 8.25, 11.0, 8.25, "#1565c0", "a", 0.12)
arr(11.0, 7.35, 9.9, 7.35, "#c62828", "b", 0.12)
ax.text(10.45, 6.55, "waves: two one-way signals,\none in each direction", ha="center", fontsize=9.5)
ax.text(6.5, 6.0, "a = (V + R0·I)/2      b = (V − R0·I)/2      ⇔      V = a + b      I = (a − b)/R0",
        ha="center", fontsize=12.5, bbox=dict(fc="#fffbe6", ec="#c9a400"))
# ---- (2) three loads, same incident wave
ax.text(0.1, 5.25, "(2) Send the same wave a = 1 V at three loads (R0 = 50 Ω)", fontsize=13, weight="bold")
for k, (name, G, Vt) in enumerate([("matched 50 Ω", "Γ = 0", "b = 0,   V = a + b = 1 V"),
                                   ("open circuit", "Γ = +1", "b = +1,   V = 2 V,   I = 0"),
                                   ("short circuit", "Γ = −1", "b = −1,   V = 0,   I = 2/R0")]):
    x = 0.3 + 4.3*k
    arr(x, 4.3, x + 1.6, 4.3, "#1565c0", "a = 1")
    if G != "Γ = 0": arr(x + 1.6, 3.7, x, 3.7, "#c62828", "b", -0.42)
    box(x + 1.6, 3.45, 1.9, 1.1, f"{name}\n{G}", "#f4f4f4", 9.5)
    ax.text(x + 1.75, 2.95, Vt, ha="center", fontsize=10)
ax.text(6.5, 2.45, "The load answers with b = Γ·a,  Γ = (Z − R0)/(Z + R0).   The voltage V is not sent: it is the result a + b.",
        ha="center", fontsize=11)
# ---- (3) why the simulator prefers waves
ax.text(0.1, 1.85, "(3) Why INTERCONNECT works with waves", fontsize=13, weight="bold")
ax.text(0.3, 0.15,
 "• Each element is a rule  'outgoing waves = S × incoming waves' (b = S·a): a cause→effect filter it can run sample by sample.\n"
 "• A node voltage has no direction: it depends on both sides at the same instant, so it cannot be computed as one element's output.\n"
 "• A bidirectional wire therefore carries two sample streams: a (to the right) and b (to the left). A reflection is just b.\n"
 "• A driver is described by the wave it launches: a matched source of EMF V_emf launches a = V_emf/2 (panel 2, matched case: V = a).",
 fontsize=10.5, va="bottom")
plt.savefig("waves.png", dpi=140, bbox_inches="tight")
