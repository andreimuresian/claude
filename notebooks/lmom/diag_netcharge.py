"""Net z-current and net charge per cell of the driven mode (m = 0 harmonic at kx = 0), relative to
the signal's own.  A quasi-TEM CPW mode carries none (signal +I, grounds -I/2 each); any net part
radiates into the Si half-space like a single wire, at any frequency.
usage: python diag_netcharge.py f_GHz n_real {tee|plain}   (Z cached as in diag_finite_rad.py)"""
import os, sys
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
from scipy import sparse
import stack as S, tee3d as T, tee3d_solve as TS, tee3d_kern as K

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, nr, kind = float(sys.argv[1]), complex(sys.argv[2]), sys.argv[3]
tee = kind == "tee"
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6,
         W1=d.W1*1e-6*tee, W2=d.W2*1e-6*tee, L1=d.L1*1e-6*tee, L2=d.L2*1e-6*tee)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(fG*1e9, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(cell, line, verbose=True, cache=f"{scr}/zdiag_r49{kind}{fG:.0f}_lossless")
beta = nr*line.k0
Z = sol.Z(beta)
J = np.linalg.solve(Z, sol.y)
xs = sol.xs; rows, cols, coef, zf = sol.pm
Cz = K.zspec(cell, beta + 0j, +1)
a = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, cell.N)) @ J      # piece amplitudes
s0 = xs.spectra(np.array([0j]), np.array([0j]), +1)[0]                             # piece integrals
sig = xs.xmax <= cell.xs["x_si"] + 1e-12
gin = (xs.xmin >= cell.xs["x_gi"] - 1e-12)
print(f"{fG:.0f} GHz {kind}, n {nr}, N {cell.N}")
for c, name in ((2, "J_z"), (3, "charge"), (1, "J_y")):
    m = xs.comp == c
    tot = np.sum(s0[m]*a[m]); ss = np.sum(s0[m & sig]*a[m & sig]); gg = np.sum(s0[m & gin]*a[m & gin])
    print(f"  {name:6}: signal {abs(ss):.4e}  grounds/signal {gg/ss:+.5f}{'':2} net/signal {tot/ss:+.5f}  |net/signal| {abs(tot/ss):.5f}")
