"""Z0 (power-current, Z_PI = N/I^2 by reciprocity) of the plain line, row 49, PEC, mom_code;
mesh convergence; vs the quasi-static value, the 2D FD solver and CST."""
import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
rects = [(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)]
FD = {20: (36.40, 36.27, 36.54), 60: (36.39, 36.15, 36.62), 100: None}       # VI, PV, PI (fw1_v2_fine)
CST = {20: 36.40, 60: 36.33, 100: 36.12}
for hmin in (0.4e-6, 0.2e-6, 0.1e-6):
    g = M.Geometry(rects, hmin, 20*hmin); nn = g.nnode
    for fG in (20, 60, 100):
        f = fG*1e9
        L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*M.EPS0))
        ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=1e7))
        t0 = time.time(); b, _ = fw.find_mode(ln, 1.95)
        y = np.zeros(2*g.nseg + 0*nn + (nn - g.nseg)); y = np.zeros(nn + g.nseg); y[nn:][g.owner == 0] = g.L[g.owner == 0]
        J = fw.mode_current(ln.Z(b), y); Jb = J.copy(); Jb[nn:] *= -1
        Zpi, N = fw.impedance(ln.Z, b, J, Jb, 1.0)
        fd = FD[fG]
        print(f"hmin {hmin*1e6:.1f} um ({g.nseg:3d} seg) {fG:3d} GHz: n {b.real/ln.k0:.5f}  Z_PI {Zpi.real:.3f} {Zpi.imag:+.3f}j ohm"
              f"   | FD PI {fd[2] if fd else '-'}  VI {fd[0] if fd else '-'}   CST {CST[fG]}   ({time.time()-t0:.0f} s)", flush=True)
