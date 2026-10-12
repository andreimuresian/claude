"""mom_code (2D) on the cross-section mesh of tee3d.Cell (its x/y grid lines, mirrored): the exact
reference for the plain-cell check of the general periodic code."""
import sys
import numpy as np, pandas as pd
import mom2d as M, stack as S, fw, tee3d as T


def geometry_from_cell(cell):
    X, Y = cell.X, cell.Y
    xs = cell.xs
    Xf = np.r_[-X[:0:-1], X]                                  # full x grid
    rects = [(-xs["x_si"], xs["x_si"], 0, Y[-1]), (xs["x_gi"], xs["x_go"], 0, Y[-1]), (-xs["x_go"], -xs["x_gi"], 0, Y[-1])]
    g = M.Geometry.__new__(M.Geometry)
    P0, P1, owner, sn, en = [], [], [], [], []
    nodes = 0; g.rect_seg = []
    for r, (x0, x1, y0, y1) in enumerate(rects):
        xin = Xf[(Xf >= x0 - 1e-12) & (Xf <= x1 + 1e-12)]; yin = Y
        pts = [(x, y0) for x in xin[:-1]] + [(x1, y) for y in yin[:-1]] + [(x, y1) for x in xin[::-1][:-1]] + [(x0, y) for y in yin[::-1][:-1]]
        pts = np.array(pts); n = len(pts); first = len(P0)
        for i in range(n):
            P0.append(pts[i]); P1.append(pts[(i + 1) % n]); owner.append(r); sn.append(nodes + i); en.append(nodes + (i + 1) % n)
        g.rect_seg.append(np.arange(first, first + n)); nodes += n
    g.p0, g.p1 = np.array(P0), np.array(P1)
    g.owner, g.sn, g.en = np.array(owner), np.array(sn), np.array(en)
    g.L = np.linalg.norm(g.p1 - g.p0, axis=1); g.t = (g.p1 - g.p0)/g.L[:, None]
    g.nseg, g.nnode = len(g.L), nodes
    u, w = M.GL; g.qu, g.qw = 0.5*(u + 1), 0.5*w
    g.qp = g.p0[:, None, :] + g.qu[None, :, None]*(g.p1 - g.p0)[:, None, :]
    return g


if __name__ == "__main__":
    d = pd.read_excel("../mom/data/EVALUATED_FULL_LHS_DATASET.xlsx").loc[49]
    hmin = float(sys.argv[1])*1e-6 if len(sys.argv) > 1 else 0.4e-6
    cell = T.Cell(dict(WS=d.WS*1e-6, GAP=d.GAP*1e-6, MTX=d.MTX*1e-6, W1=0, W2=0, L1=0, L2=0), hmin=hmin, hmax=20*hmin)
    g = geometry_from_cell(cell); nn = g.nnode
    for fG in (20, 60, 100):
        f = fG*1e9
        L, bot = S.tfln_layers(0.46e-6 - d.ETCH_DEPTH*1e-6, 11.7 - 1j*2.5e-4/(2*np.pi*f*M.EPS0))
        ln = fw.Line2D(g, f, L, bot, np.sqrt(28*43), kq=dict(k_lin=2e6, dk=2e3, ratio=1.02, kmax=1e7))
        b, _ = fw.find_mode(ln, 1.95)
        y = np.zeros(nn + g.nseg); y[nn:][g.owner == 0] = g.L[g.owner == 0]
        J = fw.mode_current(ln.Z(b), y); Jb = J.copy(); Jb[nn:] *= -1
        Zpi, _ = fw.impedance(ln.Z, b, J, Jb, 1.0)
        print(f"{fG} GHz, 2D on the cell mesh ({g.nseg} seg): n {b.real/ln.k0:.5f}  alpha {-b.imag*8.686/100:.5f}  Z {Zpi.real:.3f}", flush=True)
