"""Layered-medium mixed-potential Green's functions for the TFLN stack.

Same-interface (source & observation both on the metal plane) scalar-potential
kernel G_q(rho) and vector-potential kernel G_A(rho), built from the
transmission-line Green's function of the stratified medium and inverted to real
space by a Sommerfeld integral with quasi-static singularity extraction.

Conventions
-----------
SI units, metres.  Time convention exp(+j w t).  Vertical axis z; the metal
plane is z = 0, the interface between the top half-space (air) and the first
layer below.  For a layer:  k_z = sqrt(k^2 - krho^2), branch Im(k_z) <= 0 so
exp(-j k_z z) decays into z > 0.

Potential admittances (the combinations that appear in the same-interface
kernels, derived and checked against the free-space Sommerfeld identity and the
static two-dielectric image result):
    TM (scalar potential):  eta   = eps_r * k_z
    TE (vector potential):  zeta  = k_z
A finite layer transforms its load admittance by the standard lossless-line
input-admittance formula.  Then
    G~_q(krho) = 1 / ( j eps0 (eta_up  + eta_dn ) )
    G~_A(krho) = mu0 / ( j       (zeta_up + zeta_dn) )
which reduce to the free-space  1/(4 pi eps0) exp(-jkr)/r  and
mu0/(4 pi) exp(-jkr)/r  when both sides are identical.
"""
import numpy as np
from scipy import special, integrate, optimize

C0 = 299792458.0
EPS0 = 8.8541878128e-12
MU0 = 4.0e-7 * np.pi


def kz(krho, eps_r, k0):
    """Vertical wavenumber, branch Im<=0 (decaying into +z / outgoing)."""
    k2 = eps_r * k0 * k0
    kz_ = np.sqrt(k2 - krho * krho + 0j)
    return np.where(kz_.imag > 0, -kz_, kz_)


def _input_adm(eta_load, eta_c, kzc, d):
    """Lossless transmission-line input admittance: load eta_load seen through a
    layer of characteristic admittance eta_c, vertical wavenumber kzc, height d."""
    t = np.tan(kzc * d)
    return eta_c * (eta_load + 1j * eta_c * t) / (eta_c + 1j * eta_load * t)


class Stack:
    """A layered medium.  `layers` are the FINITE layers between the two
    semi-infinite claddings, ordered from the metal plane downward:
        top_eps  | [ (eps, thickness), ... ]  | bot_eps
    The metal plane sits between top_eps (above) and layers[0] (below)."""

    def __init__(self, top_eps, layers, bot_eps, f=60e9):
        self.top_eps = complex(top_eps)
        self.layers = [(complex(e), float(d)) for e, d in layers]
        self.bot_eps = complex(bot_eps)
        self.f = f
        self.k0 = 2.0 * np.pi * f / C0
        self.n_max = np.sqrt(max([self.top_eps.real, self.bot_eps.real]
                                 + [e.real for e, _ in self.layers]))

    # ---- downward input admittances looking from the metal plane ----------
    def _eta_dn(self, krho, kind):
        """kind = 'TM' -> eps_r k_z ; 'TE' -> k_z. Cascade bottom-up."""
        k0 = self.k0
        e_bot = self.bot_eps
        kzb = kz(krho, e_bot, k0)
        eta = e_bot * kzb if kind == "TM" else kzb          # bottom semi-inf
        for e, d in reversed(self.layers):
            kzc = kz(krho, e, k0)
            eta_c = e * kzc if kind == "TM" else kzc
            eta = _input_adm(eta, eta_c, kzc, d)
        return eta

    def _eta_up(self, krho, kind):
        e = self.top_eps
        kzt = kz(krho, e, k0=self.k0)
        return e * kzt if kind == "TM" else kzt              # semi-inf above

    # ---- spectral kernels --------------------------------------------------
    def Gq_spectral(self, krho):
        return 1.0 / (1j * EPS0 * (self._eta_up(krho, "TM") + self._eta_dn(krho, "TM")))

    def GA_spectral(self, krho):
        return MU0 / (1j * (self._eta_up(krho, "TE") + self._eta_dn(krho, "TE")))

    # ---- quasi-static large-krho asymptotes (for singularity extraction) --
    def _asym(self, kind):
        """G~ -> 1/(eps0 (eps_top+eps_first) krho) [TM]  or  mu0/(2 krho) [TE];
        real-space transform of C/krho is  C/(2 pi rho)."""
        e_first = self.layers[0][0] if self.layers else self.bot_eps
        if kind == "TM":
            C = 1.0 / (EPS0 * (self.top_eps + e_first))
        else:
            C = MU0 / 2.0
        return C                                             # spectral coeff of 1/krho

    # ---- Sommerfeld inversion ---------------------------------------------
    # ---- robust Sommerfeld inversion (contour deformation) ---------------
    def _sommerfeld(self, rho, spectral, C_asym):
        """(1/2pi) int_0^inf [spectral - C_asym/krho] J0(krho rho) krho dkrho
        + C_asym/(2 pi rho).

        Head [0, a]: real axis, a just past the surface-wave poles, adaptive
        quad with breakpoints at the material wavenumbers and poles (finite
        material loss makes the poles sharp but integrable).
        Tail [a, inf): J0 = (H0(1)+H0(2))/2; the H0(2) piece is integrated on a
        ray into Im(krho) < 0 and the H0(1) piece on a ray into Im(krho) > 0, so
        each decays exponentially and the oscillatory tail converges fast."""
        k0 = self.k0
        a = 6.0 * self.n_max * k0
        Cq = C_asym

        def rem(kr):
            return spectral(kr) - Cq / kr

        # -- head --
        def h_re(kr):
            return (rem(kr) * special.j0(kr * rho) * kr).real / (2 * np.pi)

        def h_im(kr):
            return (rem(kr) * special.j0(kr * rho) * kr).imag / (2 * np.pi)

        bps = sorted(set(
            [k0 * np.sqrt(abs(e)) for e in [self.top_eps, self.bot_eps]
             + [e for e, _ in self.layers]]
            + [n * k0 for n in self._poles()]))
        seg = [0.0] + [b for b in bps if 0 < b < a] + [a]
        head = sum(integrate.quad(h_re, u, v, limit=200)[0]
                   + 1j * integrate.quad(h_im, u, v, limit=200)[0]
                   for u, v in zip(seg[:-1], seg[1:]))

        # -- tail on the two exponentially-decaying rays --
        theta = 0.5
        T = 40.0 / (rho * np.sin(theta))                    # decay length of H0
        T = max(T, 6.0 / min([d for _, d in self.layers] + [1.0 / k0]))

        def ray(sign, hankel):
            e = np.exp(sign * 1j * theta)

            def fr(t):
                kr = a + t * e
                return (rem(kr) * hankel(0, kr * rho) * kr * e).real / (2 * np.pi)

            def fi(t):
                kr = a + t * e
                return (rem(kr) * hankel(0, kr * rho) * kr * e).imag / (2 * np.pi)

            return (integrate.quad(fr, 0, T, limit=400)[0]
                    + 1j * integrate.quad(fi, 0, T, limit=400)[0])

        tail = 0.5 * (ray(+1, special.hankel1) + ray(-1, special.hankel2))
        return head + tail + Cq / (2.0 * np.pi * rho)

    def _poles(self):
        if not hasattr(self, "_poles_cache"):
            self._poles_cache = self.surface_waves("TM") + self.surface_waves("TE")
        return self._poles_cache

    def table(self, rho_arr):
        rho_arr = np.asarray(rho_arr, float)
        GA = np.array([self._sommerfeld(r, self.GA_spectral, self._asym("TE")) for r in rho_arr])
        Gq = np.array([self._sommerfeld(r, self.Gq_spectral, self._asym("TM")) for r in rho_arr])
        return GA, Gq

    def Gq(self, rho):
        return self._sommerfeld(rho, self.Gq_spectral, self._asym("TM"))

    def GA(self, rho):
        return self._sommerfeld(rho, self.GA_spectral, self._asym("TE"))

    # ---- surface-wave poles ----------------------------------------------
    # A bound surface wave is a pole of the SAME-INTERFACE kernel, i.e. a zero
    # of its denominator  (eta_up + eta_dn) [TM]  or  (zeta_up + zeta_dn) [TE].
    # We locate poles as minima of |denominator| over real n in (1, n_max) and
    # refine each one -- this is exactly the transverse-resonance condition the
    # Sommerfeld contour needs, and it is self-consistent with the kernel the
    # integrator evaluates (a separate transfer-matrix determinant is not).
    def _sw_den(self, n, pol):
        kind = "TE" if pol == "TE" else "TM"
        kr = n * self.k0
        return self._eta_up(kr, kind) + self._eta_dn(kr, kind)

    def surface_waves(self, pol="TE", n_scan=4000):
        lo, hi = 1.0 + 1e-4, self.n_max - 1e-4
        if hi <= lo:                      # no guiding range (e.g. free space)
            return []
        ns = np.linspace(lo, hi, n_scan)
        a = np.abs([self._sw_den(x, pol) for x in ns])
        med = np.median(a)
        out = []
        for i in range(1, n_scan - 1):
            if a[i] < a[i - 1] and a[i] < a[i + 1] and a[i] < 0.2 * med:
                res = optimize.minimize_scalar(
                    lambda x: abs(self._sw_den(x, pol)),
                    bounds=(ns[i - 1], ns[i + 1]), method="bounded",
                    options={"xatol": 1e-10})
                out.append(res.x)
        return out

    def te0_pole(self):
        return self.surface_waves("TE")
