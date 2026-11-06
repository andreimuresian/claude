"""v2_box_both_wafers.png (figs_v2.py) with the median of each box written next to it -> v2_box_both_wafers_medians.png.
Same data (out_<wafer>/values_FOM.csv, 4CA0163 line 04 already excluded there), same axes; medians also printed."""
import os, csv
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
YS = {"n_m": (2.20, 2.35, 0.01), "Z0": (40.0, 45.0, 0.5)}; LAB = {"noALD": "no ALD", "ALD": "ALD"}
fig, ax = plt.subplots(1, 2, figsize=(10, 4.8))
for a, (key, col, ylab, fmt) in zip(ax, (("n_m", "n_m @ 60 GHz", "n_m at 60 GHz (fit)", "{:.4f}"),
                                         ("Z0", "Re Z0 (ohm), 10-43 GHz avg", "Re Z0 (ohm), mean 10-43 GHz", "{:.2f}"))):
    groups, labels = [], []
    for w in ("4CA0162", "4CA0163"):
        rows = list(csv.DictReader(open(os.path.join(HERE, f"out_{w}", "values_FOM.csv"))))
        for s_ in ("noALD", "ALD"):
            groups.append([float(r[col]) for r in rows if r["state"] == s_]); labels.append(f"{w}\n{LAB[s_]}")
    pos = [0, 1, 2.6, 3.6]
    a.boxplot(groups, positions=pos, widths=0.5, showfliers=False, medianprops=dict(color="k"))
    rng = np.random.default_rng(1)
    for p, g, lab in zip(pos, groups, labels):
        a.scatter(p + rng.uniform(-0.08, 0.08, len(g)), g, color="k", s=12, zorder=3)
        med = np.median(g); a.text(p + 0.28, med, fmt.format(med), va="center", ha="left", fontsize=8, color="#c0392b")
        print(f"{key:3s} {lab.replace(chr(10), ' '):18s} n={len(g):2d} median {fmt.format(med)}")
    a.set_xticks(pos); a.set_xticklabels(labels, fontsize=8.5); a.set_ylabel(ylab); a.grid(alpha=0.3, axis="y")
    lo, hi, st = YS[key]; a.set_ylim(lo, hi); a.set_yticks(np.round(np.arange(lo, hi + st / 2, st), 3)); a.set_xlim(-0.5, 4.3)
    a.set_title(ylab.split(" (")[0].split(" at")[0] + ": both wafers (medians in red)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "v2_box_both_wafers_medians.png"), dpi=150)
