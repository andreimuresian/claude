"""
Line model (mzm_interconnect.bend_cpw) vs the reference over the inverse-design
space: S 30-40, W 4-5, Wg 50-60 um, t = 2 um, bend stack; 9 frequencies 1-200 GHz
(doe_design.py).

Reference = R, L from the current inside the gold (eddy_tensor.py) + C from
  (a) the FEM notebook's quasi-static solve on its default mesh (bend_fem.py), and
  (b) the same equations mesh-converged (qs_tensor.py at hfine 0.025 um; the
      notebook mesh is +0.18..0.25 % high in C, see results/eval_design.log).
Writes results/eval_design.{json,log} and results/fig_design_validation.png.
"""
import json
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from mzm_interconnect.bend_cpw import BendGeometry, line_model          # noqa: E402
import qs_tensor as Q                                                   # noqa: E402

C0 = 299792458.0
DB = 20 * np.log10(np.e)
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.grid": True, "grid.color": GRID,
                     "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "axes.titleweight": "bold", "axes.titlesize": 12, "savefig.dpi": 160, "lines.linewidth": 2})


def ref_line(R, L, C, G, f):
    w = 2 * np.pi * f
    g = np.sqrt((R + 1j * w * L) * (G + 1j * w * C))
    return DB * g.real / 100, g.imag / w * C0, np.abs(np.sqrt((R + 1j * w * L) / (G + 1j * w * C)))


rows = [json.loads(l) for l in open("results/doe_design.jsonl")]
cache = "results/doe_design_qs_conv.json"
conv = json.load(open(cache)) if os.path.exists(cache) else {}
out, log = [], []
for r in rows:
    key = f"{r['S']}_{r['W']}_{r['Wg']}"
    if key not in conv:
        Ce, Ca, _ = Q.capacitance(r["S"], r["W"], r["Wg"], 2.0, hfine=0.025)
        conv[key] = dict(C_eps=Ce, C_air=Ca)
        json.dump(conv, open(cache, "w"), indent=1)
    g = BendGeometry(r["S"], r["W"], r["Wg"], 2.0)
    f = np.array(r["f"]) * 1e9
    m = line_model(g).evaluate(f)
    R, L = np.array(r["R"]), np.array(r["L"])
    errs = {}
    for name, C in (("notebook", r["C_eps"]), ("converged", conv[key]["C_eps"])):
        a, n, Z = ref_line(R, L, C, m["G"], f)
        errs[name] = dict(alpha=((m["alpha_dB_cm"] / a - 1) * 100).tolist(), n_m=((m["n_m"] / n - 1) * 100).tolist(),
                          Z0=((m["Z0"] / Z - 1) * 100).tolist(), ref_alpha=a.tolist(), ref_n=n.tolist(),
                          ref_Z=Z.tolist())
    errs["C_model_vs_conv_pct"] = (m["C"] / conv[key]["C_eps"] - 1) * 100
    errs["C_notebook_vs_conv_pct"] = (r["C_eps"] / conv[key]["C_eps"] - 1) * 100
    out.append(dict(S=r["S"], W=r["W"], Wg=r["Wg"], f=r["f"], **errs))

f = np.array(rows[0]["f"])
i60 = list(f).index(60)
for name in ("converged", "notebook"):
    log.append(f"== reference C: {name} ({len(out)} geometries)")
    for k in ("alpha", "n_m", "Z0"):
        e = np.array([o[name][k] for o in out])
        log.append(f"  {k:6s} model - ref (%) per frequency {list(f)} GHz")
        log.append(f"     mean   {np.round(e.mean(0), 2).tolist()}")
        log.append(f"     max|.| {np.round(np.abs(e).max(0), 2).tolist()}")
cm = np.array([o["C_model_vs_conv_pct"] for o in out])
cn = np.array([o["C_notebook_vs_conv_pct"] for o in out])
log.append(f"C: line model vs converged FEM {cm.mean():+.3f} % (range {cm.min():+.3f} .. {cm.max():+.3f})")
log.append(f"C: notebook mesh vs converged FEM {cn.mean():+.3f} % (range {cn.min():+.3f} .. {cn.max():+.3f})")
log.append(f"at 60 GHz vs converged reference: alpha max|err| "
           f"{max(abs(o['converged']['alpha'][i60]) for o in out):.2f} %, n_m "
           f"{max(abs(o['converged']['n_m'][i60]) for o in out):.2f} %, Z0 "
           f"{max(abs(o['converged']['Z0'][i60]) for o in out):.2f} %")
print("\n".join(log))
open("results/eval_design.log", "w").write("\n".join(log) + "\n")
json.dump(out, open("results/eval_design.json", "w"), indent=1)

fig, axs = plt.subplots(1, 3, figsize=(16, 4.4))
for ax, k, lab in zip(axs, ("alpha", "n_m", "Z0"), ("α", "n_m", "|Zc|")):
    e = np.array([o["converged"][k] for o in out])
    en = np.array([o["notebook"][k] for o in out])
    ax.fill_between(f, e.min(0), e.max(0), color=BLUE, alpha=0.25, lw=0)
    ax.plot(f, e.mean(0), "o-", color=BLUE, ms=5, label="vs converged FEM C (mean, band = all)")
    ax.plot(f, en.mean(0), "s--", color=ORANGE, ms=5, mfc="none", label="vs notebook-mesh FEM C (mean)")
    ax.axhline(0, color=MUTED, lw=1)
    ax.set_xscale("log")
    ax.set_xlabel("Frequency (GHz)")
    ax.set_ylabel("line model − reference (%)")
    ax.set_title(f"{lab}: {len(out)} geometries in the design space")
    ax.legend(fontsize=8.5, loc="best")
fig.suptitle("Bend line model vs reference: S 30–40, W 4–5, Wg 50–60 µm, Au 2 µm", y=1.02)
fig.subplots_adjust(wspace=0.3)
fig.savefig("results/fig_design_validation.png", bbox_inches="tight", facecolor="white")
