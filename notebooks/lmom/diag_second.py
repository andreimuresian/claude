"""Second even mode of the tee cell: zero of 1 / (h_c(beta) (beta - beta1)), h_c = y_c^T Z^-1 y_c with a
common-mode drive y_c (J_z on all conductors across plane 0) and mom_cell's root beta1 deflated.
Newton inside the linear model Z(b1) + (beta - b1) D as Solver.solve_driven, trust region per pass.
usage: python diag_second.py f_GHz n_start n_root [trust]   (lossless Si; Z cached)"""
import os, sys
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
from scipy import linalg
import stack as S, tee3d as T, tee3d_solve as TS

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, n_s, n_r = float(sys.argv[1]), complex(sys.argv[2]), complex(sys.argv[3])
trust = float(sys.argv[4]) if len(sys.argv) > 4 else 0.03
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(fG*1e9, L, bot, np.sqrt(28*43))
c = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(c, line, verbose=True, cache=f"{scr}/zdiag_r49tee{fG:.0f}_lossless")
k0 = line.k0
# common drive: every pure z-current edge on plane 0 (signal and grounds), weight = edge width
yc = np.zeros(c.N); ys = np.zeros(c.N); yg = np.zeros(c.N)
for i, key in enumerate(c.bkey):
    if key[0] != "tp" or key[2] != 0 or c.btype[i] != "tz":
        continue
    dd, a, b = key[1]
    x0, x1, w = (c.X[a], c.X[a + 1], c.X[a + 1] - c.X[a]) if dd == "x" else (c.X[a], c.X[a], c.Y[b + 1] - c.Y[b])
    p, f, coef = next((p, f, cf) for p, f, cf in c.B[i] if c.pieces[p][3] == "z")
    v = w*np.sign(coef)
    yc[i] = v
    if x1 <= c.xs["x_si"] + 1e-12:
        ys[i] = v
    else:
        yg[i] = v
br = n_r*k0
beta = n_s*k0
D = None
for it in range(12):
    b1 = beta
    Z1 = sol.Z(b1)
    if D is None:
        b2 = b1*1.001
        D = (sol.Z(b2) - Z1)/(b2 - b1)
    for _ in range(60):
        lu = linalg.lu_factor(Z1 + (beta - b1)*D)
        x = linalg.lu_solve(lu, yc); xt = linalg.lu_solve(lu, yc, trans=1)
        h = yc @ x; hp = -(xt @ (D @ x))
        F = 1/(h*(beta - br)); Fp = -(hp*(beta - br) + h)/(h*(beta - br))**2
        step = -F/Fp
        beta = beta + step
        if abs(step) < 1e-12*abs(beta):
            break
    mv = beta - b1
    if abs(mv) > trust*abs(b1):
        beta = b1 + mv*trust*abs(b1)/abs(mv)
        print(f"pass {it}: built at n {b1/k0:.5f} -> clipped to {beta/k0:.5f}", flush=True)
        continue
    J = linalg.lu_solve(linalg.lu_factor(Z1 + (beta - b1)*D), yc)
    print(f"pass {it}: built at n {b1/k0:.5f} -> n {beta.real/k0:.5f} alpha {-beta.imag*8.686/100:.4f} dB/cm"
          f"   I_gnd/I_sig {complex((yg @ J)/(ys @ J)):.3f}", flush=True)
    if abs(beta - b1) < 1e-3*abs(b1):
        break
