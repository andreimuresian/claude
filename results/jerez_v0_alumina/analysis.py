import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = sorted({round(json.loads(l[7:])["T_nm"]): json.loads(l[7:]) for l in open("sweep.txt") if l.startswith("RESULT")}.items())
t = np.array([k for k, _ in R]); il = np.array([r["IL_dBcm"] for _, r in R]); v = np.array([r["VpiL_Vcm"] for _, r in R])
with open("jerez_v0_alumina_sweep.csv", "w") as f:
    f.write("T_ALD_nm,IL_dB_per_cm,VpiL_Vcm,neff,triangles\n")
    for k, r in R: f.write(f"{k},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f},{r['tri']}\n")
C = [l.split(",") for l in open("../cordoba_alumina/alumina_sweep.csv").read().split("\n")[1:] if l]
tc = np.array([float(c[0]) for c in C]); ilc = np.array([float(c[4]) for c in C]); vc = np.array([float(c[5]) for c in C])
fig, (a, b) = plt.subplots(1, 2, figsize=(13, 4.6))
a.plot(t, il, "o-", c="#1b9e77", label="Jerez V0, 1310 nm"); a.plot(tc, ilc, "s--", c="#c0392b", mfc="none", label="Cordoba (WG 1.4), 1575 nm")
a.set_xlabel("ALD Al₂O₃ thickness (nm)"); a.set_ylabel("IL (dB/cm)"); a.grid(alpha=.3); a.legend(); a.set_ylim(0, None)
b.plot(t, v, "o-", c="#1b9e77", label="Jerez V0, 1310 nm"); b.plot(tc, vc, "s--", c="#c0392b", mfc="none", label="Cordoba (WG 1.4), 1575 nm")
b.set_xlabel("ALD Al₂O₃ thickness (nm)"); b.set_ylabel("Vπ·L (V·cm)"); b.grid(alpha=.3); b.legend()
fig.suptitle("Jerez V0 + conformal ALD Al₂O₃ (n 1.74, ε 9.8): gap 4.15 µm, unetched slab, rib top 1.0 µm")
plt.tight_layout(); plt.savefig("jerez_v0_alumina_sweep.png", dpi=130)
for k, r in R: print(k, f"{r['IL_dBcm']:.4f}", f"{r['VpiL_Vcm']:.4f}")
