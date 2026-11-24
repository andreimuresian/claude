"""Robust optimum: min nominal Vpi*L s.t. IL_hi95 <= IL_MAX at BUFFER_H - 40 nm (process worst case), nominal buffer >= 100 nm."""
import sys, json, itertools, numpy as np
from predictor import Predictor
IL_MAX = float(sys.argv[1]) if len(sys.argv) > 1 else 0.4
P = Predictor()
import os
GAP_MIN = float(os.environ.get("GAP_MIN", "3.0"))
G = np.round(np.arange(GAP_MIN, 4.5001, 0.05), 3); Bf = np.round(np.arange(0.10, 0.2001, 0.005), 4)
F = np.round(np.linspace(0, 1, 11), 3); CH = np.round(np.arange(0.5, 1.4001, 0.1), 3); MS = np.round(np.arange(0.5, 1.0001, 0.1), 3)
X = np.array(list(itertools.product(G, Bf, F, CH, MS))); Xw = X.copy(); Xw[:, 1] -= 0.04
V, ILn, ILw, ILwhi, Vw = [], [], [], [], []
for i in range(0, len(X), 20000):
    a = P.predict_array(X[i:i + 20000]); b = P.predict_array(Xw[i:i + 20000])
    V.append(a["VpiL"]["mean"]); ILn.append(a["IL"]["mean"]); ILw.append(b["IL"]["mean"]); ILwhi.append(b["IL"]["hi95"]); Vw.append(b["VpiL"]["mean"])
V, ILn, ILw, ILwhi, Vw = map(np.concatenate, (V, ILn, ILw, ILwhi, Vw))
ok = ILwhi <= IL_MAX; order = np.argsort(np.where(ok, V, np.inf)); top, seen = [], set()
for j in order:
    k = (X[j, 0], X[j, 2], X[j, 3])
    if k in seen: continue
    seen.add(k); top.append(j)
    if len(top) == 10: break
out = [dict(rank=n + 1, GAP=X[j, 0], BUFFER_H=X[j, 1], CAP_W=round(X[j, 0] - X[j, 2] * (X[j, 0] - 2.8), 4), CAP_H=X[j, 3], MTX_SMALL=X[j, 4],
            VpiL=float(V[j]), IL=float(ILn[j]), VpiL_buf_m40=float(Vw[j]), IL_buf_m40=float(ILw[j]), IL_buf_m40_hi95=float(ILwhi[j])) for n, j in enumerate(top)]
json.dump(out, open(f"optimum_robust_IL{IL_MAX}" + (f"_gap{GAP_MIN}" if GAP_MIN != 3.0 else "") + ".json", "w"), indent=1)
for o in out: print(o["rank"], o["GAP"], round(o["BUFFER_H"]*1e3), o["CAP_W"], o["CAP_H"], o["MTX_SMALL"], "| nom", round(o["VpiL"], 4), round(o["IL"], 4), "| -40nm", round(o["VpiL_buf_m40"], 4), round(o["IL_buf_m40"], 4))
