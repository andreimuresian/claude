import sys
import pandas as pd
sys.path.insert(0, "../mom")
import stack_params as sp, fw2d
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, t_LN=sp.TFLN - d.ETCH_DEPTH*1e-6)
he = float(sys.argv[1])
for f in [float(x)*1e9 for x in sys.argv[2:]]:
    m = fw2d.Mode2D(g, f, smax=0, homog=4.0, wall_ground=True, h_edge=he, side=200e-6, top=200e-6, si_extra=0, pml=50e-6)
    b, V = m.solve(2.0, k=2)
    r = m.line_params(b[0], V[:, 0])
    print(he, f/1e9, round(r["n"], 6), round(r["Z_VI"].real, 3), flush=True)
