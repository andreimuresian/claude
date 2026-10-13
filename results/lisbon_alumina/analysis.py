"""Lisbon lifted + buffer + ALD Al2O3: thickness sweep, gap relaxation, +-10 nm tolerance."""
import json, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "font.size": 10.5})
R = [json.loads(l) for l in open("results.jsonl") if l.startswith("{")]
nom = [r for r in R if r["mesh_scale"] == 1.0 and r["ald_cells"] == 3.0]
key = {(round(r["T_nm"]), round(r["gap"], 2)): r for r in nom}
C = json.load(open("../cordoba_alumina/summary.json"))["sweep"]
cT = np.array([r["T_nm"] for r in C]); cIL = np.array([r["IL_dBcm"] for r in C]); cV = np.array([r["VpiL_Vcm"] for r in C])
COL = {0: "#6b7280", 30: "#0f766e", 40: "#1f5aa6", 50: "#c2410c"}
N = {}
with open("lisbon_alumina_all.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["T_nm", "gap_bot_um", "mesh_scale", "ald_cells", "tri", "neff", "im_neff", "IL_dBcm", "VpiL_Vcm", "Gamma"])
    for r in sorted(R, key=lambda r: (r["mesh_scale"], r["ald_cells"], r["T_nm"], r["gap"])):
        w.writerow([r["T_nm"], r["gap"], r["mesh_scale"], r["ald_cells"], r["tri"], f'{r["neff"]:.6f}', f'{r["im_neff"]:.4e}',
                    f'{r["IL_dBcm"]:.5f}', f'{r["VpiL_Vcm"]:.4f}', f'{r["Gamma"]:.4f}'])

# ---------- 1. thickness sweep at gap 3.4 vs Cordoba gap 4.2
ts = sorted(t for (t, g) in key if g == 3.4)
lT = np.array(ts); lIL = np.array([key[(t, 3.4)]["IL_dBcm"] for t in ts]); lV = np.array([key[(t, 3.4)]["VpiL_Vcm"] for t in ts])
V_ref = key[(0, 3.4)]["VpiL_Vcm"]; N["VpiL_ref_lisbon_gap3.4_noALD"] = V_ref
N["VpiL_cordoba_gap4.2_noALD"] = float(cV[0]); N["IL_cordoba_gap4.2_noALD"] = float(cIL[0])
fig, axs = plt.subplots(2, 2, figsize=(13, 8))
a = axs[0, 0]; a.plot(lT, lV, "o-", c="#1f5aa6", label="Lisbon lifted + 200 nm buffer, gap 3.4 µm"); a.plot(cT, cV, "s--", c="#d4a017", label="Cordoba, gap 4.2 µm")
a.set_ylabel("Vπ·L (V·cm)"); a.set_title("Vπ·L vs Al$_2$O$_3$ thickness", weight="bold")
a = axs[0, 1]; a.semilogy(lT, lIL, "o-", c="#1f5aa6", label="Lisbon lifted + buffer, gap 3.4 µm"); a.semilogy(cT, cIL, "s--", c="#d4a017", label="Cordoba, gap 4.2 µm")
a.set_ylabel("IL (dB/cm, log)"); a.set_title("Optical attenuation vs Al$_2$O$_3$ thickness", weight="bold")
a = axs[1, 0]; a.plot(lT, lV - lV[0], "o-", c="#1f5aa6", label="Lisbon"); a.plot(cT, cV - cV[0], "s--", c="#d4a017", label="Cordoba")
a.set_ylabel("ΔVπ·L from no-ALD (V·cm)"); a.set_title("Vπ·L change: same physics?", weight="bold")
a = axs[1, 1]; a.plot(lT, lIL / lIL[0], "o-", c="#1f5aa6", label="Lisbon"); a.plot(cT, cIL / cIL[0], "s--", c="#d4a017", label="Cordoba")
a.set_ylabel("IL / IL(no ALD)"); a.set_title("Relative IL increase", weight="bold")
for a in axs.flat:
    a.set_xlabel("ALD Al$_2$O$_3$ thickness (nm)"); a.grid(alpha=.3, which="both"); a.legend(frameon=False, fontsize=9)
fig.suptitle("ALD Al$_2$O$_3$ on Lisbon lifted (buffer 200 nm, gap 3.4 µm) vs Cordoba (gap 4.2 µm) — WG_TOP 1.4 µm, 1575 nm", weight="bold")
fig.tight_layout(); fig.savefig("P1_thickness_sweep_vs_cordoba.png", dpi=170); plt.close(fig)
N["sweep_gap3.4"] = [dict(T=int(t), IL=float(i), VpiL=float(v)) for t, i, v in zip(lT, lIL, lV)]

# ---------- 2/3. gap sweeps
def curve(t):
    gs = sorted(g for (tt, g) in key if tt == t)
    return np.array(gs), np.array([key[(t, g)]["IL_dBcm"] for g in gs]), np.array([key[(t, g)]["VpiL_Vcm"] for g in gs])
g40, il40, v40 = curve(40)
G_star = float(np.interp(V_ref, v40, g40)) if v40.min() <= V_ref <= v40.max() else None
N["G_star_40nm"] = G_star
fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 4.8))
for t in (0, 30, 40, 50):
    g, il, v = curve(t)
    if len(g) < 2: continue
    lw = 2.4 if t == 40 else 1.5
    a1.plot(g, v, "o-", c=COL[t], lw=lw, ms=5, label=f"Al$_2$O$_3$ {t} nm" if t else "no Al$_2$O$_3$")
    a2.plot(g, il, "o-", c=COL[t], lw=lw, ms=5, label=f"Al$_2$O$_3$ {t} nm" if t else "no Al$_2$O$_3$")
a1.axhline(V_ref, c="k", ls="--", lw=1); a1.text(a1.get_xlim()[0] + 0.02, V_ref + 0.004, f"target: no-ALD Lisbon @ 3.4 µm = {V_ref:.3f} V·cm", fontsize=8.5)
a1.axhline(cV[0], c="#d4a017", ls=":", lw=1.2); a1.text(4.3, cV[0] - 0.018, f"Cordoba 4.2 µm = {cV[0]:.3f}", fontsize=8.5, color="#8a6a00")
a2.axhline(cIL[0], c="#d4a017", ls=":", lw=1.2); a2.text(3.42, cIL[0] * 1.05, f"Cordoba IL = {cIL[0]:.2f} dB/cm", fontsize=8.5, color="#8a6a00")
if G_star:
    for a in (a1, a2): a.axvline(G_star, c="#1f5aa6", ls=":", lw=1.2)
    a1.text(G_star + 0.02, a1.get_ylim()[1] - 0.02, f"relaxed gap\n{G_star:.2f} µm", color="#1f5aa6", fontsize=9, va="top")
a1.set_ylabel("Vπ·L (V·cm)"); a2.set_ylabel("IL (dB/cm)"); a2.set_yscale("log")
a1.set_title("Vπ·L vs bottom gap", weight="bold"); a2.set_title("Optical attenuation vs bottom gap", weight="bold")
for a in (a1, a2): a.set_xlabel("bottom gap GAP_BOT (µm)"); a.grid(alpha=.3, which="both"); a.legend(frameon=False, fontsize=9)
fig.suptitle("Gap relaxation with ALD Al$_2$O$_3$ — Lisbon lifted, buffer 200 nm, WG_TOP 1.4 µm, 1575 nm", weight="bold")
fig.tight_layout(); fig.savefig("P2_gap_relaxation.png", dpi=170); plt.close(fig)

# tolerance at G*: interpolate 30/50 nm curves at G_star
if G_star:
    rows = []
    for t in (30, 40, 50):
        g, il, v = curve(t)
        rows.append(dict(T=t, gap=G_star, VpiL=float(np.interp(G_star, g, v)), IL=float(np.exp(np.interp(G_star, g, np.log(il))))))
    N["tolerance_at_G_star"] = rows
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.4))
    for a, k, lab in [(a1, "VpiL", "Vπ·L (V·cm)"), (a2, "IL", "IL (dB/cm)")]:
        xs = [r["T"] for r in rows]; ys = [r[k] for r in rows]
        a.bar([f"{x} nm\n({x-40:+d} nm)" if x != 40 else "40 nm\n(nominal)" for x in xs], ys, color=[COL[x] for x in xs])
        for i, y in enumerate(ys): a.text(i, y, f"{y:.3f}" if k == "VpiL" else f"{y:.4f}", ha="center", va="bottom")
        a.set_ylabel(lab)
    a1.axhline(V_ref, c="k", ls="--", lw=1); a1.set_ylim(min(r["VpiL"] for r in rows) - 0.06, max(r["VpiL"] for r in rows) + 0.03)
    a1.set_title(f"Vπ·L at the relaxed gap {G_star:.2f} µm", weight="bold")
    a2.axhline(cIL[0], c="#d4a017", ls=":", lw=1.2); a2.set_title(f"IL at the relaxed gap {G_star:.2f} µm (Cordoba 0.43 dotted)", weight="bold")
    fig.suptitle("ALD thickness error ±10 nm with the gap designed for 40 nm", weight="bold")
    fig.tight_layout(); fig.savefig("P3_ald_tolerance.png", dpi=170); plt.close(fig)

# mesh check
N["mesh"] = [r for r in R if r["mesh_scale"] != 1.0 or r["ald_cells"] != 3.0] + [key.get((40, 3.4)), key.get((40, 4.2))]
json.dump(N, open("summary.json", "w"), indent=1)
print(json.dumps({k: v for k, v in N.items() if k != "sweep_gap3.4"}, indent=1))
for t in (0, 30, 40, 50):
    g, il, v = curve(t); print(t, [f"{a}:{b:.4f}/{c:.3f}" for a, b, c in zip(g, il, v)])
