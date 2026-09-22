"""Phase 3 scatter plots: MoM perturbations vs the CST reference columns."""
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def scatter(res, path="phase3_validation.png"):
    keys = [("dal", "alpha_delta_val", r"$\Delta\alpha$  [dB/cm]"),
            ("dL", "deltaL lumped", r"$\Delta L$  [H/m]"),
            ("dC", "deltaC lumped", r"$\Delta C$  [F/m]")]
    fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.4))
    for a, (k, refname, lab) in zip(ax, keys):
        x = np.array([r["ref"][k] for r in res], float)
        y = np.array([r[k] for r in res], float)
        lim = np.array([min(x.min(), y.min()), max(x.max(), y.max())])
        pad = 0.15*(lim[1]-lim[0] or abs(lim[1]) or 1.0)
        lim = lim + [-pad, pad]
        a.plot(lim, lim, "k--", lw=1, label="1:1")
        a.scatter(x, y, s=70, c="tab:blue", edgecolor="k", zorder=3)
        for r, xi, yi in zip(res, x, y):
            a.annotate(str(r["row"]), (xi, yi), fontsize=7,
                       xytext=(4, 4), textcoords="offset points")
        a.set_xlim(*lim); a.set_ylim(*lim)
        a.set_xlabel(f"CST  {refname}"); a.set_ylabel(f"MoM  {lab}")
        med = np.median([r["err"][k] for r in res])*100
        a.set_title(f"{lab}   median err {med:.1f} %")
        a.grid(alpha=0.3); a.legend(loc="upper left", fontsize=8)
    fig.suptitle("Phase 3 -- periodic Floquet MoM vs CST reference "
                 "(5 rows spanning the $\\Delta\\alpha$ range)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    print("wrote", path)
    return path


if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "v34.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "phase3_validation.png"
    res = json.load(open(src))
    for r in res:
        for k in ("dal", "dL", "dC"):
            r[k] = float(r[k])
    scatter(res, out)
