"""
Line model of the electrode bend: CPW geometry and materials in, Z0, n_m and
alpha(f) out. No mesh; one geometry costs ~0.5 s the first time (boundary
elements + spectral integrals), every later frequency evaluation is closed form.

The bend is modelled as a straight coplanar line with the bend's cross-section
(signal S, gaps W, grounds Wg, gold thickness t) on the layer stack under the
electrodes, air above and in the gaps.

Capacitance (quasi-TEM), galerkin.py:
  * zero-thickness strips with FINITE grounds on the layered half-space by the
    spectral-domain Galerkin method (charge basis with the edge singularity,
    layered Green's function by transmission-line recursion, LN anisotropy
    exact): exact for zero thickness (checked against the conformal map in air
    to 1e-8);
  * thickness: C += C_air,thick - C_air,thin, with C_air,thick from boundary
    elements (bem.py). The air-filled capacitance gives L_ext = 1/(c^2 C_air).
  Against the mesh-converged FEM of the bend: C -0.28 %, C_air -0.002 %.

Series impedance (conductor loss and internal inductance):
  * DC: 1/(sigma S t) + 1/(2 sigma Wg t); uniform-current inductance from the
    exact mean log-distance between rectangles;
  * skin effect: the exact PEC surface current of the thick electrodes (top,
    bottom AND sidewalls) from boundary elements, on the electrodes receded by
    delta/2 (the current flows inside the metal), minus c K^2 delta^(1/3) per
    corner for the r^(-1/3) corner current (c = 0.70 from an isolated square
    bar, not fitted to the CPW);
  * R = sqrt(R_dc^2 + R_hf^2); L_int blended between the DC value and R_hf/w.
  Reference: current solved inside the gold by FEM (tools/bend_cpw), itself
  checked against the exact coax solution, a PEEC integral equation and a
  full-wave solve with the gold meshed.

Dielectric loss: G = sum_i sigma_i dC/d(eps0 eps_i) (+ tan(delta) terms).
Line constants exact: gamma = sqrt((R + jwL)(G + jwC)), Zc = sqrt((R + jwL)/(G + jwC)).
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

from . import bem, galerkin

C0 = 299792458.0
EPS0 = 8.8541878128e-12
MU0 = 4e-7 * np.pi
DB_PER_NEPER = 20.0 * np.log10(np.e)
UM = 1e-6
SIGMA_AU = 4.56e7
F_REF_GHZ = 60.0                 # where Z0 and n_m are quoted and matched
C_CORNER = 0.70                  # right-angle corner constant (tools/bend_cpw/corner_constant.py)
F_FLOOR_HZ = 1e6                 # below this the line constants are taken at 1 MHz

# Materials of the stack under the bend (the FEM reference notebook's values):
# (name, eps_h, eps_v, sigma S/m) from the metal down; the substrate is last.
LAYER_MATERIALS = (("SiO2 buffer", 3.9, 3.9, 1e-13),
                   ("LN slab", 28.0, 44.0, 1e-3),
                   ("SiO2 BOX", 3.9, 3.9, 1e-13),
                   ("Si substrate", 11.7, 11.7, 1e-12))


@dataclass(frozen=True)
class BendGeometry:
    """Cross-section of the bend line. Lengths in um, sigma in S/m."""
    S_um: float = 35.0               # signal width
    W_um: float = 4.5                # gap
    Wg_um: float = 55.0              # ground width
    t_um: float = 2.0                # gold thickness
    buf_um: float = 3.6              # SiO2 between the gold and the LN slab
    slab_um: float = 0.275           # LN slab
    box_um: float = 4.7              # buried oxide
    si_um: float = 550.0             # substrate
    sigma: float = SIGMA_AU

    def rounded(self) -> "BendGeometry":
        """Same geometry with float noise removed (cache key)."""
        return BendGeometry(*(round(float(v), 9) if i < 8 else float(f"{float(v):.9g}")
                              for i, v in enumerate(self.astuple())))

    def astuple(self):
        return (self.S_um, self.W_um, self.Wg_um, self.t_um, self.buf_um, self.slab_um,
                self.box_um, self.si_um, self.sigma)

    def layers(self):
        hs = (self.buf_um, self.slab_um, self.box_um, self.si_um)
        return [(h * UM, eh, ev) for h, (_n, eh, ev, _s) in zip(hs, LAYER_MATERIALS)]

    def layer_sigma(self):
        return [s for _n, _eh, _ev, s in LAYER_MATERIALS]

    def with_(self, **kw) -> "BendGeometry":
        return replace(self, **kw)

    def check(self):
        for k in ("S_um", "W_um", "Wg_um", "t_um", "buf_um", "slab_um", "box_um", "si_um", "sigma"):
            if not float(getattr(self, k)) > 0:
                raise ValueError(f"bend geometry: {k} must be > 0 (got {getattr(self, k)})")
        return self


def geometry_from_params(p: dict) -> BendGeometry:
    return BendGeometry(S_um=float(p.get("bend_S_um", 35.0)), W_um=float(p.get("bend_W_um", 4.5)),
                        Wg_um=float(p.get("bend_Wg_um", 55.0)), t_um=float(p.get("bend_t_um", 2.0)),
                        buf_um=float(p.get("bend_buf_um", 3.6)), slab_um=float(p.get("bend_slab_um", 0.275)),
                        box_um=float(p.get("bend_box_um", 4.7)),
                        sigma=float(p.get("bend_sigma_MSm", SIGMA_AU / 1e6)) * 1e6).check()


# ---------------------------------------------------------------------------
# DC inductance: exact mean log-distance between rectangles
# ---------------------------------------------------------------------------
def _F(u, v):
    """F_uuvv = ln(u^2 + v^2); even in u and v."""
    u, v = np.abs(u), np.abs(v)
    r2 = u * u + v * v
    lg = np.where(r2 > 0, np.log(np.where(r2 > 0, r2, 1.0)), 0.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        at1 = np.where(u > 0, np.arctan(v / np.where(u > 0, u, 1.0)), 0.0)
        at2 = np.where(v > 0, np.arctan(u / np.where(v > 0, v, 1.0)), 0.0)
    return ((u * u * v * v / 4 - u ** 4 / 24 - v ** 4 / 24) * lg
            + u ** 3 * v * at1 / 3 + u * v ** 3 * at2 / 3 - 25 * u * u * v * v / 24)


def mean_log(ra, rb):
    """<ln r> between rectangles ra = (x1, x2, y1, y2) and rb."""
    x1, x2, y1, y2 = ra
    x3, x4, y3, y4 = rb
    s = 0.0
    for xa, xb, sx in ((x2, x3, 1), (x1, x4, 1), (x1, x3, -1), (x2, x4, -1)):
        for ya, yb, sy in ((y2, y3, 1), (y1, y4, 1), (y1, y3, -1), (y2, y4, -1)):
            s = s + sx * sy * _F(xa - xb, ya - yb)
    area = (x2 - x1) * (y2 - y1) * (x4 - x3) * (y4 - y3)
    return 0.5 * s / area


def inductance_dc(S, W, Wg, t):
    """Loop inductance (H/m) with uniform current in each electrode (signal +1,
    grounds -1/2 each). Lengths in m."""
    xs, xgi = S / 2, S / 2 + W
    rects = [(-xs, xs, 0.0, t), (xgi, xgi + Wg, 0.0, t), (-xgi - Wg, -xgi, 0.0, t)]
    cur = (1.0, -0.5, -0.5)
    return sum(cur[a] * cur[b] * (-MU0 / (2 * np.pi)) * float(mean_log(rects[a], rects[b]))
               for a in range(3) for b in range(3))


# ---------------------------------------------------------------------------
# The model
# ---------------------------------------------------------------------------
class LineModel:
    """Everything that depends on the geometry only is computed once here;
    evaluate(f) is then closed form (plus a boundary-element solve per new
    skin depth, cached)."""

    N_PER_DECADE = 8             # receding-depth table density for frequency sweeps

    def __init__(self, g: BendGeometry):
        self.g = g.check()
        S, W, Wg, t = g.S_um * UM, g.W_um * UM, g.Wg_um * UM, g.t_um * UM
        self._dims = (S, W, Wg, t)
        lay = g.layers()
        self.C_eps, self.C_air = galerkin.capacitance(S, W, Wg, t, lay)
        self.L_ext = 1.0 / (C0 ** 2 * self.C_air)
        self.R_dc = 1.0 / (g.sigma * S * t) + 0.5 / (g.sigma * Wg * t)
        self.dL_dc = max(inductance_dc(S, W, Wg, t) - self.L_ext, 1e-30)
        self._lay = lay
        self._dC = None          # dC/d(eps_r) per lossy layer, on first use
        self._bem = {}

    # -- conductor -----------------------------------------------------------
    def _bem_at(self, d):
        key = float(f"{d:.6e}")
        if key not in self._bem:
            S, W, Wg, t = self._dims
            b = bem.solve(S - key, W + key, Wg - key, t - key)
            self._bem[key] = (b["G_pec"], 4 * sum(k * k for k in b["K_corners"]))
        return self._bem[key]

    def conductor(self, f_Hz):
        """R (ohm/m), L_int (H/m) at the frequencies f_Hz."""
        f = np.maximum(np.atleast_1d(np.asarray(f_Hz, float)), F_FLOOR_HZ)
        w = 2 * np.pi * f
        t = self._dims[3]
        delta = np.sqrt(2.0 / (w * MU0 * self.g.sigma))
        Rs = 1.0 / (self.g.sigma * delta)
        d_eff = np.minimum(delta, 0.45 * t)          # the receded metal keeps a core
        u = np.unique(np.round(d_eff, 15))
        if u.size <= 3:
            G = np.empty_like(d_eff)
            Ks = np.empty_like(d_eff)
            for d in u:
                gk, kk = self._bem_at(d)
                sel = np.isclose(d_eff, d, rtol=1e-9, atol=0)
                G[sel], Ks[sel] = gk, kk
        else:
            # fixed table in log(depth), top node at 0.45 t, so that later sweeps
            # on other grids reuse the same solves
            top = 0.45 * t
            k_lo = int(np.floor(np.log10(top / d_eff.min()) * self.N_PER_DECADE)) + 1
            nodes = top * 10.0 ** (-np.arange(k_lo + 1) / self.N_PER_DECADE)
            vals = np.array([self._bem_at(d) for d in nodes])
            ln = np.log(nodes[::-1])
            G = np.interp(np.log(d_eff), ln, vals[::-1, 0])
            Ks = np.interp(np.log(d_eff), ln, vals[::-1, 1])
        R_hf = Rs * (G - C_CORNER * Ks * delta ** (1.0 / 3.0))
        R = np.sqrt(self.R_dc ** 2 + R_hf ** 2)
        # internal inductance: R_hf/w in the skin-effect regime; towards DC the
        # current spreads uniformly and L_int tends to L_dc - L_ext (exact)
        L_int = 1.0 / np.sqrt(1.0 / self.dL_dc ** 2 + 1.0 / (R_hf / w) ** 2)
        return R, L_int

    # -- dielectric ----------------------------------------------------------
    def _dC_layers(self):
        if self._dC is None:
            S, W, Wg, t = self._dims
            out = []
            for i, (h, eh, ev) in enumerate(self._lay):
                lay = list(self._lay)
                lay[i] = (h, eh * 1.001, ev * 1.001)
                Cp = galerkin.capacitance(S, W, Wg, t, lay, C_air_thick=self.C_air)[0]
                out.append((Cp - self.C_eps) / (0.001 * np.sqrt(eh * ev)))
            self._dC = out
        return self._dC

    def G_diel(self, f_Hz, layer_tand=None):
        f = np.atleast_1d(np.asarray(f_Hz, float))
        w = 2 * np.pi * f
        G = np.zeros_like(f)
        sig = self.g.layer_sigma()
        for i, ((h, eh, ev), dC) in enumerate(zip(self._lay, self._dC_layers())):
            td = 0.0 if layer_tand is None else float(layer_tand[i])
            G = G + (sig[i] / EPS0 + w * td * np.sqrt(eh * ev)) * dC
        return G

    # -- line constants ------------------------------------------------------
    def evaluate(self, f_Hz, dielectric=True) -> dict:
        f_in = np.atleast_1d(np.asarray(f_Hz, float))
        f = np.maximum(f_in, F_FLOOR_HZ)
        w = 2 * np.pi * f
        R, L_int = self.conductor(f)
        L = self.L_ext + L_int
        Gd = self.G_diel(f) if dielectric else np.zeros_like(f)
        Zser = R + 1j * w * L
        Ysh = Gd + 1j * w * self.C_eps
        gamma = np.sqrt(Zser * Ysh)
        Zc = np.sqrt(Zser / Ysh)
        a_c0, a_d0 = R / (2 * np.abs(Zc)), Gd * np.abs(Zc) / 2
        tot = a_c0 + a_d0
        return dict(f_GHz=f_in / 1e9, alpha_dB_cm=DB_PER_NEPER * gamma.real / 100,
                    alpha_c_dB_cm=DB_PER_NEPER * gamma.real * a_c0 / tot / 100,
                    alpha_d_dB_cm=DB_PER_NEPER * gamma.real * a_d0 / tot / 100,
                    n_m=gamma.imag / w * C0, Zc=Zc, Z0=np.abs(Zc), R=R, L=L, L_int=L_int,
                    G=Gd, C=self.C_eps, C_air=self.C_air, L_ext=self.L_ext, R_dc=self.R_dc)

    def at_ref(self, f_GHz=F_REF_GHZ, dielectric=True) -> dict:
        """Z0, n_m, alpha (dB/cm) at one frequency, as plain floats."""
        r = self.evaluate(np.array([f_GHz * 1e9]), dielectric)
        return {k: (float(v[0]) if isinstance(v, np.ndarray) and v.size == 1 and k != "Zc" else v)
                for k, v in r.items()} | dict(Zc=complex(r["Zc"][0]))


@lru_cache(maxsize=256)
def _model_cached(key: tuple) -> LineModel:
    return LineModel(BendGeometry(*key))


def line_model(g: BendGeometry) -> LineModel:
    """Cached LineModel for this geometry."""
    return _model_cached(g.rounded().astuple())


def line_constants(g: BendGeometry, f_GHz) -> dict:
    """alpha (dB/cm), n_m, complex Zc on the grid f_GHz (any shape of 1-D array)."""
    return line_model(g).evaluate(np.asarray(f_GHz, float) * 1e9)
