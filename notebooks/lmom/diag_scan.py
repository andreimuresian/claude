"""Driven response along real beta: h = y^T Z^-1 y and the net current of J = Z^-1 y.
A guided (low-loss) pole shows as a sharp peak in |h| with a phase swing of pi.
usage: python diag_scan.py f_GHz n1 n2 ... (lossless Si; Z cached)"""
import os, sys
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
from scipy import sparse
import stack as S, tee3d as T, tee3d_solve as TS, tee3d_kern as K

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG = float(sys.argv[1])
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(fG*1e9, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(cell, line, verbose=False, cache=f"{scr}/zdiag_r49tee{fG:.0f}_lossless")
k0 = line.k0
xs = sol.xs; rows, cols, coef, zf = sol.pm
s0 = xs.spectra(np.array([0j]), np.array([0j]), +1)[0]
zc = xs.comp == 2
sig = xs.xmax <= cell.xs["x_si"] + 1e-12
print(f"{'n':>8} {'|h|':>11} {'arg h':>8} {'net/signal':>18}", flush=True)
for t in sys.argv[2:]:
    beta = complex(t)*k0
    J = np.linalg.solve(sol.Z(beta), sol.y)
    h = sol.y @ J
    Cz = K.zspec(cell, beta, +1)
    a = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, cell.N)) @ J
    ss = np.sum(s0[zc & sig]*a[zc & sig]); tot = np.sum(s0[zc]*a[zc])
    print(f"{t:>8} {abs(h):11.4e} {np.degrees(np.angle(h)):8.1f} {complex(tot/ss):18.4f}", flush=True)
