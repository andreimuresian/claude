"""Why far-end crosstalk accumulates and near-end crosstalk saturates (slice-by-slice picture)."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
tr = 1.0                                    # aggressor edge duration (time units); v = 1 (length = time)
def edge(t):  return np.clip(t/tr, 0, 1)    # aggressor voltage: 0 -> 1 ramp
def dedge(t): return ((t > 0) & (t < tr))/tr
def victim(z, t, Lline, N=600):
    """Sum of slice contributions (weak coupling): forward and backward parts on the victim at (z, t)."""
    zk = (np.arange(N) + 0.5)*Lline/N; dz = Lline/N
    fwd = sum(dz*dedge(t - z) for zk_ in zk[zk < z])            # all forward bits ride with the edge
    bwd = np.sum(dz*dedge(t - zk[zk > z] - (zk[zk > z] - z)))  # each backward bit leaves at a different time
    return fwd, bwd
fig = plt.figure(figsize=(14, 12.5))
# ---- row 1: snapshots along the line
Lline = 6.0; zz = np.linspace(0, Lline, 400)
for i, t in enumerate((2.0, 4.0, 6.0)):
    ax = fig.add_axes([0.09, 0.80 - i*0.12, 0.85, 0.10])
    F = np.array([victim(z, t, Lline)[0] for z in zz]); B = np.array([victim(z, t, Lline)[1] for z in zz])
    ax.plot(zz, edge(t - zz), color="#999", lw=1.5, label="aggressor voltage" if i == 0 else None, alpha=0.9)
    ax.fill_between(zz, 0, 0.8*F/Lline, color="#c62828", alpha=0.6, label="victim: forward-going crosstalk" if i == 0 else None)
    ax.fill_between(zz, 0, -0.5*B, color="#1565c0", alpha=0.6, label="victim: backward-going crosstalk" if i == 0 else None)
    ax.set_xlim(0, Lline); ax.set_ylim(-0.45, 1.1); ax.set_yticks([])
    ax.text(-0.05, 0.4, f"time {t:.0f}", ha="right", fontsize=11, transform=ax.get_yaxis_transform())
    ax.axvline(t - tr/2, color="k", lw=0.6, ls=":")
    if i == 0:
        ax.set_title("(1) Snapshots: the aggressor's edge (grey) travels right; every slice it passes throws a small bit into the victim",
                     fontsize=12, loc="left")
        ax.legend(loc="upper right", fontsize=9, ncol=3)
    if i == 2: ax.set_xlabel("position along the line  (near end at left, far end at right)")
fig.text(0.06, 0.475, "Red: the forward bits travel at the same speed as the edge, so they stay on top of each other and PILE UP into one taller pulse.\n"
         "Blue: the backward bits travel against the edge; each one is thrown at a different place and time, so they line up one AFTER another\n"
         "into a long, flat tail. Adding more line makes the blue tail LONGER, not TALLER.", fontsize=11)
# ---- row 2: what arrives at the two ends, for three lengths
t = np.linspace(-1, 16, 1500)
axn = fig.add_axes([0.06, 0.27, 0.42, 0.16]); axf = fig.add_axes([0.54, 0.27, 0.42, 0.16])
for Lx, c in ((0.2, "C2"), (1.0, "C1"), (4.0, "C4")):
    near = np.array([victim(0.0, ti, Lx, 300)[1] for ti in t])
    far = np.array([victim(Lx, ti, Lx, 300)[0] for ti in t])
    axn.plot(t, near, c, lw=2, label=f"length {Lx:g}")
    axf.plot(t - Lx, far, c, lw=2, label=f"length {Lx:g}")
axn.set_title("(2) At the NEAR end: grows until the line is half an edge long,\nthen only gets LONGER, not taller", fontsize=11, loc="left")
axf.set_title("At the FAR end: one pulse, its height grows\nin proportion to the length", fontsize=11, loc="left")
for a in (axn, axf): a.set_xlabel("time"); a.set_yticks([]); a.legend(fontsize=9); a.grid(alpha=0.3)
axf.set_xlim(-0.5, 2.5)
# ---- row 3: phasor picture for a sine wave
ax1 = fig.add_axes([0.06, 0.01, 0.40, 0.14]); ax2 = fig.add_axes([0.56, 0.01, 0.40, 0.14])
n = 40
ph_f = np.zeros(n); ph_b = np.linspace(0, 2*np.pi, n, endpoint=False)   # backward: phase turns with position
for ax, ph, col, title in ((ax2, ph_f, "#c62828", "far end, sine wave: every slice's arrow points the same way:\nthe chain is a straight line, longer line = longer sum"),
                           (ax1, ph_b, "#1565c0", "near end, sine wave: each slice's arrow is rotated a bit more:\nthe chain curls into a circle and never gets far")):
    p = np.concatenate([[0], np.cumsum(np.exp(1j*ph))])
    for k in range(n):
        ax.annotate("", xy=(p[k+1].real, p[k+1].imag), xytext=(p[k].real, p[k].imag),
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.2))
    ax.plot([0, p[-1].real], [0, p[-1].imag], "k--", lw=1)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title, fontsize=10.5)
    ax.set_xlim(min(p.real.min(), -1) - 0.5, max(p.real.max(), 1) + 0.5); ax.set_ylim(p.imag.min() - 0.6, p.imag.max() + 0.6)
fig.text(0.06, 0.205, "(3) The same for a sine wave: add one arrow per slice (dashed = total crosstalk)", fontsize=12)
plt.savefig("accumulate.png", dpi=120)
