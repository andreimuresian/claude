import csv, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = list(csv.DictReader(open("group_index_ALD.csv")))
fig, axs = plt.subplots(1, 3, figsize=(17, 4.8))
for ax, (d, lab, c) in zip(axs, (("cordoba", "Cordoba, 1575 nm (rib 1.4 µm)", "#e8590c"), ("cordoba_wg1.0", "Cordoba, 1575 nm (rib 1.0 µm)", "#7b3fa0"), ("jerez", "Jerez V0, 1310 nm (rib 1.0 µm)", "#1b9e77"))):
    rows = [r for r in R if r["design"] == d]; base = [r for r in rows if r["T_ALD_nm"] == "0"][0]
    for m, ls, mk, ml in (("sellmeier", "-", "o", "ALD Sellmeier (n ≈ 1.61)"), ("scaled", "--", "s", "ALD scaled to n = 1.74")):
        pts = [(0, float(base["ng_pm1nm"]))] + sorted((int(r["T_ALD_nm"]), float(r["ng_pm1nm"])) for r in rows if r["ALD_model"] == m)
        ax.plot(*zip(*pts), ls, marker=mk, ms=7, c=c, mfc="white" if m == "scaled" else c, lw=2, label=ml)
        ax.annotate(f"{pts[-1][1]-pts[0][1]:+.4f}", pts[-1], textcoords="offset points", xytext=(-8, 8 if m == "sellmeier" else -16), ha="right", fontsize=9, color=c)
    b = float(base["ng_pm1nm"]); ax.set_ylim(b - 0.007, b + 0.001)
    ax.set_title(lab); ax.set_xlabel("ALD Al₂O₃ thickness (nm)"); ax.set_ylabel("group index n_g"); ax.grid(alpha=.3); ax.legend(loc="lower left")
    ax.set_xticks([0, 40, 100])
fig.suptitle("Optical group index vs ALD thickness (central difference ±1 nm; same 0.008 y-span on all panels)")
plt.tight_layout(); plt.savefig("group_index_vs_ALD.png", dpi=140)
