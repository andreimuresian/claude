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

SURFACE-WAVE RESIDUE EXTRACTION
-------------------------------
A plain Gaussian split does NOT work here.  The sharp weight 1-exp(-k^2/4E^2)
is ~ k_p^2/(4E^2) at the surface-wave pole -- 0.5 % for E*P = 6 -- so the sharp
part keeps half a percent of the surface wave, hence a residual 1/sqrt(rho)
tail, and its real-space lattice sum never converges (n_sharp 4 -> 8 moved G_A
by 1040 %).  Raising E only trades that for an unaffordable harmonic count.

So the poles are removed BEFORE splitting.  Each pole is a zero k_p of the
kernel denominator (found in the complex plane; Im k_p < 0 from the Si loss):

    G~(k) = N / D(k),   S_p = 2 k_p N / D'(k_p),
    G~_reg(k) = G~(k) - sum_p S_p/(k^2 - k_p^2)

which is numerically flat through the pole (|G-pole| constant to 5 decades of
detuning).  G~_reg is Ewald-split as before; both halves now decay properly.

The removed part is put back in closed form.  Its real-space image is
-(j S_p/4) H0^(2)(k_p rho), and its Floquet lattice sum is the classical
1D-periodic 2D-Helmholtz Ewald pair, derived from

    I_n(u) = (1/pi) Int_0^inf cos(k_u u)/(k_u^2 + beta_n^2 - k_p^2) dk_u
           = exp(-a_n |u|)/(2 a_n),   a_n = sqrt(beta_n^2 - k_p^2), Re a_n > 0

by splitting exp(-a|u|)/(2a) = (1/2 sqrt(pi)) Int_0^inf t^-1/2 exp(-a^2 t
- u^2/4t) dt at t = 1/(4E^2):

  spectral (t > 1/4E^2)   T1 = 1/(4P) sum_n e^{j beta_n v}/a_n
                               * [ e^{ a_n u} erfc(a_n/2E + E u)
                                 + e^{-a_n u} erfc(a_n/2E - E u) ]
  spatial  (t < 1/4E^2)   T2 = 1/(4 pi) sum_m e^{j beta m P}
                               * sum_q (k_p/2E)^{2q}/q! E_{q+1}(R_m^2 E^2)

T1 is Gaussian-convergent in n and T2 Gaussian-convergent in m, so both fold
into the existing machinery at no extra cost: T1 is added to the harmonic
coefficients I_n, T2 (radial) is added to the sharp radial table.  Verified
against a 8e5-term brute-force harmonic sum to 1e-16, invariant over E*P in
[3, 24].
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


def _sqrt_rp(z):
    """sqrt with Re >= 0 (the decaying / outgoing branch for exp(-a|u|))."""
    r = np.sqrt(np.asarray(z, complex))
    return np.where(r.real < 0, -r, r)


def _wexp(a, E, u, sign):
    """exp(+-a u) * erfc(a/(2E) +- E u), evaluated in the numerically stable
    scaled form  exp(-a^2/4E^2 - E^2 u^2) w(j z)  (w = Faddeeva).  For sign=-1
    and Re z < 0 the erfc saturates at 2, so use erfc(z) = 2 - erfc(-z)."""
    z = a/(2*E) + sign*E*u
    pre = np.exp(-(a*a)/(4*E*E) - (E*u)**2)
    if sign > 0:
        return pre*special.wofz(1j*z)
    ok = z.real >= 0
    return np.where(ok,
                    pre*special.wofz(1j*np.where(ok, z, 0.0)),
                    2*np.exp(-a*u) - pre*special.wofz(-1j*np.where(ok, 0.0, z)))


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
                 nk=0, kfac=8.0, du_max=1.5e-3, n_sharp_max=16):
        self.st = Stack(sp.EPS_AIR, sp.device_layers(t_LN=t_LN, lossy=True),
                        sp.EPS_AIR, f=f)
        self.f = f
        self.w = 2*np.pi*f
        self.k0 = self.w/C0
        self.P = P
        self.du_max = du_max
        self.n_sharp_max = n_sharp_max
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
        self.kmax = kfac*self.E             # Gaussian kills the integrand here
        self._residues()
        # with the poles extracted the sharp part is genuinely high-pass; what
        # is left of it decays as ~1/(4 E^2 rho^3), so a few images suffice
        self.n_sharp = 6
        # the radial table has to reach the farthest image actually asked for,
        # otherwise Gq_sharp clips and the image sum picks up a constant
        self.rho_max = np.hypot(du_max, (self.n_sharp_max + 0.5)*P)
        # set_beta's grid only has to resolve cos(ku*du) out to du_max; the
        # radial table sizes its own (larger) grid from rho_max
        self.nk = nk if nk else self._nk_for(du_max)
        self._build_radial(n_rad)
        self.beta = None

    # ---------------- surface-wave poles: location, residue, removal -------
    def _den(self, kr, kind):
        return self.st._eta_up(kr, kind) + self.st._eta_dn(kr, kind)

    def _refine_pole(self, n0, kind):
        """Complex secant on the kernel denominator, started from the real-axis
        scan value.  Loss pushes the root just below the real axis."""
        z0 = complex(n0*self.k0)
        z1 = z0*(1 - 1e-6j)
        f0, f1 = self._den(z0, kind), self._den(z1, kind)
        for _ in range(60):
            if abs(f1 - f0) == 0.0:
                break
            z2 = z1 - f1*(z1 - z0)/(f1 - f0)
            f2 = self._den(z2, kind)
            if abs(z2 - z1) < 1e-14*abs(z2):
                z1, f1 = z2, f2
                break
            z0, f0, z1, f1 = z1, f1, z2, f2
        return z1

    def _residues(self):
        """Poles k_p and even-form residues S_p with G~ ~ S_p/(k^2 - k_p^2).

        G~ = N/D, so the simple residue is R_p = N/D'(k_p) and, because the
        kernel is even in k, the pole pair +-k_p is captured by
        S_p/(k^2-k_p^2) with S_p = 2 k_p R_p.  D' by 5-point central
        difference, h = 1e-4 |k_p| (the denominator is analytic, so this is
        accurate to ~1e-12 relative)."""
        num = {"TM": 1.0/(1j*EPS0), "TE": MU0/1j}
        self.poles = {"TM": [], "TE": []}
        self.pole_k, self.pole_w = [], []
        for kind in ("TM", "TE"):
            for n0 in self.st.surface_waves(kind):
                kp = self._refine_pole(n0, kind)
                h = 1e-4*abs(kp)
                d = (-self._den(kp + 2*h, kind) + 8*self._den(kp + h, kind)
                     - 8*self._den(kp - h, kind) + self._den(kp - 2*h, kind))/(12*h)
                self.poles[kind].append((kp, 2*kp*num[kind]/d))
                self.pole_k.append(kp.real)
                self.pole_w.append(max(2*abs(kp.imag), 1e-9*abs(kp)))

    def _spec_reg(self, kr, kind):
        """Pole-free spectral kernel."""
        g = (self.st.Gq_spectral(kr) if kind == "TM"
             else self.st.GA_spectral(kr))
        for kp, S in self.poles[kind]:
            g = g - S/(kr*kr - kp*kp)
        return g

    def _reg_real(self, rho):
        """Real-space regularised kernel, obtained by Sommerfeld-inverting
        G~_reg DIRECTLY rather than as G_full - pole.

        Two reasons.  (i) Accuracy: on the real axis the pole contributes
        1/(k^2-k_p^2) ~ 1/(2 k_p) * 1/(k - Re k_p + j Im k_p); its real part is
        odd about the pole and integrates as a principal value, while its whole
        resonant content -- the surface wave -- is a Lorentzian of relative
        width |Im k_p|/Re k_p ~ 4e-6.  Phase 1 put the pole on a quad segment
        ENDPOINT, which captures the odd part but not the Lorentzian, so
        G_full's far field has the right real part and a surface wave that is
        largely missing (checked at 20/50/100 mm).  G~_reg has no pole at all,
        so the same contour integrator is accurate on it.  (ii) Cancellation:
        beyond ~1 mm the surface wave dominates G_full, so G_full - pole is a
        difference of near-equal numbers.

        The asymptote is unchanged: the subtracted term falls as S/k^2, faster
        than C/k, so rem(k) = G~_reg(k) - C/k still vanishes correctly."""
        rho = np.asarray(rho, float)
        gq = np.array([self.st._sommerfeld(r, lambda k: self._spec_reg(k, "TM"),
                                           self.Cq) for r in rho])
        ga = np.array([self.st._sommerfeld(r, lambda k: self._spec_reg(k, "TE"),
                                           self.CA) for r in rho])
        return gq, ga

    def _pole_real(self, rho, kind):
        """Real-space image of the removed part: sum_p -(j S_p/4) H0^(2)(k_p rho)
        (verified against a direct Hankel-transform quadrature)."""
        out = np.zeros(np.shape(rho), complex)
        for kp, S in self.poles[kind]:
            out = out - 0.25j*S*special.hankel2(0, kp*rho)
        return out

    def _pole_spatial(self, rho, kind, nq=8):
        """Ewald spatial half of the pole lattice sum, m = 0 term (radial).
        sum_q (k_p/2E)^{2q}/q! E_{q+1}(rho^2 E^2) / (4 pi), times S_p."""
        x = (np.asarray(rho, float)*self.E)**2
        out = np.zeros(x.shape, complex)
        for kp, S in self.poles[kind]:
            s = np.zeros(x.shape, complex)
            for q in range(nq):
                c = (kp/(2*self.E))**(2*q)/special.factorial(q)
                if abs(c) < 1e-18 and q > 1:
                    break
                s = s + c*special.expn(q + 1, x)
            out = out + S*s/(4*np.pi)
        return out

    def _pole_harm(self, du, bn, kind):
        """Ewald spectral half: the coefficient the pole adds to I_n(du)."""
        u = np.abs(np.asarray(du, float))
        out = np.zeros(u.shape, complex)
        for kp, S in self.poles[kind]:
            a = _sqrt_rp(bn*bn - kp*kp)
            out = out + S*(_wexp(a, self.E, u, +1)
                           + _wexp(a, self.E, u, -1))/(4*a)
        return out

    def _ku_grid(self, bn=0.0):
        """Quadrature grid in ku.  The poles have been extracted, so away from
        the branch point the integrand is smooth and a uniform grid is right;
        the requirement there is that it resolve the cos(ku du) / J0(k rho)
        oscillation out to the largest offset the kernel is evaluated at.
        Trapezoid error is ~(dk rho_max)^2/12, so dk rho_max <~ 0.03 buys ~1e-4.

        A PROPAGATING Floquet harmonic (|beta_n| < k0) needs more than that.
        The spectral kernels carry 1/k_z with k_z = sqrt(k0^2 - k_rho^2), so at
        k_rho = k0 -- i.e. ku* = sqrt(k0^2 - beta_n^2) -- the integrand has an
        integrable inverse-square-root branch point that a uniform grid steps
        straight over.  Points are clustered geometrically towards ku* from
        both sides, which is enough for the trapezoid to resolve a 1/sqrt.

        Production never reaches this branch: the CPW mode has n_m > 1, so
        beta > k0 and every harmonic is evanescent.  It is exercised by the
        beta = 0 leg of the free-space kernel test."""
        g = np.linspace(0.0, self.kmax, self.nk)
        if abs(np.real(bn)) >= self.k0 or abs(np.imag(bn)) > 1e-6*self.k0:
            return g
        kus = np.sqrt(max(self.k0**2 - np.real(bn)**2, 0.0))
        if not (0.0 < kus < self.kmax):
            return g
        # approach ku* from both sides but never land on it: k_z = 0 there
        d = kus*np.logspace(-10, -1.3, 80)
        extra = np.concatenate([kus - d, kus + d])
        extra = extra[(extra > 0.0) & (extra < self.kmax)]
        return np.unique(np.concatenate([g, extra]))

    def _nk_for(self, r_max):
        # trapezoid error ~(dk r_max)^2/12; 0.0125 targets ~1e-5, which keeps
        # the ku quadrature clear of the 1e-4 kernel accuracy gate rather than
        # sitting on it (0.03 buys only ~1e-4 and measured 2.8e-4).
        n = int(np.ceil(self.kmax*r_max/0.0125)) + 1
        return int(np.clip(n, 2000, 400000))

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

    def _sharp_real(self, rho):
        """SHARP radial kernels, straight from their own high-pass integral.

            sharp(rho) = (1/2pi) Int_0^inf G~_reg(k) [1 - exp(-k^2/4E^2)]
                                          J0(k rho) k dk

        Phase 3 built this as  G_reg(rho) - soft_reg(rho): two separately
        quadratured Sommerfeld integrals, each O(K/rho), differenced to leave
        the O(K/(4 E^2 rho^3)) sharp tail.  Beyond a few hundred um that
        cancels four to five significant digits and what survives is quadrature
        noise.  Against the analytic tail the old table ran to a ratio of -4071
        at rho = 3.2 mm, and because the image sum adds 2 n_sharp + 1 copies of
        that noise, RAISING n_sharp made the periodic kernel worse -- measured
        against the exact free-space form in air, 2.6e-2 at n_sharp = 6 going
        to 3.9e-2 at n_sharp = 16.

        Evaluating the high-pass integral directly removes the cancellation:
        every part of the integrand is O(sharp), so the answer is computed at
        its own magnitude.  The 1/k asymptote still has to come out -- G~ does
        not reach C/k until k >> 1/t_LN ~ 3e6, far beyond kmax = 8E -- but
        _sommerfeld already extracts C/k and adds back C/(2 pi rho), and

            Int_0^inf exp(-k^2/4E^2) J0(k rho) dk
                = sqrt(pi) E exp(-x) I0(x),      x = E^2 rho^2 / 2,

        so folding the (1 - gauss) weight into the spectral argument turns that
        add-back into  C/(2 pi) [1/rho - sqrt(pi) E exp(-x) I0(x)]  exactly.
        That difference is still 1/rho minus something that approaches 1/rho,
        but it is now taken between two closed forms at machine precision
        instead of between two quadratures -- which is the whole of the fix.

        1 - exp(-k^2/4E^2) is formed with expm1 so the low-k weight (~k^2/4E^2)
        keeps full precision instead of cancelling against 1.
        """
        E2 = 4*self.E**2

        def spec(kind, C):
            """G~_reg with the 1/k asymptote extracted UNDER the (1 - gauss)
            weight, then added back bare so _sommerfeld's own C/k subtraction
            leaves exactly  [G~_reg - C/k] (1 - gauss).

            Extracting a bare C/k instead is wrong and was the first attempt at
            this fix: at k << E the true high-pass integrand vanishes like
            k^2/4E^2, so a bare subtraction leaves rem -> -C/k there, the head
            integral becomes ~ -C/rho and the tail has to cancel it -- the same
            five-digit cancellation, just moved.  Weighting the extraction
            makes rem vanish at BOTH ends."""
            def f(k):
                k = np.asarray(k)
                w = -np.expm1(-k*k/E2)          # 1 - gauss, exact at small k
                return (self._spec_reg(k, kind) - C/k)*w + C/k
            return f

        # closed form of  (C/2pi) Int_0^inf gauss J0(k rho) dk, the piece
        # _sommerfeld adds as C/(2 pi rho) but which the (1 - gauss) weight
        # must remove:  Int exp(-k^2/4E^2) J0 dk = sqrt(pi) E exp(-x) I0(x).
        # i0e IS exp(-x) I0(x), so no overflow at the x ~ 5e3 reached here.
        x = (self.E*np.asarray(rho))**2/2.0
        corr = np.sqrt(np.pi)*self.E*special.i0e(x)/(2*np.pi)
        gq = np.array([self.st._sommerfeld(r, spec("TM", self.Cq), self.Cq)
                       for r in rho]) - self.Cq*corr
        ga = np.array([self.st._sommerfeld(r, spec("TE", self.CA), self.CA)
                       for r in rho]) - self.CA*corr
        return gq, ga

    def _build_radial(self, n_rad):
        """Tabulate the SHARP radial kernels (see _sharp_real for the method).

        sharp = highpass(G~_reg) + pole_spatial, the first decaying as
        ~K/(4 E^2 rho^3) with no surface-wave tail and the second as
        exp(-rho^2 E^2), so the real-space image sum converges."""
        rho = np.logspace(np.log10(2e-8), np.log10(self.rho_max), n_rad)
        shq, sha = self._sharp_real(rho)
        shq = shq + self._pole_spatial(rho, "TM")
        sha = sha + self._pole_spatial(rho, "TE")
        lr = np.log(rho)
        self.rho_tab = rho
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
            # I_n(du) decays on the scale 1/a_n ~ P/(2 pi n), i.e. ~32 um/n,
            # so the grid has to resolve the HIGHEST retained harmonic, not
            # just the slowest.  220 log points left ~16 um spacing near
            # du = 400 um and a cubic-spline error of ~1.6e-4, which was the
            # floor on the free-space kernel test; 600 takes it to ~3e-6.
            du_grid = np.concatenate([[0.0],
                                      np.logspace(np.log10(2e-7),
                                                  np.log10(self.du_max), 600)])
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
            gq = self._spec_reg(kr, "TM")*gauss*wq
            ga = self._spec_reg(kr, "TE")*gauss*wq
            # I_n(du) = (1/2pi) Int_-inf^inf ... = (1/pi) Int_0^inf ... cos(ku du)
            cos = np.cos(np.outer(du_grid, ku))
            # + the Ewald spectral half of the extracted pole lattice sum
            Iq[i] = cos @ gq/np.pi + self._pole_harm(du_grid, bn, "TM")
            Ia[i] = cos @ ga/np.pi + self._pole_harm(du_grid, bn, "TE")
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
