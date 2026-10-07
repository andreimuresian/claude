"""IL and Vpi*L vs SiO2 buffer thickness (130-270 nm), buffered lifted designs, gap 3.4 um.

Lisbon lifted (550 nm film, 275 etch / 275 slab) @ 1575 nm and Jerez lifted (400 nm film,
170 etch / 230 slab) @ 1360 nm; WG_TOP 1.0 and 1.4 um; CAP_H 1.4 (from the buffer top),
CAP_W 2.0, GAP_TOP 10.  Reference: unbuffered (BUFFER_H = 0) at gap 4.2 um.
Input: raw solver log lines (bt_out.txt) -> buffer_thickness_sweep.csv + figures.
"""
import re, sys, json
import numpy as np
import matplotlib.pyplot as plt

HERE = __file__.rsplit("/", 1)[0]
WL = {"L": 1.575, "J": 1.360}
NAME = {"L": "Lisbon lifted, C band 1575 nm (550 nm film)", "J": "Jerez lifted, O band 1360 nm (400 nm film)"}
COL = {"L": "#c0392b", "J": "#1f5fa8"}

rows = []
pat = re.compile(r"BT_(\w)_w([\d.]+)_b(\d+)\s+tri=\s*(\d+) neff=([\d.]+) Im=(\S+) IL=x VpiL=([\d.]+) Gamma=([\d.]+)")
for line in open(sys.argv[1]):
    m = pat.search(line)
    if not m:
        continue
    d, w, b, tri, ne, im, vpil, gam = m.groups()
    k0_cm = 2 * np.pi / WL[d] * 1e4
    rows.append(dict(design=d, wg_top=float(w), buffer_nm=int(b), tri=int(tri), neff=float(ne),
                     im_neff=float(im), IL_dBcm=20 * np.log10(np.e) * k0_cm * abs(float(im)),
                     VpiL_Vcm=float(vpil), Gamma=float(gam)))
rows.sort(key=lambda r: (r["design"], r["wg_top"], r["buffer_nm"]))
assert len(rows) == 64, len(rows)
with open(f"{HERE}/buffer_thickness_sweep.csv", "w") as f:
    keys = list(rows[0])
    f.write(",".join(keys) + "\n")
    for r in rows:
        f.write(",".join(f"{r[k]:.6g}" if isinstance(r[k], float) else str(r[k]) for k in keys) + "\n")


def series(d, w):
    rr = [r for r in rows if r["design"] == d and r["wg_top"] == w and r["buffer_nm"] > 0]
    ref = [r for r in rows if r["design"] == d and r["wg_top"] == w and r["buffer_nm"] == 0][0]
    b = np.array([r["buffer_nm"] for r in rr], float)
    return b, np.array([r["VpiL_Vcm"] for r in rr]), np.array([r["IL_dBcm"] for r in rr]), ref


summary = {}
for d in "LJ":
    for w in (1.0, 1.4):
        b, v, il, ref = series(d, w)
        at = lambda arr, x: float(arr[b == x][0])
        v0, il0 = at(v, 200), at(il, 200)
        s = {"VpiL_200": v0, "IL_200": il0, "ref_VpiL_gap4.2": ref["VpiL_Vcm"], "ref_IL_gap4.2": ref["IL_dBcm"],
             "dVpiL_dB_mVcm_per_10nm": float(np.polyfit(b, v, 1)[0] * 10 * 1e3)}
        for dd in (20, 40, 70):
            s[f"VpiL_{200-dd}"], s[f"VpiL_{200+dd}"] = at(v, 200 - dd), at(v, 200 + dd)
            s[f"IL_{200-dd}"], s[f"IL_{200+dd}"] = at(il, 200 - dd), at(il, 200 + dd)
        summary[f"{d}_w{w}"] = s
json.dump(summary, open(f"{HERE}/summary.json", "w"), indent=1)

# common axes for both width figures
allv = [r["VpiL_Vcm"] for r in rows]
alli = [r["IL_dBcm"] for r in rows if r["buffer_nm"] > 0]
VLIM = (np.floor(min(allv) * 20) / 20 - 0.02, np.ceil(max(allv) * 20) / 20 + 0.02)
ILIM = (min(alli) / 1.5, max(alli) * 2.5)


def panel(axv, axi, w, legend=True):
    for ax in (axv, axi):
        ax.axvspan(160, 240, color="0.93", zorder=0, label="±40 nm (extreme)")
        ax.axvspan(180, 220, color="0.84", zorder=0, label="±20 nm (typical, wafer sil-A)")
        ax.axvline(200, color="0.5", lw=0.8, ls=":", zorder=1)
    for d in "LJ":
        b, v, il, ref = series(d, w)
        axv.plot(b, v, "o-", color=COL[d], ms=5, lw=1.4, label=NAME[d])
        axv.axhline(ref["VpiL_Vcm"], color=COL[d], ls="--", lw=1.0,
                    label=f"unbuffered, gap 4.2 µm ({ref['VpiL_Vcm']:.3f} V·cm)")
        axi.semilogy(b, il, "s-", color=COL[d], ms=5, lw=1.4, label=NAME[d])
    axv.set_ylim(*VLIM); axi.set_ylim(*ILIM)
    axv.set_ylabel(r"V$_\pi$·L  (V·cm)"); axi.set_ylabel("IL  (dB/cm)")
    axi.set_xlabel("SiO$_2$ buffer thickness  BUFFER_H  (nm)")
    for ax in (axv, axi):
        ax.set_xlim(125, 275); ax.set_xticks(range(130, 271, 10)); ax.grid(alpha=0.3, which="both")
        ax.tick_params(axis="x", labelsize=8)
    axv.set_title(f"WG_TOP = {w:.1f} µm  |  gap 3.4 µm, CAP_H 1.4 µm, CAP_W 2.0 µm, GAP_TOP 10 µm", fontsize=10)
    if legend:
        h, l = axv.get_legend_handles_labels()
        axv.legend(h[2:], l[2:], fontsize=7.5, loc="center", bbox_to_anchor=(0.5, 0.5), ncol=2, framealpha=0.95)
        axi.legend(fontsize=7.5, loc="upper right", ncol=2, framealpha=0.95)


def table_text(w):
    out = []
    for d, tag in (("L", "C 1575"), ("J", "O 1360")):
        s = summary[f"{d}_w{w}"]
        v0 = s["VpiL_200"]
        out.append(f"{tag}: Vπ·L(200)={v0:.4f} V·cm | ±20 nm: {s['VpiL_180']-v0:+.4f}/{s['VpiL_220']-v0:+.4f} "
                   f"({(s['VpiL_180']/v0-1)*100:+.1f}/{(s['VpiL_220']/v0-1)*100:+.1f} %) | "
                   f"±40 nm: {(s['VpiL_160']/v0-1)*100:+.1f}/{(s['VpiL_240']/v0-1)*100:+.1f} % | "
                   f"IL(200)={s['IL_200']:.4f} dB/cm, ±40 nm: {s['IL_160']:.4f}–{s['IL_240']:.4f}")
    return "\n".join(out)


for w in (1.0, 1.4):
    fig, (axv, axi) = plt.subplots(2, 1, figsize=(10, 8.6), sharex=True, gridspec_kw={"height_ratios": [1.25, 1]})
    panel(axv, axi, w)
    fig.text(0.5, 0.005, table_text(w), ha="center", va="bottom", fontsize=7.6, family="monospace")
    fig.suptitle(f"Buffered lifted designs: Vπ·L and IL vs SiO$_2$ buffer thickness (WG_TOP {w:.1f} µm)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    fig.savefig(f"{HERE}/buffer_thickness_WG{w:.1f}.png", dpi=170)
    plt.close(fig)

fig, ax = plt.subplots(2, 2, figsize=(16, 8.6), sharex=True, sharey="row", gridspec_kw={"height_ratios": [1.25, 1]})
for j, w in enumerate((1.0, 1.4)):
    panel(ax[0, j], ax[1, j], w, legend=(j == 0))
    if j:
        ax[0, j].set_ylabel(""); ax[1, j].set_ylabel("")
fig.suptitle("Buffered lifted designs: Vπ·L and IL vs SiO$_2$ buffer thickness", fontsize=13, fontweight="bold")
fig.tight_layout()
fig.savefig(f"{HERE}/buffer_thickness_both_widths.png", dpi=150)

for k, s in summary.items():
    print(k, {a: round(b, 5) for a, b in s.items()})
