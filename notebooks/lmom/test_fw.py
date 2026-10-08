import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
rects = [(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)]
g = M.Geometry(rects, 0.2e-6, 4e-6)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*20e9*M.EPS0))
f = float(sys.argv[1])*1e9 if len(sys.argv) > 1 else 20e9
ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=2e8))
print("segments", g.nseg, "k points", len(ln.k), flush=True)
for n in (1.90, 1.93, 1.95, 1.97, 2.00):
    t0 = time.time()
    gv = ln.gfun(n*ln.k0)
    print(f"n {n:.3f}: g = {gv:.4e}  |g| {abs(gv):.3e}  {time.time() - t0:.0f} s", flush=True)
