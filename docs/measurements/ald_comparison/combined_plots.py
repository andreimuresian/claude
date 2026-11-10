"""All designs on one graph: n_m and Z0 boxplots (CORDOBA axes, medians in red), mean measured |S11| and |S21|.
Inputs: values_FOM.csv and raw/<wafer>/*.s2p of each study (4CA0163 chip 04 excluded, as in the analysis).
Outputs: combined_box_n_m.png, combined_box_Z0.png, combined_S11.png, combined_S21.png"""
import os, csv, glob, re
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__)); M = os.path.join(HERE, "..")
WAF = [("CORDOBA", "4CA0162", "ald_cordoba8mm", 8, "#0E2268"), ("CORDOBA", "4CA0163", "ald_cordoba8mm", 8, "#5A7BD8"),
       ("JEREZ", "6JZ0011", "jerez", 8, "#1BAA7D"), ("HELSINKI", "5HK0005", "helsinki", 13, "#EB6834")]
EXCL = {"4CA0163": ["04"]}; LAB = {"noALD": "no ALD", "ALD": "ALD"}
YS = {"n_m": (2.20, 2.35, 0.01, "{:.4f}", "n_m at 60 GHz (fit)"), "Z0": (40.0, 45.0, 0.5, "{:.2f}", "Re Z0 (ohm), band average")}

for key in ("n_m", "Z0"):
    lo, hi, st, fmt, ylab = YS[key]
    groups, labels, pos = [], [], []
    for k, (d, w, fo, L, c) in enumerate(WAF):
        rows = list(csv.DictReader(open(os.path.join(M, fo, f"out_{w}", "values_FOM.csv"))))
        col = next(x for x in rows[0] if (x.startswith("n_m") if key == "n_m" else x.startswith("Re Z0")))
        for i, s in enumerate(("noALD", "ALD")):
            groups.append([float(r[col]) for r in rows if r["state"] == s]); labels.append(f"{d}\n{w}\n{LAB[s]}"); pos.append(k * 2.6 + i)
    fig, ax = plt.subplots(figsize=(12, 5.2))
    ax.boxplot(groups, positions=pos, widths=0.5, showfliers=False, medianprops=dict(color="k"))
    rng = np.random.default_rng(1)
    for p, g_ in zip(pos, groups):
        ax.scatter(p + rng.uniform(-0.08, 0.08, len(g_)), g_, color="k", s=12, zorder=3)
        ax.text(p + 0.28, np.median(g_), fmt.format(np.median(g_)), va="center", ha="left", fontsize=8, color="#c0392b")
    ax.set_xticks(pos); ax.set_xticklabels(labels, fontsize=8.5); ax.set_ylabel(ylab); ax.grid(alpha=0.3, axis="y")
    ax.set_ylim(lo, hi); ax.set_yticks(np.round(np.arange(lo, hi + st / 2, st), 3)); ax.set_xlim(-0.5, pos[-1] + 0.9)
    ax.set_title(f"{ylab.split(' (')[0].split(' at')[0]}: all designs, before and after ALD (medians in red)", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, f"combined_box_{key}.png"), dpi=150); plt.close(fig)

for q, idx, ylim in (("S11", (0, 0), (-32.5, 0)), ("S21", (1, 0), (-7, 0))):
    fig, ax = plt.subplots(figsize=(11, 6.2))
    for d, w, fo, L, c in WAF:
        for s, ls in (("noALD", "-"), ("ALD", "--")):
            ys = []
            for fn in sorted(glob.glob(os.path.join(M, fo, "raw", w, f"{w}_{s}_*.s2p"))):
                if re.search(r"_(\d{2})\.s2p$", fn).group(1) in EXCL.get(w, []): continue
                n = rf.Network(fn); ys.append(20 * np.log10(abs(n.s[:, idx[0], idx[1]]))); f = n.f / 1e9
            ax.plot(f, np.mean(ys, 0), ls, color=c, lw=1.1, label=f"{d} {w} ({L} mm), {LAB[s]}, mean of {len(ys)}")
    ax.set_xlim(0, 60); ax.set_ylim(*ylim); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(f"|{q}| (dB)"); ax.grid(alpha=0.3)
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.12)); ax.set_title(f"|{q}|, measured, mean over chips: all designs, before (solid) and after (dashed) ALD", fontsize=11)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, f"combined_{q}.png"), dpi=150); plt.close(fig)
print("done")
