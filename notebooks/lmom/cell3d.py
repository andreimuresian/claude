"""Periodic (Floquet) 3D MoM of one period of the line, built from the validated 2D kernel.

A current that is Bloch-periodic in z, f_B(z) = sum_n f(z - nP) exp(-j beta n P), is a sum of
Floquet harmonics exp(-j k_m z), k_m = beta + 2 pi m / P, with weights
    C_m = (1/P) int f(z) exp(+j k_m z) dz            (Poisson summation).
Each harmonic of a current  e(x, y) exp(-j k_m z)  radiates exactly as the 2D problem at
beta = k_m, so with test functions t(z) e'(x, y) the 3D Galerkin matrix is
    Z3D[(e', t), (e, f)] = sum_m  T_m(t) C_m(f) Z2D(k_m)[e', e],
    T_m(t) = int t(z) exp(-j k_m z) dz,
where Z2D(beta) is Line2D.Z (direct K0 + spectral stack reflection + LN image; leaky
branch handled there).  The z-derivative in the charge term becomes -j k_m on each harmonic,
which is what Line2D.Z already uses for J_z.  No ports, no Ewald split: the eigenvalue
beta of the periodic cell is found by the same complex secant as in 2D.

Plain cell (this file): the cross-section is the same at every z.  Unknowns
    J_t: 2D rooftop at contour node n  x  pulse on z-cell k,
    J_z: 2D pulse on segment s         x  rooftop centred on z-node k,
on a uniform z grid of Nz cells.  The exact Bloch mode is exp(-j beta z) (u_t, u_z): the
3D result must reproduce the 2D one as Nz and the harmonic range grow.
"""
import numpy as np

P_DEFAULT = 200e-6


def pulse_spec(a, h, k):
    """int_a^{a+h} exp(-j k z) dz for arrays a (cells) and k (harmonics): (ncell, nk)."""
    a = np.asarray(a)[:, None]; k = np.asarray(k)[None, :]
    return h*np.exp(-1j*k*(a + h/2))*np.sinc(k*h/(2*np.pi))


def roof_spec(z0, h, k):
    """int of the unit rooftop centred at z0, half-width h, times exp(-j k z)."""
    z0 = np.asarray(z0)[:, None]; k = np.asarray(k)[None, :]
    return h*np.exp(-1j*k*z0)*np.sinc(k*h/(2*np.pi))**2


class PlainCell:
    """line: fw.Line2D of the cross-section; Nz uniform z cells over the period P."""

    def __init__(self, line, Nz, P=P_DEFAULT):
        self.line, self.Nz, self.P = line, Nz, P
        self.h = P/Nz
        self.nn, self.ns = line.g.nnode, line.g.nseg
        self.cache = {}                                   # m -> (beta_m, Z2D)

    def z2d(self, km, m, refresh):
        if refresh or m not in self.cache:
            self.cache[m] = (km, self.line.Z(km))
        return self.cache[m][1]

    def Z(self, beta, M, m_fresh=1):
        """3D matrix for harmonics |m| <= M.  Harmonics with |m| > m_fresh are reused from the
        cache (computed at an earlier beta): they change by O(d beta / (2 pi m / P))."""
        nn, ns, Nz, h, P = self.nn, self.ns, self.Nz, self.h, self.P
        ms = np.arange(-M, M + 1)
        km = beta + 2*np.pi*ms/P
        zc = np.arange(Nz)*h                              # cell starts = node positions
        Tp, Tr = pulse_spec(zc, h, km), roof_spec(zc, h, km)
        Cp, Cr = pulse_spec(zc, h, -km)/P, roof_spec(zc, h, -km)/P
        Ztt = np.zeros((Nz, nn, Nz, nn), complex); Ztz = np.zeros((Nz, nn, Nz, ns), complex)
        Zzt = np.zeros((Nz, ns, Nz, nn), complex); Zzz = np.zeros((Nz, ns, Nz, ns), complex)
        for i, m in enumerate(ms):
            Z2 = self.z2d(km[i], m, abs(m) <= m_fresh)
            tt, tz, zt, zz = Z2[:nn, :nn], Z2[:nn, nn:], Z2[nn:, :nn], Z2[nn:, nn:]
            Ztt += np.einsum("k,l,ab->kalb", Tp[:, i], Cp[:, i], tt)
            Ztz += np.einsum("k,l,ab->kalb", Tp[:, i], Cr[:, i], tz)
            Zzt += np.einsum("k,l,ab->kalb", Tr[:, i], Cp[:, i], zt)
            Zzz += np.einsum("k,l,ab->kalb", Tr[:, i], Cr[:, i], zz)
        Nt, Nzz = Nz*nn, Nz*ns
        return np.block([[Ztt.reshape(Nt, Nt), Ztz.reshape(Nt, Nzz)],
                         [Zzt.reshape(Nzz, Nt), Zzz.reshape(Nzz, Nzz)]])

    def gfun(self, beta, M, m_fresh=1):
        Z = self.Z(beta, M, m_fresh)
        g = self.line.g
        y = np.zeros(Z.shape[0])
        y[self.Nz*self.nn:][:self.ns][g.owner == 0] = g.L[g.owner == 0]   # J_z on the signal, z-node 0
        return 1/(y @ np.linalg.solve(Z, y))


def find_mode(cell, n0, M, tol=1e-7, maxit=12, dn=0.01, m_fresh=1):
    k0 = cell.line.k0
    b0, b1 = n0*k0, (n0 + dn)*k0
    g0, g1 = cell.gfun(b0, M, m_fresh), cell.gfun(b1, M, m_fresh)
    for it in range(maxit):
        b2 = b1 - g1*(b1 - b0)/(g1 - g0)
        if abs(b2 - b1) < tol*abs(b1):
            return b2, it
        b0, g0, b1, g1 = b1, g1, b2, cell.gfun(b2, M, m_fresh)
    return b1, maxit


def plain_impedance(cell, beta0, M):
    """Z_PI = N / I(z=0)^2 of the Bloch mode of the plain cell (fw.impedance with scale P).
    Partner (backward) mode for reciprocity: J_t(-z), -J_z(-z); for the plain cell that is
    exp(+j beta0 z) (u_t, -u_z) on the same local basis over one period."""
    import fw
    nn, ns, Nz, h = cell.nn, cell.ns, cell.Nz, cell.h
    g = cell.line.g
    Zf = lambda b: cell.Z(b, M, m_fresh=M)
    Z0 = Zf(beta0)
    y = np.zeros(Z0.shape[0]); y[Nz*nn:][:ns][g.owner == 0] = g.L[g.owner == 0]
    J = fw.mode_current(Z0, y)                          # I(z=0) = y.J = 1
    Jt, Jz = J[:Nz*nn].reshape(Nz, nn), J[Nz*nn:].reshape(Nz, ns)
    zc, zn = (np.arange(Nz) + 0.5)*h, np.arange(Nz)*h
    ut = Jt*np.exp(1j*beta0*zc)[:, None]                 # forward: J_t(z) = u_t exp(-j beta z)
    uz = Jz*np.exp(1j*beta0*zn)[:, None]
    Jb = np.r_[(ut*np.exp(1j*beta0*zc)[:, None]).ravel(), (-uz*np.exp(1j*beta0*zn)[:, None]).ravel()]
    spread = np.abs(ut - ut.mean(0)).max()/np.abs(ut).max(), np.abs(uz - uz.mean(0)).max()/np.abs(uz).max()
    Zpi, N = fw.impedance(Zf, beta0, J, Jb, 1.0, scale=cell.P)
    return Zpi, N, spread
