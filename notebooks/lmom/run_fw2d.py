"""Plain line, row 49, PEC: complex mode by the layered MoM at 20 / 60 / 100 GHz vs FD and CST."""
import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
rects = [(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)]
hmin = float(sys.argv[1]) if len(sys.argv) > 1 else 0.2e-6
REF = {20: ("1.952 / 0.009", "1.969 / 0.000"), 60: ("1.954 / 0.051", "1.972 / 0.109"), 100: ("1.959 / 0.153", "1.972 / 0.144")}
g = M.Geometry(rects, hmin, 20*hmin)
for fG in (20, 60, 100):
    f = fG*1e9
    L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*M.EPS0))
    ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=2e8))
    t0 = time.time()
    b, it = fw.find_mode(ln, 1.95)
    n, a = b.real/ln.k0, -b.imag*8.686/100
    print(f"{fG:4d} GHz ({g.nseg} seg): n {n:.4f}  alpha {a:.4f} dB/cm   | FD {REF[fG][0]}  CST {REF[fG][1]}   ({it} it, {time.time()-t0:.0f} s)", flush=True)
