import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 12, "axes.titleweight": "bold"})
CB, CL, CG = "#d4a017", "#1f5aa6", "#6b7280"
C = json.load(open("../cordoba_alumina/summary.json"))["sweep"]
cT = np.array([r["T_nm"] for r in C]); cIL = np.array([r["IL_dBcm"] for r in C]); cV = np.array([r["VpiL_Vcm"] for r in C])
R = [json.loads(l) for l in open("../lisbon_alumina/results.jsonl") if l.startswith("{")]
K = {(round(r["T_nm"]), r["gap"]): r for r in R if r["mesh_scale"] == 1 and r["ald_cells"] == 3}
lT = np.array(sorted(t for t, g in K if g == 3.4)); lIL = np.array([K[(t, 3.4)]["IL_dBcm"] for t in lT]); lV = np.array([K[(t, 3.4)]["VpiL_Vcm"] for t in lT])

def two(T, V, IL, col, name, fn, ilfmt="{:.2f}"):
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.3))
    a.plot(T, V, "o-", c=col, lw=2.2); b.plot(T, IL, "o-", c=col, lw=2.2)
    for ax, y, f in [(a, V, "{:.3f}"), (b, IL, ilfmt)]:
        for t in (0, 40, 100):
            i = list(T).index(t); ax.annotate(f.format(y[i]), (t, y[i]), xytext=(0, 10), textcoords="offset points", ha="center", fontsize=11, color=col, weight="bold")
        ax.axvline(40, c="0.7", ls=":"); ax.set_xlabel("Al$_2$O$_3$ thickness (nm)"); ax.grid(alpha=.3)
    a.set_ylabel("Vπ·L (V·cm)"); b.set_ylabel("Insertion loss (dB/cm)")
    a.set_title("Half-wave voltage × length"); b.set_title("Optical insertion loss")
    a.margins(y=0.15); b.margins(y=0.15)
    fig.tight_layout(); fig.savefig(fn, dpi=180); plt.close(fig)
two(cT, cV, cIL, CB, "Cordoba", "figs/cordoba_sweep.png")
two(lT, lV, lIL, CL, "Lisbon", "figs/lisbon_sweep.png", "{:.3f}")

# comparison
fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.4))
a.plot(cT, cV - cV[0], "s-", c=CB, lw=2.2, label="Cordoba (gap 4.2 µm)")
a.plot(lT, lV - lV[0], "o-", c=CL, lw=2.2, label="Lisbon buffered (gap 3.4 µm)")
a.set_ylabel("Vπ·L change vs. no Al$_2$O$_3$ (V·cm)"); a.set_title("Vπ·L reduction")
b.plot(cT, cIL / cIL[0], "s-", c=CB, lw=2.2, label="Cordoba"); b.plot(lT, lIL / lIL[0], "o-", c=CL, lw=2.2, label="Lisbon buffered")
b.set_ylabel("IL ÷ IL without Al$_2$O$_3$"); b.set_title("Relative insertion-loss increase")
for ax in (a, b): ax.set_xlabel("Al$_2$O$_3$ thickness (nm)"); ax.grid(alpha=.3); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig("figs/comparison_relative.png", dpi=180); plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 4.0))
ax.semilogy(cT, cIL, "s-", c=CB, lw=2.2, label="Cordoba (gap 4.2 µm)"); ax.semilogy(lT, lIL, "o-", c=CL, lw=2.2, label="Lisbon buffered (gap 3.4 µm)")
ax.set_xlabel("Al$_2$O$_3$ thickness (nm)"); ax.set_ylabel("Insertion loss (dB/cm, log scale)"); ax.grid(alpha=.3, which="both"); ax.legend(frameon=False)
ax.set_title("Absolute insertion loss: Lisbon stays ~15× lower at every thickness")
fig.tight_layout(); fig.savefig("figs/comparison_IL_abs.png", dpi=180); plt.close(fig)

# equal-gap test
vals = [("Cordoba\ngap 4.2 µm", cV[4] - cV[0], CB), ("Lisbon\ngap 4.2 µm", K[(40, 4.2)]["VpiL_Vcm"] - K[(0, 4.2)]["VpiL_Vcm"], CL),
        ("Lisbon\ngap 3.4 µm", lV[4] - lV[0], CL)]
fig, ax = plt.subplots(figsize=(6.2, 4.4))
bars = ax.bar([v[0] for v in vals], [v[1] for v in vals], color=[v[2] for v in vals], width=0.6)
for b_, v in zip(bars, vals): ax.text(b_.get_x() + b_.get_width() / 2, v[1] - 0.003, f"{v[1]:.3f}", ha="center", va="top", fontsize=13, weight="bold", color="k")
ax.set_ylim(-0.145, 0.005); ax.axhline(0, c="k", lw=.8); ax.set_ylabel("Vπ·L change with 40 nm Al$_2$O$_3$ (V·cm)")
ax.set_title("Same gap, different result")
fig.tight_layout(); fig.savefig("figs/equal_gap_test.png", dpi=180); plt.close(fig)
print([round(v[1], 3) for v in vals])
