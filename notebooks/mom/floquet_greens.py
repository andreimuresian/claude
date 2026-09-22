"""Floquet-periodic layered-medium Green's function (Ewald-split).

For a structure periodic with period P along the propagation axis v and Bloch
wavenumber beta, the periodic kernel is

    G_p(du, dv; beta) = sum_m G(R_m) exp(j beta m P),
    R_m = sqrt(du^2 + (dv - m P)^2)

with G the Phase-1 same-interface layered kernel.  A direct lattice sum does not
converge usefully here: beyond ~400 um the kernel is dominated by the TE0/TM0
surface waves and falls off only as 1/sqrt(rho), so the sum is still drifting at
800 images.  We therefore Ewald-split in the SPECTRAL domain with a Gaussian:

    G~(krho) = G~(krho) exp(-krho^2/4E^2)      "soft"
             + G~(krho) [1 - exp(-krho^2/4E^2)] "sharp"

* soft  -- keeps the low-krho content, hence the surface-wave poles.  Its
  Floquet sum is done in the spectral domain, where the Gaussian makes the
  harmonic series converge like exp(-beta_n^2/4E^2): a dozen harmonics.
* sharp -- low-krho suppressed, so in real space it is the mollified
  singularity: it still carries the whole 1/rho behaviour as rho -> 0 (so the
  Phase-2 singularity extraction applies unchanged, with the same K), but it
  does NOT decay as a Gaussian.  A Gaussian split in krho leaves
  exp(-x) I0(x) ~ 1/sqrt(2 pi x), so the static sharp part falls off only
  algebraically, ~ K/(4 E^2 rho^3).  At one period it is still ~0.7 % of K/rho
  for E*P = 6, so the radial table must reach several periods and a few images
  (n_sharp) are needed.  Truncating that table at a few 1/E -- which scales
  with E -- is precisely what destroys Ewald invariance.

Choosing E*P ~ 6 puts both series at a handful of terms.  The split point E is
arbitrary, so invariance of G_p under changing E is the primary correctness
test (gate V3.1b).
"""
import warnings
import numpy as np
from scipy import integrate, special
from scipy.interpolate import CubicSpline
import stack_params as sp
from layered_greens import Stack, EPS0, MU0, C0

warnings.filterwarnings("ignore")


def _tail_T(a_grid):
    """T(a) = Int_a^inf J0(u)/u^2 du, tabulated once.  Used to add the 1/k^3
    asymptotic tail of (G~ - C/k) analytically: a log grid cannot resolve the
    J0(k rho) oscillation out at k ~ 1e8, so integrating that tail numerically
    aliases badly at large rho."""
    out = []
    for a in a_grid:
        tot, seg = 0.0, a
        # integrate over successive J0 half-periods until negligible
        for _ in range(400):
            nxt = seg + np.pi
            tot += integrate.quad(lambda u: special.j0(u)/(u*u), seg, nxt,
                                  limit=60)[0]
            seg = nxt
            if seg > max(60.0, 40*a) and abs(1.0/seg) < 1e-14*max(abs(tot), 1e-30):
                break
        out.append(tot)
    return np.array(out)


_A_GRID = np.logspace(-5, 3.2, 260)
_T_TAB = None


def _T_of(a):
    global _T_TAB
    if _T_TAB is None:
        _T_TAB = CubicSpline(np.log(_A_GRID), _tail_T(_A_GRID))
    a = np.clip(a, _A_GRID[0], _A_GRID[-1])
    return _T_TAB(np.log(a))


class FloquetKernel:
    """Ewald-split Floquet kernel for one stack, one period, one polarisation
    pair (scalar G_q and vector G_A are built together).

    Usage:
        fk = FloquetKernel(t_LN, P)          # geometry-dependent, build once
        fk.set_beta(beta)                    # cheap-ish, per Bloch iterate
        fk.Gq_sharp(rho), fk.GA_sharp(rho)   # radial, singular, m=0 only
        fk.Gq_soft_p(du, dv), fk.GA_soft_p(du, dv)   # smooth periodic part
    """

    def __init__(self, t_LN, P=200e-6, f=sp.F0, EP=6.0, n_rad=140,
                 nk=1200, kfac=8.0):
        self.st = Stack(sp.EPS_AIR, sp.device_layers(t_LN=t_LN, lossy=True),
                        sp.EPS_AIR, f=f)
        self.f = f
        self.w = 2*np.pi*f
        self.k0 = self.w/C0
        self.P = P
        self.E = EP/P                       # Ewald splitting parameter [1/m]
        # provisional; raised in _measure_poles so the surface-wave poles
        # always sit inside the soft (spectral) part -- if they fall in the
        # sharp part its real-space lattice sum inherits the 1/sqrt(rho)
        # surface-wave tail and stops converging.
        self._EP = EP
        self.Cq = complex(self.st._asym("TM"))
        self.CA = complex(self.st._asym("TE"))
        self.Kq = self.Cq/(2*np.pi)         # G -> K/rho as rho->0
        self.KA = self.CA/(2*np.pi)
        self.nk = nk
        self.kmax = kfac*self.E             # Gaussian kills the integrand here
        self._measure_poles()
        self.E = max(self.E, 3.0*max(self.pole_k))
        self.kmax = kfac*self.E
        # sharp part falls off only ~1/(4 E^2 rho^3): few images when E*P
        # is large, more when it is small
        self.n_sharp = 1 if self.E*self.P > 20 else 4
        self._build_radial(n_rad)
        self.beta = None

    def _measure_poles(self):
        """Locate the surface-wave poles on the real krho axis and measure their
        width.  With sigma_Si = 2.5e-4 the TM0 pole is extremely sharp (relative
        FWHM ~1e-5); any quadrature grid that does not resolve it silently drops
        ~40 % of the spectral integral, and because a uniform grid's spacing
        scales with the Ewald parameter that shows up as fake E-dependence."""
        self.pole_k, self.pole_w = [], []
        for npole in self.st._poles():
            kp = npole*self.k0
            ks = np.linspace(kp*0.99, kp*1.01, 40001)
            v = np.abs(self.st.Gq_spectral(ks)) + np.abs(self.st.GA_spectral(ks))
            i = int(v.argmax())
            hi = np.where(v > v[i]/2)[0]
            w = (ks[hi[-1]]-ks[hi[0]]) if len(hi) > 1 else 1e-3*kp
            self.pole_k.append(ks[i])
            self.pole_w.append(max(w, 1e-9*kp))

    def _ku_grid(self, bn):
        """Quadrature grid in ku for one harmonic: a coarse base plus a
        geometric cluster around every surface-wave pole that the path crosses
        (krho = sqrt(ku^2+bn^2) = k_pole).  Only low harmonics cross at all."""
        g = [np.linspace(0.0, self.kmax, self.nk)]
        b2 = (bn*bn).real if np.iscomplexobj(bn) else bn*bn
        for kp, wp in zip(self.pole_k, self.pole_w):
            if kp*kp <= b2:
                continue                      # pole not on this path
            kup = np.sqrt(kp*kp - b2)
            wku = wp*kp/max(kup, 1e-6)        # width mapped into ku
            d = wku*np.concatenate([-np.logspace(4, -3, 220),
                                    np.logspace(-3, 4, 220)])
            g.append(np.clip(kup + d, 0.0, self.kmax))
        ku = np.unique(np.concatenate(g))
        return ku

    # ---------- soft radial part (for the sharp = G - soft split) ----------
    def _soft_radial(self, rho):
        """(1/2pi) Int_0^inf G~(k) exp(-k^2/4E^2) J0(k rho) k dk  for G_q, G_A."""
        E2 = 4*self.E**2
        # bracket each (very sharp) surface-wave pole tightly so the adaptive
        # quadrature cannot step over it
        pol = []
        for kp, wp in zip(self.pole_k, self.pole_w):
            pol += [kp - 40*wp, kp - 4*wp, kp, kp + 4*wp, kp + 40*wp]
        mat = [self.k0*np.sqrt(abs(e)) for e in
               [self.st.top_eps, self.st.bot_eps] + [e for e, _ in self.st.layers]]
        brk = sorted(b for b in set(pol + mat) if 0 < b < self.kmax)
        seg = [0.0] + brk + [self.kmax]
        out = []
        for spec in (self.st.Gq_spectral, self.st.GA_spectral):
            tot = 0.0 + 0j
            for a, b in zip(seg[:-1], seg[1:]):
                fr = lambda k: (spec(k)*np.exp(-k*k/E2)*special.j0(k*rho)*k).real
                fi = lambda k: (spec(k)*np.exp(-k*k/E2)*special.j0(k*rho)*k).imag
                tot += (integrate.quad(fr, a, b, limit=200)[0]
                        + 1j*integrate.quad(fi, a, b, limit=200)[0])
            out.append(tot/(2*np.pi))
        return out[0], out[1]

    def _build_radial(self, n_rad):
        """Tabulate the SHARP radial kernels  G_sharp = G_full - G_soft.

        The soft part is Gaussian-damped in krho, so it is a short, well behaved
        integral: one pole-resolved grid applied to every rho at once.  The
        sharp part, however, carries the whole high-krho content, and that
        cannot be reconstructed from an asymptote here: the LN film is only
        ~0.3 um thick, so G~ does not reach its C/krho asymptote until
        krho >> 1/t_LN ~ 3e6, far beyond kmax = 8E.  We therefore take G_full
        from the Phase-1 Sommerfeld routine (which handles that tail with its
        Hankel-split contour) and subtract the soft part."""
        rho_max = max((self.n_sharp + 1.5)*self.P, 20.0/self.E)
        rho = np.logspace(np.log10(2e-8), np.log10(rho_max), n_rad)
        GA_f, Gq_f = self.st.table(rho)          # Phase-1 validated full kernel

        # --- soft radial, vectorised over rho on one pole-resolved grid ------
        kk = self._ku_grid(0.0)
        kk = kk[kk > 0]
        wq = np.empty_like(kk)
        wq[1:-1] = 0.5*(kk[2:]-kk[:-2])
        wq[0] = 0.5*(kk[1]-kk[0]); wq[-1] = 0.5*(kk[-1]-kk[-2])
        gauss = np.exp(-kk*kk/(4*self.E**2))
        wq_q = self.st.Gq_spectral(kk)*gauss*kk*wq/(2*np.pi)
        wq_a = self.st.GA_spectral(kk)*gauss*kk*wq/(2*np.pi)
        J = special.j0(np.outer(rho, kk))
        softq = J @ wq_q
        softa = J @ wq_a

        shq = Gq_f - softq
        sha = GA_f - softa
        lr = np.log(rho)
        self.rho_tab = rho
        self._soft_rad = (softq, softa)
        self._shq = (CubicSpline(lr, shq.real), CubicSpline(lr, shq.imag))
        self._sha = (CubicSpline(lr, sha.real), CubicSpline(lr, sha.imag))

    def Gq_sharp(self, rho):
        lr = np.log(np.clip(rho, self.rho_tab[0], self.rho_tab[-1]))
        return self._shq[0](lr) + 1j*self._shq[1](lr)

    def GA_sharp(self, rho):
        lr = np.log(np.clip(rho, self.rho_tab[0], self.rho_tab[-1]))
        return self._sha[0](lr) + 1j*self._sha[1](lr)

    # ---------- soft periodic part (spectral Floquet sum) ------------------
    def set_beta(self, beta, du_grid=None, nharm=None):
        """Precompute I_n(du) for the harmonics that survive the Gaussian."""
        self.beta = complex(beta)
        E2 = 4*self.E**2
        if nharm is None:
            # keep harmonics with exp(-|beta_n|^2/4E^2) > ~1e-10
            nharm = int(np.ceil((np.sqrt(10*np.log(10))*2*self.E
                                 + abs(beta.real if hasattr(beta, "real") else beta))
                                * self.P/(2*np.pi))) + 2
        self.nharm = nharm
        if du_grid is None:
            du_grid = np.concatenate([[0.0],
                                      np.logspace(np.log10(2e-7), np.log10(6e-4), 180)])
        self.du_grid = du_grid
        ns = np.arange(-nharm, nharm+1)
        self.betan = self.beta + 2*np.pi*ns/self.P
        Iq = np.empty((len(ns), len(du_grid)), complex)
        Ia = np.empty((len(ns), len(du_grid)), complex)
        for i, bn in enumerate(self.betan):
            ku = self._ku_grid(bn)                       # pole-resolving grid
            wq = np.empty_like(ku)                       # trapezoid, non-uniform
            wq[1:-1] = 0.5*(ku[2:] - ku[:-2])
            wq[0] = 0.5*(ku[1] - ku[0])
            wq[-1] = 0.5*(ku[-1] - ku[-2])
            kr = np.sqrt(ku*ku + bn*bn)
            gauss = np.exp(-(ku*ku + bn*bn)/E2)
            gq = self.st.Gq_spectral(kr)*gauss*wq
            ga = self.st.GA_spectral(kr)*gauss*wq
            # I_n(du) = (1/2pi) Int_-inf^inf ... = (1/pi) Int_0^inf ... cos(ku du)
            cos = np.cos(np.outer(du_grid, ku))
            Iq[i] = cos @ gq/np.pi
            Ia[i] = cos @ ga/np.pi
        self._Iq, self._Ia = Iq, Ia
        self._Iq_i = [CubicSpline(du_grid, Iq[i].real) for i in range(len(ns))]
        self._Iq_j = [CubicSpline(du_grid, Iq[i].imag) for i in range(len(ns))]
        self._Ia_i = [CubicSpline(du_grid, Ia[i].real) for i in range(len(ns))]
        self._Ia_j = [CubicSpline(du_grid, Ia[i].imag) for i in range(len(ns))]

    def soft_p(self, du, dv):
        """Smooth periodic part (G_q, G_A) at lateral offsets (du, dv)."""
        du = np.atleast_1d(np.abs(du)); dv = np.atleast_1d(dv)
        du = np.clip(du, self.du_grid[0], self.du_grid[-1])
        gq = np.zeros(du.shape, complex); ga = np.zeros(du.shape, complex)
        for i, bn in enumerate(self.betan):
            ph = np.exp(1j*bn*dv)      # Poisson gives exp(+j beta_n dv)
            gq += (self._Iq_i[i](du) + 1j*self._Iq_j[i](du))*ph
            ga += (self._Ia_i[i](du) + 1j*self._Ia_j[i](du))*ph
        return gq/self.P, ga/self.P

    # ---------- full periodic kernel ---------------------------------------
    def G_periodic(self, du, dv, n_sharp=None):
        if n_sharp is None:
            n_sharp = self.n_sharp
        """G_q,p and G_A,p.  The sharp part needs only |m| <= n_sharp images."""
        du = np.atleast_1d(du); dv = np.atleast_1d(dv)
        gq, ga = self.soft_p(du, dv)
        for m in range(-n_sharp, n_sharp+1):
            R = np.hypot(du, dv - m*self.P)
            ph = np.exp(1j*self.beta*m*self.P)
            gq = gq + self.Gq_sharp(R)*ph
            ga = ga + self.GA_sharp(R)*ph
        return gq, ga
