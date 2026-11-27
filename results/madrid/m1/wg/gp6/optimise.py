"""Exhaustive constrained search on the GP surrogate (the surrogate costs microseconds, so no GA is needed).
min Vpi*L  s.t.  IL_upper95 <= IL_MAX  (conservative), BUFFER_H >= BUF_MIN (nominal), all within the trained box.
Also reports the IL / Vpi*L at BUFFER_H - 40 nm for every candidate, and the Pareto front Vpi*L vs IL.
Run: python3 optimise.py [IL_MAX=0.4] [BUF_MIN=0.10]"""
import sys, json, itertools, numpy as np
from predictor import Predictor
IL_MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4; BUF_MIN = float(sys.argv[2]) if len(sys.argv) > 2 else 0.10
P = Predictor("models/model_card.json")
import os
GAP_MIN = float(os.environ.get("GAP_MIN", "3.0"))
G = np.round(np.arange(GAP_MIN, 4.5001, 0.05), 3); Bf = np.round(np.arange(BUF_MIN, 0.2001, 0.005), 4)
F = np.round(np.linspace(0, 1, 11), 3); CH = np.round(np.arange(0.5, 1.4001, 0.1), 3); MS = np.round(np.arange(0.5, 1.0001, 0.1), 3); WGs = np.round(np.arange(1.0, 1.5001, 0.1), 3)
X = np.array(list(itertools.product(G, Bf, F, CH, MS, WGs))); X = X[~((X[:, 0] - 2 * X[:, 5] < 1e-6) & (X[:, 2] > 0))]; print("grid", len(X))
res = {"VpiL": [], "IL": [], "ILhi": []}
for i in range(0, len(X), 20000):
    r = P.predict_array(X[i:i + 20000]); res["VpiL"].append(r["VpiL"]["mean"]); res["IL"].append(r["IL"]["mean"]); res["ILhi"].append(r["IL"]["hi95"])
V, IL, ILhi = (np.concatenate(res[k]) for k in ("VpiL", "IL", "ILhi"))
ok = ILhi <= IL_MAX; order = np.argsort(np.where(ok, V, np.inf))[:4000]
# de-duplicate near-identical designs: keep best per (GAP, CAP_F, CAP_H) family
top, seen = [], set()
for j in order:
    key = (X[j, 0], X[j, 2], X[j, 3], X[j, 5])
    if key in seen: continue
    seen.add(key); top.append(j)
    if len(top) == 15: break
Xw = X[top].copy(); Xw[:, 1] -= 0.04; rw = P.predict_array(Xw)
out = []
for n, j in enumerate(top):
    g, b, f, ch, ms, wg = X[j]; cw = g - f * (g - 2 * wg)
    out.append(dict(rank=n + 1, GAP=g, BUFFER_H=b, CAP_W=round(cw, 4), CAP_F=f, CAP_H=ch, MTX_SMALL=ms, WG=wg, VpiL=float(V[j]), IL=float(IL[j]), IL_hi95=float(ILhi[j]),
                    VpiL_buf_m40=float(rw["VpiL"]["mean"][n]), IL_buf_m40=float(rw["IL"]["mean"][n])))
# Pareto front (all grid, mean values)
idx = np.argsort(IL); pf, best = [], np.inf
for j in idx:
    if V[j] < best - 1e-6: best = V[j]; pf.append(j)
pareto = [dict(IL=float(IL[j]), VpiL=float(V[j]), x=X[j].tolist()) for j in pf]
# one-at-a-time sensitivity around the optimum
j0 = top[0]; sens = {}
for k, name in enumerate(["GAP", "BUFFER_H", "CAP_F", "CAP_H", "MTX_SMALL", "WG"]):
    grid = np.linspace(P.lo[k], P.hi[k], 31); Xs = np.repeat(X[j0][None], 31, 0); Xs[:, k] = grid; r = P.predict_array(Xs)
    sens[name] = dict(x=grid.tolist(), VpiL=r["VpiL"]["mean"].tolist(), IL=r["IL"]["mean"].tolist())
json.dump(dict(IL_MAX=IL_MAX, BUF_MIN=BUF_MIN, top=out, pareto=pareto, sensitivity=sens), open(f"optimum_IL{IL_MAX}_buf{BUF_MIN}" + (f"_gap{GAP_MIN}" if GAP_MIN != 3.0 else "") + ".json", "w"), indent=1)
print(f"{'#':>2} {'GAP':>5} {'BUF':>5} {'CAP_W':>6} {'CAP_H':>5} {'MTXs':>4} | {'VpiL':>6} {'IL':>6} {'ILhi':>6} | buf-40: {'VpiL':>6} {'IL':>6}")
for o in out: print(f"{o['rank']:>2} {o['GAP']:5.2f} {o['BUFFER_H']*1e3:5.0f} {o['CAP_W']:6.3f} {o['CAP_H']:5.2f} {o['MTX_SMALL']:4.1f} {o['WG']:4.1f} | {o['VpiL']:6.4f} {o['IL']:6.4f} {o['IL_hi95']:6.4f} | {o['VpiL_buf_m40']:13.4f} {o['IL_buf_m40']:6.4f}")
