"""mom_cell (general tee code) on the plain line, row 49, PEC: must reproduce the plain cell / 2D."""
import sys, time
import numpy as np, pandas as pd
import stack as S, tee3d as T, tee3d_solve as TS
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=0.0, W2=0.0, L1=0.0, L2=0.0)
fG = float(sys.argv[1]) if len(sys.argv) > 1 else 60
hmin = float(sys.argv[2])*1e-6 if len(sys.argv) > 2 else 0.4e-6
f = fG*1e9
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*8.8541878128e-12))
line = TS.Stack(f, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=hmin, hmax=20*hmin)
t0 = time.time()
sol = TS.Solver(cell, line)
r = sol.solve(1.95)
print(f"{fG:.0f} GHz hmin {hmin*1e6:.1f} um, N {cell.N}: n {r['n']:.5f}  alpha {r['alpha']:.5f} dB/cm  Z {r['Z'].real:.3f} {r['Z'].imag:+.3f}j  ({time.time()-t0:.0f} s)")
