"""|S11| and |S21| of the four ALD wafers: chip average and Savitzky-Golay smoothed chip average, no ALD and ALD.
Raw average: arithmetic mean over chips of |S| in dB at each frequency (no smoothing).
Smoothed: scipy.signal.savgol_filter on that average, window WIN points, polynomial order ORD.
Chips excluded as in the wafer analyses (4CA0163 chip 04).
Outputs (this folder): S11_<wafer>.png, S21_<wafer>.png, smoothing_example.png, smoothing_stats.csv"""
import os, glob, re, csv
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(HERE, "..")
WAF = [("CORDOBA", "4CA0162", "ald_cordoba8mm", 8), ("CORDOBA", "4CA0163", "ald_cordoba8mm", 8),
       ("JEREZ", "6JZ0011", "jerez", 8), ("HELSINKI", "5HK0005", "helsinki", 13)]
EXCL = {"4CA0163": ["04"]}; WIN, ORD = 21, 3
COL = {"noALD": "#2a78d6", "ALD": "#eb6834"}; LAB = {"noALD": "no ALD", "ALD": "ALD"}
YMIN = {"S11": -32.5, "S21": -7.0}
def load(fo, w):
    d = {s: {"S11": [], "S21": []} for s in COL}
    for fn in sorted(glob.glob(os.path.join(M, fo, "raw", w, f"{w}_*_*.s2p"))):
        s, nn = re.search(r"_(noALD|ALD)_(\d{2})\.s2p$", fn).groups()
        if nn in EXCL.get(w, []): continue
        n = rf.Network(fn); f = n.f / 1e9
        d[s]["S11"].append(20 * np.log10(abs(n.s[:, 0, 0]))); d[s]["S21"].append(20 * np.log10(abs(n.s[:, 1, 0])))
    return f, d
stats = []
for name, w, fo, L in WAF:
    f, d = load(fo, w); df = f[1] - f[0]
    for q in ("S11", "S21"):
        fig, ax = plt.subplots(figsize=(6.4, 5.3))
        for s in COL:
            n = len(d[s][q]); avg = np.mean(d[s][q], 0); sm = savgol_filter(avg, WIN, ORD)
            ax.plot(f, avg, color=COL[s], lw=0.7, alpha=0.45, label=f"{LAB[s]}: raw average ({n} chips)")
            ax.plot(f, sm, color=COL[s], lw=2.0, label=f"{LAB[s]}: Savitzky–Golay smoothed")
            for lo, hi in ((1, 20), (20, 40), (40, 60)):
                k = (f >= lo) & (f < hi)
                stats.append([w, q, s, n, f"{lo}-{hi}", round(float(np.sqrt(np.mean((avg[k] - sm[k]) ** 2))), 3)])
        ax.set_xlim(0, 60); ax.set_ylim(YMIN[q], 0); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(f"|{q}| (dB)")
        ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8.5, ncol=1 if q == "S21" else 2,
                  loc="upper center" if (w, q) == ("6JZ0011", "S11") else "lower left")   # JEREZ S11 nulls reach the axis floor (user)
        ax.set_title(f"{name} {w} ({L} mm): |{q}|\nSavitzky–Golay {WIN} points ({WIN * df:.2f} GHz), order {ORD}", fontsize=10)
        fig.tight_layout(); fig.savefig(os.path.join(HERE, f"{q}_{w}.png"), dpi=200); plt.close(fig)
    print(w, "done", "df =", round(df * 1e3, 3), "MHz")
    if w == "5HK0005": ex = (f, np.mean(d["noALD"]["S11"], 0), df)
with open(os.path.join(HERE, "smoothing_stats.csv"), "w", newline="") as fh:
    c = csv.writer(fh); c.writerow(["wafer", "S", "state", "chips", "band_GHz", "rms_raw_minus_smoothed_dB"]); c.writerows(stats)
# illustration of the filter on a zoom of the HELSINKI no-ALD S11 average
f, y, df = ex; sm = savgol_filter(y, WIN, ORD); k = (f > 44) & (f < 50); i0 = np.argmin(abs(f - 47.0)); h = WIN // 2
fig, ax = plt.subplots(figsize=(8, 4.2))
ax.plot(f[k], y[k], "o", ms=2.5, color="#2a78d6", alpha=0.55, label="raw average (one point every 37.5 MHz)")
ax.plot(f[k], sm[k], color="#0E2268", lw=2, label="smoothed curve")
x = f[i0 - h:i0 + h + 1]; p = np.polyfit(x - f[i0], y[i0 - h:i0 + h + 1], ORD)
ax.axvspan(x[0], x[-1], color="#eb6834", alpha=0.12, label=f"window: {WIN} points ({WIN * df:.2f} GHz)")
ax.plot(x, np.polyval(p, x - f[i0]), color="#eb6834", lw=2, ls="--", label=f"least-squares polynomial, order {ORD}")
ax.plot(f[i0], np.polyval(p, 0), "s", color="#eb6834", ms=8, label="value kept at the window centre")
ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("|S11| (dB)"); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8.5, loc="lower left")
ax.set_title("Savitzky–Golay filter: HELSINKI 5HK0005, |S11| average, no ALD (zoom 44–50 GHz)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "smoothing_example.png"), dpi=200); plt.close(fig)
