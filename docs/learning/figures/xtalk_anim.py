"""Animation: how far-end (FEXT) and near-end (NEXT) crosstalk build up on the victim line B while a pulse travels on
line A. Weak coupling, both lines with the same wave speed v = 1, line length 1, matched ends (no reflections).
At every point the pulse on A leaks a little into B:
  - a forward wavelet, which travels with the pulse: they pile up -> FEXT = Kf * z * dp/dt (grows with length);
  - a backward wavelet, which travels back toward the near end: they spread out -> NEXT = Kb * integral of p (saturates).
Total on B = FEXT + NEXT. Right column: what a probe sees at the two ends of B."""
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
w = 0.06                                   # pulse width (fraction of the line delay)
p = lambda t: np.exp(-((t - 0.15) / w) ** 2)
dp = lambda t: -2 * (t - 0.15) / w ** 2 * p(t)
z = np.linspace(0, 1, 300); zp = np.linspace(0, 1, 600); dzp = zp[1] - zp[0]
Kf, Kb = -0.004, 0.66          # chosen so the NEXT plateau is ~60 % of the FEXT peak (similar sizes, as in the CST runs)
def fwd(zz, t):  return Kf * zz * dp(t - zz)                                  # piled-up forward wavelets
def bwd(zz, t):                                                                 # wavelets born at z' >= z, travelled back
    zz = np.atleast_1d(zz)
    return np.array([Kb * np.sum(p(t - (2 * zp[zp >= x] - x))) * dzp for x in zz])
T = np.linspace(0, 2.35, 150)
nearN = bwd(np.array([0.0]), 0)[0]
near = np.array([bwd(0.0, t)[0] + fwd(0.0, t) for t in T]); far = np.array([bwd(1.0, t)[0] + fwd(1.0, t) for t in T])
sF = np.max(np.abs([fwd(z, t) for t in T])); sB = np.max(np.abs(near)); s = max(sF, sB)
C = dict(A="0.25", F="#2a78d6", N="#eb6834", T="#1baa7d")
fig = plt.figure(figsize=(12, 9)); g = fig.add_gridspec(4, 2, width_ratios=[1.7, 1])
ax = [fig.add_subplot(g[i, 0]) for i in range(4)]; bn = fig.add_subplot(g[0:2, 1]); bf = fig.add_subplot(g[2:4, 1])
titles = ["Line A: the driving pulse (moves right)", "Line B, forward part = FEXT (rides with the pulse, grows)",
          "Line B, backward part = NEXT (runs back to the near end, spreads out)", "Line B, total = FEXT + NEXT"]
lines = []
for a, ti, col in zip(ax, titles, (C["A"], C["F"], C["N"], C["T"])):
    l, = a.plot([], [], color=col, lw=2); lines.append(l); a.axhline(0, color="0.85", lw=0.8)
    a.set_xlim(0, 1); a.set_title(ti, fontsize=10, loc="left"); a.set_yticks([]); a.set_xticks([0, 1])
    a.set_xticklabels(["near end", "far end"] if a is ax[3] else ["", ""])
ax[0].set_ylim(-0.2, 1.2)
for a in ax[1:3]: a.set_ylim(-1.15 * s, 1.15 * s)
ax[3].set_ylim(-1.1 * (sF + sB), 1.1 * (sF + sB))
ax[1].text(0.99, 0.85, f"B magnified x{1 / s:.0f} vs A", transform=ax[1].transAxes, ha="right", fontsize=9, color="0.4")
for b, tr, ti in ((bn, near, "Probe at B near end: NEXT arrives\n(low, long: lasts twice the line delay)"),
                  (bf, far, "Probe at B far end: FEXT arrives\n(short, strong, with the pulse)")):
    b.plot(T, tr, color="0.85", lw=1); b.set_xlim(0, T[-1]); b.set_ylim(-1.15 * s, 1.15 * s); b.axhline(0, color="0.85", lw=0.8)
    b.set_title(ti, fontsize=10); b.set_yticks([]); b.set_xlabel("time (line delays)")
pn, = bn.plot([], [], color=C["N"], lw=2); pf, = bf.plot([], [], color=C["F"], lw=2)
mk = [a.axvline(0, color="0.6", lw=0.8, ls=":") for a in ax]
fig.tight_layout()
def frame(i):
    t = T[i]; F = fwd(z, t); N = bwd(z, t)
    for l, y in zip(lines, (p(t - z), F, N, F + N)): l.set_data(z, y)
    for m in mk: m.set_xdata([min(max(t - 0.15, 0), 1)] * 2)
    pn.set_data(T[:i + 1], near[:i + 1]); pf.set_data(T[:i + 1], far[:i + 1])
    return []
FuncAnimation(fig, frame, frames=len(T), interval=70).save("xtalk_next_fext.gif", writer=PillowWriter(fps=14), dpi=75)
frame(60); fig.savefig("xtalk_next_fext_frame.png", dpi=75)
