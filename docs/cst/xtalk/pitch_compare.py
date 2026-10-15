"""1 mm coupled pair at three channel pitches (200, 400, 625 um).
Solid: crosstalk. Dotted: |S21 - S43|, the line A / line B mismatch, which
should be zero by symmetry and so marks the numerical error floor."""
import numpy as np, matplotlib.pyplot as plt
from first_look_lib import load4
db = lambda x: 20*np.log10(abs(x) + 1e-30)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.4), sharey=True)
for p, col in [(200, "k"), (400, "C0"), (625, "C3")]:
    f, S = load4(f"LINEA0_1MM_{p}UM_PITCH.s4p"); G = f/1e9
    for a, (r, t) in zip(ax, [(2, "NEXT S31"), (3, "FEXT S41")]):
        a.plot(G, db(S[:, r, 0]), color=col, lw=1.8, label=f"{p} um pitch")
        a.plot(G, db(S[:, 1, 0] - S[:, 3, 2]), color=col, lw=1, ls=":", label=f"{p} um: |S21-S43| (error floor)")
for a, t in zip(ax, ["NEXT S31", "FEXT S41"]):
    a.axvline(36, color="0.5", lw=1, ls="--")
    a.text(36.5, -135, "Si slab TE0 index = 2\n(about 36 GHz)", fontsize=8, color="0.4")
    a.set_title(t + ", 1 mm"); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=.3)
ax[0].set_ylabel("dB"); ax[0].set_ylim(-140, -40); ax[1].legend(fontsize=7, loc="lower right")
plt.tight_layout(); plt.savefig("pitch_compare.png", dpi=130)
