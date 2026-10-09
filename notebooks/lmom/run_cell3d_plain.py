"""Plain periodic cell (row 49, PEC): 3D Floquet-harmonic MoM vs the 2D mode on the same contour mesh."""
import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw, cell3d as C
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
g = M.Geometry([(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)], 0.4e-6, 8e-6)
fG = float(sys.argv[1]); f = fG*1e9
runs = [tuple(int(v) for v in a.split(",")) for a in sys.argv[2:]]          # Nz,M pairs
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*M.EPS0))
ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=1e7))
t0 = time.time(); b2, _ = fw.find_mode(ln, 1.95)
n2, a2 = b2.real/ln.k0, -b2.imag*8.686/100
print(f"{fG:.0f} GHz, {g.nseg} segments.  2D: n {n2:.5f}  alpha {a2:.5f} dB/cm  ({time.time()-t0:.0f} s)", flush=True)
for Nz, Mh in runs:
    cell = C.PlainCell(ln, Nz)
    t0 = time.time(); b, it = C.find_mode(cell, n2, Mh)
    n, a = b.real/ln.k0, -b.imag*8.686/100
    print(f"  3D Nz {Nz:3d} M {Mh:4d}: n {n:.5f} ({(n/n2-1)*100:+.4f} %)  alpha {a:.5f} ({(a/a2-1)*100:+.2f} %)  "
          f"{it} it, {time.time()-t0:.0f} s", flush=True)
