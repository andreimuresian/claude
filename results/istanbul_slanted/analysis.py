import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ld = lambda f: [json.loads(l[7:]) for l in open(f) if l.startswith("RESULT")]
S = sorted([r for r in ld("results.txt") if r["alpha_slab"] == 60.0], key=lambda r: r["slab_w"])
V = sorted(ld("../istanbul/results.txt"), key=lambda r: r["slab_w"])
w = np.array([r["slab_w"] for r in S]); il = np.array([r["IL_dBcm"] for r in S]); v = np.array([r["VpiL_Vcm"] for r in S])
wv = np.array([r["slab_w"] for r in V]); ilv = np.array([r["IL_dBcm"] for r in V])
def peaks(w, il): return [(float(w[i]), float(il[i])) for i in range(1, len(il) - 1) if il[i] > il[i-1] and il[i] >= il[i+1] and il[i] > 3 * np.median(il)]
def troughs(w, il): return [(float(w[i]), float(il[i])) for i in range(1, len(il) - 1) if il[i] < il[i-1] and il[i] <= il[i+1]]
with open("istanbul_slanted_vs_vertical.csv", "w") as f:
    f.write("slab_w_top_um,IL_vertical_dB_per_cm,IL_60deg_dB_per_cm,VpiL_vertical_Vcm,VpiL_60deg_Vcm\n")
    for a, b in zip(V, S): f.write(f"{a['slab_w']:.2f},{a['IL_dBcm']:.5f},{b['IL_dBcm']:.5f},{a['VpiL_Vcm']:.4f},{b['VpiL_Vcm']:.4f}\n")
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
a.plot(wv, ilv, "o-", ms=2.5, c="#c0392b", label="vertical slab end (90°)")
a.plot(w, il, "o-", ms=2.5, c="#1f4e79", label="60° slab end (process)")
a.axvline(10.15, c="k", ls="--"); a.set_ylabel("IL (dB/cm)"); a.grid(alpha=.3); a.legend()
a.set_yticks(np.arange(0, max(il.max(), ilv.max()) + 0.1, 0.1))
a.set_title("Istanbul, gap 4.45 µm, 1575 nm: slab-end etch angle (slab width = top width)")
b.plot(wv, [r["VpiL_Vcm"] for r in V], "o-", ms=2.5, c="#c0392b"); b.plot(w, v, "o-", ms=2.5, c="#1f4e79")
b.set_ylim(v.mean() * 0.95, v.mean() * 1.05); b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("slab width at the top (µm)"); b.grid(alpha=.3)
plt.tight_layout(); plt.savefig("istanbul_slanted_vs_vertical.png", dpi=130)
i0 = int(np.argmin(abs(w - 10.15)))
Sm = dict(vertical=dict(IL_nominal=float(ilv[i0]), peaks=peaks(wv, ilv), troughs=troughs(wv, ilv)),
          slanted60=dict(IL_nominal=float(il[i0]), VpiL_nominal=float(v[i0]), peaks=peaks(w, il), troughs=troughs(w, il)))
json.dump(Sm, open("summary.json", "w"), indent=1); print(json.dumps(Sm, indent=1))
