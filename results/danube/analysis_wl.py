import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = {}
for l in open("wl.txt"):
    if l.startswith("RESULT"):
        r = json.loads(l[7:]); R[(r["tee"], round(r["wl"], 3))] = r
fig, (a, b) = plt.subplots(2, 1, figsize=(9, 7), sharex=True, gridspec_kw=dict(height_ratios=[2, 1]))
with open("danube_wavelength_sweep_overetched.csv", "w") as f:
    f.write("case,wavelength_nm,IL_dB_per_cm,VpiL_Vcm,neff\n")
    for tee, lab, c, m in ((0, "outside of tee, over-etched", "#c0392b", "o"), (1, "inside of tee, over-etched", "#2a78d6", "s")):
        T = sorted([r for k, r in R.items() if k[0] == tee], key=lambda r: r["wl"])
        wl = np.array([r["wl"] * 1e3 for r in T]); il = np.array([r["IL_dBcm"] for r in T]); v = np.array([r["VpiL_Vcm"] for r in T])
        for r in T: f.write(f"{lab},{r['wl']*1e3:.0f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f}\n")
        a.plot(wl, il, "-", marker=m, mfc="none" if m == "s" else c, c=c, label=f"{lab} ({len(T)} pts)")
        b.plot(wl, v, "-", marker=m, mfc="none" if m == "s" else c, c=c)
        print(lab, len(T), " ".join(f"{x:.0f}:{y:.4f}/{z:.3f}" for x, y, z in zip(wl, il, v)))
a.set_ylabel("IL (dB/cm)"); a.grid(alpha=.3); a.legend(); a.set_title("Danube, slab 10.15 µm, over-etched 700 nm: IL vs wavelength")
b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("wavelength (nm)"); b.grid(alpha=.3)
vm = np.mean([r["VpiL_Vcm"] for r in R.values()]); b.set_ylim(vm * 0.95, vm * 1.05)
plt.tight_layout(); plt.savefig("danube_IL_vs_wavelength_overetched.png", dpi=130)
