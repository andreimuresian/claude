import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = sorted((json.loads(l[7:]) for l in open("results.txt") if l.startswith("RESULT")), key=lambda r: r["slab_w"])
w = np.array([r["slab_w"] for r in R]); il = np.array([r["IL_dBcm"] for r in R]); v = np.array([r["VpiL_Vcm"] for r in R])
GAP = 4.45
with open("istanbul_slab_w_sweep.csv", "w") as f:
    f.write("slab_w_um,slab_w_minus_gap_um,slab_under_gold_per_side_um,IL_dB_per_cm,VpiL_Vcm,triangles\n")
    for r in R: f.write(f"{r['slab_w']:.2f},{r['slab_w']-GAP:.2f},{(r['slab_w']-GAP)/2:.3f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['tri']}\n")
# ripple period from FFT of detrended IL
d = il - np.polyval(np.polyfit(w, il, 2), w)
F = np.abs(np.fft.rfft(d, 1024)); fr = np.fft.rfftfreq(1024, 0.1); P = 1 / fr[1:][np.argmax(F[1:])]
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
a.plot(w, il, "o-", ms=3, c="#c0392b"); a.axvline(10.15, c="k", ls="--"); a.text(10.2, il.max()*0.95, "Istanbul nominal\n10.15 µm")
a.set_ylabel("IL (dB/cm)"); a.set_yticks(np.arange(0, il.max() + 0.1, 0.1)); a.set_title(f"Istanbul, gap 4.45 µm, 1575 nm: IL vs slab width (ripple period ≈ {P:.2f} µm)"); a.grid(alpha=.3)
b.plot(w, v, "o-", ms=3, c="#1f4e79"); b.axvline(10.15, c="k", ls="--"); b.set_ylim(v.mean()*0.95, v.mean()*1.05); b.text(0.02, 0.85, f"Vπ·L = {v.mean():.3f} V·cm, flat within ±{(v.max()-v.min())/2/v.mean()*100:.2f} % (axis ±5 %)", transform=b.transAxes); b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("slab width (µm)"); b.grid(alpha=.3)
sec = a.secondary_xaxis("top", functions=(lambda x: x - GAP, lambda x: x + GAP)); sec.set_xlabel("slab width − gap (µm)")
plt.tight_layout(); plt.savefig("istanbul_IL_VpiL_vs_slab_w.png", dpi=130)
i0 = np.argmin(abs(w - 10.15))
S = dict(n=len(R), nominal=R[i0], IL_min=[float(w[il.argmin()]), float(il.min())], IL_max=[float(w[il.argmax()]), float(il.max())],
         IL_max_over_min_beyond_8um=float(il[w>=8].max()/il[w>=8].min()), ripple_period_um=float(P), VpiL_range=[float(v.min()), float(v.max())])
json.dump(S, open("summary.json", "w"), indent=1); print(json.dumps(S, indent=1))
