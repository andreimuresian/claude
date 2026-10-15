"""Signal and ground z-current through every node plane of the cell, for the driven current at beta
(mom_cell's mode when beta is its root).  Phase-normalised by exp(j beta z).  A CPW mode has
I_gnd = -I_sig on every plane; at the tee centre the ground current can only pass the outer rim.
usage: python diag_planes.py f_GHz n   (lossless Si; Z cached as in diag_scan.py)"""
import os, sys
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np, pandas as pd
import stack as S, tee3d as T, tee3d_solve as TS

d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
fG, n = float(sys.argv[1]), complex(sys.argv[2])
g = dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=d.W1*1e-6, W2=d.W2*1e-6, L1=d.L1*1e-6, L2=d.L2*1e-6)
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
line = TS.Stack(fG*1e9, L, bot, np.sqrt(28*43))
c = T.Cell(g, hmin=1.5e-6, hmax=12e-6, hz_min=4e-6, hz_max=10e-6)
scr = os.environ.get("SCR", ".")
sol = TS.Solver(c, line, verbose=False, cache=f"{scr}/zdiag_r49tee{fG:.0f}_lossless")
beta = n*line.k0
J = np.linalg.solve(sol.Z(beta), sol.y)
nz = len(c.Zg) - 1
Is = np.zeros(nz, complex); Ig = np.zeros(nz, complex); Ir = np.zeros(nz, complex)
for i, key in enumerate(c.bkey):
    if key[0] != "tp" or c.btype[i] != "tz":            # pure z-current edges only (not the ones
        continue                                        # turning onto a slot end wall)
    (dd, a, b), k = key[1], key[2]
    if dd == "x":
        x0, x1, w = c.X[a], c.X[a + 1], c.X[a + 1] - c.X[a]
    else:
        x0 = x1 = c.X[a]; w = c.Y[b + 1] - c.Y[b]
    p, f, coef = next((p, f, cf) for p, f, cf in c.B[i] if c.pieces[p][3] == "z")
    v = w*np.sign(coef)*J[i]*(np.exp(1j*beta*c.P) if k == 0 else 1.0)
    if x1 <= c.xs["x_si"] + 1e-12:
        Is[k] += v
    elif x0 >= c.xs["x_gi"] - 1e-12:
        Ig[k] += v
        if x0 >= c.xs["xb2"] - 1e-12:
            Ir[k] += v
zc = c.Zg[:-1]
ph = np.exp(1j*beta*zc)
print(f"{fG:.0f} GHz, n {n}: per node plane (signal, both halves of the x mirror counted the same way)")
print(f"{'z um':>7} {'I_sig':>18} {'I_gnd/I_sig':>18} {'rim share of I_gnd':>18}")
for k in range(nz):
    print(f"{zc[k]*1e6:7.1f} {complex(Is[k]*ph[k]):18.4f} {complex(Ig[k]/Is[k]):18.4f} {complex(Ir[k]/Ig[k]) if Ig[k] else 0:18.4f}")
