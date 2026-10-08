"""Full-wave periodic cell of the tee-loaded line (3D FDFD, Bloch-periodic, open boundaries).

One period P = 200 um along z, with the tee centred at z = P/2 (cell boundaries z = 0, P
midway between tees, as the CST lines' cell boundaries).  Half domain x >= 0: x = 0 is a
PMC plane (even CPW mode).  Stack as CST: air / LN slab (28, 43, 43) / SiO2 / Si 550 um /
Si half-space; stretched-coordinate PML on the open sides (x, top, bottom), PEC behind.
Thick PEC metal; the tee slots are vacuum through the full metal thickness.

Yee grid, E on edges.  Bloch condition E(z + P) = E(z) exp(-j beta P) closes z.
For a real beta the cell is a linear eigenproblem
    curl curl E = k0^2 eps E,        (mu = mu0)
whose complex k0 = w/c gives the leaky Bloch mode: n = beta c / Re w, and the
attenuation per length alpha = Im(w) / v_g with v_g = d Re w / d beta (two betas).
The PML stretch is frequency-independent, so the problem stays linear in k0^2.
Thin layers (LN slab, oxide) need not lie on grid lines: each cell's permittivity is
the sub-cell average (arithmetic for x, z; harmonic for y, the layer normal).
"""
import os
import sys

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import LinearOperator, eigs

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "mom"))
import stack_params as sp          # noqa: E402
import pardiso_c                   # noqa: E402
from fw2d import pml_s              # noqa: E402


def axis(breaks, hmax, growth=1.4):
    """Graded axis through break points.  breaks: {coordinate: local cell size}.  Cells grow
    by `growth` away from each break up to hmax; the last cell of a segment absorbs the
    remainder (never smaller than the local size / 2)."""
    pts = sorted(breaks)
    out = [pts[0]]
    for a, b in zip(pts[:-1], pts[1:]):
        L = b - a
        ha, hb = breaks[a], breaks[b]
        left, right = [], []
        sa = sb = 0.0
        while True:                                   # grow from both ends toward the middle
            if ha <= hb:
                if sa + sb + ha > L: break
                left.append(ha); sa += ha; ha = min(ha*growth, hmax)
            else:
                if sa + sb + hb > L: break
                right.append(hb); sb += hb; hb = min(hb*growth, hmax)
        steps = left + right[::-1]
        rem = L - sum(steps)
        if steps and rem < 0.5*min(steps[len(left) - 1] if left else hb, steps[len(left)] if right else ha):
            # merge a tiny remainder into the largest neighbouring step
            k = int(np.argmax(steps)); steps[k] += rem
        else:
            steps.insert(len(left), rem)
        out += list(a + np.cumsum(steps))
        out[-1] = b
    return np.array(out)

C0, EPS0 = sp.C0, sp.EPS0
P = 200e-6
EPS_LN = (28.0, 43.0, 43.0)


def layers(tLN, eps_si):
    """(y_top, y_bottom, (ex, ey, ez)) from top to bottom, below the metal plane y = 0."""
    yL, yB = -tLN, -tLN - sp.BOX_H
    return [(np.inf, 0.0, (1.0, 1.0, 1.0)), (0.0, yL, EPS_LN),
            (yL, yB, (sp.EPS_SIO2,)*3), (yB, -np.inf, (eps_si,)*3)]


def cell_eps(yn, lay):
    """Per y-cell permittivity (ny-1, 3): arithmetic x, z; harmonic y."""
    out = np.zeros((len(yn) - 1, 3), complex)
    for j, (a, b) in enumerate(zip(yn[:-1], yn[1:])):
        h = b - a
        ar = np.zeros(3, complex); hr = 0.0
        for top, bot, e in lay:
            o = max(0.0, min(b, top) - max(a, bot))
            if o > 0:
                ar += np.array(e)*o; hr += o/e[1]
        out[j] = ar[0]/h, h/hr, ar[2]/h
    return out


class Cell3D:
    def __init__(self, g, tee=True, f0=60e9, h_edge=0.4e-6, hmax=40e-6, side=400e-6, top=400e-6,
                 si_extra=150e-6, pml=300e-6, smax=12.0, hz_min=1e-6, hz_max=8e-6, growth=1.4, nz_plain=8):
        WS, GAP, MTX, tLN = g["WS"], g["GAP"], g["MTX"], g["t_LN"]
        x_si, x_gi, x_go = WS/2, WS/2 + GAP, WS/2 + GAP + 70e-6
        yS = -tLN - sp.BOX_H - sp.SI_H
        X1, Ytop, Ybot = x_go + side, MTX + top, yS - si_extra
        xb1, xb2 = x_gi + g["W1"], x_gi + g["W1"] + g["W2"]
        hf = hmax                                              # far breaks: coarse
        xbreaks = {0.0: 4*h_edge, x_si: h_edge, x_gi: h_edge, x_go: h_edge, X1: hf, X1 + pml: hf}
        if tee:
            xbreaks.update({xb1: h_edge, xb2: h_edge})
        xn = axis(xbreaks, hmax, growth)
        yn = axis({Ybot - pml: hf, Ybot: hf, yS: hf/2, -tLN - sp.BOX_H: 2*h_edge, 0.0: h_edge, MTX: h_edge,
                   Ytop: hf, Ytop + pml: hf}, hmax, growth)
        if tee:
            zb = {0.0: hz_max, P/2 - g["L2"]/2: hz_min, P/2 - g["L1"]/2: hz_min,
                  P/2 + g["L1"]/2: hz_min, P/2 + g["L2"]/2: hz_min, P: hz_max}
            zn = axis(zb, hz_max, growth)
        else:
            zn = np.linspace(0, P, int(nz_plain) + 1)
        zn = zn[:-1]                                           # z = P is z = 0 of the next cell
        hz = np.diff(np.r_[zn, P])
        nx, ny, nz = len(xn), len(yn), len(zn)
        self.xn, self.yn, self.zn, self.hz = xn, yn, zn, hz
        self.g = dict(x_si=x_si, x_gi=x_gi, x_go=x_go, MTX=MTX, yL=-tLN)
        self.box = (X1, Ybot, Ytop)
        w0 = 2*np.pi*f0
        eps_si = sp.EPS_SI - 1j*sp.SIGMA_SI/(w0*EPS0)          # Si conductivity at f0 (negligible)
        ce = cell_eps(yn, layers(tLN, eps_si))
        xc, yc = 0.5*(xn[1:] + xn[:-1]), 0.5*(yn[1:] + yn[:-1])
        sxc = pml_s(xc, (-1, X1), -2, X1 + pml, w0, smax)
        syc = pml_s(yc, (Ybot, Ytop), Ybot - pml, Ytop + pml, w0, smax)
        dx, dy = np.diff(xn)*sxc, np.diff(yn)*syc
        dxd = np.r_[dx[0]/2, 0.5*(dx[1:] + dx[:-1]), dx[-1]/2]
        dyd = np.r_[dy[0]/2, 0.5*(dy[1:] + dy[:-1]), dy[-1]/2]
        hzd = 0.5*(hz + np.roll(hz, 1))
        self.d = (dx, dy, hz, dxd, dyd, hzd)
        # permittivity at the E points (layers vary in y only)
        wy = np.diff(yn)
        def node_avg(k):                                       # y nodes: average of the two cells
            v = np.zeros(ny, complex); wsum = np.zeros(ny)
            v[:-1] += ce[:, k]*wy; wsum[:-1] += wy
            v[1:] += ce[:, k]*wy; wsum[1:] += wy
            return v/wsum
        epx_y, epy_y, epz_y = node_avg(0), ce[:, 1], node_avg(2)
        # metal: nodes inside the closed metal
        tol = 1e-12
        X, Y, Z = np.meshgrid(xn, yn, zn, indexing="ij")
        inm = (Y >= -tol) & (Y <= MTX + tol)
        sig = inm & (X <= x_si + tol)
        gnd = inm & (X >= x_gi - tol) & (X <= x_go + tol)
        if tee:
            zr = np.abs(Z - P/2)
            stem = (X > x_gi + tol) & (X < xb1 - tol) & (zr < g["L1"]/2 - tol)
            head = (X > xb1 - tol) & (X < xb2 - tol) & (zr < g["L2"]/2 - tol)
            # nodes strictly inside the slot are not metal; stem/head join at x = xb1
            stem |= (np.abs(X - xb1) < tol) & (zr < g["L1"]/2 - tol)
            gnd &= ~(stem | head)
        m = sig | gnd
        del X, Y, Z
        # E edge masks: an edge is PEC if both end nodes and its midpoint are metal
        mid_ok = self._mid_metal(g, tee, xn, yn, zn, x_si, x_gi, x_go, xb1, xb2, MTX)
        mEx = m[:-1] & m[1:] & mid_ok[0]
        mEy = m[:, :-1] & m[:, 1:] & mid_ok[1]
        mEz = m & np.roll(m, -1, axis=2) & mid_ok[2]
        # outer PEC walls behind the PML (x = X1 + pml, y top and bottom); x = 0 is PMC
        mEy[-1] = True; mEz[-1] = True
        mEx[:, 0] = mEx[:, -1] = True; mEz[:, 0] = mEz[:, -1] = True
        self.masks = (mEx, mEy, mEz)
        self.shape = (nx, ny, nz)
        eps = np.r_[np.broadcast_to(epx_y[None, :, None], (nx - 1, ny, nz)).ravel(),
                    np.broadcast_to(epy_y[None, :, None], (nx, ny - 1, nz)).ravel(),
                    np.broadcast_to(epz_y[None, :, None], (nx, ny, nz)).ravel()]
        free = ~np.r_[mEx.ravel(), mEy.ravel(), mEz.ravel()]
        self.free = np.where(free)[0]
        self.eps = eps[self.free]
        self.N = len(self.free)

    @staticmethod
    def _mid_metal(g, tee, xn, yn, zn, x_si, x_gi, x_go, xb1, xb2, MTX):
        """Is the midpoint of each edge inside (or on) metal?  Catches edges that span a slot."""
        def metal(x, y, z):
            tol = 1e-12
            inm = (y >= -tol) & (y <= MTX + tol)
            s = inm & (x <= x_si + tol)
            gd = inm & (x >= x_gi - tol) & (x <= x_go + tol)
            if tee:
                zr = np.abs(z - P/2)
                slot = (((x > x_gi + tol) & (x < xb1 + tol) & (zr < g["L1"]/2 - tol))
                        | ((x > xb1 - tol) & (x < xb2 - tol) & (zr < g["L2"]/2 - tol)))
                gd &= ~slot
            return s | gd
        xm, ym = 0.5*(xn[1:] + xn[:-1]), 0.5*(yn[1:] + yn[:-1])
        zm = np.r_[0.5*(zn[1:] + zn[:-1]), 0.5*(zn[-1] + P)]
        return (metal(*np.meshgrid(xm, yn, zn, indexing="ij")),
                metal(*np.meshgrid(xn, ym, zn, indexing="ij")),
                metal(*np.meshgrid(xn, yn, zm, indexing="ij")))

    def operator(self, beta):
        """curl curl on the free E unknowns for Bloch phase exp(-j beta P)."""
        nx, ny, nz = self.shape
        dx, dy, hz, dxd, dyd, hzd = self.d
        ph = np.exp(-1j*beta*P)
        I = lambda n: sparse.identity(n, format="csr")
        def Df(n, h):            # nodes -> edges
            return sparse.diags([-1/h, 1/h], [0, 1], shape=(n - 1, n), format="csr")
        def Db(n, hd):           # dual values (n-1) -> nodes (n), zero outside
            M = sparse.diags([np.ones(n - 1), -np.ones(n - 1)], [0, -1], shape=(n, n - 1), format="csr")
            return sparse.diags(1/hd) @ M
        Dzf = sparse.diags([-1/hz, 1/hz[:-1]], [0, 1], shape=(nz, nz), format="lil", dtype=complex)
        Dzf[nz - 1, 0] = ph/hz[-1]
        Dzf = Dzf.tocsr()
        Dzb = sparse.diags([1/hzd, -1/hzd[1:]], [0, -1], shape=(nz, nz), format="lil", dtype=complex)
        Dzb[0, nz - 1] = -1/(ph*hzd[0])
        Dzb = Dzb.tocsr()
        k3 = lambda a, b, c: sparse.kron(a, sparse.kron(b, c, format="csr"), format="csr")
        X, Y = nx, ny
        # curl E: [Ex, Ey, Ez] -> [Hx (X, Y-1, nz), Hy (X-1, Y, nz), Hz (X-1, Y-1, nz)]
        CE = sparse.bmat([
            [None, -k3(I(X), I(Y - 1), Dzf), k3(I(X), Df(Y, dy), I(nz))],
            [k3(I(X - 1), I(Y), Dzf), None, -k3(Df(X, dx), I(Y), I(nz))],
            [-k3(I(X - 1), Df(Y, dy), I(nz)), k3(Df(X, dx), I(Y - 1), I(nz)), None]], format="csr")
        # curl H: [Hx, Hy, Hz] -> [Ex (X-1, Y, nz), Ey (X, Y-1, nz), Ez (X, Y, nz)]
        CH = sparse.bmat([
            [None, -k3(I(X - 1), I(Y), Dzb), k3(I(X - 1), Db(Y, dyd), I(nz))],
            [k3(I(X), I(Y - 1), Dzb), None, -k3(Db(X, dxd), I(Y - 1), I(nz))],
            [-k3(I(X), Db(Y, dyd), I(nz)), k3(Db(X, dxd), I(Y), I(nz)), None]], format="csr")
        K = (CH @ CE).tocsr()
        K = K[self.free][:, self.free]
        return K, CE

    def solve(self, beta, k0_guess, k=6):
        """Eigenpairs (k0^2, e) of K e = k0^2 eps e nearest k0_guess^2."""
        K, CE = self.operator(beta)
        sig = k0_guess**2
        Ei = sparse.diags(1/self.eps)
        A = (Ei @ K - sig*sparse.identity(self.N)).tocsr()
        import time
        t = time.time()
        F = pardiso_c.Factor(A, ooc=self.N > 400000)
        print(f"    factor: N {self.N}, nnz {A.nnz}, {time.time() - t:.0f} s, {F.mem_GB:.2f} GB", flush=True)
        self.nsolve = 0
        def mv(v):
            self.nsolve += 1
            return F.solve(v)
        op = LinearOperator(A.shape, matvec=mv, dtype=complex)
        t = time.time()
        vals, vecs = eigs(op, k=k, which="LM", tol=1e-8, ncv=max(2*k + 1, 20))
        print(f"    eigs: {self.nsolve} solves, {time.time() - t:.0f} s", flush=True)
        lam = sig + 1/vals
        self._last = (K, CE, F.mem_GB)
        F.free()
        return lam, vecs

    def full(self, e):
        out = np.zeros(sum(np.prod(s.shape) for s in self.masks), complex)
        out[self.free] = e
        nx, ny, nz = self.shape
        n1, n2 = (nx - 1)*ny*nz, nx*(ny - 1)*nz
        return (out[:n1].reshape(nx - 1, ny, nz), out[n1:n1 + n2].reshape(nx, ny - 1, nz),
                out[n1 + n2:].reshape(nx, ny, nz))

    def gap_voltage(self, e):
        """Integral of Ex across the gap at metal mid-height, averaged over z (Bloch phase removed later)."""
        Ex, _, _ = self.full(e)
        j = int(np.argmin(abs(self.yn - self.g["MTX"]/2)))
        xm = 0.5*(self.xn[1:] + self.xn[:-1])
        sel = (xm > self.g["x_si"]) & (xm < self.g["x_gi"])
        return (Ex[sel, j, :]*np.diff(self.xn)[sel, None]).sum(axis=0)       # per z node
