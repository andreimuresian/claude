import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = [json.loads(l[7:]) for l in open("results.txt") if l.startswith("RESULT")]
for r in R: r["wl"] = 1.575
R += [json.loads(l[7:]) for l in open("wl_results.txt") if l.startswith("RESULT")]
cols = {1.525: "#2a78d6", 1.575: "#c0392b", 1.625: "#1b9e77"}
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
S = {}; rows = []
for wl in (1.525, 1.575, 1.625):
    T = sorted((r for r in R if abs(r["wl"] - wl) < 1e-9), key=lambda r: r["slab_w"])
    w = np.array([r["slab_w"] for r in T]); il = np.array([r["IL_dBcm"] for r in T]); v = np.array([r["VpiL_Vcm"] for r in T])
    rows += [(wl, r) for r in T]
    pk = [i for i in range(1, len(il) - 1) if il[i] > il[i-1] and il[i] >= il[i+1] and il[i] > 3 * np.median(il)]
    i0 = int(np.argmin(abs(w - 10.15)))
    # nearest peak / trough to nominal
    tr = [i for i in range(1, len(il) - 1) if il[i] < il[i-1] and il[i] <= il[i+1]]
    npk = min(pk, key=lambda i: abs(w[i] - 10.15)) if pk else None; ntr = min(tr, key=lambda i: abs(w[i] - 10.15)) if tr else None
    S[f"{wl*1e3:.0f}nm"] = dict(n=len(T), IL_nominal=float(il[i0]), VpiL_nominal=float(v[i0]), peaks=[[float(w[i]), float(il[i])] for i in pk],
        nearest_peak=[float(w[npk]), float(il[npk])] if npk is not None else None, nearest_trough=[float(w[ntr]), float(il[ntr])] if ntr is not None else None,
        period_um=float(np.mean(np.diff(w[pk]))) if len(pk) > 1 else None)
    a.plot(w, il, "o-", ms=2.5, c=cols[wl], label=f"{wl*1e3:.0f} nm  (nominal {il[i0]:.3f} dB/cm)")
    b.plot(w, v, "o-", ms=2.5, c=cols[wl], label=f"{wl*1e3:.0f} nm")
a.axvline(10.15, c="k", ls="--"); a.text(10.2, 1.0, "nominal 10.15 µm"); a.set_ylabel("IL (dB/cm)"); a.grid(alpha=.3); a.legend()
a.set_title("Istanbul (no buffer, gap 4.45 µm): IL ripples vs slab width at three wavelengths")
a.set_yticks(np.arange(0, a.get_ylim()[1], 0.1))
vm = np.mean([r["VpiL_Vcm"] for r in R]); b.set_ylim(vm * 0.9, vm * 1.1); b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("slab width (µm)"); b.grid(alpha=.3); b.legend(ncol=3)
plt.tight_layout(); plt.savefig("istanbul_IL_vs_slab_w_3wl.png", dpi=130)
with open("istanbul_slab_w_sweep_3wl.csv", "w") as f:
    f.write("wavelength_nm,slab_w_um,IL_dB_per_cm,VpiL_Vcm,neff\n")
    for wl, r in rows: f.write(f"{wl*1e3:.0f},{r['slab_w']:.2f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f}\n")
json.dump(S, open("summary_3wl.json", "w"), indent=1); print(json.dumps(S, indent=1))
