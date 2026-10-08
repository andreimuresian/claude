"""Full-wave 2D mode solver of the uniform (no-tee) line, open boundaries (PML).

Step FW1 of the full-wave periodic cell: the z-invariant line is the
building block, and it has its own CST targets (no-tee 400/600 um lines,
PEC, line-line and port de-embedding in ../qs3d/zbloch_row49.py):
    20 GHz: n 1.969, alpha 0.000 dB/cm, Z 36.40 ohm
    60 GHz: n 1.972, alpha 0.109 dB/cm, Z 36.33 ohm
   100 GHz: n 1.972, alpha 0.144 dB/cm, Z 36.12 ohm

Yee FDFD on a graded tensor grid in the cross-section (x lateral, y
vertical), fields ~ exp(j w t - gamma z), gamma = alpha + j beta.
    curl E = -j w mu0 H,  curl H = j w eps E,  d/dz -> -j beta
Ez and Hz are eliminated; the transverse equations give
    -beta^2 e = J^-1 A J^-1 B e,   e = [Ex, Ey]
(A, B below; J [u, v] = [v, -u]).  Complex beta: alpha = -Im beta.
Metal: thick PEC, E tangential to and inside the metal set to zero.
Stack as CST: air / LN slab (28, 43, 43) / SiO2 / Si 550 um / Si half-space.
Open boundaries: stretched-coordinate PML on all four sides (PEC behind).
"""
import os
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import eigs

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "mom"))
import stack_params as sp

C0, EPS0, MU0 = sp.C0, sp.EPS0, sp.MU0
EPS_LN = (28.0, 43.0, 43.0)           # (lateral x, vertical y, along-line z)


def axis(points, hmin, hmax, growth=1.25):
    """Graded axis through sorted break points: hmin at every break, growing to hmax."""
    pts = sorted(set(points))
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = b - a
        # symmetric grading from both ends
        left, h = [], hmin
        s = 0.0
        while s + h < L/2:
            left.append(h); s += h; h = min(h*growth, hmax)
        rem = L - 2*s
        n = max(1, int(np.ceil(rem/hmax)))
        steps = left + [rem/n]*n + left[::-1]
        out += list(a + np.cumsum(steps))
        out[-1] = b
    return np.array(out)


def pml_s(nodes, inner, outer_lo, outer_hi, w, smax=12.0, p=3):
    """Complex stretch factor at given coordinates (1 inside [inner])."""
    lo, hi = inner
    d = np.where(nodes < lo, (lo - nodes)/(lo - outer_lo), np.where(nodes > hi, (nodes - hi)/(outer_hi - hi), 0.0))
    return 1.0 - 1j*smax*np.clip(d, 0, 1)**p


class Mode2D:
    def __init__(self, g, f, metal="pec", h_edge=0.1e-6, side=600e-6, top=600e-6, si_extra=200e-6,
                 pml=500e-6, hmax=25e-6, smax=12.0):
        self.f, self.w = f, 2*np.pi*f
        WS, GAP, MTX, tLN = g["WS"], g["GAP"], g["MTX"], g["t_LN"]
        WG = 70e-6
        x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + WG
        yL, yB, yS = -tLN, -tLN - sp.BOX_H, -tLN - sp.BOX_H - sp.SI_H
        X1 = x_go + side
        Ytop, Ybot = MTX + top, yS - si_extra
        xb = [-X1 - pml, -X1, -x_go, -x_gi, -x_si, 0.0, x_si, x_gi, x_go, X1, X1 + pml]
        yb = [Ybot - pml, Ybot, yS, yB, yL, 0.0, MTX, Ytop, Ytop + pml]
        xn = axis(xb, h_edge, hmax)
        yn = axis(yb, min(h_edge, tLN/3), hmax)
        self.xn, self.yn = xn, yn
        self.box = (X1, Ybot, Ytop)
        self.geo = dict(x_si=x_si, x_gi=x_gi, x_go=x_go, MTX=MTX, yL=yL, yB=yB, yS=yS)
        nx, ny = len(xn), len(yn)
        xc, yc = 0.5*(xn[1:] + xn[:-1]), 0.5*(yn[1:] + yn[:-1])
        # stretched spacings: primal (between nodes) and dual (between cell centres)
        sxc = pml_s(xc, (-X1, X1), -X1 - pml, X1 + pml, self.w, smax)
        syc = pml_s(yc, (Ybot, Ytop), Ybot - pml, Ytop + pml, self.w, smax)
        sxn = pml_s(xn, (-X1, X1), -X1 - pml, X1 + pml, self.w, smax)
        syn = pml_s(yn, (Ybot, Ytop), Ybot - pml, Ytop + pml, self.w, smax)
        dx = np.diff(xn)*sxc; dy = np.diff(yn)*syc                       # primal edges
        dxd = np.r_[dx[0]/2, 0.5*(dx[1:] + dx[:-1]), dx[-1]/2]           # dual, at nodes
        dyd = np.r_[dy[0]/2, 0.5*(dy[1:] + dy[:-1]), dy[-1]/2]
        # materials per primal cell (nx-1, ny-1): eps tensors
        XC, YC = np.meshgrid(xc, yc, indexing="ij")
        ex = np.ones(XC.shape, complex); ey = ex.copy(); ez = ex.copy()
        ln = (YC > yL) & (YC < 0)
        ex[ln], ey[ln], ez[ln] = EPS_LN
        ox = (YC > yB) & (YC < yL)
        ex[ox] = ey[ox] = ez[ox] = sp.EPS_SIO2
        eps_si = sp.EPS_SI - 1j*sp.SIGMA_SI/(self.w*EPS0)
        si = YC < yB
        ex[si] = ey[si] = ez[si] = eps_si
        # metal nodes (closed rectangles)
        XN, YN = np.meshgrid(xn, yn, indexing="ij")
        tol = 1e-12
        inm = (YN >= -tol) & (YN <= MTX + tol)
        ax = np.abs(XN)
        mnode = inm & ((ax <= x_si + tol) | ((ax >= x_gi - tol) & (ax <= x_go + tol)))
        # unknown layout: Ex at (i+1/2, j): (nx-1, ny); Ey at (i, j+1/2): (nx, ny-1);
        # Ez at (i, j): (nx, ny); Hx at (i, j+1/2); Hy at (i+1/2, j); Hz at (i+1/2, j+1/2)
        nEx, nEy, nEz = (nx - 1)*ny, nx*(ny - 1), nx*ny
        # permittivities at E locations (arithmetic average of adjacent cells, weighted)
        def avg_y(e):   # cell (nx-1, ny-1) -> Ex points (nx-1, ny)
            w = np.abs(np.diff(yn))
            num = np.zeros((nx - 1, ny), complex); den = np.zeros((nx - 1, ny))
            num[:, :-1] += e*w; den[:, :-1] += w
            num[:, 1:] += e*w; den[:, 1:] += w
            return num/den
        def avg_x(e):   # -> Ey points (nx, ny-1)
            w = np.abs(np.diff(xn))[:, None]
            num = np.zeros((nx, ny - 1), complex); den = np.zeros((nx, ny - 1))
            num[:-1] += e*w; den[:-1] += w
            num[1:] += e*w; den[1:] += w
            return num/den
        def avg_xy(e):  # -> nodes (nx, ny)
            w = np.abs(np.diff(xn))[:, None]*np.abs(np.diff(yn))[None, :]
            num = np.zeros((nx, ny), complex); den = np.zeros((nx, ny))
            for a in (0, 1):
                for b in (0, 1):
                    num[a:nx - 1 + a, b:ny - 1 + b] += e*w; den[a:nx - 1 + a, b:ny - 1 + b] += w
            return num/den
        epx, epy, epz = avg_y(ex), avg_x(ey), avg_xy(ez)
        # PEC: zero E on/in metal
        mEx = mnode[:-1, :] & mnode[1:, :]
        mEy = mnode[:, :-1] & mnode[:, 1:]
        mEz = mnode.copy()
        # outer PEC walls (behind the PML)
        mEx[:, 0] = mEx[:, -1] = True; mEy[0, :] = mEy[-1, :] = True
        mEz[0, :] = mEz[-1, :] = mEz[:, 0] = mEz[:, -1] = True
        I = lambda n: sparse.identity(n, format="csr")
        def D(n, h):     # forward difference n nodes -> n-1 edges, spacing h (n-1)
            return sparse.diags([-1/h, 1/h], [0, 1], shape=(n - 1, n), format="csr")
        # E-derivatives (node/edge -> dual), H-derivatives = -adjoint pattern with dual spacing
        DxE_ez = sparse.kron(D(nx, dx), I(ny))                 # Ez(nx,ny) -> (nx-1, ny)  [Hy loc]
        DyE_ez = sparse.kron(I(nx), D(ny, dy))                 # Ez -> (nx, ny-1)         [Hx loc]
        DxE_ey = sparse.kron(D(nx, dx), I(ny - 1))             # Ey(nx,ny-1) -> (nx-1,ny-1) [Hz loc]
        DyE_ex = sparse.kron(I(nx - 1), D(ny, dy))             # Ex(nx-1,ny) -> (nx-1,ny-1) [Hz loc]
        # H derivatives: backward differences on dual spacing; H fields live on dual,
        # boundary H outside are zero (PEC walls), so use -D^T scaled by dual spacing
        def Dh(n, hd):   # (n-1) dual values -> n nodes : (H_i - H_{i-1}) / hd_i
            M = sparse.diags([1.0*np.ones(n - 1), -1.0*np.ones(n - 1)], [0, -1], shape=(n, n - 1), format="csr")
            return sparse.diags(1/hd) @ M
        DxH_hy = sparse.kron(Dh(nx, dxd), I(ny))               # Hy(nx-1,ny) -> (nx,ny)   [Ez loc]
        DyH_hx = sparse.kron(I(nx), Dh(ny, dyd))               # Hx(nx,ny-1) -> (nx,ny)   [Ez loc]
        DxH_hz = sparse.kron(Dh(nx, dxd), I(ny - 1))           # Hz(nx-1,ny-1) -> (nx,ny-1) [Ey loc]
        DyH_hz = sparse.kron(I(nx - 1), Dh(ny, dyd))           # Hz -> (nx-1, ny)          [Ex loc]
        w = self.w
        jw = 1j*w
        iez = np.where(mEz.ravel(), 0.0, 1.0/(jw*EPS0*epz.ravel()))
        # Ez = (jw eps_z)^-1 (DxH Hy - DyH Hx);  h = [Hx, Hy]
        Ez_of_h = sparse.diags(iez) @ sparse.hstack([-DyH_hx, DxH_hy])
        # Hz = (-jw mu)^-1 (DxE Ey - DyE Ex);    e = [Ex, Ey]
        Hz_of_e = (-1/(jw*MU0))*sparse.hstack([-DyE_ex, DxE_ey])
        # jb J e = A h,  J e = [Ey; -Ex]: from  -jw mu Hx = DyE Ez + jb Ey ;  -jw mu Hy = -jb Ex - DxE Ez
        nHx, nHy = nx*(ny - 1), (nx - 1)*ny
        A = -jw*MU0*sparse.identity(nHx + nHy) - sparse.vstack([DyE_ez, -DxE_ez]) @ Ez_of_h
        # jb J h = B e,  J h = [Hy; -Hx]: from  jw eps Ex = DyH Hz + jb Hy ;  jw eps Ey = -jb Hx - DxH Hz
        B = sparse.diags(np.r_[jw*EPS0*epx.ravel(), jw*EPS0*epy.ravel()]) - sparse.vstack([DyH_hz, -DxH_hz]) @ Hz_of_e
        # J for e (rows ordered [Ex; Ey]) maps e -> [Ey; -Ex]: shapes differ, so write the
        # equations directly: rows of A are ordered [Hx-eq ~ Ey, Hy-eq ~ -Ex]
        # A h = jb [Ey; -Ex]  ->  [Ex; Ey] = (1/jb) Pe A h,  Pe = [[0, -I], [I, 0]] on (Hx-rows, Hy-rows)
        Pe = sparse.bmat([[None, -sparse.identity(nEx)], [sparse.identity(nEy), None]])   # rows: Ex, Ey
        # B e = jb [Hy; -Hx]  ->  [Hx; Hy] = (1/jb) Ph B e,  Ph = [[0, -I], [I, 0]] on (Ex-rows, Ey-rows)
        Ph = sparse.bmat([[None, -sparse.identity(nHx)], [sparse.identity(nHy), None]])
        # check shapes: A rows = [Hx(nHx); Hy(nHy)] locations... rows of A: first block from DyE_ez (Hx loc, nHx)
        Mfull = (Pe @ A @ Ph @ B).tocsr()                      # (jb)^2 e = M e
        free = ~np.r_[mEx.ravel(), mEy.ravel()]
        S = sparse.identity(nEx + nEy, format="csr")[np.where(free)[0]]
        self.M = (S @ Mfull @ S.T).tocsc()
        self.S, self.free = S, free
        self.shape = dict(nx=nx, ny=ny, nEx=nEx, nEy=nEy)
        self.ops = dict(Ez_of_h=Ez_of_h, Hz_of_e=Hz_of_e, Ph=Ph, B=B, epx=epx, epy=epy)
        self.nodes = (xn, yn)
        self.N = self.M.shape[0]

    def solve(self, n_guess=2.0, k=4):
        k0 = self.w/C0
        sig = -(n_guess*k0)**2                                  # (jb)^2 = -b^2
        vals, vecs = eigs(self.M, k=k, sigma=sig, which="LM")
        beta = np.sqrt(-vals)
        beta = np.where(beta.real < 0, -beta, beta)
        order = np.argsort(np.abs(beta/k0 - n_guess))
        return beta[order], vecs[:, order]

    def fields(self, beta, v):
        """E and H on the Yee grid for one mode, scaled to V = 1 across the right gap."""
        e = self.S.T @ v
        jb = 1j*beta
        h = (self.ops["Ph"] @ (self.ops["B"] @ e))/jb
        nx, ny = self.shape["nx"], self.shape["ny"]
        nEx = self.shape["nEx"]
        Ex = e[:nEx].reshape(nx - 1, ny); Ey = e[nEx:].reshape(nx, ny - 1)
        nHx = nx*(ny - 1)
        Hx = h[:nHx].reshape(nx, ny - 1); Hy = h[nHx:].reshape(nx - 1, ny)
        return Ex, Ey, Hx, Hy

    def line_params(self, beta, v):
        """n, alpha [dB/cm] and Z0 three ways: V/I, |V|^2/2P, 2P/|I|^2.
        V: integral of Ex across the right gap at metal mid-height.  I: loop of H
        around the signal on dual grid lines half-way into the gaps.  P: Poynting
        flux over the region inside the PML."""
        xn, yn = self.nodes
        g = self.geo
        Ex, Ey, Hx, Hy = self.fields(beta, v)
        dxn, dyn = np.diff(xn), np.diff(yn)
        dxd = np.r_[dxn[0]/2, 0.5*(dxn[1:] + dxn[:-1]), dxn[-1]/2]
        dyd = np.r_[dyn[0]/2, 0.5*(dyn[1:] + dyn[:-1]), dyn[-1]/2]
        j = int(np.argmin(np.abs(yn - g["MTX"]/2)))
        xm = 0.5*(xn[1:] + xn[:-1])
        sel = (xm > g["x_si"]) & (xm < g["x_gi"])
        V = np.sum(Ex[sel, j]*dxn[sel])
        # loop: dual columns ia, ib (x half-way into the gaps), dual rows ja, jt
        xmid = (g["x_si"] + g["x_gi"])/2
        ia, ib = int(np.argmin(abs(xm + xmid))), int(np.argmin(abs(xm - xmid)))
        ym = 0.5*(yn[1:] + yn[:-1])
        ja, jt = int(np.argmin(abs(ym - g["yL"]/2))), int(np.argmin(abs(ym - (g["MTX"] + 3e-6))))
        I = (np.sum(Hx[ia + 1:ib + 1, ja]*dxd[ia + 1:ib + 1]) + np.sum(Hy[ib, ja + 1:jt + 1]*dyd[ja + 1:jt + 1])
             - np.sum(Hx[ia + 1:ib + 1, jt]*dxd[ia + 1:ib + 1]) - np.sum(Hy[ia, ja + 1:jt + 1]*dyd[ja + 1:jt + 1]))
        # Poynting flux inside the PML-free box
        X1 = self.box[0]; yb0, yb1 = self.box[1], self.box[2]
        mx = (np.abs(xm) < X1)[:, None] & ((yn > yb0) & (yn < yb1))[None, :]
        my = (np.abs(xn) < X1)[:, None] & ((ym > yb0) & (ym < yb1))[None, :]
        P = 0.5*(np.sum((Ex*np.conj(Hy)*dxn[:, None]*dyd[None, :])[mx])
                 - np.sum((Ey*np.conj(Hx)*dxd[:, None]*dyn[None, :])[my]))
        k0 = self.w/C0
        n, a = beta.real/k0, -beta.imag*8.686/100
        return dict(n=n, alpha=a, Z_VI=V/I, Z_PV=abs(V)**2/(2*P.real), Z_PI=2*P.real/abs(I)**2)
