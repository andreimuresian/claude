"""Run (d) simulated EO crosstalk vs the measured curve MZ3toMZ4 (module K00626, extracted from the lab plot)."""
import os
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
s = np.loadtxt(os.path.join(HERE, "xtalk_run_d.csv"), delimiter=",", skiprows=1)
m = np.loadtxt(os.path.join(HERE, "lab_MZ3toMZ4_extracted.csv"), delimiter=",", skiprows=2)
m = m[np.argsort(m[:, 0])]
fs, eo = s[:, 0], s[:, 3]
def period(f, y, lo=5, hi=60, df=0.1):
    g = np.arange(lo, hi, df); v = np.interp(g, f, y); v -= v.mean()
    sp = np.abs(np.fft.rfft(v * np.hanning(len(v)))); fr = np.fft.rfftfreq(len(v), df)
    k = (fr > 1 / 15) & (fr < 1 / 2); return 1 / fr[k][np.argmax(sp[k])]
km, ks = (m[:, 0] >= 5) & (m[:, 0] <= 60), (fs >= 5)
g = np.arange(5, 60.01, 0.5); mi = np.interp(g, m[:, 0], m[:, 1])  # uniform grid: digitized points are unevenly spaced
print(f"median 5-60 GHz: measured {np.median(mi):.1f} dB (uniform grid), simulated {np.median(eo[ks]):.1f} dB")
print(f"max 5-60 GHz: measured {mi.max():.1f} dB, simulated {eo[ks].max():.1f} dB")
print(f"ripple period 5-60 GHz: measured {period(*m.T):.1f} GHz, simulated {period(fs, eo):.1f} GHz")
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(fs, eo, "o-", color="#7a4bd1", ms=3, lw=1.3, label="simulated, run (d) full module (gap fields)")
ax.plot(m[:, 0], m[:, 1], "s-", color="#eb6834", ms=3, lw=1.3, label="measured MZ3toMZ4, module K00626 (digitized)")
ax.plot([0, 60, 60, 62], [-30, -30, -22, -22], color="0.3", lw=1, ls="--", label="spec")
ax.set_xlim(0, 62); ax.set_ylim(-50, -10); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk (dB)"); ax.grid(alpha=0.3)
ax.set_title("Istanbul: EO crosstalk, simulation (run d) vs measurement", fontsize=9.5)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "sim_vs_lab.png"), dpi=150)
