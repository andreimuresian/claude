"""Radiation into the Si half-space of a finite piece (N cells) of the infinite line's current,
from mom_cell's own m = 0 kernel.  Row 49 tee, PEC, lossless Si, real beta.
rho(kz) = J^H H(kz) J, H = Hermitian part of the reflected kernel restricted to its radiating
region |kx| < sqrt(eps_Si k0^2 - kz^2), assembled with the cell's z spectra at kz.
Infinite line, per cell: rho(beta) / P.  N cells: int dkz/(2 pi) |F_N(kz)|^2 rho(kz),
F_N = sum_n exp(j (kz - beta) n P).  R_N = (N-cell power) / (N x per-cell power).
usage: python diag_finite_rad.py f_GHz n_real"""
import os, sys, time
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
from scipy import sparse
import stack as S, tee3d as T, tee3d_solve as TS, tee3d_kern as K

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, nr = float(sys.argv[1]), float(sys.argv[2])
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6)
f = fG*1e9
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(f, L, bot, np.sqrt(28*43))
cell = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(cell, line, verbose=True, cache=f"{scr}/zdiag_r49tee{fG:.0f}_lossless")
k0, P = line.k0, cell.P
beta = nr*k0
J = np.linalg.solve(sol.Z(beta), sol.y)
xs = sol.xs; rows, cols, coef, zf = sol.pm
ksi = np.sqrt(line.eps_bot.real)*k0


def H_of(kz):
    kb = np.sqrt(ksi**2 - kz**2)
    u, wu = np.polynomial.legendre.leggauss(200); u, wu = 0.5*(u + 1), 0.5*wu
    kk = kb*(1 - (1 - u)**2); ww = kb*2*(1 - u)*wu             # clustered at the branch point
    grid = (np.r_[-kk[::-1], kk], np.r_[ww[::-1], ww])
    old = K.spec_grid, K.COMPLEX_PATH
    K.spec_grid = lambda *a, **k: grid; K.COMPLEX_PATH = False
    try:
        X = K.spec_kernel(xs, line, kz + 0j, kref=ksi)
    finally:
        K.spec_grid, K.COMPLEX_PATH = old
    Tz, Cz = K.zspec(cell, kz + 0j, -1), K.zspec(cell, kz + 0j, +1)
    V = sparse.csr_matrix((coef*Tz[zf], (rows, cols)), shape=(xs.n, cell.N))
    W = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, cell.N))
    Zv = V.T @ (W.T @ X.T).T
    return -(J.conj() @ ((Zv + Zv.conj().T)/2) @ J).real


t0 = time.time()
u, wu = np.polynomial.legendre.leggauss(48)
kzs = ksi*np.sin(0.5*np.pi*u)                   # (-k_Si, k_Si), clustered at the ends
wz = ksi*0.5*np.pi*np.cos(0.5*np.pi*u)*wu
rho = np.array([H_of(k) for k in kzs])
rb = H_of(beta)
print(f"rho(kz) on {len(kzs)} points: {time.time() - t0:.0f} s;  rho(beta) {rb:.4e}, max rho {rho.max():.4e}"
      f" at kz/k0 {kzs[np.argmax(rho)]/k0:+.3f};  rho(-beta) {H_of(-beta):.4e}")
for i in range(0, len(kzs), 4):
    print(f"   kz/k0 {kzs[i]/k0:+.3f}  rho {rho[i]:.4e}")
print(f"{fG:.0f} GHz, n {nr}: k_Si - beta = {ksi - beta:.0f} rad/m  (2 pi / that = {2*np.pi/(ksi - beta)*1e3:.1f} mm)")
np.save(f"{scr}/rho_{fG:.0f}.npy", np.c_[kzs, rho])
from scipy.interpolate import CubicSpline
th = np.arcsin(kzs/ksi)                          # rho is smooth in theta (sqrt edges)
sp = CubicSpline(th, rho)
td = np.linspace(-np.pi/2, np.pi/2, 200001)
kd, wd, rd = ksi*np.sin(td), ksi*np.cos(td)*(td[1] - td[0]), np.maximum(sp(td), 0)
Pinf = rb/P
prev = None
for N in (1, 2, 3, 5, 7, 10, 20, 50, 100, 300):
    FN = (np.sin(N*(kd - beta)*P/2)/np.sin((kd - beta)*P/2))**2
    PN = np.sum(wd*FN*rd)/(2*np.pi)
    print(f"   N {N:4d} ({N*0.2:5.1f} mm): R_N = {PN/(N*Pinf):.4f}" +
          (f"   added cells radiate {(PN - prev[1])/((N - prev[0])*Pinf):.4f} x the infinite-line rate" if prev else ""))
    prev = (N, PN)
