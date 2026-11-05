"""Per-line change ALD - noALD of each figure of merit, both wafers side by side: 4CA0162 (15 lines), 4CA0162 without
the high-loss lines 00 and 04 (13), 4CA0163 (14; line 04 excluded as a bad ALD measurement). Inputs: out_<wafer>/
values_FOM.csv. Output: compare_wafers.png, compare_wafers.csv."""
import os, csv
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
HERE = os.path.dirname(os.path.abspath(__file__))
def load(w):
    rows = list(csv.DictReader(open(os.path.join(HERE, f"out_{w}", "values_FOM.csv"))))
    foms = [k for k in rows[0] if k not in ("line", "state")]
    V = {(r["state"], r["line"]): {k: float(r[k]) for k in foms} for r in rows}
    return V, foms
V2, FOM = load("4CA0162"); V3, _ = load("4CA0163")
def deltas(V, excl=()):
    ls = sorted({l for (s, l) in V if s == "noALD" and l not in excl})
    return {q: np.array([V[("ALD", l)][q] - V[("noALD", l)][q] for l in ls]) for q in FOM}
G = [("4CA0162\nall 15", deltas(V2), "#eb6834"), ("4CA0162\nw/o 00, 04", deltas(V2, ("00", "04")), "#f2a07a"),
     ("4CA0163\n14 lines", deltas(V3), "#2a78d6")]
UNIT = {"n_m @ 60 GHz": "", "Re Z0 (ohm), 10-43 GHz avg": " (ohm)", "alpha (dB/cm) @ 30 GHz": " (dB/cm)",
        "alpha (dB/cm) @ 60 GHz": " (dB/cm)", "|S21| (dB) @ 30 GHz": " (dB)", "|S21| (dB) @ 60 GHz": " (dB)"}
fig, ax = plt.subplots(2, 3, figsize=(14, 8)); ax = ax.ravel(); rng = np.random.default_rng(0)
with open(os.path.join(HERE, "compare_wafers.csv"), "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["FOM", "group", "n", "median_change", "q1", "q3", "lines_up"])
    for a, q in zip(ax, FOM):
        for i, (lab, D, c) in enumerate(G):
            d = D[q]
            a.boxplot([d], positions=[i], widths=0.5, showfliers=False, medianprops=dict(color="k"))
            a.scatter(i + rng.uniform(-0.12, 0.12, len(d)), d, color=c, s=16, zorder=3, edgecolor="white", linewidth=0.4)
            q1, q3 = np.percentile(d, [25, 75])
            w.writerow([q, lab.replace("\n", " "), len(d), f"{np.median(d):.5g}", f"{q1:.5g}", f"{q3:.5g}", int(np.sum(d > 0))])
        a.axhline(0, color="0.4", lw=0.8); a.set_xticks(range(3)); a.set_xticklabels([g[0] for g in G], fontsize=8.5)
        a.set_title("change " + q.replace(" (ohm)", "").replace(" (dB/cm)", "").replace(" (dB)", "") + UNIT[q], fontsize=10.5)
        a.grid(alpha=0.3, axis="y")
fig.suptitle("Per-line change after 40 nm Al2O3 (ALD - no ALD), both wafers", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "compare_wafers.png"), dpi=150)
