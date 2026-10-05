import json, sys
import numpy as np
from bend_fem import run
rng = np.random.default_rng(3)
pts = [(35, 4.15, 2.0, 3.6)]
# Latin hypercube over S 8-70 um, W 2-16 um, t 0.5-4 um, buffer 1-6 um
n = 22
u = (rng.permuted(np.tile(np.arange(n), (4, 1)), axis=1).T + rng.random((n, 4))) / n
for a, b, c, d in u:
    S = 8 * (70 / 8) ** a
    W = 2 * (16 / 2) ** b
    t = 0.5 + 3.5 * c
    h = 1 + 5 * d
    pts.append((round(S, 2), round(W, 2), round(t, 2), round(h, 2)))
for S, W, t, h in pts:
    try:
        r = run(60e9, geom=dict(sig_w=S, gap=W, au_h=t, buf_h=h), mesh_opts=dict(SKIN_REACH=min(S / 2, 17.5)),
                qs_only=True)
        print(json.dumps(dict(S=S, W=W, t=t, h=h, **{k: float(v) for k, v in r.items()})), flush=True)
    except Exception as e:
        print(json.dumps(dict(S=S, W=W, t=t, h=h, error=str(e)[:200])), flush=True)
