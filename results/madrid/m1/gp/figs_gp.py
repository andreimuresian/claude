"""Figures for deck slides 5-8 (dataset, optimum/Pareto/sensitivity, validation)."""
import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from gp_build import load
plt.rcParams.update({"font.size": 11})
R, X, IL, V = load()
# F5 dataset
f, ax = plt.subplots(1, 2, figsize=(12, 4.4))
sc = ax[0].scatter(IL, V, c=X[:, 0], cmap="viridis", s=22, edgecolors="k", linewidths=.3); ax[0].set_xscale("log")
ax[0].axvline(0.4, c="r", ls="--", lw=1); ax[0].set_xlabel("IL (dB/cm)"); ax[0].set_ylabel("Vπ·L (V·cm)"); plt.colorbar(sc, ax=ax[0], label="GAP (µm)")
ax[0].set_title(f"{len(R)} FEM points (32 corners + LHS), 1625 nm", fontsize=10.5); ax[0].grid(alpha=.3, which="both")
U = (X - X.min(0)) / (X.max(0) - X.min(0)); names = ["GAP", "BUFFER", "CAP_F", "CAP_H", "MTX_s"]
for i in range(5): ax[1].scatter(np.full(len(U), i) + np.random.default_rng(i).uniform(-.18, .18, len(U)), U[:, i], s=9, alpha=.7)
ax[1].set_xticks(range(5)); ax[1].set_xticklabels(names); ax[1].set_ylabel("normalised value"); ax[1].set_title("Coverage of each parameter range", fontsize=10.5)
f.tight_layout(); f.savefig("F5_dataset.png", dpi=170); plt.close()
# F7 optimum
O = json.load(open("optimum_IL0.4_buf0.1.json")); pf = O["pareto"]
f, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
ax[0].scatter(IL, V, s=10, c="#bbb", label="FEM dataset"); ax[0].plot([p["IL"] for p in pf], [p["VpiL"] for p in pf], "-", c="#1f4e79", lw=2, label="surrogate Pareto front")
t = O["top"][0]; ax[0].plot(t["IL"], t["VpiL"], "*", c="#c0392b", ms=15, label="optimum (IL+2σ ≤ 0.4)")
ax[0].plot(0.2615, 1.8268, "s", c="k", ms=7, label="baseline (FEM)")
ax[0].set_xscale("log"); ax[0].axvline(0.4, c="r", ls="--", lw=1); ax[0].set_xlim(0.01, 3); ax[0].set_xlabel("IL (dB/cm)"); ax[0].set_ylabel("Vπ·L (V·cm)"); ax[0].legend(fontsize=8.5); ax[0].grid(alpha=.3, which="both")
ax[0].set_title("Vπ·L–IL trade-off, buffer ≥ 100 nm on the front", fontsize=10.5)
S = O["sensitivity"]; lab = {"GAP": "GAP", "BUFFER_H": "BUFFER_H", "CAP_F": "CAP_F (0 = fills gap)", "CAP_H": "CAP_H", "MTX_SMALL": "MTX_small"}
for k, s in S.items():
    x = np.array(s["x"]); z = (x - x.min()) / (x.max() - x.min()); ax[1].plot(z, np.array(s["VpiL"]) - t["VpiL"], lw=2, label=lab[k])
ax[1].axhline(0, c="k", lw=.6); ax[1].set_xlabel("parameter, normalised to its range"); ax[1].set_ylabel("ΔVπ·L from optimum (V·cm)"); ax[1].legend(fontsize=8.5); ax[1].grid(alpha=.3)
ax[1].set_title("One-at-a-time sensitivity around the optimum", fontsize=10.5)
f.tight_layout(); f.savefig("F7_optimum.png", dpi=170); plt.close()
print("figs ok")
