"""mom_cell (general periodic code), one dataset row, PEC: tee cell or plain cell on the same mesh settings.
usage: python run_tee_cell.py f_GHz {tee|plain} hmin_um hmax_um hz_min_um hz_max_um n_guess [cache_prefix]
Dataset row: environment variable ROW (default 49)."""
import os, sys, time
import numpy as np, pandas as pd
import stack as S, tee3d as T, tee3d_solve as TS
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[int(os.environ.get("ROW", 49))]
fG, kind = float(sys.argv[1]), sys.argv[2]
hmin, hmax, hz0, hz1 = (float(v)*1e-6 for v in sys.argv[3:7])
n0 = float(sys.argv[7])
tee = kind == "tee"
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6,
         W1=d.W1*1e-6*tee, W2=d.W2*1e-6*tee, L1=d.L1*1e-6*tee, L2=d.L2*1e-6*tee)
f = fG*1e9
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*8.8541878128e-12))
line = TS.Stack(f, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=hmin, hmax=hmax, hz_min=hz0, hz_max=hz1)
t0 = time.time()
save = sys.argv[8] if len(sys.argv) > 8 else None
r = TS.Solver(cell, line, cache=save).solve(n0)
print(f"{fG:.0f} GHz {kind} mesh ({hmin*1e6:g}, {hmax*1e6:g}, {hz0*1e6:g}, {hz1*1e6:g}) um, N {cell.N}: "
      f"n {r['n']:.5f}  alpha {r['alpha']:.5f} dB/cm  Z {r['Z'].real:.3f} {r['Z'].imag:+.3f}j  ({time.time()-t0:.0f} s)", flush=True)
