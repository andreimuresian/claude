"""Compare femwell Al2O3 sweep with COMSOL (values read off the user's plots)."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = [json.loads(l) for l in open("results.jsonl") if l.strip()]
nom = sorted([r for r in R if r["mesh_scale"] == 1.0 and r["ald_cells"] == 3.0], key=lambda r: r["T_nm"])
T = np.array([r["T_nm"] for r in nom]); IL = np.array([r["IL_dBcm"] for r in nom]); V = np.array([r["VpiL_Vcm"] for r in nom])
cT = np.array([0, 20, 30, 40, 50, 60, 70, 80, 90, 100])
cV = np.array([2.134, 2.102, 2.086, 2.071, 2.057, 2.043, 2.029, 2.016, 2.003, 1.991])
cIL = np.array([0.55, 0.83, 0.98, 1.16, 1.35, 1.55, 1.77, 2.01, 2.24, 2.47])
import csv
with open("alumina_sweep.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["T_nm", "tri", "neff", "im_neff", "IL_dBcm", "VpiL_Vcm", "Gamma", "COMSOL_IL", "COMSOL_VpiL"])
    for r in nom:
        i = np.where(cT == r["T_nm"])[0]
        w.writerow([r["T_nm"], r["tri"], f'{r["neff"]:.6f}', f'{r["im_neff"]:.4e}', f'{r["IL_dBcm"]:.4f}', f'{r["VpiL_Vcm"]:.4f}',
                    f'{r["Gamma"]:.4f}', cIL[i[0]] if len(i) else "", cV[i[0]] if len(i) else ""])
C1, C2 = "#1f5aa6", "#c2410c"
fig, axs = plt.subplots(2, 2, figsize=(13, 8.2))
a = axs[0, 0]; a.plot(T, V, "o-", c=C1, label="femwell (this work)"); a.plot(cT, cV, "s--", c=C2, label="COMSOL")
a.set_ylabel("Vπ·L (V·cm)"); a.set_title("Vπ·L vs Al$_2$O$_3$ thickness")
a = axs[0, 1]; a.plot(T, IL, "o-", c=C1, label="femwell (this work)"); a.plot(cT, cIL, "s--", c=C2, label="COMSOL")
a.set_ylabel("IL (dB/cm)"); a.set_title("Optical attenuation vs Al$_2$O$_3$ thickness")
cm = np.isin(T, cT); ci = np.isin(cT, T)
a = axs[1, 0]
a.plot(T, V - V[0], "o-", c=C1, label="femwell"); a.plot(cT, cV - cV[0], "s--", c=C2, label="COMSOL")
a.set_ylabel("ΔVπ·L from bare (V·cm)"); a.set_title("Change relative to t = 0 (removes the baseline offset)")
a = axs[1, 1]
a.plot(T, IL / IL[0], "o-", c=C1, label="femwell"); a.plot(cT, cIL / cIL[0], "s--", c=C2, label="COMSOL")
a.set_ylabel("IL / IL(t=0)"); a.set_title("Relative IL increase")
for a in axs.flat:
    a.set_xlabel("Al$_2$O$_3$ thickness (nm)"); a.grid(alpha=.3); a.legend(frameon=False)
fig.suptitle("Cordoba, WG_TOP 1.4 µm, gap 4.2 µm, unetched slab, 1575 nm — femwell vs COMSOL", weight="bold")
fig.tight_layout(); fig.savefig("alumina_vs_comsol.png", dpi=170)
# mesh convergence
M = [r for r in R if abs(r["T_nm"] - 40) < 1e-6] + [r for r in R if r["T_nm"] == 0]
print("mesh study:")
for r in sorted(M, key=lambda r: (r["T_nm"], r["mesh_scale"], r["ald_cells"])):
    print(f'  T {r["T_nm"]:5.1f}  scale {r["mesh_scale"]:.1f}  cells {r["ald_cells"]:.0f}  tri {r["tri"]:7d}  IL {r["IL_dBcm"]:.4f}  VpiL {r["VpiL_Vcm"]:.4f}')
json.dump(dict(sweep=nom, mesh=M), open("summary.json", "w"), indent=1)
for r in nom:
    print(f'{r["T_nm"]:5.0f} nm  IL {r["IL_dBcm"]:.4f}  VpiL {r["VpiL_Vcm"]:.4f}  Gamma {r["Gamma"]:.4f}')
