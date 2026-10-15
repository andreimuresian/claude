"""Plain row-49 cross-section (2D layered MoM): look for an even mode other than the CPW mode near
n0 (the common / antenna mode of three strips on the air/Si interface), and its ground return.
usage: python diag_common2d.py f_GHz n0 [n0 ...]"""
import sys, time
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw
d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
WS, GAP, t = d.WS*1e-6, d.GAP*1e-6, d.MTX*1e-6
xs, xg, xo = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
g = M.Geometry([(-xs, xs, 0, t), (xg, xo, 0, t), (-xo, -xg, 0, t)], 0.4e-6, 8e-6)
fG = float(sys.argv[1]); f = fG*1e9
L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 + 0j)
ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=2e8))
for s in sys.argv[2:2]:
    t0 = time.time()
    try:
        b, it = fw.find_mode(ln, complex(s))
        print(f"{fG:.0f} GHz, start {s}: n {b.real/ln.k0:.5f}  alpha {-b.imag*8.686/100:.4f} dB/cm  ({it} it, {time.time() - t0:.0f} s)", flush=True)
    except Exception as e:
        print(f"start {s}: {e}", flush=True)

# deflated search with a common-mode drive (J_z on all three strips)
bc = fw.find_mode(ln, 1.95)[0]
y = np.zeros(ln.Z(bc).shape[0]); nn = g.nnode
y[nn:] = g.L
gc = lambda b: ln.gfun(b, y)/(b - bc)
k0 = ln.k0
for s in ("2.5-0.05j", "2.3-0.2j", "2.6-0.02j"):
    b0, b1 = complex(s)*k0, (complex(s) + 0.01)*k0
    g0, g1 = gc(b0), gc(b1)
    for it in range(15):
        b2 = b1 - g1*(b1 - b0)/(g1 - g0)
        if abs(b2 - b1) < 1e-7*abs(b1):
            break
        b0, g0, b1, g1 = b1, g1, b2, gc(b2)
    J = np.linalg.solve(ln.Z(b2), y)
    zs = J[nn:]*g.L
    Is, Ig = zs[g.owner == 0].sum(), zs[g.owner != 0].sum()
    print(f"deflated common drive from {s}: n {b2.real/k0:.5f}  alpha {-b2.imag*8.686/100:.4f} dB/cm  ({it} it)"
          f"  I_gnd/I_sig {complex(Ig/Is):.3f}", flush=True)
