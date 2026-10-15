"""As diag_modes.py, but shift-invert Arnoldi around a few target n (one LU each): fast.
usage: python diag_modes_si.py f_GHz n0 target1 [target2 ...]"""
import os, sys
import numpy as np, pandas as pd
from scipy import sparse, linalg
from scipy.sparse.linalg import eigs, LinearOperator
import stack as S, tee3d as T, tee3d_solve as TS, tee3d_kern as K

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, n0 = float(sys.argv[1]), float(sys.argv[2])
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(fG*1e9, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(cell, line, verbose=False, cache=f"{scr}/zdiag_r49tee{fG:.0f}_lossless")
k0 = line.k0
b1 = n0*k0; b2 = b1*1.001
Z1, Z2 = sol.Z(b1), sol.Z(b2)
D = (Z2 - Z1)/(b2 - b1)
xs = sol.xs; rows, cols, coef, zf = sol.pm
s0 = xs.spectra(np.array([0j]), np.array([0j]), +1)[0]
zc = xs.comp == 2
sig = xs.xmax <= cell.xs["x_si"] + 1e-12
print(f"{fG:.0f} GHz, linear model at n {n0}")
print(f"{'target':>14} {'n':>9} {'alpha dB/cm':>11} {'|I_sig|/|J|':>11} {'net/signal':>18}", flush=True)
for t in sys.argv[3:]:
    s = complex(t)*k0 - b1                                     # shift in mu = beta - b1
    lu = linalg.lu_factor(Z1 + s*D)
    op = LinearOperator(Z1.shape, matvec=lambda x: linalg.lu_solve(lu, -D @ x), dtype=complex)
    vals, V = eigs(op, k=8, which="LM")
    mu = s + 1/vals
    cur = np.abs(sol.y @ V)/np.linalg.norm(V, axis=0)
    for o in np.argsort(np.abs(mu - s)):
        beta = b1 + mu[o]
        Cz = K.zspec(cell, beta, +1)
        a = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, cell.N)) @ V[:, o]
        ss = np.sum(s0[zc & sig]*a[zc & sig]); tot = np.sum(s0[zc]*a[zc])
        print(f"{t:>14} {beta.real/k0:9.5f} {-beta.imag*8.686/100:11.4f} {cur[o]:11.3e} {complex(tot/ss):18.4f}", flush=True)
