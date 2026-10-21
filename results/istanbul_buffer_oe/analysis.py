import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = [json.loads(l[7:]) for l in open("sweep.txt") if l.startswith("RESULT")]
A = sorted([r for r in R if abs(r["L"] - 0.2) < 1e-9], key=lambda r: r["oe"])
B = sorted([r for r in R if abs(r["oe"] - 0.7) < 1e-9], key=lambda r: r["L"])
REF = dict(IL=0.01261, V=2.4237)   # buffered Istanbul, vertical slab ends, no over-etch, gap 3.65, slab 10.15
U = dict(IL=0.0917, V=2.4215)      # unbuffered Istanbul, gap 4.45 (vertical); 60 deg: 0.138
with open("overetch_sweep.csv", "w") as f:
    f.write("overetch_nm,lateral_buffer_nm,IL_dB_per_cm,VpiL_Vcm,neff\n")
    for r in A: f.write(f"{r['oe']*1e3:.0f},{r['L']*1e3:.0f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f}\n")
with open("lateral_buffer_sweep.csv", "w") as f:
    f.write("overetch_nm,lateral_buffer_nm,IL_dB_per_cm,VpiL_Vcm,neff\n")
    for r in B: f.write(f"{r['oe']*1e3:.0f},{r['L']*1e3:.0f},{r['IL_dBcm']:.5f},{r['VpiL_Vcm']:.4f},{r['neff']:.6f}\n")
fig, ax = plt.subplots(2, 2, figsize=(13, 7.5), sharex="col")
for j, (T, key, lab) in enumerate(((A, "oe", "over-etch (nm)  [lateral buffer 200 nm]"), (B, "L", "lateral buffer (nm)  [over-etch 700 nm]"))):
    x = np.array([r[key] * 1e3 for r in T]); il = np.array([r["IL_dBcm"] for r in T]); v = np.array([r["VpiL_Vcm"] for r in T])
    ax[0, j].plot(x, il, "o-", c="#1b9e77"); ax[0, j].set_ylabel("IL (dB/cm)"); ax[0, j].grid(alpha=.3)
    ax[0, j].set_ylim(0, max(0.03, il.max() * 1.3))
    ax[1, j].plot(x, v, "o-", c="#1f4e79"); ax[1, j].set_ylabel("Vπ·L (V·cm)"); ax[1, j].grid(alpha=.3); ax[1, j].set_xlabel(lab)
    ax[1, j].set_ylim(v.mean() * 0.98, v.mean() * 1.02)
    print(key, " ".join(f"{a:.0f}:{b:.5f}/{c:.4f}" for a, b, c in zip(x, il, v)))
ax[0, 0].set_title("Over-etch sweep"); ax[0, 1].set_title("Lateral buffer sweep")
fig.suptitle("Istanbul + 200 nm buffer, 60° slab ends, gap 3.65 µm, slab 10.15 µm, 1575 nm")
plt.tight_layout(); plt.savefig("istanbul_buffer_overetch_sweeps.png", dpi=130)
