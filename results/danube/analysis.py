import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = [json.loads(l[7:]) for l in open("sweep.txt") if l.startswith("RESULT")]
CASES = [((0, 0.0), "1. outside of tee, standard", "#c0392b", "-"), ((1, 0.0), "2. inside of tee, standard", "#2a78d6", "-"),
         ((0, 0.7), "3. outside of tee, over-etched", "#c0392b", "--"), ((1, 0.7), "4. inside of tee, over-etched", "#2a78d6", "--")]
fig, (a, b) = plt.subplots(2, 1, figsize=(11, 8), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
S = {}
with open("danube_slab_w_sweep.csv", "w") as f:
    f.write("case,tee,overetch_um,slab_w_top_um,IL_dB_per_cm,VpiL_Vcm,neff,triangles\n")
    for (key, lab, c, ls) in CASES:
        T = sorted([r for r in R if (r["tee"], r["oe"]) == key], key=lambda r: r["slab_w"])
        w = np.array([r["slab_w"] for r in T]); il = np.array([r["IL_dBcm"] for r in T]); v = np.array([r["VpiL_Vcm"] for r in T])
        for r in T: f.write(f"{lab[0]},{r['tee']},{r['oe']},{r['slab_w']:.2f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f},{r['tri']}\n")
        a.plot(w, il, ls, marker="o", ms=2.5, c=c, label=lab); b.plot(w, v, ls, marker="o", ms=2.5, c=c, label=lab)
        i0 = int(np.argmin(abs(w - 10.15)))
        pk = [(float(w[i]), float(il[i])) for i in range(1, len(il) - 1) if il[i] > il[i-1] and il[i] >= il[i+1]]
        tr = [(float(w[i]), float(il[i])) for i in range(1, len(il) - 1) if il[i] < il[i-1] and il[i] <= il[i+1]]
        S[lab] = dict(n=len(T), IL_nominal=float(il[i0]), VpiL_nominal=float(v[i0]), IL_min=float(il.min()), IL_max=float(il.max()),
                      VpiL_range=[float(v.min()), float(v.max())], peaks=pk, troughs=tr)
a.axvline(10.15, c="k", ls=":"); a.set_ylabel("IL (dB/cm)"); a.grid(alpha=.3); a.legend(fontsize=9)
a.set_title("Danube, one arm, 1310 nm, gap 4.15 µm, 60° slab ends: IL and Vπ·L vs slab top width")
vm = np.mean([r["VpiL_Vcm"] for r in R]); b.set_ylim(vm * 0.95, vm * 1.05); b.axvline(10.15, c="k", ls=":")
b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("slab top width (µm)"); b.grid(alpha=.3)
plt.tight_layout(); plt.savefig("danube_IL_VpiL_vs_slab_w.png", dpi=130)
json.dump(S, open("summary.json", "w"), indent=1)
for k, v in S.items(): print(k, f"nom IL {v['IL_nominal']:.4f} VpiL {v['VpiL_nominal']:.4f} | IL {v['IL_min']:.4f}-{v['IL_max']:.4f} | peaks", [(a, round(b, 3)) for a, b in v["peaks"]])
