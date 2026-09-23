"""Phase 3 remediation scatter: common-mesh vs independent-mesh differencing.

Same layout and conventions as phase3_plot.py, with the Phase 3 independent-
mesh result overlaid as open markers so the effect of the common mesh is
visible per row rather than only in the medians."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

P = 200e-6


def scatter(res, base, path="phase3_remediation.png"):
    keys = [("dal", "e_dal", "alpha_delta_val", r"$\Delta\alpha$  [dB/cm]"),
            ("dL_svd", "e_dL_svd", "deltaL lumped", r"$\Delta L$  [H]"),
            ("dC_svd", "e_dC_svd", "deltaC lumped", r"$\Delta C$  [F]")]
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.6))
    for a, (k, ek, refname, lab) in zip(ax, keys):
        rk = k.split("_")[0]
        x = np.array([r["ref"][rk] for r in res], float)
        y = np.array([float(r[k]) for r in res], float)
        yb = np.array([float(b[k]) for b in base], float) if base else None
        allv = np.concatenate([x, y] + ([yb] if yb is not None else []))
        lim = np.array([allv.min(), allv.max()])
        pad = 0.15*(lim[1]-lim[0] or abs(lim[1]) or 1.0)
        lim = lim + [-pad, pad]
        a.plot(lim, lim, "k--", lw=1, label="1:1")
        if yb is not None:
            a.scatter(x, yb, s=70, facecolor="none", edgecolor="tab:gray",
                      zorder=2, label="independent mesh")
            for xi, y0, y1 in zip(x, yb, y):
                a.annotate("", xy=(xi, y1), xytext=(xi, y0),
                           arrowprops=dict(arrowstyle="->", color="tab:gray",
                                           lw=0.8, alpha=0.7))
        a.scatter(x, y, s=70, c="tab:blue", edgecolor="k", zorder=3,
                  label="common mesh")
        for r, xi, yi in zip(res, x, y):
            a.annotate(str(r["row"]), (xi, yi), fontsize=7,
                       xytext=(4, 4), textcoords="offset points")
        a.set_xlim(*lim); a.set_ylim(*lim)
        a.set_xlabel(f"CST  {refname}"); a.set_ylabel(f"MoM  {lab}")
        med = np.median([r[ek] for r in res])*100
        a.set_title(f"{lab}   median err {med:.1f} %")
        a.grid(alpha=0.3); a.legend(loc="upper left", fontsize=8)
    fig.suptitle("Phase 3 remediation -- common-mesh differencing vs the "
                 "Phase 3 independent-mesh result (h = 9 um, same 5 rows)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print("wrote", path)
    return path


if __name__ == "__main__":
    import sys
    src = sys.argv[1]
    bsrc = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "-" else None
    out = sys.argv[3] if len(sys.argv) > 3 else "phase3_remediation.png"
    res = json.load(open(src))
    base = json.load(open(bsrc)) if bsrc else None
    if base:                      # Phase 3 json stores per-length dL/dC
        base = [dict(dal=float(b["dal"]), dL_svd=float(b["dL"])*P,
                     dC_svd=float(b["dC"])*P, row=b["row"]) for b in base]
        order = {r["row"]: i for i, r in enumerate(res)}
        base.sort(key=lambda b: order[b["row"]])
    scatter(res, base, out)
