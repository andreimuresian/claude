import csv, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = list(csv.DictReader(open("cap_sweep.csv")))
H = ["0.5", "0.8", "1.1", "1.4"]; cols = plt.cm.viridis(np.linspace(0.05, 0.85, len(H)))
fig, axs = plt.subplots(1, 2, figsize=(14, 5.4))
for ax, (k, lab) in zip(axs, (("VpiL_Vcm", "Vπ·L (V·cm)"), ("IL_dB_per_cm", "IL (dB/cm)"))):
    for wg, ls, mk in (("1.0", "-", "o"), ("1.4", "--", "s")):
        for h, c in zip(H, cols):
            p = sorted((float(r["cap_w_um"]), float(r[k])) for r in R if r["wg_top_um"] == wg and r["cap_h_um"] == h)
            ax.plot(*zip(*p), ls, marker=mk, ms=4, c=c, mfc=c if wg == "1.0" else "white", label=f"rib {wg} µm, cap h {h} µm")
    ax.set_xlabel("cap width (µm)"); ax.set_ylabel(lab); ax.grid(alpha=.3); ax.set_title(lab + ": both rib widths on one scale")
axs[0].legend(fontsize=8, ncol=2)
fig.suptitle("Lisbon lifted + 200 nm buffer, gap 3.4 µm, 1575 nm — solid/filled: rib 1.0 µm, dashed/open: rib 1.4 µm; colour = cap height")
plt.tight_layout(); plt.savefig("cap_sweep_merged_lines.png", dpi=130); plt.close()
# maps with one shared colour scale per quantity
Hs = np.round(np.arange(0.5, 1.401, 0.1), 2); Ws = np.round(np.arange(2.0, 2.901, 0.1), 2)
fig, axs = plt.subplots(2, 2, figsize=(13, 10))
for j, (k, lab, cm, fmt) in enumerate((("VpiL_Vcm", "Vπ·L (V·cm)", "viridis", "{:.3f}"), ("IL_dB_per_cm", "IL (dB/cm)", "magma", "{:.4f}"))):
    Ms = {}
    for wg in ("1.0", "1.4"):
        M = np.zeros((len(Hs), len(Ws)))
        for r in R:
            if r["wg_top_um"] == wg: M[list(Hs).index(float(r["cap_h_um"])), list(Ws).index(float(r["cap_w_um"]))] = float(r[k])
        Ms[wg] = M
    lo, hi = min(M.min() for M in Ms.values()), max(M.max() for M in Ms.values())
    for i, wg in enumerate(("1.0", "1.4")):
        ax = axs[i, j]; M = Ms[wg]
        im = ax.imshow(M, origin="lower", cmap=cm, vmin=lo, vmax=hi, aspect="auto", extent=(1.95, 2.95, 0.45, 1.45))
        for a, h in enumerate(Hs):
            for b, w in enumerate(Ws):
                val = M[a, b]; ax.text(w, h, fmt.format(val)[1:] if k == "IL_dB_per_cm" else fmt.format(val), ha="center", va="center",
                                       fontsize=6.5, color="white" if val < (lo + hi) / 2 else "black")
        plt.colorbar(im, ax=ax, label=lab); ax.set_xticks(Ws); ax.set_yticks(Hs)
        ax.set_xlabel("cap width (µm)"); ax.set_ylabel("cap height (µm)"); ax.set_title(f"rib {wg} µm: {lab}")
fig.suptitle("Cap sweep maps with ONE colour scale per quantity (rib 1.0 vs 1.4 directly comparable)")
plt.tight_layout(); plt.savefig("cap_sweep_maps_shared_scale.png", dpi=120); print("ok")
