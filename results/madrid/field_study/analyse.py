import numpy as np, json
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.tri import Triangulation
C = {k: dict(np.load(f"{k}.npz", allow_pickle=False)) for k in ("noald_thick","noald_thin","ald_thick","ald_thin")}
REG = ["inner wall", "underside ≤1 µm from gap", "underside >1 µm (under gold)", "top face", "outer wall"]
out = {}
for k, d in C.items():
    gold = np.char.startswith(d["mat"], "Au")
    xg = float(d["gap"]) / 2; yb = float(d["slab_h"]) + float(d["buf"]); yt = yb + float(d["mtx"])
    ax = np.abs(d["cx"]); y = d["cy"]
    dist = np.vstack([ax - xg, y - yb, yt - y, (xg + 30) - ax])          # inner, bottom, top, outer
    near = dist.argmin(0)
    reg = np.select([near == 0, (near == 1) & (ax - xg <= 1.0), near == 1, near == 2, near == 3], [0, 1, 2, 3, 4])
    A = d["imeps"] * d["E2int"]
    scale = float(d["IL"]) / A[gold].sum()          # absorbed power ∝ |Im eps| |E|^2 ; scaled so that the sum = IL
    d["absd"] = A * scale / d["area"]; d["reg"] = reg; d["gold"] = gold
    out[k] = {"IL": float(d["IL"]), "VpiL": float(d["VpiL"]), "IL_by_region_dBcm": {REG[i]: float(A[gold & (reg == i)].sum() * scale) for i in range(5)},
              "check_IL_over_absorption_raw": float(d["IL"]) / float(A[gold].sum())}
    # field energy fractions
    tot = d["E2int"].sum()
    out[k]["E2_fraction"] = {m: float(d["E2int"][d["mat"] == m].sum() / tot) for m in np.unique(d["mat"])}
json.dump(out, open("field_study.json", "w"), indent=1)
for k in out:
    print(k, f'IL {out[k]["IL"]:.4f}', {r: round(v, 4) for r, v in out[k]["IL_by_region_dBcm"].items()}, "chk", f'{out[k]["check_IL_over_absorption_raw"]:.4e}')
    print("   E2 frac", {m: round(v, 5) for m, v in out[k]["E2_fraction"].items()})

# ---- 1. log |E|^2 maps --------------------------------------------------------------
def tri(d):
    return Triangulation(d["p"][0], d["p"][1], d["t"].T)
fig, axs = plt.subplots(2, 2, figsize=(15, 8.6))
for a, k, t in zip(axs.flat, ["noald_thick", "noald_thin", "ald_thick", "ald_thin"],
                   ["no ALD, Au 2.0 µm", "no ALD, Au 0.3 µm", "ALD 40 nm, Au 2.0 µm", "ALD 40 nm, Au 0.3 µm"]):
    d = C[k]; dens = d["E2int"] / d["area"]; dens = dens / dens.max()
    im = a.tripcolor(tri(d), facecolors=np.log10(np.maximum(dens, 1e-8)), cmap="inferno", vmin=-7, vmax=0, shading="flat")
    gm = d["gold"]
    a.tricontour(tri(d), np.ones(d["p"].shape[1]), levels=[])
    for m, col in (("Au", "w"),):
        pass
    xg = float(d["gap"]) / 2; yb = float(d["slab_h"]) + float(d["buf"])
    for s in (-1, 1):
        a.plot([s * xg, s * xg, s * 4], [yb + float(d["mtx"]), yb, yb], color="w", lw=.8)
        a.plot([s * xg, s * 4], [yb + float(d["mtx"])] * 2, color="w", lw=.8)
    a.set_xlim(-4, 4); a.set_ylim(-1.0, 2.6); a.set_aspect("equal"); a.set_title(f"{t}: IL {float(d['IL']):.3f} dB/cm", fontsize=10)
fig.colorbar(im, ax=axs, label="log₁₀ |E|² (normalised)", shrink=.8)
fig.suptitle("Optical mode |E|² at 1625 nm (gap 3.5 µm, buffer 80 nm); white = gold outline", fontsize=12)
fig.savefig("F1_E2_maps.png", dpi=150, bbox_inches="tight")

# ---- 2. absorption density in the gold near the gap (signal side) ------------------
fig, axs = plt.subplots(1, 4, figsize=(16, 5.2))
for a, k, t in zip(axs, ["noald_thick", "noald_thin", "ald_thick", "ald_thin"], ["no ALD 2.0", "no ALD 0.3", "ALD 2.0", "ALD 0.3"]):
    d = C[k]; v = np.where(d["gold"], d["absd"], np.nan)
    im = a.tripcolor(tri(d), facecolors=np.log10(np.nan_to_num(v, nan=1e-12) + 1e-12), cmap="viridis", vmin=-4, vmax=1, shading="flat")
    xg = float(d["gap"]) / 2; yb = float(d["slab_h"]) + float(d["buf"])
    a.set_xlim(xg - 0.3, xg + 1.2); a.set_ylim(yb - 0.2, yb + 2.1); a.set_aspect("equal"); a.set_title(f"Au µm {t}", fontsize=10)
    a.axvline(xg, color="w", lw=.5); a.axhline(yb, color="w", lw=.5)
fig.colorbar(im, ax=axs, label="log₁₀ absorbed power density (dB/cm per µm²)", shrink=.8)
fig.suptitle("Where the light is absorbed: inside the signal electrode near the gap (x from the gold inner edge)", fontsize=12)
fig.savefig("F2_absorption_maps.png", dpi=150, bbox_inches="tight")

# ---- 3. absorption by surface -----------------------------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(14, 4.8), sharey=True)
for a, pre, t in zip(axs, ["noald", "ald"], ["no ALD", "ALD 40 nm"]):
    th = [out[pre + "_thick"]["IL_by_region_dBcm"][r] for r in REG]; tn = [out[pre + "_thin"]["IL_by_region_dBcm"][r] for r in REG]
    x = np.arange(5); b1 = a.bar(x - 0.2, th, 0.4, color="#0E2268", label=f"Au 2.0 µm (IL {out[pre+'_thick']['IL']:.3f})")
    b2 = a.bar(x + 0.2, tn, 0.4, color="#F20013", label=f"Au 0.3 µm (IL {out[pre+'_thin']['IL']:.3f})")
    a.bar_label(b1, fmt="%.3f", fontsize=8); a.bar_label(b2, fmt="%.3f", fontsize=8)
    a.set_xticks(x, [r.replace(" (", "\n(") for r in REG], fontsize=8.5); a.set_title(t); a.legend(fontsize=9); a.grid(alpha=.3, axis="y")
axs[0].set_ylabel("absorbed (dB/cm)")
fig.suptitle("Optical loss split by gold surface (both electrodes, gap 3.5 µm, buffer 80 nm, 1625 nm)")
fig.tight_layout(); fig.savefig("F3_loss_by_surface.png", dpi=150)

# ---- 4. |E|^2 profiles -------------------------------------------------------------------------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(14, 4.6))
for k, col, ls in (("noald_thick", "#0E2268", "-"), ("noald_thin", "#0E2268", "--"), ("ald_thick", "#e0218a", "-"), ("ald_thin", "#e0218a", "--")):
    d = C[k]; dens = d["E2int"] / d["area"]; n0 = dens.max()
    sel = (d["mat"] == "LN") & (np.abs(d["cy"] - 0.14) < 0.06) & (d["cx"] > 0)
    xb = np.arange(0, 20, 0.1); ib = np.digitize(d["cx"][sel], xb)
    prof = [dens[sel][ib == i].mean() / n0 if np.any(ib == i) else np.nan for i in range(1, len(xb))]
    a1.semilogy(xb[:-1] + 0.05, prof, ls, color=col, label=k.replace("_", ", ").replace("thick", "Au 2.0").replace("thin", "Au 0.3"))
    xg = float(d["gap"]) / 2
    sel = (np.abs(d["cx"] - (xg - 0.03)) < 0.03) & (d["cy"] > 0.3)
    yb_ = np.arange(0.3, 3.0, 0.05); ib = np.digitize(d["cy"][sel], yb_)
    prof = [dens[sel][ib == i].mean() / n0 if np.any(ib == i) else np.nan for i in range(1, len(yb_))]
    a2.semilogy(yb_[:-1] + 0.025, prof, ls, color=col, label=k)
a1.axvline(1.75, color="0.5", ls=":"); a1.text(1.8, 1e-1, "gold edge", fontsize=8)
a1.set_xlabel("x (µm)"); a1.set_ylabel("|E|² / max"); a1.set_title("Along the LN slab (y = 0.14 µm): wave under the gold"); a1.legend(fontsize=8)
a2.set_xlabel("y (µm)"); a2.set_title("Along the gold inner wall (30 nm into the gap/slot)"); a2.axvline(0.355 + 0.3, color="0.5", ls=":"); a2.text(0.68, 1e-6, "thin gold top", fontsize=8)
for a in (a1, a2): a.grid(alpha=.3, which="both")
fig.tight_layout(); fig.savefig("F4_profiles.png", dpi=150)
