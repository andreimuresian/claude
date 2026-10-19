"""Hybrid cross-section model (see modal_vs_s4p_v3.py) evaluated for 1, 5 and 14 mm."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from modal_vs_s4p_v3 import xtalk, db
f = np.linspace(0.1e9, 60e9, 600)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2), sharey=True)
for L, col in [(1e-3, "0.6"), (5e-3, "C0"), (14e-3, "C3")]:
    for i, name in enumerate(["NEXT", "FEXT"]):
        lo, hi = db(xtalk(f, L, 0.0030)[i]), db(xtalk(f, L, 0.0045)[i])
        axs[i].fill_between(f/1e9, np.minimum(lo, hi), np.maximum(lo, hi), color=col, alpha=.5, label=f"{L*1e3:.0f} mm")
for a, n in zip(axs, ["NEXT", "FEXT"]):
    a.set_title(f"{n}: cross-section model, pitch 200 µm"); a.set_xlabel("frequency (GHz)"); a.grid(alpha=.3); a.set_ylim(-100, -20)
axs[0].set_ylabel("dB"); axs[1].legend()
fig.tight_layout(); fig.savefig("predict_14mm.png", dpi=110)
for g in (10, 30, 60):
    k = np.argmin(abs(f-g*1e9)); n, fe = xtalk(f[k:k+1], 14e-3, 0.0045)
    print(g, "GHz 14mm NEXT %.1f FEXT %.1f" % (db(n)[0], db(fe)[0]))
