"""Matrix of the periodic tee cell (tee3d.Cell): Z(beta) = static + dynamic + reflected.

Kernel split (all three parts use the same Bloch-periodic Green's functions as cell3d):
  1. static, 3D spatial:  sum_n exp(-j beta n P) / (4 pi R_n)  for the direct field (vector and
     scalar potential) and for the LN quasi-static image (scalar, coefficient K, source mirrored
     in y).  Per face pair the nearest image is integrated analytically over the source
     rectangle (exact for any distance) at Gauss points of the observation face; the other
     images form a smooth function T(rho, dz) (closed-form tail), applied at the face centres.
  2. dynamic correction, Floquet harmonics |m| <= Mc: [K0(gamma_m rho) - K0(k_m rho)] / (2 pi),
     smooth, Gauss x Gauss over the cross-section elements.
  3. reflected field minus the image, Floquet harmonics |k_m| <= Ks: the stack's full spectral
     response (stack.py, leaky branch as in fw.Line2D) minus the spectral image K/(2 eps0 j ky).
Parts 2 and 3 are 2D cross-section interactions per harmonic, weighted by the z spectra of the
basis pieces exactly as cell3d.PlainCell.  Half structure with the x = 0 mirror (J_x odd).
"""
import numpy as np
from scipy import sparse, special

import stack as S
import fw

EPS0, MU0, C0 = fw.EPS0, fw.MU0, fw.C0
COMP = {"x": 0, "y": 1, "z": 2, "q": 3}
XSIGN = np.array([-1.0, 1.0, 1.0, 1.0])            # x-mirror parity of J_x, J_y, J_z, charge


# ------------------------------------------------------------------ geometry tables
class Faces:
    """Rectangles of the cell surface: origin o, axis indices (a1, a2), extents (l1, l2).
    qmul multiplies the number of observation Gauss points per axis (accuracy check)."""

    def __init__(self, cell, qmul=1):
        X, Y, Zg = cell.X, cell.Y, cell.Zg
        n = len(cell.faces)
        self.o = np.zeros((n, 3)); self.ax = np.zeros((n, 2), int); self.l = np.zeros((n, 2))
        self.key = {}
        for f, (kind, i, j, k) in enumerate(cell.faces):
            if kind == "x":
                self.o[f] = (X[i], Y[j], Zg[k]); self.ax[f] = (1, 2); self.l[f] = (Y[j + 1] - Y[j], Zg[k + 1] - Zg[k])
            elif kind == "y":
                self.o[f] = (X[i], Y[j], Zg[k]); self.ax[f] = (0, 2); self.l[f] = (X[i + 1] - X[i], Zg[k + 1] - Zg[k])
            else:
                self.o[f] = (X[i], Y[j], Zg[k]); self.ax[f] = (0, 1); self.l[f] = (X[i + 1] - X[i], Y[j + 1] - Y[j])
            self.key[(cell.face_elem[f], k)] = f
        self.n = n
        self.area = self.l[:, 0]*self.l[:, 1]
        e = np.eye(3)
        self.E1 = e[self.ax[:, 0]]; self.E2 = e[self.ax[:, 1]]
        self.c = self.o + 0.5*self.l[:, :1]*self.E1 + 0.5*self.l[:, 1:]*self.E2
        # observation points: Gauss n1 x n2, more points along the long side
        pts, wts, fid, m1, m2 = [], [], [], [], []
        for f in range(n):
            l1, l2 = self.l[f]
            r = max(l1, l2)/min(l1, l2)
            n1 = int(np.clip(np.ceil(2*l1/min(l1, l2)), 3, 8)) if l1 >= l2 else 3
            n2 = int(np.clip(np.ceil(2*l2/min(l1, l2)), 3, 8)) if l2 > l1 else 3
            u1, w1 = np.polynomial.legendre.leggauss(n1); u2, w2 = np.polynomial.legendre.leggauss(n2)
            u1, w1, u2, w2 = 0.5*(u1 + 1), 0.5*w1, 0.5*(u2 + 1), 0.5*w2
            n1, n2 = n1*qmul, n2*qmul
            u1, w1 = np.polynomial.legendre.leggauss(n1); u2, w2 = np.polynomial.legendre.leggauss(n2)
            u1, w1, u2, w2 = 0.5*(u1 + 1), 0.5*w1, 0.5*(u2 + 1), 0.5*w2
            U1, U2 = np.meshgrid(u1, u2, indexing="ij"); W = np.outer(w1, w2)*l1*l2
            p = self.o[f] + U1.ravel()[:, None]*l1*self.E1[f] + U2.ravel()[:, None]*l2*self.E2[f]
            pts.append(p); wts.append(W.ravel()); fid.append(np.full(p.shape[0], f)); m1.append(U1.ravel()); m2.append(U2.ravel())
        self.pts = np.concatenate(pts); self.pw = np.concatenate(wts); self.pf = np.concatenate(fid)
        self.pu1 = np.concatenate(m1); self.pu2 = np.concatenate(m2)


def basis_maps(cell, F):
    """Sparse maps (3 nf x N) per component x, y, z, q: rows (face, moment 1/u1/u2),
    and the wrap flag per entry (piece at z >= P: Bloch phase applied later)."""
    P, Zg = cell.P, cell.Zg
    MOM_S = {("s", "p"): (1, -1, 0), ("e", "p"): (0, 1, 0), ("c", "p"): (1, 0, 0),
             ("c", "u"): (0, 0, 1), ("c", "d"): (1, 0, -1)}
    MOM_C = {"xu": (0, 1, 0), "xd": (1, -1, 0), "yu": (0, 0, 1), "yd": (1, 0, -1), "c": (1, 0, 0)}
    rows = {c: [] for c in range(4)}; cols = {c: [] for c in range(4)}
    vals = {c: [] for c in range(4)}; wrap = {c: [] for c in range(4)}
    for i, (cur, div) in enumerate(zip(cell.B, cell.Q)):
        for p, f, coef in cur + div:
            kind, elem, wt, comp = cell.pieces[p]
            typ, a, b = cell.zfs[f]
            w = a >= P - 1e-15
            a0 = a - P if w else a
            k = int(np.argmin(np.abs(Zg - a0)))
            if kind == "s":
                face = F.key[(("s", elem), k)]
                mom = MOM_S[(wt, typ)]
            else:
                face = F.key[(("c", elem), k)]
                mom = MOM_C[wt]
            c = COMP[comp]
            for al in range(3):
                if mom[al]:
                    rows[c].append(3*face + al); cols[c].append(i); vals[c].append(coef*mom[al]); wrap[c].append(w)
    out = []
    for c in range(4):
        out.append((np.array(rows[c], int), np.array(cols[c], int), np.array(vals[c]), np.array(wrap[c], bool)))
    return out


def wmat(maps, c, nf, N, phase):
    r, cc, v, w = maps[c]
    vv = v*np.where(w, phase, 1.0)
    return sparse.csr_matrix((vv, (r, cc)), shape=(3*nf, N))


# ------------------------------------------------------------------ analytic rectangle potential
def _lnp(v, R, q):
    """ln(v + R), stable for v < 0 (q = R^2 - v^2); 0 where q = 0 and v < 0 (term multiplied by 0)."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.where(v >= 0, np.log(np.maximum(v + R, 1e-300)), np.log(np.maximum(q, 1e-300)/np.maximum(R - v, 1e-300)))
    return np.where(q <= 1e-300*(1 + v*v), 0.0, out)        # multiplied by 0 there


def rect_moments(p, o, E1, E2, l1, l2):
    """int over the rectangle (o + s1 E1 + s2 E2, s in [0,l]) of (1, s1/l1, s2/l2) / R at points p.
    Broadcasting shapes (..., 3) for p, o, E1, E2 and (...) for l1, l2.  Returns 3 arrays."""
    D = p - o
    xi0 = np.sum(D*E1, -1); eta0 = np.sum(D*E2, -1)
    n = np.cross(E1, E2)
    d = np.abs(np.sum(D*n, -1))
    d2 = d*d
    Ic = np.zeros(np.broadcast(xi0, l1).shape); Iu = np.zeros_like(Ic); Iv = np.zeros_like(Ic)
    for su, u in ((1, l1 - xi0), (-1, -xi0)):
        for sv, v in ((1, l2 - eta0), (-1, -eta0)):
            s = su*sv
            R = np.sqrt(u*u + v*v + d2)
            Lv = _lnp(v, R, u*u + d2); Lu = _lnp(u, R, v*v + d2)
            with np.errstate(divide="ignore", invalid="ignore"):
                at = np.where(d > 0, d*np.arctan(u*v/np.where(d > 0, d*R, 1.0)), 0.0)
            Ic = Ic + s*(u*Lv + v*Lu - at)
            Iu = Iu + s*0.5*(v*R + (u*u + d2)*Lv)
            Iv = Iv + s*0.5*(u*R + (v*v + d2)*Lu)
    return Ic, (Iu + xi0*Ic)/l1, (Iv + eta0*Ic)/l2


# ------------------------------------------------------------------ periodic tail T(rho, dz)
def tail_table(beta, P, rho_max, nr=48, nz=65, N=40, m0=1):
    """T(rho, dz) = sum_{|m| >= m0} exp(-j beta m P) / (4 pi sqrt(rho^2 + (dz - m P)^2)) for
    dz in [-P/2, P/2]: exact for |m| <= N, then the 1/m expansion to O(m^-3) summed in closed
    form with polylogarithms (analytic continuation for complex beta).  dz spans [-P, P] so that
    point pairs of long faces (beyond the centre offset range [-P/2, P/2]) stay inside."""
    rho = np.linspace(0, rho_max, nr); dz = np.linspace(-P, P, 2*nz - 1)
    Rr, Dz = np.meshgrid(rho, dz, indexing="ij")
    th = complex(beta)*P
    T = np.zeros(Rr.shape, complex)
    for m in range(m0, N + 1):
        T += np.exp(-1j*th*m)/np.sqrt(Rr**2 + (Dz - m*P)**2) + np.exp(1j*th*m)/np.sqrt(Rr**2 + (Dz + m*P)**2)
    for sgn in (1, -1):                                   # z = exp(-+ j th), distance m P -+ dz
        z = np.exp(-sgn*1j*th)
        mm = np.arange(1, N + 1)
        tails = [-np.log(1 - z) - np.sum(z**mm/mm)]      # Li_1 (analytic continuation)
        zu = z/abs(z)                                     # |z| = 1 +- O(Im beta P): negligible in the
        mt = np.arange(N + 1, 200001)                     # small m^-2, m^-3 terms
        for s in (2, 3):
            tails.append(np.sum(zu**mt/mt.astype(float)**s))
        dd = sgn*Dz                                       # 1/(mP - dd) expansion with rho
        T += (tails[0]/P + tails[1]*dd/P**2 + tails[2]*(dd**2 - Rr**2/2)/P**3)
    return rho, dz, T/(4*np.pi)


def tail_eval(tab, rho, dz):
    r, z, T = tab
    from scipy.interpolate import RectBivariateSpline
    fr = RectBivariateSpline(r, z, T.real, kx=3, ky=3); fi = RectBivariateSpline(r, z, T.imag, kx=3, ky=3)
    return fr.ev(rho, dz) + 1j*fi.ev(rho, dz)


# ------------------------------------------------------------------ static part
MIRRORS = {"d": np.array([1, 1, 1.]), "x": np.array([-1, 1, 1.]), "y": np.array([1, -1, 1.]), "xy": np.array([-1, -1, 1.])}


def static_face_matrix(F, beta, P, mir, chunk=60, tgauss=0, near=1):
    """Generator over obs-face chunks: (face slice, M) with M (3 nc x 3 nf) complex =
    int_a int_b (1,u1,u2)_a (1,u1,u2)_b G_per(r, mirror r') for the static periodic kernel.
    The images n* - near .. n* + near (n*: nearest by the centres) are integrated analytically,
    the others come from the table: with near = 0 a long face (h_z ~ P/2) would touch an
    image treated as distant."""
    m = MIRRORS[mir]
    om = F.o*m; E1m = F.E1*m; E2m = F.E2*m
    cm = F.c*m
    rho_max = np.max(np.hypot(F.c[:, None, 0] - cm[None, :, 0], F.c[:, None, 1] - cm[None, :, 1]))*1.05 + 1e-6
    tab = tail_table(beta, P, rho_max, m0=near + 1)
    nf = F.n
    for a0 in range(0, nf, chunk):
        a1 = min(nf, a0 + chunk)
        sel = (F.pf >= a0) & (F.pf < a1)
        pts, pw, pf, pu1, pu2 = F.pts[sel], F.pw[sel], F.pf[sel], F.pu1[sel], F.pu2[sel]
        # nearest image per face pair from the centres
        dzc = F.c[a0:a1, None, 2] - cm[None, :, 2]
        nst = np.round(dzc/P)                              # (nc, nf)
        nsp = nst[pf - a0]                                 # (np, nf)
        I = np.zeros((len(pf), nf, 3), complex)
        for s_ in range(-near, near + 1):
            shift = np.zeros((len(pf), nf, 3)); shift[..., 2] = (nsp + s_)*P
            I0, I1, I2 = rect_moments(pts[:, None, :], om[None] + shift, E1m[None], E2m[None], F.l[None, :, 0], F.l[None, :, 1])
            I += np.exp(-1j*beta*s_*P)*np.stack([I0, I1, I2], -1)/(4*np.pi)    # (np, nf, 3)
        # integrate over the obs face with weights (1, u1, u2)
        nc = a1 - a0
        rowsO = np.concatenate([3*(pf - a0) + k for k in range(3)])
        colsO = np.tile(np.arange(len(pf)), 3)
        valsO = np.concatenate([pw, pw*pu1, pw*pu2])
        O = sparse.csr_matrix((valsO, (rowsO, colsO)), shape=(3*nc, len(pf)))
        Mn = (O @ I.reshape(len(pf), 3*nf)).reshape(nc, 3, nf, 3)
        # far images at the centres, monopole moments
        dzw = dzc - nst*P
        rho = np.hypot(F.c[a0:a1, None, 0] - cm[None, :, 0], F.c[a0:a1, None, 1] - cm[None, :, 1])
        ph = np.exp(-1j*beta*nst*P)
        if tgauss:
            # obs Gauss points x src tgauss^2 Gauss points, moments (1, u1, u2) on both sides
            u, wq = np.polynomial.legendre.leggauss(tgauss); u, wq = 0.5*(u + 1), 0.5*wq
            U1, U2 = np.meshgrid(u, u, indexing="ij"); WQ = np.outer(wq, wq).ravel(); U1, U2 = U1.ravel(), U2.ravel()
            sp = om[:, None, :] + U1[None, :, None]*F.l[:, None, :1]*E1m[:, None, :] + U2[None, :, None]*F.l[:, None, 1:]*E2m[:, None, :]
            sw = WQ[None, :]*F.area[:, None]                                  # (nf, nq)
            Tm = np.zeros((len(pf), nf, 3), complex)
            for q in range(len(WQ)):
                dzq = pts[:, None, 2] - sp[None, :, q, 2] - nsp*P
                rq = np.hypot(pts[:, None, 0] - sp[None, :, q, 0], pts[:, None, 1] - sp[None, :, q, 1])
                Tq = tail_eval(tab, rq.ravel(), dzq.ravel()).reshape(len(pf), nf)*sw[None, :, q]
                Tm[..., 0] += Tq; Tm[..., 1] += Tq*U1[q]; Tm[..., 2] += Tq*U2[q]
            MT = (O @ Tm.reshape(len(pf), 3*nf)).reshape(nc, 3, nf, 3)
            M = (Mn + MT)*ph[:, None, :, None]
        else:
            T = tail_eval(tab, rho.ravel(), dzw.ravel()).reshape(nc, nf)
            momA = np.stack([F.area[a0:a1], F.area[a0:a1]/2, F.area[a0:a1]/2], -1)
            momB = np.stack([F.area, F.area/2, F.area/2], -1)
            M = (Mn + T[:, None, :, None]*momA[:, :, None, None]*momB[None, None, :, :])*ph[:, None, :, None]
        yield slice(a0, a1), M.reshape(3*nc, 3*nf)


def static_Z(cell, F, maps, beta, w, K, chunk=60, tgauss=0, near=1):
    """Static part of Z (N x N)."""
    N, nf, P = cell.N, F.n, cell.P
    Wo = [wmat(maps, c, nf, N, np.exp(-1j*beta*P)) for c in range(4)]
    Ws = [wmat(maps, c, nf, N, np.exp(1j*beta*P)) for c in range(4)]
    Z = np.zeros((N, N), complex)
    gens = {mir: static_face_matrix(F, beta, P, mir, chunk, tgauss, near) for mir in MIRRORS}
    while True:
        try:
            blocks = {mir: next(g) for mir, g in gens.items()}
        except StopIteration:
            break
        sl = blocks["d"][0]
        rs = slice(3*sl.start, 3*sl.stop)
        Md, Mx, My, Mxy = (blocks[k][1] for k in ("d", "x", "y", "xy"))
        for c in range(3):
            Oc = Wo[c][rs]
            if Oc.nnz == 0:
                continue
            Mc = Md + XSIGN[c]*Mx
            Z += (-1j*w*MU0)*(Oc.T @ (Ws[c].T @ Mc.T).T)
        Mq = (Md + Mx) + K*(My + Mxy)
        Oq = Wo[3][rs]
        if Oq.nnz:
            Z += (-1/(1j*w*EPS0))*(Oq.T @ (Ws[3].T @ Mq.T).T)
    return Z


def _near_buckets(F, P, mir, a0, a1, near=1):
    """Near-image part of static_face_matrix for obs faces a0:a1 without its Bloch phases:
    {q: M_q (3 nc x 3 nf, real)}, the total phase of M_q being exp(-j beta q P)."""
    m = MIRRORS[mir]
    om = F.o*m; E1m = F.E1*m; E2m = F.E2*m; cm = F.c*m
    nf = F.n
    sel = (F.pf >= a0) & (F.pf < a1)
    pts, pw, pf, pu1, pu2 = F.pts[sel], F.pw[sel], F.pf[sel], F.pu1[sel], F.pu2[sel]
    dzc = F.c[a0:a1, None, 2] - cm[None, :, 2]
    nst = np.round(dzc/P)
    nsp = nst[pf - a0]
    nc = a1 - a0
    rowsO = np.concatenate([3*(pf - a0) + kk for kk in range(3)])
    colsO = np.tile(np.arange(len(pf)), 3)
    O = sparse.csr_matrix((np.concatenate([pw, pw*pu1, pw*pu2]), (rowsO, colsO)), shape=(3*nc, len(pf)))
    out = {}
    for s_ in range(-near, near + 1):
        shift = np.zeros((len(pf), nf, 3)); shift[..., 2] = (nsp + s_)*P
        I0, I1, I2 = rect_moments(pts[:, None, :], om[None] + shift, E1m[None], E2m[None], F.l[None, :, 0], F.l[None, :, 1])
        Mn = (O @ (np.stack([I0, I1, I2], -1)/(4*np.pi)).reshape(len(pf), 3*nf)).reshape(nc, 3, nf, 3)
        for q0 in np.unique(nst):
            q = int(q0) + s_
            Mq = np.where((nst == q0)[:, None, :, None], Mn, 0.0)
            out[q] = out.get(q, 0) + Mq
    return {q: v.reshape(3*nc, 3*nf) for q, v in out.items()}


def _wsplit(maps, c, nf, N):
    """Basis map of component c split into its unwrapped and wrapped entries (real)."""
    r, cc, v, w = maps[c]
    return [sparse.csr_matrix((np.where(w == f, v, 0.0), (r, cc)), shape=(3*nf, N)) for f in (False, True)]


def _static_chunks(args):
    F, maps, N, P, K, chunks, near = args
    nf = F.n
    W = [_wsplit(maps, c, nf, N) for c in range(4)]
    A = {p: np.zeros((N, N)) for p in range(-2*near - 1, 2*near + 2)}
    Phi = {p: np.zeros((N, N)) for p in A}
    for a0, a1 in chunks:
        rs = slice(3*a0, 3*a1)
        B = {mir: _near_buckets(F, P, mir, a0, a1, near) for mir in MIRRORS}
        qs = set().union(*[set(b) for b in B.values()])
        z = lambda mir, q: B[mir].get(q, 0.0)
        for c in range(4):
            for q in qs:
                if c < 3:
                    M = z("d", q) + XSIGN[c]*z("x", q); tgt = A
                else:
                    M = (z("d", q) + z("x", q)) + K*(z("y", q) + z("xy", q)); tgt = Phi
                if np.isscalar(M):
                    continue
                for a in (0, 1):                       # obs wrapped: exp(-j beta P)
                    Oc = W[c][a][rs]
                    if Oc.nnz == 0:
                        continue
                    rows = np.unique(Oc.indices)
                    Oc = Oc.tocsc()[:, rows]
                    for b in (0, 1):                   # src wrapped: exp(+j beta P)
                        if W[c][b].nnz == 0:
                            continue
                        tgt[q + a - b][rows] += Oc.T @ (W[c][b].T @ M.T).T
    return A, Phi


class StaticCache:
    """The near-image part of static_Z does not depend on beta except through the Bloch phases
    exp(-j beta p P), p = -3..3: it is stored per p at basis level (vector part A_p, scalar part
    Phi_p, both real N x N) once per geometry; static_Z(beta) is then sum_p phase_p (-j w mu0 A_p
    - Phi_p/(j w eps0)) + the far-image tail (cheap, evaluated per beta).  Same result as static_Z."""

    def __init__(self, cell, F, maps, K, chunk=60, near=1, workers=4):
        import multiprocessing as mp
        self.cell, self.F, self.maps, self.K, self.near = cell, F, maps, K, near
        N, nf, P = cell.N, F.n, cell.P
        allc = [(a0, min(nf, a0 + chunk)) for a0 in range(0, nf, chunk)]
        parts = [allc[i::workers] for i in range(workers)]
        args = [(F, maps, N, P, K, pc, near) for pc in parts if pc]
        if workers > 1:
            with mp.get_context("fork").Pool(len(args)) as pool:
                res = pool.map(_static_chunks, args)
        else:
            res = [_static_chunks(a) for a in args]
        self.A = {p: sum(r[0][p] for r in res) for p in res[0][0]}
        self.Phi = {p: sum(r[1][p] for r in res) for p in res[0][1]}
        # tail: monopole moments of each face mapped to the bases
        mom = np.stack([F.area, F.area/2, F.area/2], -1).ravel()
        S = sparse.csr_matrix((np.ones(3*nf), (np.repeat(np.arange(nf), 3), np.arange(3*nf))), shape=(nf, 3*nf))
        self.U = [[S @ sparse.diags(mom) @ Wc for Wc in _wsplit(maps, c, nf, N)] for c in range(4)]

    def Z(self, beta, w):
        P, F, near = self.cell.P, self.F, self.near
        N = self.cell.N
        Z = np.zeros((N, N), complex)
        for p in self.A:
            ph = np.exp(-1j*beta*p*P)
            Z += ph*((-1j*w*MU0)*self.A[p] + (-1/(1j*w*EPS0))*self.Phi[p])
        # far images (|n - n*| > near) at the face centres
        T = {}
        for mir, m in MIRRORS.items():
            cm = F.c*m
            rho_max = np.max(np.hypot(F.c[:, None, 0] - cm[None, :, 0], F.c[:, None, 1] - cm[None, :, 1]))*1.05 + 1e-6
            tab = tail_table(beta, P, rho_max, m0=near + 1)
            dzc = F.c[:, None, 2] - cm[None, :, 2]
            nst = np.round(dzc/P)
            rho = np.hypot(F.c[:, None, 0] - cm[None, :, 0], F.c[:, None, 1] - cm[None, :, 1])
            T[mir] = tail_eval(tab, rho.ravel(), (dzc - nst*P).ravel()).reshape(F.n, F.n)*np.exp(-1j*beta*nst*P)
        for c in range(4):
            Tc = (T["d"] + XSIGN[c]*T["x"]) if c < 3 else (T["d"] + T["x"]) + self.K*(T["y"] + T["xy"])
            fac = (-1j*w*MU0) if c < 3 else (-1/(1j*w*EPS0))
            Uo = self.U[c][0] + np.exp(-1j*beta*P)*self.U[c][1]
            Us = self.U[c][0] + np.exp(1j*beta*P)*self.U[c][1]
            if Uo.nnz == 0:
                continue
            Z += fac*(Uo.T @ (Us.T @ Tc.T).T)
        return Z


# ------------------------------------------------------------------ harmonic parts (cross-section)
def sinh_grid(km, kmax=1e7, dt=0.05):
    """k >= 0 grid for an evanescent harmonic (|k_m| >> k_Si): k = |k_m| sinh(t), trapezoid in t;
    aliasing period 2 pi / (|k_m| dt) >> the 1/|k_m| decay length of the kernel."""
    a = abs(km.real)
    tmax = np.arcsinh(max(kmax, 4*a)/a)
    t = np.arange(0, tmax + dt/2, dt)
    k = a*np.sinh(t); w = a*np.cosh(t)*dt
    w[0] *= 0.5
    return k, w


class XS:
    """Cross-section pieces of the cell: Gauss points and spectral factors."""

    def __init__(self, cell):
        self.cell = cell
        pcs = cell.pieces
        self.n = len(pcs)
        self.comp = np.array([COMP[p[3]] for p in pcs])
        # Gauss points per piece (weights include the length / area and the piece weight)
        g4u, g4w = np.polynomial.legendre.leggauss(4); g4u, g4w = 0.5*(g4u + 1), 0.5*g4w
        g3u, g3w = np.polynomial.legendre.leggauss(3); g3u, g3w = 0.5*(g3u + 1), 0.5*g3w
        pts, wts, pid = [], [], []
        for ip, (kind, e, wt, comp) in enumerate(pcs):
            if kind == "s":
                d, p0, p1 = cell.segs[e][:3]
                p0, p1 = np.array(p0), np.array(p1); L = np.linalg.norm(p1 - p0)
                ww = {"s": 1 - g4u, "e": g4u, "c": np.ones(4)}[wt]
                pts.append(p0 + g4u[:, None]*(p1 - p0)); wts.append(ww*g4w*L)
            else:
                xa, xb, ya, yb = cell.cells[e][:4]
                U, V = np.meshgrid(g3u, g3u, indexing="ij"); W = np.outer(g3w, g3w)*(xb - xa)*(yb - ya)
                ww = {"xu": U, "xd": 1 - U, "yu": V, "yd": 1 - V, "c": np.ones_like(U)}[wt]
                pts.append(np.stack([xa + U.ravel()*(xb - xa), ya + V.ravel()*(yb - ya)], -1)); wts.append((ww*W).ravel())
            pid.append(np.full(len(wts[-1]), ip))
        self.pts = np.concatenate(pts); self.pw = np.concatenate(wts); self.pid = np.concatenate(pid)
        self.xmin = np.array([self.pts[self.pid == i, 0].min() for i in range(self.n)])
        self.xmax = np.array([self.pts[self.pid == i, 0].max() for i in range(self.n)])
        for ip, (kind, e, wt, comp) in enumerate(pcs):             # exact extents (Gauss points are interior)
            if kind == "s":
                d, p0, p1 = cell.segs[e][:3]; self.xmin[ip], self.xmax[ip] = min(p0[0], p1[0]), max(p0[0], p1[0])
            else:
                self.xmin[ip], self.xmax[ip] = cell.cells[e][0], cell.cells[e][1]
        self.Wp = sparse.csr_matrix((self.pw, (self.pid, np.arange(len(self.pid)))), shape=(self.n, len(self.pid)))

    def spectra(self, k, ky, sign):
        """(Nk, npieces) spectral factor: int w(r) exp(sign j k x - j ky y) over the piece."""
        cell = self.cell
        out = np.zeros((len(k), self.n), complex)
        kk = k[:, None]; ky = ky[:, None]
        segs = [(ip, p) for ip, p in enumerate(cell.pieces) if p[0] == "s"]
        if segs:
            ips = np.array([ip for ip, _ in segs])
            S = [cell.segs[p[1]] for _, p in segs]
            x0 = np.array([s[1][0] for s in S]); y0 = np.array([s[1][1] for s in S])
            x1 = np.array([s[2][0] for s in S]); y1 = np.array([s[2][1] for s in S])
            hor = np.array([s[0] == "x" for s in S])
            L = np.where(hor, x1 - x0, y1 - y0)
            a = np.where(hor, sign*1j*kk*L, -1j*ky*L)
            pref = np.exp(sign*1j*kk*x0 - 1j*ky*y0)*L
            I1, Iu = fw._If(a, "1"), fw._If(a, "u")
            wt = np.array([p[2] for _, p in segs])
            val = np.where(wt == "s", I1 - Iu, np.where(wt == "e", Iu, I1))
            out[:, ips] = pref*val
        cel = [(ip, p) for ip, p in enumerate(cell.pieces) if p[0] == "c"]
        if cel:
            ips = np.array([ip for ip, _ in cel])
            C = np.array([cell.cells[p[1]][:4] for _, p in cel])
            xa, xb, ya, yb = C.T
            ax = sign*1j*kk*(xb - xa); ay = -1j*ky*(yb - ya)
            Xf = np.exp(sign*1j*kk*xa)*(xb - xa); Yf = np.exp(-1j*ky*ya)*(yb - ya)
            I1x, Iux, I1y, Iuy = fw._If(ax, "1"), fw._If(ax, "u"), fw._If(ay, "1"), fw._If(ay, "u")
            wt = np.array([p[2] for _, p in cel])
            fx = np.where(wt == "xu", Iux, np.where(wt == "xd", I1x - Iux, I1x))
            fy = np.where(wt == "yu", Iuy, np.where(wt == "yd", I1y - Iuy, I1y))
            out[:, ips] = Xf*fx*Yf*fy
        return out


def _dyn_f(r, gam, kap):
    return (special.k0(gam.real*r) - 1j*gam.imag*r*special.k1(gam.real*r)
            - special.k0(kap.real*r) + 1j*kap.imag*r*special.k1(kap.real*r))


def dyn_kernel(xs, km, k0, table=True):
    """X (npieces^2): [K0(gamma rho) - K0(kappa rho)]/(2 pi), gamma = sqrt(km^2 - k0^2),
    kappa = sqrt(km^2); first order in the (tiny) imaginary parts, real Bessel functions.
    Returns dict mirror -> matrix (pieces x pieces, source mirrored).
    table: the function of rho is tabulated once per harmonic (cubic spline on a grid refined
    towards rho = 0, where it behaves as rho^2 ln rho) and interpolated at the ~10^7 point pairs,
    whose distances are computed once per cell (xs._rho); False: Bessel functions at every pair."""
    from scipy.interpolate import CubicSpline
    gam = np.sqrt(km**2 - k0**2 + 0j); kap = np.sqrt(km**2 + 0j)
    gam = gam if gam.real > 0 else -gam; kap = kap if kap.real > 0 else -kap
    out = {}
    p = xs.pts
    if not hasattr(xs, "_rho"):
        xs._rho = {}
        for mir, m in MIRRORS.items():
            q = p*m[:2]
            xs._rho[mir] = np.hypot(p[:, None, 0] - q[None, :, 0], p[:, None, 1] - q[None, :, 1])
    if table:
        if not hasattr(xs, "_t"):
            xs._rmax = max(r.max() for r in xs._rho.values())*1.0001
            xs._t = {mir: np.cbrt(r/xs._rmax) for mir, r in xs._rho.items()}
        t = np.linspace(0, 1, 6001)
        rg = xs._rmax*t**3
        fg = np.empty(len(rg), complex); fg[0] = np.log(kap/gam); fg[1:] = _dyn_f(rg[1:], gam, kap)
        spl = CubicSpline(t, fg/(2*np.pi))             # in t = (rho/rmax)^(1/3): smooth near 0
    for mir in MIRRORS:
        rho = xs._rho[mir]
        if table:
            D = spl(xs._t[mir])
        else:
            r = np.maximum(rho, 1e-30)
            D = np.where(rho < 1e-15, np.log(kap/gam), _dyn_f(r, gam, kap))/(2*np.pi)
        out[mir] = xs.Wp @ (xs.Wp @ D.T).T
    return out


def spec_grid(line, km, gmax, kmax=1.5e7, wmax=0.0):
    """k grid for harmonic km: m = 0 (|k_m| near the silicon light line): Gauss pieces clustered at
    the branch point up to 4 k_Si (as fw.Line2D); then uniform with dk = 2 pi/(4 gmax + 2 wmax) up
    to kmax.  Uniform spacing: two kept pieces (gap < gmax, widths <= wmax) have points at most
    gmax + 2 wmax apart, so their aliases lie >= 3 gmax away, where the kernel of an evanescent
    harmonic is below exp(-75) (m = 0: alias period > 4 x the cell).  Without wmax the aliases of
    wide pieces came within ~1 um for high harmonics (gmax 8 um, pieces 12 um)."""
    k0 = line.k0
    eb = line.eps_bot.real
    lng = abs(km.real) < 1.5*np.sqrt(eb)*k0              # m = 0: long-range kernel
    dk = 2e3 if lng else 2*np.pi/(4*gmax + 2*wmax)
    kb2 = eb*k0**2 - km.real**2
    ks, ws = [], []
    kstart = 0.0
    if lng:
        u, wu = np.polynomial.legendre.leggauss(160); u, wu = 0.5*(u + 1), 0.5*wu
        k4 = 4*np.sqrt(eb)*k0
        if kb2 > 0:
            kb = np.sqrt(kb2)
            ks += [kb*(1 - (1 - u)**2), kb + (k4 - kb)*u**2]; ws += [kb*2*(1 - u)*wu, (k4 - kb)*2*u*wu]
        else:
            ks.append(k4*u); ws.append(k4*wu)
        kstart = k4
    n = int(np.ceil((kmax - kstart)/dk))
    ku = kstart + dk*np.arange(n + 1)
    wu_ = np.full(n + 1, dk); wu_[-1] = dk/2
    if kstart > 0:                     # trapezoid from the end of the Gauss pieces
        wu_[0] = dk/2
        k = np.concatenate(ks + [ku]); w = np.concatenate(ws + [wu_])
        return np.r_[-k[::-1], k], np.r_[w[::-1], w]
    # k = 0 is an interior point of the mirrored trapezoid: full weight, counted once
    return np.r_[-ku[:0:-1], ku], np.r_[wu_[:0:-1], wu_]


# long-range harmonic on a complex k path (analytic in beta); False: real axis with the
# improper sheet below the branch point (not analytic: wrong Z0 and alpha for leaky tee modes)
COMPLEX_PATH = True


def _path_m0(line, km, kmax=1.5e7):
    """k path for the long-range harmonic (|k_m| below the silicon branch point), as an analytic
    function of k_m: t on the real axis (Gauss pieces clustered at Re k_b, then uniform), mapped
    to k = t + j A sin(pi t / k4) on [0, k4] (odd in t), A > Im k_b: the path passes above the
    branch point k_b = sqrt(eps_b k0^2 - k_m^2), as the real axis does for a real k_m.  On it the
    bottom wave is continued from the proper sheet at |t| = k4; flip marks where that continuation
    is on the other sheet.  Returns k, weights (dk = k'(t) dt), flip."""
    k0 = line.k0
    eb = line.eps_bot
    kb = np.sqrt(eb*k0**2 - km**2 + 0j)
    kb = kb if kb.real > 0 else -kb
    A = 2*max(kb.imag, 0.0) + 0.03*kb.real
    k4 = 4*np.sqrt(eb.real)*k0
    u, wu = np.polynomial.legendre.leggauss(160); u, wu = 0.5*(u + 1), 0.5*wu
    t0 = min(kb.real, 0.95*k4)
    t = np.r_[t0*(1 - (1 - u)**2), t0 + (k4 - t0)*u**2]
    wt = np.r_[t0*2*(1 - u)*wu, (k4 - t0)*2*u*wu]
    k = t + 1j*A*np.sin(np.pi*t/k4)
    dk = 1 + 1j*A*np.pi/k4*np.cos(np.pi*t/k4)
    w = wt*dk
    dk_u = 2e3
    n = int(np.ceil((kmax - k4)/dk_u))
    ku = k4 + dk_u*np.arange(n + 1)
    wu_ = np.full(n + 1, dk_u); wu_[0] = wu_[-1] = dk_u/2
    k = np.r_[k, ku]; w = np.r_[w, wu_]
    # continuation of lam = sqrt(k^2 + k_m^2 - eps_b k0^2) (down wave, proper: Re lam > 0) inward
    L = np.sqrt(k**2 + km**2 - eb*k0**2 + 0j)
    L = np.where(L.real < 0, -L, L)
    flip = np.zeros(len(k), bool)
    prev = L[-1]
    for i in range(len(k) - 1, -1, -1):
        s = 1 if abs(L[i] - prev) <= abs(-L[i] - prev) else -1
        flip[i] = s < 0
        prev = s*L[i]
    return np.r_[-k[::-1], k], np.r_[w[::-1], w], np.r_[flip[::-1], flip]


def spec_kernel(xs, line, km, sym=True, Gmax=None, kmax=1.5e7, decay=150.0, kref=None):
    """Reflected-field interaction (pieces x pieces) for harmonic km (field formulation, stack.py),
    minus the spectral image on the charge pieces; x mirror added on the source side.  Pairs whose
    lateral gap exceeds gmax = min(Gmax, decay/|k_m|) are set to zero (an evanescent harmonic's
    kernel is analytic in a strip of half-width |k_m|: it decays as exp(-|k_m| gap))."""
    k0 = line.k0
    if Gmax is None:                           # the whole cell and its mirror: no pair is ever cut
        Gmax = 1.05*2*xs.xmax.max()            # by the cutoff (a fixed 220 um dropped substrate
                                               # coupling once the cell got wider, alpha / 3)
    # kref: |2 pi m / P| + k_Si (>= |k_m|) from harmonic_Z, never beta itself: a cutoff or grid that
    # moves with beta drops or adds pairs between two nearby builds (Z not smooth in beta; on the
    # row 161 tee the m = 5 kernel was 98 % non-analytic -> Z0 30 instead of 48 ohm)
    kref = abs(km.real) if kref is None else kref
    gmax = Gmax if kref < 1.5*np.sqrt(line.eps_bot.real)*k0 else min(Gmax, decay/kref)
    if COMPLEX_PATH and kref < 1.5*np.sqrt(line.eps_bot.real)*k0:
        k, kw, flip = _path_m0(line, km, kmax)
        R = S.stack_admittance(k, km, k0, line.layers, line.bottom, flip=flip)
    else:
        k, kw = spec_grid(line, km, gmax, kmax, wmax=np.max(xs.xmax - xs.xmin))
        R = S.stack_admittance(k, km, k0, line.layers, line.bottom, leaky=True)
    air = S.Air(k, km, k0)
    R = air.reflection(R)
    ky = air.ky
    Dc = [air.sheet_down(J)[0] for J in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
    M3 = np.stack([air.up_field((R @ d[..., None])[..., 0]) for d in Dc], -1)      # (Nk, obs, src)
    T = xs.spectra(k, ky, -1); Sp = xs.spectra(k, ky, +1)
    Sm = Sp[::-1]                                                                  # source at -k: x mirror
    comp = xs.comp
    gd = np.maximum(0, np.maximum(xs.xmin[None, :] - xs.xmax[:, None], xs.xmin[:, None] - xs.xmax[None, :]))
    gm = np.maximum(0, xs.xmin[:, None] + xs.xmin[None, :])                      # to the mirrored source
    keep_d, keep_m = gd <= gmax, gm <= gmax
    X = np.zeros((xs.n, xs.n), complex)
    kwf = kw/(2*np.pi)
    for ci in range(3):
        oi = comp == ci
        if not oi.any():
            continue
        To = T[:, oi]*kwf[:, None]
        for cj in range(3):
            sj = comp == cj
            if not sj.any():
                continue
            A = To*M3[:, ci, cj][:, None]
            blk = np.where(keep_d[np.ix_(oi, sj)], A.T @ Sp[:, sj], 0)
            if sym:
                blk = blk + XSIGN[cj]*np.where(keep_m[np.ix_(oi, sj)], A.T @ Sm[:, sj], 0)
            X[np.ix_(oi, sj)] += blk
    q = comp == 3
    Tq = T[:, q]*(kwf*line.K/(2*EPS0*1j*ky))[:, None]
    blk = np.where(keep_d[np.ix_(q, q)], Tq.T @ Sp[:, q], 0)
    if sym:
        blk = blk + np.where(keep_m[np.ix_(q, q)], Tq.T @ Sm[:, q], 0)
    X[np.ix_(q, q)] += (1/(1j*line.w))*blk
    return X


def zspec(cell, k, sign):
    """z spectra of the z functions: sign -1: T = int f exp(-j k z) dz; +1: C = (1/P) int f exp(+j k z)."""
    out = np.zeros(len(cell.zfs), complex)
    for i, (typ, a, b) in enumerate(cell.zfs):
        if typ == "D":
            out[i] = np.exp(sign*1j*k*a)
        else:
            h = b - a; s = sign*1j*k*h
            pre = h*np.exp(sign*1j*k*a)
            I1, Iu = complex(fw._If(s, "1")), complex(fw._If(s, "u"))
            out[i] = pre*{"p": I1, "u": Iu, "d": I1 - Iu}[typ]
    return out if sign < 0 else out/cell.P


def piece_maps(cell):
    rows, cols, coef, zf = [], [], [], []
    for i, (cur, div) in enumerate(zip(cell.B, cell.Q)):
        for p, f, c in cur + div:
            rows.append(p); cols.append(i); coef.append(c); zf.append(f)
    return np.array(rows), np.array(cols), np.array(coef), np.array(zf)


_HCTX = {}


def _harm_part(ms):
    """Sum of the harmonic terms m in ms (worker; context in _HCTX, inherited by fork)."""
    try:
        from threadpoolctl import threadpool_limits
        lim = threadpool_limits(1)
    except ImportError:
        lim = None
    cell, xs, line, beta, Mc, pm = (_HCTX[k] for k in ("cell", "xs", "line", "beta", "Mc", "pm"))
    N, P, w, k0 = cell.N, cell.P, line.w, line.k0
    rows, cols, coef, zf = pm
    comp = xs.comp
    same = (comp[:, None] == comp[None, :])
    isq = comp == 3
    Z = np.zeros((N, N), complex)
    for m in ms:
        km = beta + 2*np.pi*m/P
        kref = abs(2*np.pi*m/P) + np.sqrt(line.eps_bot.real)*k0      # beta-independent choices
        X = spec_kernel(xs, line, km, kref=kref)
        if abs(m) <= Mc:
            D = dyn_kernel(xs, km, k0)
            A = (D["d"] + XSIGN[comp][None, :]*D["x"])*same
            X += (-1j*w*MU0)*np.where(isq[:, None] | isq[None, :], 0, A)
            Q = (D["d"] + D["x"]) + line.K*(D["y"] + D["xy"])
            X += (-1/(1j*w*EPS0))*np.where(isq[:, None] & isq[None, :], Q, 0)
        Tz, Cz = zspec(cell, km, -1), zspec(cell, km, +1)
        V = sparse.csr_matrix((coef*Tz[zf], (rows, cols)), shape=(xs.n, N))
        W = sparse.csr_matrix((coef*Cz[zf], (rows, cols)), shape=(xs.n, N))
        Z += V.T @ (W.T @ X.T).T
    return Z


def harmonic_Z(cell, xs, line, beta, Mc, Ks, pm=None, verbose=False, workers=4):
    """Sum over harmonics of the dynamic correction (|m| <= Mc) and the reflected part
    (|k_m| <= Ks), assembled with the z spectra.  workers: harmonics shared among processes
    (each harmonic is independent; the sum is the same up to rounding)."""
    import multiprocessing as mp
    P, k0 = cell.P, line.k0
    pm = pm if pm is not None else piece_maps(cell)
    Mmax = int(np.floor(Ks*P/(2*np.pi))) + 1
    ms = [m for m in range(-Mmax, Mmax + 1)
          if not (abs(2*np.pi*m/P) + np.sqrt(line.eps_bot.real)*k0 > Ks and abs(m) > Mc)]
    if not hasattr(xs, "_t"):                        # pair distances, shared with the workers
        dyn_kernel(xs, beta, k0)
    _HCTX.update(cell=cell, xs=xs, line=line, beta=beta, Mc=Mc, pm=pm)
    if workers <= 1:
        return _harm_part(ms)
    # the costly harmonics (|m| <= Mc: dynamic part as well) dealt out first, round robin
    order = sorted(ms, key=lambda m: (abs(m) > Mc, abs(m)))
    parts = [order[i::workers] for i in range(workers)]
    with mp.get_context("fork").Pool(workers) as pool:
        res = pool.map(_harm_part, parts)
    return sum(res)
