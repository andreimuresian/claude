import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ld = lambda f: [json.loads(l[7:]) for l in open(f) if l.startswith("RESULT")]
C = ld("cases.txt")
cases = [(0, 0, "Baseline"), (200, 0, "SiO₂ buffer\n200 nm"), (0, 40, "ALD\n40 nm"), (200, 40, "Buffer\n+ ALD")]
cols = ["#7f8c8d", "#2a78d6", "#d6409f", "#1b9e77"]
def get(lp, b, a, tan=0.0, mf=0.35):
    return [r for r in C if r["lat_pad"] == lp and r["buffer_nm"] == b and r["ald_nm"] == a and r["tan_ald"] == tan and r["mesh_factor"] == mf][0]
# 1. absolute FOMs (window 200 um)
fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
for ax, (k, lab, fmt) in zip(axs, (("n_m", "microwave index n_m", "{:.4f}"), ("Z0", "Z0 (Ω)", "{:.2f}"), ("alpha_dBcm", "attenuation α (dB/cm)", "{:.3f}"))):
    v = [get(200, b, a)[k] for b, a, _ in cases]
    bars = ax.bar([c[2] for c in cases], v, color=cols)
    for bb, x in zip(bars, v): ax.text(bb.get_x() + bb.get_width() / 2, x, fmt.format(x), ha="center", va="bottom", fontsize=10)
    lo, hi = min(v), max(v); ax.set_ylim(lo - 0.6 * (hi - lo), hi + 0.4 * (hi - lo)); ax.set_title(lab); ax.grid(axis="y", alpha=.3)
fig.suptitle("Cordoba RF figures of merit at 60 GHz (volumetric gold loss; lateral padding 200 µm, mesh factor 0.35)\nnote: y-axes do not start at zero")
plt.tight_layout(); plt.savefig("rf_fom_absolute.png", dpi=130); plt.close()
# 2. relative changes, both windows
fig, ax = plt.subplots(figsize=(11, 4.8))
keys = (("n_m", "n_m"), ("Z0", "Z0"), ("alpha_dBcm", "α"))
w = 0.12; x = np.arange(3)
for j, ((b, a, lab), c) in enumerate(zip(cases[1:], cols[1:])):
    for k, (lp, hatch) in enumerate(((200, ""), (800, "//"))):
        base = get(lp, 0, 0); r = get(lp, b, a)
        d = [(r[q] / base[q] - 1) * 100 for q, _ in keys]
        pos = x + (j * 2 + k - 2.5) * w
        bars = ax.bar(pos, d, w, color=c, hatch=hatch, edgecolor="white", label=f"{lab.replace(chr(10), ' ')} (padding {lp} µm)")
        for p, v in zip(pos, d): ax.text(p, v + (0.08 if v >= 0 else -0.08), f"{v:+.2f}", ha="center", va="bottom" if v >= 0 else "top", fontsize=7.5, rotation=90)
ax.axhline(0, c="k", lw=0.8); ax.set_xticks(x); ax.set_xticklabels([l for _, l in keys], fontsize=12)
ax.set_ylabel("change vs baseline (%)"); ax.set_ylim(-5.2, 5.2); ax.grid(axis="y", alpha=.3); ax.legend(fontsize=8, ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.38))
ax.set_title("Effect of the SiO₂ buffer and the ALD on the RF figures of merit (60 GHz): same at both window widths")
plt.tight_layout(); plt.savefig("rf_fom_changes.png", dpi=130); plt.close()
# 3. window and mesh studies
W = sorted(ld("window035.txt"), key=lambda r: (r["air_h"], r["lat_pad"]))
M = sorted([r for r in ld("window.txt") + ld("mesh_conv.txt") if r["lat_pad"] == 200 and r["air_h"] == 550], key=lambda r: -r["mesh_factor"])
fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
lw = [r for r in W if r["air_h"] == 550]
axs[0].plot([r["lat_pad"] for r in lw], [r["Z0"] for r in lw], "o-", c="#c0392b", label="full-wave Z0 (volumetric)")
axs[0].plot([r["lat_pad"] for r in lw], [r["Z0_qs"] for r in lw], "s--", c="#1f4e79", label="quasi-static Z0")
axs[0].axvline(200, c="grey", ls=":"); axs[0].set_xlabel("lateral padding (µm)"); axs[0].set_ylabel("Z0 (Ω)"); axs[0].legend(); axs[0].grid(alpha=.3)
axs[0].set_title("Window width: full-wave Z0 drifts (PEC box + Si substrate),\nquasi-static Z0 does not")
la = sorted([r for r in W if r["lat_pad"] == 200], key=lambda r: r["air_h"])
axs[1].plot([r["air_h"] for r in la], [r["Z0"] for r in la], "o-", c="#c0392b"); axs[1].set_ylim(35.5, 36.5)
axs[1].set_xlabel("air height (µm)"); axs[1].set_ylabel("Z0 (Ω)"); axs[1].grid(alpha=.3); axs[1].set_title("Air height: converged (padding 200 µm)")
axs[2].plot([r["tri"] / 1e3 for r in M], [r["Z0"] for r in M], "o-", c="#c0392b")
for r in M: axs[2].annotate(f"{r['mesh_factor']}", (r["tri"] / 1e3, r["Z0"]), textcoords="offset points", xytext=(4, -12), fontsize=8)
axs[2].axvline([r["tri"] for r in M if r["mesh_factor"] == 0.35][0] / 1e3, c="grey", ls=":")
axs[2].set_xscale("log"); axs[2].set_xticks([25, 50, 100, 200, 400]); axs[2].set_xticklabels(["25", "50", "100", "200", "400"]); axs[2].minorticks_off(); axs[2].set_xlabel("triangles (thousands); labels = mesh factor"); axs[2].set_ylabel("Z0 (Ω)"); axs[2].grid(alpha=.3)
axs[2].set_title("Mesh convergence (baseline); 0.35 used")
plt.tight_layout(); plt.savefig("rf_window_mesh_studies.png", dpi=130); plt.close()
# 4. ALD loss tangent
T = sorted([r for r in C if r["buffer_nm"] == 200 and r["ald_nm"] == 40 and r["lat_pad"] == 200 and r["mesh_factor"] == 0.35], key=lambda r: r["tan_ald"])
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.plot([r["tan_ald"] for r in T], [r["alpha_dBcm"] for r in T], "o-", c="#d6409f", label="total α")
ax2 = ax.twinx(); ax2.plot([r["tan_ald"] for r in T], [r["alpha_d_dBcm"] for r in T], "s--", c="#555", label="dielectric part")
ax.set_xlabel("ALD loss tangent tan δ"); ax.set_ylabel("total α (dB/cm)"); ax2.set_ylabel("dielectric loss (dB/cm)")
ax.set_ylim(5.0, 5.4); ax.grid(alpha=.3); ax.set_title("Buffer + ALD: effect of an ALD loss tangent (60 GHz)")
ax.legend(loc="upper left"); ax2.legend(loc="lower right")
plt.tight_layout(); plt.savefig("rf_ald_loss_tangent.png", dpi=130); plt.close(); print("ok")
