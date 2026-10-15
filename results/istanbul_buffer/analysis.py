import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ld = lambda f: sorted((json.loads(l[7:]) for l in open(f) if l.startswith("RESULT")), key=lambda r: (r.get("gap", 0), r["slab_w"]))
A = ld("all.txt"); S = [r for r in A if abs(r["gap"] - 3.65) < 1e-9]
G = sorted([r for r in A if abs(r["slab_w"] - 10.15) < 1e-9], key=lambda r: r["gap"]); U = ld("../istanbul/results.txt")
V0 = [r for r in U if abs(r["slab_w"] - 10.15) < 1e-6][0]["VpiL_Vcm"]
g = np.array([r["gap"] for r in G]); gv = np.array([r["VpiL_Vcm"] for r in G]); gi = np.array([r["IL_dBcm"] for r in G])
Gs = float(np.interp(V0, gv, g))
with open("gap_sweep.csv", "w") as f:
    f.write("gap_um,slab_w_um,IL_dB_per_cm,VpiL_Vcm\n")
    for r in G: f.write(f"{r['gap']:.2f},{r['slab_w']:.2f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f}\n")
with open("slab_w_sweep_gap3.65.csv", "w") as f:
    f.write("slab_w_um,IL_dB_per_cm,VpiL_Vcm,triangles\n")
    for r in S: f.write(f"{r['slab_w']:.2f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['tri']}\n")
# gap plot
fig, a = plt.subplots(figsize=(8, 4.5)); b = a.twinx()
a.plot(g, gv, "o-", c="#1f4e79"); a.axhline(V0, c="#1f4e79", ls=":"); a.axvline(Gs, c="k", ls="--")
b.plot(g, gi, "s-", c="#c0392b"); a.set_xlabel("gap on the buffer (µm)"); a.set_ylabel("Vπ·L (V·cm)", color="#1f4e79"); b.set_ylabel("IL (dB/cm)", color="#c0392b")
a.text(Gs + 0.02, gv.max() * 0.98, f"G* = {Gs:.3f} µm\n(Vπ·L = {V0:.3f}, unbuffered)"); a.set_title("Istanbul + 200 nm buffer, slab 10.15 µm: gap sweep"); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig("gap_sweep.png", dpi=130)
# slab sweep comparison
w = np.array([r["slab_w"] for r in S]); il = np.array([r["IL_dBcm"] for r in S]); v = np.array([r["VpiL_Vcm"] for r in S])
wu = np.array([r["slab_w"] for r in U]); ilu = np.array([r["IL_dBcm"] for r in U])
fig, (a, b) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
a.plot(wu, ilu, "o-", ms=3, c="#c0392b", label="Istanbul, no buffer, gap 4.45 µm")
a.plot(w, il, "o-", ms=3, c="#1b9e77", label="Istanbul + 200 nm SiO₂ buffer, gap 3.65 µm")
a.axvline(10.15, c="k", ls="--"); a.set_ylabel("IL (dB/cm)"); a.legend(); a.grid(alpha=.3)
a.set_yticks(np.arange(0, ilu.max() + 0.1, 0.1)); a.set_title("Slab-width sweep, 1575 nm (same Vπ·L at nominal)")
b.plot(w, v, "o-", ms=3, c="#1b9e77"); b.axhline(V0, c="#c0392b", ls=":", label="no buffer, nominal")
b.set_ylim(V0 * 0.95, V0 * 1.05); b.set_ylabel("Vπ·L (V·cm)"); b.set_xlabel("slab width (µm)"); b.grid(alpha=.3); b.legend()
plt.tight_layout(); plt.savefig("slab_w_sweep_buffer_vs_nobuffer.png", dpi=130)
fig, a = plt.subplots(figsize=(10, 3.8)); a.plot(w, il, "o-", ms=3, c="#1b9e77"); a.axvline(10.15, c="k", ls="--")
a.set_xlabel("slab width (µm)"); a.set_ylabel("IL (dB/cm)"); a.set_title("Istanbul + buffer, gap 3.65 µm: IL zoom"); a.grid(alpha=.3)
plt.tight_layout(); plt.savefig("slab_w_sweep_buffer_zoom.png", dpi=130)
Sm = dict(V_ref_unbuffered=V0, G_star=Gs, gap_used=3.65, n=len(S), IL_min=[float(w[il.argmin()]), float(il.min())],
          IL_max=[float(w[il.argmax()]), float(il.max())], IL_nominal=float(il[np.argmin(abs(w - 10.15))]),
          VpiL_range=[float(v.min()), float(v.max())], unbuffered_IL_range=[float(ilu.min()), float(ilu.max())])
json.dump(Sm, open("summary.json", "w"), indent=1); print(json.dumps(Sm, indent=1))
