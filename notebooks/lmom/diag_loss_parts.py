"""Where does the tee cell's loss come from?  Row 49, PEC, lossless Si (sigma = 0), real beta.
With nothing lossy, J^H Z J can only have a real (dissipative) part through radiation into the
Si half-space, i.e. the m = 0 reflected kernel in its visible region |kx| < sqrt(eps_Si k0^2 - beta^2);
all other harmonics are evanescent everywhere.  The driven current J = Z^-1 y is split by kernel part:
static (Bloch image sums), m = 0 reflected, m = 0 dynamic correction, other harmonics.
usage: python diag_loss_parts.py f_GHz n_real [tee|plain]"""
import os, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
from scipy import sparse
import stack as S, tee3d as T, tee3d_solve as TS, tee3d_kern as K

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, nr = float(sys.argv[1]), float(sys.argv[2])
tee = (sys.argv[3] if len(sys.argv) > 3 else "tee") == "tee"
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6,
         W1=d.W1*1e-6*tee, W2=d.W2*1e-6*tee, L1=d.L1*1e-6*tee, L2=d.L2*1e-6*tee)
f = fG*1e9
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(f, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
sol = TS.Solver(cell, line, verbose=False)
beta = nr*line.k0
t0 = time.time()
sol.sc = K.StaticCache(cell, sol.F, sol.maps, line.K, workers=4)
parts = {"static": sol.sc.Z(beta, line.w)}

xs, pm, P, k0, w = sol.xs, sol.pm, cell.P, line.k0, line.w
rows, cols, coef, zf = pm
comp = xs.comp


def assemble(X, km):
    Tz, Cz = K.zspec(cell, km, -1), K.zspec(cell, km, +1)
    V = sparse.csr_matrix((coef*Tz[zf], (rows, cols)), shape=(xs.n, cell.N))
    W = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, cell.N))
    return V.T @ (W.T @ X.T).T


K.dyn_kernel(xs, beta, k0)
kref0 = np.sqrt(line.eps_bot.real)*k0
parts["m0 reflected"] = assemble(K.spec_kernel(xs, line, beta, kref=kref0), beta)
D = K.dyn_kernel(xs, beta, k0)
same = (comp[:, None] == comp[None, :]); isq = comp == 3
A = (D["d"] + K.XSIGN[comp][None, :]*D["x"])*same
X = (-1j*w*K.MU0)*np.where(isq[:, None] | isq[None, :], 0, A)
Q = (D["d"] + D["x"]) + line.K*(D["y"] + D["xy"])
X += (-1/(1j*w*K.EPS0))*np.where(isq[:, None] & isq[None, :], Q, 0)
parts["m0 dynamic"] = assemble(X, beta)
Mmax = int(np.floor(sol.Ks*P/(2*np.pi))) + 1
ms = [m for m in range(-Mmax, Mmax + 1) if m != 0
      and not (abs(2*np.pi*m/P) + kref0 > sol.Ks and abs(m) > sol.Mc)]
import multiprocessing as mp
K._HCTX.update(cell=cell, xs=xs, line=line, beta=beta, Mc=sol.Mc, pm=pm)
order = sorted(ms, key=lambda m: abs(m))
with mp.get_context("fork").Pool(4) as pool:
    parts["m != 0"] = sum(pool.map(K._harm_part, [order[i::4] for i in range(4)]))
print(f"built in {time.time() - t0:.0f} s, N {cell.N}", flush=True)

Z = sum(parts.values())
J = np.linalg.solve(Z, sol.y)
tot = J.conj() @ Z @ J
print(f"{fG:.0f} GHz {'tee' if tee else 'plain'}, real n {nr}: J^H Z J = {tot:.4e}")
print(f"{'part':14} {'Re J^H Z J':>12} {'/ |Im total|':>12}   {'min eig of -(Z+Z^H)/2':>22}")
for k, Zp in parts.items():
    p = J.conj() @ Zp @ J
    H = -(Zp + Zp.conj().T)/2
    ev = np.linalg.eigvalsh(H)
    print(f"{k:14} {p.real:12.4e} {p.real/abs(tot.imag):12.4e}   {ev[0]:11.3e} .. {ev[-1]:10.3e}", flush=True)
