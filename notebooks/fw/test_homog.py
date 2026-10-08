"""TEM check: homogeneous eps -> n = sqrt(eps) exactly, Z = Z_air/sqrt(eps)."""
import sys
import pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp, fw2d
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6)
for he in (0.1e-6, 0.05e-6):
    m = fw2d.Mode2D(g, 20e9, smax=0, homog=4.0, wall_ground=True, h_edge=he, side=200e-6, top=200e-6, si_extra=0, pml=50e-6)
    b, V = m.solve(2.0, k=6)
    r = m.line_params(b[0], V[:, 0])
    print(he, m.N, [round(x.real/(m.w/fw2d.C0), 5) for x in b], {k: round(abs(v), 3) for k, v in r.items()}, flush=True)
