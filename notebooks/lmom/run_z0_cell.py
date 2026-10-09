"""Z0 of the plain periodic cell (mom_cell) vs mom_code on the same contour mesh (row 49, PEC)."""
import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw, cell3d as C
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
g = M.Geometry([(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)], 0.4e-6, 8e-6); nn = g.nnode
for fG in (20, 60, 100):
    f = fG*1e9
    L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*M.EPS0))
    ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=1e7))
    b2, _ = fw.find_mode(ln, 1.95)
    y = np.zeros(nn + g.nseg); y[nn:][g.owner == 0] = g.L[g.owner == 0]
    J = fw.mode_current(ln.Z(b2), y); Jb = J.copy(); Jb[nn:] *= -1
    Z2, _ = fw.impedance(ln.Z, b2, J, Jb, 1.0)
    for Nz in (4, 8):
        cell = C.PlainCell(ln, Nz); t0 = time.time()
        b3, _ = C.find_mode(cell, b2.real/ln.k0, 2*Nz)
        Z3, N3, sp = C.plain_impedance(cell, b3, 2*Nz)
        print(f"{fG:3d} GHz Nz {Nz}: mom_code Z_PI {Z2.real:.4f} | mom_cell Z_PI {Z3.real:.4f} {Z3.imag:+.4f}j "
              f"({(Z3.real/Z2.real-1)*100:+.4f} %)  n {b3.real/ln.k0:.5f} vs {b2.real/ln.k0:.5f}  "
              f"(Bloch-mode uniformity {sp[0]:.1e} {sp[1]:.1e}, {time.time()-t0:.0f} s)", flush=True)
