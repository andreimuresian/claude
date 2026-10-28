import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = [json.loads(l[7:]) for l in open("sweep.txt") if l.startswith("RESULT")]
H = np.round(np.arange(0.5, 1.401, 0.1), 2); W = np.round(np.arange(2.0, 2.901, 0.1), 2)
with open("cap_sweep.csv", "w") as f:
    f.write("wg_top_um,cap_h_um,cap_w_um,neff,IL_dB_per_cm,VpiL_Vcm\n")
    for r in sorted(R, key=lambda r: (r["wg_top"], r["cap_h"], r["cap_w"])):
        f.write(f"{r['wg_top']},{r['cap_h']},{r['cap_w']},{r['neff']:.6f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f}\n")
grid = {}
for wg in (1.0, 1.4):
    for k in ("IL_dBcm", "VpiL_Vcm"):
        M = np.full((len(H), len(W)), np.nan)
        for r in R:
            if r["wg_top"] == wg: M[list(H).index(round(r["cap_h"], 2)), list(W).index(round(r["cap_w"], 2))] = r[k]
        grid[(wg, k)] = M
fig, axs = plt.subplots(2, 2, figsize=(13, 10))
for i, wg in enumerate((1.0, 1.4)):
    for j, (k, lab, cm, fmt) in enumerate((("VpiL_Vcm", "Vπ·L (V·cm)", "viridis", "{:.3f}"), ("IL_dBcm", "IL (dB/cm)", "magma", "{:.4f}"))):
        M = grid[(wg, k)]; ax = axs[i, j]
        im = ax.imshow(M, origin="lower", cmap=cm, aspect="auto", extent=(1.95, 2.95, 0.45, 1.45))
        for a, h in enumerate(H):
            for b, w in enumerate(W):
                v = M[a, b]; ax.text(w, h, fmt.format(v)[1:] if k == "IL_dBcm" else fmt.format(v), ha="center", va="center", fontsize=6.5,
                                     color="white" if v < np.nanmean(M) else "black")
        plt.colorbar(im, ax=ax, label=lab); ax.set_xticks(W); ax.set_yticks(H)
        ax.set_xlabel("cap width (µm)"); ax.set_ylabel("cap height (µm, from the buffer top)")
        ax.set_title(f"rib {wg} µm: {lab}  [{np.nanmin(M):.4g} – {np.nanmax(M):.4g}]")
fig.suptitle("Lisbon lifted + 200 nm SiO₂ buffer, gap 3.4 µm, 1575 nm: SiO₂ cap sweep")
plt.tight_layout(); plt.savefig("cap_sweep_maps.png", dpi=120); plt.close()
fig, axs = plt.subplots(2, 2, figsize=(13, 8))
for i, wg in enumerate((1.0, 1.4)):
    for j, (k, lab) in enumerate((("VpiL_Vcm", "Vπ·L (V·cm)"), ("IL_dBcm", "IL (dB/cm)"))):
        M = grid[(wg, k)]; ax = axs[i, j]; cs = plt.cm.viridis(np.linspace(0, 0.9, len(W)))
        for b, w in enumerate(W): ax.plot(H, M[:, b], "o-", ms=3, c=cs[b], label=f"cap_w {w}")
        ax.set_xlabel("cap height (µm)"); ax.set_ylabel(lab); ax.set_title(f"rib {wg} µm"); ax.grid(alpha=.3)
        if i == 0 and j == 0: ax.legend(fontsize=7, ncol=2)
plt.tight_layout(); plt.savefig("cap_sweep_lines.png", dpi=120); plt.close()
for wg in (1.0, 1.4):
    V, I = grid[(wg, "VpiL_Vcm")], grid[(wg, "IL_dBcm")]
    print(f"rib {wg}: VpiL {np.nanmin(V):.4f}-{np.nanmax(V):.4f}  IL {np.nanmin(I):.4f}-{np.nanmax(I):.4f}")
    print("   ref (1.4,2.0):", V[-1, 0], I[-1, 0], "| (0.5,2.0):", V[0, 0], I[0, 0], "| (1.4,2.9):", V[-1, -1], I[-1, -1], "| (0.5,2.9):", V[0, -1], I[0, -1])
