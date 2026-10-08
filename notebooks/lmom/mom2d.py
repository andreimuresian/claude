"""2D (z-invariant) MoM of the thick-metal CPW over the layered TFLN stack.

Metal: rectangles (signal, two grounds) in the air half-space y in [0, t], bottom faces on
the LN.  Unknowns on every metal face, closed contours, graded toward the corners:
    J_t (along the contour): rooftops at the contour nodes,
    J_z (along the line):   pulses on the segments.
Green's function of the air half-space over the stack = free space + reflected:
    free space, spatial domain:  G = K0(gamma rho) / (2 pi), gamma = sqrt(beta^2 - k0^2),
        mixed potentials, log singularity integrated analytically;
    reflected, spectral domain in x (stack.py), with the quasi-static image of the LN
        half-space extracted and added back in the spatial domain.
This module: geometry, segment kernels, and the electrostatic check (C', C'_air).
"""
import numpy as np
from scipy import special

EPS0 = 8.8541878128e-12
GL = np.polynomial.legendre.leggauss(8)


def graded(L, hmin, hmax, growth=1.3):
    """Breakpoints on [0, L], hmin at both ends, growing to hmax."""
    left, h, s = [], hmin, 0.0
    while s + h < L/2:
        left.append(h); s += h; h = min(h*growth, hmax)
    rem = L - 2*s
    n = max(1, int(np.ceil(rem/hmax)))
    steps = left + [rem/n]*n + left[::-1]
    return np.r_[0, np.cumsum(steps)]


class Geometry:
    """Segments of all rectangle contours, counter-clockwise."""

    def __init__(self, rects, hmin, hmax):
        P0, P1, owner, start_node, end_node = [], [], [], [], []
        nodes = 0
        self.rect_seg = []
        for r, (x0, x1, y0, y1) in enumerate(rects):
            corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
            pts = []
            for c in range(4):
                a, b = np.array(corners[c]), np.array(corners[(c + 1) % 4])
                L = np.linalg.norm(b - a)
                br = graded(L, hmin, hmax)
                for u in br[:-1]:
                    pts.append(a + (b - a)*u/L)
            pts = np.array(pts)
            n = len(pts)
            first = len(P0)
            for i in range(n):
                P0.append(pts[i]); P1.append(pts[(i + 1) % n]); owner.append(r)
                start_node.append(nodes + i); end_node.append(nodes + (i + 1) % n)
            self.rect_seg.append(np.arange(first, first + n))
            nodes += n
        self.p0, self.p1 = np.array(P0), np.array(P1)
        self.owner, self.sn, self.en = np.array(owner), np.array(start_node), np.array(end_node)
        self.L = np.linalg.norm(self.p1 - self.p0, axis=1)
        self.t = (self.p1 - self.p0)/self.L[:, None]
        self.nseg, self.nnode = len(self.L), nodes
        u, w = GL
        self.qu, self.qw = 0.5*(u + 1), 0.5*w                          # Gauss on [0, 1]
        self.qp = self.p0[:, None, :] + self.qu[None, :, None]*(self.p1 - self.p0)[:, None, :]


def _log_inner(g, r):
    """For every segment b and point(s) r (..., 2): I0 = int_b ln|r - r'| ds',
    I1 = int_b (s'/L_b) ln|r - r'| ds'.  Returns arrays (..., nseg)."""
    d = r[..., None, :] - g.p0                                          # (..., nb, 2)
    u = np.einsum("...bk,bk->...b", d, g.t)
    v = np.einsum("...bk,bk->...b", d, np.stack([-g.t[:, 1], g.t[:, 0]], 1))
    L = g.L
    def F0(w):                                                           # int ln sqrt(w^2+v^2) dw
        r2 = w*w + v*v
        with np.errstate(divide="ignore", invalid="ignore"):
            lg = np.where(r2 > 0, np.log(r2), 0.0)
            at = np.where(np.abs(v) > 0, np.arctan2(w, np.abs(v))*np.abs(v), 0.0)
        return 0.5*w*lg - w + at
    def F1(w):                                                           # int w ln sqrt(w^2+v^2) dw
        r2 = w*w + v*v
        with np.errstate(divide="ignore", invalid="ignore"):
            lg = np.where(r2 > 0, np.log(r2), 0.0)
        return 0.25*(r2*lg - w*w)
    wa, wb = -u, L - u                                                   # w = s' - u
    I0 = F0(wb) - F0(wa)
    Iw = F1(wb) - F1(wa)
    I1 = (Iw + u*I0)/L
    return I0, I1


def kernel_blocks(g, gamma=None):
    """Segment-pair integrals of G = K0(gamma rho)/(2 pi) (gamma None: static -ln(rho)/(2 pi)):
    G00 = int_a int_b G, G10 = int (s/La) G, G01 = int (s'/Lb) G, G11 = int (s/La)(s'/Lb) G."""
    qp, qw, qu = g.qp, g.qw, g.qu
    I0, I1 = _log_inner(g, qp)                                           # (na, nq, nb)
    # log part: G_log = -(1/2pi) ln rho
    w = qw[None, :, None]*g.L[:, None, None]
    S0 = -(1/(2*np.pi))*I0*w
    S1 = -(1/(2*np.pi))*I1*w
    G00 = S0.sum(1); G01 = S1.sum(1)
    G10 = (S0*qu[None, :, None]).sum(1); G11 = (S1*qu[None, :, None]).sum(1)
    if gamma is not None:
        # smooth remainder (K0(gamma rho) + ln rho)/(2 pi), Gauss x Gauss
        d = qp[:, :, None, None, :] - qp[None, None, :, :, :]
        rho = np.linalg.norm(d, axis=-1)
        with np.errstate(divide="ignore", invalid="ignore"):
            sm = np.where(rho > 0, special.kv(0, gamma*rho) + np.log(rho), -np.log(gamma/2) - np.euler_gamma)
        sm = sm/(2*np.pi)
        wa = (qw[None, :]*g.L[:, None])[:, :, None, None]
        wb = (qw[None, :]*g.L[:, None])[None, None, :, :]
        T = sm*wa*wb
        ua = qu[None, :, None, None]; ub = qu[None, None, None, :]
        G00 = G00 + T.sum((1, 3)); G10 = G10 + (T*ua).sum((1, 3))
        G01 = G01 + (T*ub).sum((1, 3)); G11 = G11 + (T*ua*ub).sum((1, 3))
    return G00, G10, G01, G11


def static_capacitance(g, signal_rects, eps_image=None, refl=None):
    """C' per length with signal rectangles at 1 V, the others at 0, total charge zero.
    eps_image: add the quasi-static image of a dielectric half-space with this eps at y = 0
    (test of the image path).  refl: callable giving the extra potential matrix (spectral)."""
    G00 = kernel_blocks(g)[0]/EPS0                                      # potential per unit charge density
    P = G00/g.L[None, :]                                                # segment a potential integral per unit q (C/m) on b
    if eps_image is not None:
        K = (1 - eps_image)/(1 + eps_image)
        gm = Geometry.__new__(Geometry)
        gm.__dict__.update(g.__dict__)
        gm.p0 = g.p0*[1, -1]; gm.p1 = g.p1*[1, -1]
        gm.t = (gm.p1 - gm.p0)/g.L[:, None]
        Pm = np.zeros_like(P)
        # potential on segment a (Gauss points) from mirrored segment b
        I0, _ = _log_inner(gm, g.qp)
        Pm = (-(1/(2*np.pi))*I0*(g.qw[None, :, None]*g.L[:, None, None])).sum(1)/EPS0/g.L[None, :]
        P = P + K*Pm
    if refl is not None:
        P = P + refl
    n = g.nseg
    # unknowns: q_b (line charge on segment b, C/m total), and a constant phi_inf
    V = np.where(np.isin(g.owner, signal_rects), 1.0, 0.0)*g.L          # int_a phi ds = L_a V_a
    A = np.zeros((n + 1, n + 1))
    A[:n, :n] = P; A[:n, n] = g.L; A[n, :n] = 1.0
    sol = np.linalg.solve(A, np.r_[V, 0.0])
    q = sol[:n]
    return q[np.isin(g.owner, signal_rects)].sum(), q


def kgrid(kmax=2e8, k_lin=2e6, dk=1e3, ratio=1.01, kmin=1e2):
    """Quadrature on [kmin, kmax]: linear up to k_lin, geometric after.  Trapezoid weights."""
    k = np.r_[np.arange(kmin, k_lin, dk), k_lin*ratio**np.arange(0, int(np.log(kmax/k_lin)/np.log(ratio)) + 1)]
    w = np.gradient(k)
    return k, w


def seg_spectra(g, k, decay):
    """Per segment: int_seg exp(+j k x) exp(-decay y) ds / L (source, unit total), shape (Nk, nseg).
    decay: (Nk,) vertical decay constant (|k| for statics, j ky for waves)."""
    k = k[:, None]; dcy = decay[:, None]
    x0, y0, x1, y1 = g.p0[:, 0], g.p0[:, 1], g.p1[:, 0], g.p1[:, 1]
    hor = np.abs(y1 - y0) < 1e-15
    out = np.zeros((len(k), g.nseg), complex)
    # horizontal: exp(-decay y0) (exp(jk x1) - exp(jk x0)) / (jk L)
    xa, xb = np.minimum(x0, x1), np.maximum(x0, x1)
    out[:, hor] = (np.exp(-dcy*y0[hor])*(np.exp(1j*k*xb[hor]) - np.exp(1j*k*xa[hor]))/(1j*k*(xb - xa)[hor]))
    ya, yb = np.minimum(y0, y1), np.maximum(y0, y1)
    v = ~hor
    out[:, v] = np.exp(1j*k*x0[v])*(np.exp(-dcy*ya[v]) - np.exp(-dcy*yb[v]))/(dcy*(yb - ya)[v])
    return out


def refl_static(g, layers, bottom, K, f_static=1e6, **kq):
    """Reflected potential matrix (as in static_capacitance's P): spectral (R_s - K) part only;
    K's image is added in the spatial domain.  R_s from stack.py at beta = 0 and a tiny k0."""
    import stack as S
    k, w = kgrid(**kq)
    k0 = 2*np.pi*f_static/S.C0
    air = S.Air(k, 0.0, k0)
    Rs = air.reflection(S.stack_admittance(k, 0.0, k0, layers, bottom))[:, 0, 0]
    F = seg_spectra(g, k, k.astype(complex))                            # source, per unit charge
    T = np.conj(F)*g.L[None, :]                                         # test: int_a ds exp(-jkx) exp(-k y)
    kern = w*(Rs - K)/(2*EPS0*k)
    return np.real((T*kern[:, None]).T @ F)/np.pi
