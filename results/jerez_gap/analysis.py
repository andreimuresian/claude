"""Buffered Jerez lifted, 1360 nm: Vpi*L and IL vs bottom gap (3.2-4.0 um, 200 nm buffer)
for CAP_H 1.4 / 0.5 um and WG_TOP 1.0 / 1.4 um, against the unbuffered gap 4.2 um reference
of each case.  Gap at which the buffered Vpi*L equals the unbuffered reference."""
import re, json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SP = "/tmp/claude-0/-home-user-claude/fd41e088-2b12-5532-ab62-ef0605547492/scratchpad/"
OUT = "/home/user/claude/results/jerez_gap/"
K = 20 * np.log10(np.e) * 2 * np.pi / 1.36e-6 / 100        # dB/cm per |Im neff| at 1360 nm
COL = {"1.0": "#2a78d6", "1.4": "#eb6834"}
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})

d = {}
for l in open(SP + "j1_out.txt"):
    m = re.match(r"(J[BN])_c(\S+)_w(\S+)_g(\S+)\s+tri=\s*(\d+).*neff=(\S+) Im=(\S+) IL=\S+ VpiL=(\S+)", l)
    if m:
        d[(m[1], m[2], m[3], float(m[4]))] = dict(tri=int(m[5]), neff=float(m[6]), IL=K * abs(float(m[7])),
                                                   VpiL=float(m[8]))
with open(OUT + "jerez_gap_sweep.csv", "w") as f:
    f.write("design,cap_h_um,wg_top_um,gap_bot_um,neff_re,IL_dB_per_cm,VpiL_Vcm,triangles\n")
    for (k, c, w, g), v in sorted(d.items()):
        f.write(f"{'buffer_200nm' if k == 'JB' else 'no_buffer'},{c},{w},{g:.1f},{v['neff']:.6f},"
                f"{v['IL']:.5f},{v['VpiL']:.4f},{v['tri']}\n")

summary = {}
fig, axs = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey="row")
for j, cap in enumerate(("1.4", "0.5")):
    av, ai = axs[0, j], axs[1, j]
    for w in ("1.0", "1.4"):
        pts = sorted((g, v) for (k, c, ww, g), v in d.items() if k == "JB" and c == cap and ww == w)
        if not pts:
            continue
        g = np.array([p[0] for p in pts]); vp = np.array([p[1]["VpiL"] for p in pts])
        il = np.array([p[1]["IL"] for p in pts])
        ref = d.get(("JN", cap, w, 4.2))
        av.plot(g, vp, "o-", color=COL[w], ms=5, lw=1.2, label=f"200 nm buffer, WG_TOP {w} µm")
        ai.plot(g, il, "o-", color=COL[w], ms=5, lw=1.2, label=f"200 nm buffer, WG_TOP {w} µm")
        s = dict(VpiL_at_3p2=round(float(vp[0]), 4), VpiL_at_4p0=round(float(vp[-1]), 4),
                 IL_range=[round(float(il.min()), 5), round(float(il.max()), 5)])
        if ref:
            # gap where the buffered Vpi*L equals the unbuffered reference (linear in gap)
            if vp.min() <= ref["VpiL"] <= vp.max():
                gm = float(np.interp(ref["VpiL"], vp, g)); extrap = False
            else:
                a_, b_ = np.polyfit(g[-3:], vp[-3:], 1); gm = float((ref["VpiL"] - b_) / a_); extrap = True
            av.axhline(ref["VpiL"], color=COL[w], ls="--", lw=1)
            av.axvline(gm, color=COL[w], ls=":", lw=1)
            av.plot([4.2], [ref["VpiL"]], "D", mfc="white", mec=COL[w], ms=7, mew=1.5,
                    label=f"no buffer, gap 4.2 µm: {ref['VpiL']:.3f} V·cm  →  buffered match at {gm:.2f} µm"
                          + (" (extrap.)" if extrap else ""))
            ai.plot([4.2], [ref["IL"]], "D", mfc="white", mec=COL[w], ms=7, mew=1.5,
                    label=f"no buffer, gap 4.2 µm, x_lift 6 µm: {ref['IL']:.3f} dB/cm")
            ilm = float(np.exp(np.interp(gm, g, np.log(il)))) if not extrap else None
            s.update(ref_noBuffer_VpiL=round(ref["VpiL"], 4), ref_noBuffer_IL_at_xlift6=round(ref["IL"], 4),
                     matching_gap_um=round(gm, 3), extrapolated=extrap,
                     buffered_IL_at_matching_gap=round(ilm, 5) if ilm else None)
        summary[f"CAP_H {cap} / WG_TOP {w}"] = s
    av.set_ylim(1.62, 2.45)
    ai.set_yscale("log"); ai.set_ylim(3e-4, 0.6)
    av.set_title(f"CAP_H = {cap} µm", fontsize=11)
    if j == 0:
        av.set_ylabel("Vπ·L (V·cm)"); ai.set_ylabel("IL (dB/cm)")
    ai.set_yscale("log")
    ai.set_xlabel("bottom gap GAP_BOT (µm)")
    for a, loc in ((av, "upper left"), (ai, "lower left")):
        a.grid(alpha=0.3, which="both", lw=0.4); a.legend(fontsize=8, loc=loc)
        a.tick_params(labelleft=True)
    ai.set_xticks(np.round(np.arange(3.2, 4.21, 0.1), 1))
fig.suptitle("Buffered Jerez lifted, 1360 nm (400 nm film, 170 nm etch, GAP_TOP 8 µm): "
             "dashed = unbuffered gap 4.2 µm Vπ·L, dotted = buffered gap with the same Vπ·L", fontsize=10.5)
plt.tight_layout(); fig.savefig(OUT + "jerez_VpiL_IL_vs_gap.png", dpi=150); plt.close(fig)
json.dump(summary, open(OUT + "summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
