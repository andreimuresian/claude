"""Full-wave 2D MoM of the thick-metal line over the stack: Z(beta) and the mode.

Direct part: mixed potentials in the spatial domain, G = K0(gamma rho)/(2 pi).
Reflected part: spectral in x with the stack's 2x2 reflection (stack.py), all three field
components; the quasi-static image of the LN half-space (scalar potential, coefficient K)
is subtracted from the spectral integrand and added back in the spatial domain.
Unknowns [t (rooftops J_t at the nodes), z (pulses J_z on the segments)]; Galerkin.
"""
import numpy as np
from scipy import special

import mom2d as M
import stack as S

EPS0, MU0, C0 = M.EPS0, 4e-7*np.pi, 299792458.0


def _If(a, kind):
    """int_0^1 f(u) e^{a u} du for f = 1 ('1') or u ('u'); series for small |a|."""
    a = np.asarray(a, complex)
    small = np.abs(a) < 1e-3
    out = np.empty(a.shape, complex)
    ab = np.where(small, 1.0, a)
    if kind == "1":
        out = np.where(small, 1 + a/2 + a*a/6 + a**3/24, (np.exp(ab) - 1)/ab)
    else:
        out = np.where(small, 0.5 + a/3 + a*a/8 + a**3/30, (np.exp(ab)*(ab - 1) + 1)/ab**2)
    return out


def g00_pair(go, gs, gamma):
    """int_a int_b G for observation segments of go, source segments of gs."""
    qp, qw = go.qp, go.qw
    I0, _ = M._log_inner(gs, qp)
    w = qw[None, :, None]*go.L[:, None, None]
    G = (-(1/(2*np.pi))*I0*w).sum(1)
    d = qp[:, :, None, None, :] - gs.qp[None, None, :, :, :]
    rho = np.linalg.norm(d, axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        sm = np.where(rho > 0, special.kv(0, gamma*rho) + np.log(rho), -np.log(gamma/2) - np.euler_gamma)/(2*np.pi)
    wa = (qw[None, :]*go.L[:, None])[:, :, None, None]
    wb = (gs.qw[None, :]*gs.L[:, None])[None, None, :, :]
    return G + (sm*wa*wb).sum((1, 3))


def mirrored(g):
    gm = M.Geometry.__new__(M.Geometry)
    gm.__dict__.update(g.__dict__)
    gm.p0 = g.p0*[1, -1]; gm.p1 = g.p1*[1, -1]
    gm.t = (gm.p1 - gm.p0)/g.L[:, None]
    gm.qp = g.qp*[1, -1]
    return gm


class Line2D:
    def __init__(self, g, f, layers, bottom, eps_eff, kq=None):
        self.g, self.f = g, f
        self.w = 2*np.pi*f
        self.k0 = self.w/C0
        self.layers, self.bottom = layers, bottom
        self.K = (1 - eps_eff)/(1 + eps_eff)
        n, m = g.nseg, g.nnode
        self.Ss = np.zeros((n, m)); self.Ss[np.arange(n), g.sn] = 1
        self.Se = np.zeros((n, m)); self.Se[np.arange(n), g.en] = 1
        self.D = (self.Se - self.Ss)/g.L[:, None]
        self.kq = kq or {}
        self.eps_bot = complex(bottom[0])
        self.gm = mirrored(g)

    def make_grid(self, beta, nb=160):
        """k >= 0 quadrature: Gauss pieces clustered (u^2 maps) at the bottom half-space branch
        point k_b = sqrt(eps_Si k0^2 - beta^2) up to 4 k_Si, then the coarse kgrid; mirrored to k < 0."""
        k0 = self.k0
        kb = np.sqrt(max((self.eps_bot.real*k0**2 - beta.real**2), 0.0))
        k4 = 4*np.sqrt(self.eps_bot.real)*k0
        u, wu = np.polynomial.legendre.leggauss(nb)
        u, wu = 0.5*(u + 1), 0.5*wu
        ks, ws = [], []
        if kb > 0:
            ks.append(kb*(1 - (1 - u)**2)); ws.append(kb*2*(1 - u)*wu)        # [0, kb], clustered at kb
            ks.append(kb + (k4 - kb)*u**2); ws.append((k4 - kb)*2*u*wu)       # [kb, k4], clustered at kb
        else:
            ks.append(k4*u); ws.append(k4*wu)
        kc, wc = M.kgrid(**self.kq)
        sel = kc > k4
        wc = wc.copy(); wc[sel][:1] = wc[sel][:1]
        k = np.r_[np.concatenate(ks), kc[sel]]; w = np.r_[np.concatenate(ws), wc[sel]]
        self.k = np.r_[-k[::-1], k]; self.kw = np.r_[w[::-1], w]

    def _pieces(self, ky, sign):
        """Spectral factors of the segment pieces: start (1-u), end (u), pulse; sign +1 source
        (e^{+jkx}), -1 test (e^{-jkx}).  Vertical factor e^{-j ky y} in both cases."""
        g, k = self.g, self.k[:, None]
        x0, y0, x1, y1 = g.p0[:, 0], g.p0[:, 1], g.p1[:, 0], g.p1[:, 1]
        hor = np.abs(y1 - y0) < 1e-15
        ky = ky[:, None]
        a = np.where(hor, sign*1j*k*(x1 - x0), -1j*ky*(y1 - y0))
        pref = np.where(hor, np.exp(sign*1j*k*x0 - 1j*ky*y0), np.exp(sign*1j*k*x0 - 1j*ky*y0))
        L = g.L[None, :]
        I1, Iu = _If(a, "1"), _If(a, "u")
        return pref*L*(I1 - Iu), pref*L*Iu, pref*L*I1

    def Z(self, beta):
        g, w, k0 = self.g, self.w, self.k0
        self.make_grid(beta)
        gamma = np.sqrt(beta**2 - k0**2 + 0j)
        G00, G10, G01, G11 = M.kernel_blocks(g, gamma)
        Tdot = g.t @ g.t.T
        Gss, Gse, Ges, Gee = G00 - G10 - G01 + G11, G01 - G11, G10 - G11, G11
        Ss, Se, D = self.Ss, self.Se, self.D
        ZttA = -1j*w*MU0*(Ss.T @ (Tdot*Gss) @ Ss + Ss.T @ (Tdot*Gse) @ Se + Se.T @ (Tdot*Ges) @ Ss + Se.T @ (Tdot*Gee) @ Se)
        Qt = -(1/(1j*w))*D
        Qz = (beta/w)*np.eye(g.nseg)
        # spectral reflected part
        air = S.Air(self.k, beta, k0)
        R = air.reflection(S.stack_admittance(self.k, beta, k0, self.layers, self.bottom, leaky=True))
        ky = air.ky
        Dc = [air.sheet_down(J)[0] for J in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]   # (Nk, 2) each
        M3 = np.stack([air.up_field((R @ d[..., None])[..., 0]) for d in Dc], -1)  # (Nk, 3 obs, 3 src)
        ss, se, sz = self._pieces(ky, +1)
        ts, te, tz = self._pieces(ky, -1)
        tx, ty = g.t[:, 0], g.t[:, 1]
        kw = self.kw[:, None]/(2*np.pi)
        def blk(T, oc, Sr, sc):
            """sum over components: int T_a (o_a . M3 . s_b) S_b dk"""
            out = 0
            for i, oi in enumerate(oc):
                for j, sj in enumerate(sc):
                    if oi is None or sj is None:
                        continue
                    m = M3[:, i, j][:, None]
                    out = out + ((T*oi[None, :]*kw*m).T @ (Sr*sj[None, :]))
            return out
        oc_t = [tx, ty, None]; sc_t = [tx, ty, None]
        oc_z = [None, None, np.ones(g.nseg)]; sc_z = [None, None, np.ones(g.nseg)]
        R_ss = blk(ts, oc_t, ss, sc_t); R_se = blk(ts, oc_t, se, sc_t)
        R_es = blk(te, oc_t, ss, sc_t); R_ee = blk(te, oc_t, se, sc_t)
        R_tz_s = blk(ts, oc_t, sz, sc_z); R_tz_e = blk(te, oc_t, sz, sc_z)
        R_zt_s = blk(tz, oc_z, ss, sc_t); R_zt_e = blk(tz, oc_z, se, sc_t)
        R_zz = blk(tz, oc_z, sz, sc_z)
        Zr_tt = Ss.T @ R_ss @ Ss + Ss.T @ R_se @ Se + Se.T @ R_es @ Ss + Se.T @ R_ee @ Se
        Zr_tz = Ss.T @ R_tz_s + Se.T @ R_tz_e
        Zr_zt = R_zt_s @ Ss + R_zt_e @ Se
        # image: spatial minus spectral version of the same quasi-static term
        Phi_img = self.K*g00_pair(g, self.gm, gamma)/EPS0
        Phi_spec = ((tz*kw*(self.K/(2*EPS0*1j*ky))[:, None]).T @ sz)
        dPhi = Phi_img - Phi_spec
        Phi = G00/EPS0
        Ptot = Phi + dPhi
        Ztt = ZttA + D.T @ Ptot @ Qt + Zr_tt
        Ztz = D.T @ Ptot @ Qz + Zr_tz
        Zzt = 1j*beta*Ptot @ Qt + Zr_zt
        Zzz = -1j*w*MU0*G00 + 1j*beta*Ptot @ Qz + R_zz
        return np.block([[Ztt, Ztz], [Zzt, Zzz]])

    def gfun(self, beta, y=None):
        Z = self.Z(beta)
        if y is None:
            y = np.zeros(Z.shape[0]); nn = self.g.nnode
            y[nn:][self.g.owner == 0] = self.g.L[self.g.owner == 0]      # J_z test on the signal
        return 1/(y @ np.linalg.solve(Z, y))


def find_mode(line, n0, tol=1e-7, maxit=12, dn=0.01):
    """Complex secant on g(beta) = 0 (Z evaluated at complex beta, real-axis k integration)."""
    k0 = line.k0
    b0, b1 = n0*k0, (n0 + dn)*k0
    g0, g1 = line.gfun(b0), line.gfun(b1)
    for it in range(maxit):
        b2 = b1 - g1*(b1 - b0)/(g1 - g0)
        if abs(b2 - b1) < tol*abs(b1):
            return b2, it
        b0, g0, b1, g1 = b1, g1, b2, line.gfun(b2)
    return b1, maxit
