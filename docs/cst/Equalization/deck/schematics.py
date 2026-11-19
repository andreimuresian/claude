"""Top-view schematics of the simulated structures (true path geometry; electrode and gap widths enlarged for
visibility). Output: img/sch_LS.png, img/sch_LBS.png, img/sch_LBS_waves.png, img/sch_full.png."""
import os, numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "img")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
NAVY, ORANGE, RED, GREY, INK = "#0E2268", "#EB6834", "#F20013", "#C9CDD6", "#1A1A1A"
HS, GP, WG = 0.011, 0.006, 0.020           # displayed half-signal width, gap, ground width (mm)
RB = 0.1025

def straight(z0, z1, y, n=2): z = np.linspace(z0, z1, n); return np.stack([z, np.full(n, y)], 1)
def arc(zc, yc, a0, a1, n=80):
    t = np.radians(np.linspace(a0, a1, n)); return np.stack([zc + RB * np.cos(t), yc + RB * np.sin(t)], 1)

def ribbon(ax, P, colour):
    d = np.gradient(P, axis=0); d /= np.linalg.norm(d, axis=1, keepdims=True); nrm = np.stack([-d[:, 1], d[:, 0]], 1)
    def band(o0, o1, c):
        ax.add_patch(Polygon(np.r_[P + o0 * nrm, (P + o1 * nrm)[::-1]], closed=True, fc=c, ec="none", zorder=2))
    band(-HS, HS, colour); band(HS + GP, HS + GP + WG, GREY); band(-HS - GP - WG, -HS - GP, GREY)

def port(ax, z, y, label, side):
    ax.add_patch(Rectangle((z - 0.03, y - 0.05), 0.06, 0.10, fc=RED, ec="none", zorder=4))
    ax.text(z + side * 0.06, y, label, color=RED, fontsize=11, fontweight="bold", va="center", ha="left" if side > 0 else "right")

def plane(ax, z, y, label, up=True):
    ax.plot([z, z], [y - 0.065, y + 0.065], "--", color=RED, lw=1.4, zorder=5)
    ax.text(z + 0.02, y + (0.07 if up else -0.07), label, color=RED, ha="left", va="bottom" if up else "top", fontsize=10.5, fontweight="bold")

def legend(ax, y, x0=0.0):
    for k, (c, t) in enumerate(((NAVY, "signal, buried (in the cladding)"), (ORANGE, "signal, raised (on the cladding)"), (GREY, "grounds"))):
        x = x0 + 1.25 * k; ax.add_patch(Rectangle((x, y), 0.08, 0.018, fc=c)); ax.text(x + 0.1, y + 0.009, t, va="center", fontsize=9.5)

def finish(ax, name, xl, yl, w):
    ax.set_xlim(*xl); ax.set_ylim(*yl); ax.set_aspect("equal"); ax.axis("off")
    ax.figure.savefig(os.path.join(OUT, name), dpi=220, bbox_inches="tight", pad_inches=0.02); plt.close(ax.figure)

# ---------------- L+S
fig, ax = plt.subplots(figsize=(12, 2.3))
ribbon(ax, straight(0, 3.24, 0), NAVY); port(ax, 0, 0, "Port 1", -1); port(ax, 3.24, 0, "Port 2", 1)
ax.annotate("", (0, -0.085), (3.24, -0.085), arrowprops=dict(arrowstyle="<->", color=INK)); ax.text(1.62, -0.12, "straight line, 3.24 mm (buried electrodes)", ha="center", va="top")
ax.text(1.62, HS + GP / 2 + 0.06, "gap fields exported along both gap centres, z = 0 – 3.24 mm", ha="center", fontsize=9.5, color=INK)
ax.plot([0, 3.24], [HS + GP / 2] * 2, ":", color=RED, lw=0.9, zorder=6); ax.plot([0, 3.24], [-HS - GP / 2] * 2, ":", color=RED, lw=0.9, zorder=6)
finish(ax, "sch_LS.png", (-0.5, 3.75), (-0.15, 0.12), 12)

# ---------------- L+B+S (plain, and with the waves of the field route)
def lbs(name, waves=False, leg=True):
    fig, ax = plt.subplots(figsize=(12, 3.8)); ZA = 2.43434
    ribbon(ax, straight(0, 2.16, -RB), NAVY); ribbon(ax, straight(2.16, ZA, -RB), ORANGE)
    ribbon(ax, arc(ZA, 0, -90, 90), ORANGE); ribbon(ax, straight(ZA, 2.16, RB), ORANGE); ribbon(ax, straight(2.16, 1.08, RB), NAVY)
    port(ax, 0, -RB, "Port 1", -1); port(ax, 1.08, RB, "Port 2", -1)
    plane(ax, 2.16, -RB, "plane 1", up=False); plane(ax, 2.16, RB, "plane 2")
    ax.text(1.0, -RB - 0.075, "line 1: 2.16 mm, buried", ha="center", va="top", color=NAVY, fontweight="bold")
    ax.text(1.45, RB + 0.075, "line 2: 1.08 mm, buried", ha="center", va="bottom", color=NAVY, fontweight="bold")
    ax.annotate("inner gap", (2.50, -0.03), (2.62, 0.02), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    ax.annotate("outer gap", (2.55, -0.105), (2.62, -0.15), fontsize=9.5, arrowprops=dict(arrowstyle="-", lw=0.7))
    if waves:
        kw = dict(arrowstyle="-|>", lw=1.6, mutation_scale=14)
        ax.annotate("", (2.05, -RB + 0.042), (1.75, -RB + 0.042), arrowprops=dict(color=NAVY, **kw)); ax.text(1.68, -RB + 0.042, "a$_1$", ha="right", va="center", fontsize=12)
        ax.annotate("", (1.75, -RB - 0.042), (2.05, -RB - 0.042), arrowprops=dict(color=ORANGE, **kw)); ax.text(1.68, -RB - 0.042, "b$_1$", ha="right", va="center", fontsize=12)
        ax.annotate("", (1.75, RB + 0.042), (2.05, RB + 0.042), arrowprops=dict(color=ORANGE, **kw)); ax.text(1.68, RB + 0.042, "b$_2$", ha="right", va="center", fontsize=12)
        ax.annotate("", (2.05, RB - 0.042), (1.75, RB - 0.042), arrowprops=dict(color=NAVY, **kw)); ax.text(1.68, RB - 0.042, "a$_2$", ha="right", va="center", fontsize=12)
        ax.text(0.55, -RB + 0.05, "z →", fontsize=11, va="bottom"); ax.text(0.80, RB - 0.05, "← s = 2.16 mm − z", fontsize=11, va="top")
        ax.text(2.33, 0, "block B", color=ORANGE, fontsize=12, fontweight="bold", ha="center", va="center")
    else:
        ax.text(1.4, -0.235, "block: vertical step, 50 µm gap taper (4.45 → 4.8 µm), raised straight 0.224 mm, U-bend R = 102.5 µm", ha="center", va="top", color=ORANGE, fontsize=10)
    if leg: legend(ax, -0.32)
    finish(ax, name, (-0.5, 2.85), (-0.34 if leg else -0.25, 0.26), 12)
lbs("sch_LBS.png", leg=False); lbs("sch_LBS_waves.png", waves=True)

# ---------------- full equaliser
fig, ax = plt.subplots(figsize=(12, 4.2))
ZA1, ZA2 = 2.97434, 0.98566
ribbon(ax, straight(0, 2.7, -RB), NAVY); ribbon(ax, straight(2.7, ZA1, -RB), ORANGE); ribbon(ax, arc(ZA1, 0, -90, 90), ORANGE); ribbon(ax, straight(ZA1, 2.7, RB), ORANGE)
ribbon(ax, straight(2.7, 1.26, RB), NAVY); ribbon(ax, straight(1.26, ZA2, RB), ORANGE); ribbon(ax, arc(ZA2, 2 * RB, -90, -270), ORANGE); ribbon(ax, straight(ZA2, 1.26, 3 * RB), ORANGE)
ribbon(ax, straight(1.26, 2.7, 3 * RB), NAVY)
port(ax, 0, -RB, "Port 1", -1); port(ax, 2.7, 3 * RB, "Port 2", 1)
ax.text(1.35, -RB - 0.075, "L1: 2.70 mm, polarity +", ha="center", va="top", color=NAVY, fontweight="bold")
ax.text(2.0, RB - 0.075, "L2: 1.44 mm, +", ha="center", va="top", color=NAVY, fontweight="bold")
ax.text(2.0, 3 * RB + 0.07, "L3: 1.44 mm, polarity −", ha="center", va="bottom", color=NAVY, fontweight="bold")
ax.text(3.2, 0, "bend 1", color=ORANGE, va="center", fontweight="bold"); ax.text(0.62, 2 * RB, "bend 2", color=ORANGE, va="center", ha="right", fontweight="bold")
legend(ax, -0.32); finish(ax, "sch_full.png", (-0.5, 3.6), (-0.34, 0.47), 12)
print("schematics saved")
