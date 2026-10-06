"""
Closed-form traveling-wave electro-optic physics.

This module is the numerical heart of the toolkit and deliberately has no
knowledge of files, GUIs or Lumerical. It does two things:

  1. ``LineFit``  -- holds the fitted per-unit-length microwave physics of a
     coplanar electrode (alpha, Zc, n_m) and can evaluate it at any frequency,
     with optional "what-if" perturbations applied on top.

  2. ``eo_response`` -- the Gopalakrishnan/Ghione traveling-wave EO transfer
     function, including forward/backward microwave reflections off the source
     and load, frequency-dependent loss, and velocity walk-off against n_g.

The split matters for speed: the fit is done once per Touchstone file, then
thousands of circuit evaluations (a parametric sweep) cost about a millisecond
each because no re-fitting is involved.

With every perturbation knob at its default (scales 1.0, offsets 0.0, purely
resistive source and load) the maths here is bit-for-bit the original
EXTRACTOR expression, so the Python/INTERCONNECT agreement already established
is preserved.
"""

from __future__ import annotations

import os

from dataclasses import dataclass, field, replace
from typing import Optional

import numpy as np

C0 = 299792458.0
NP_PER_DB = 1.0 / 8.686


# =====================================================================
# 1. Physical fitting forms
# =====================================================================
def fit_alpha_scaled(f_GHz, a, b, c):
    """Skin effect (sqrt f) + dielectric loss (linear f) + DC offset, dB/cm."""
    return a * np.sqrt(f_GHz) + b * f_GHz + c


def fit_beta(f_Hz, a, b, c):
    """Phase constant, cubic in frequency."""
    return a * f_Hz + b * f_Hz ** 2 + c * f_Hz ** 3


def fit_impedance_physical(f_GHz, z_inf, k1, k2):
    """Re(Zc) rolling off to its high-frequency limit z_inf."""
    return z_inf + k1 / np.sqrt(f_GHz) + k2 / f_GHz


def fit_impedance_imag(f_GHz, k1, k2):
    """Im(Zc): no constant term, tends to 0 at high frequency."""
    return k1 / np.sqrt(f_GHz) + k2 / f_GHz


def fit_nm_saturating(f_GHz, n0, dn, fc):
    """
    Microwave index with bounded dispersion: n_m rises from its quasi-static
    value n0 towards n0+dn with a corner at fc.

    Bounded is the whole point. Fitting beta(f) with a polynomial and dividing
    by omega gives an n_m that keeps climbing outside the measured band -- on a
    real 0-80 GHz dataset the cubic form reached n_m = 3.2 at 300 GHz and 6.7 at
    600 GHz, inventing a velocity walk-off that does not exist and destroying
    the extrapolated bandwidth. This form cannot do that: it saturates, and the
    extractor additionally pins fc inside the measured range so the model never
    claims dispersion it has not seen.
    """
    return n0 + dn * f_GHz / (fc + f_GHz)


# =====================================================================
# 2. The fitted line
# =====================================================================
@dataclass
class LineFit:
    """Per-unit-length microwave physics de-embedded from one .s2p file."""

    popt_alpha: np.ndarray
    popt_zre: np.ndarray
    popt_zim: np.ndarray
    popt_beta: np.ndarray            # legacy cubic beta(f), kept for nm_model="cubic-beta"
    L_meas_m: float
    z0_sys: float
    f_min_sim_GHz: float
    f_max_sim_GHz: float
    source_file: str = ""
    nm_model: str = "saturating"
    popt_nm: Optional[np.ndarray] = None    # (n0, dn, fc) for the saturating model
    alpha_constrained: bool = False         # True if the free alpha fit was unphysical
    quality: dict = field(default_factory=dict)
    # raw de-embedded points, kept for the diagnostic plots
    raw_f_GHz: np.ndarray = field(default_factory=lambda: np.empty(0))
    raw_alpha_dB_cm: np.ndarray = field(default_factory=lambda: np.empty(0))
    raw_Zc: np.ndarray = field(default_factory=lambda: np.empty(0))
    raw_nm: np.ndarray = field(default_factory=lambda: np.empty(0))

    # -- evaluation with optional perturbations ------------------------
    def alpha_dB_cm(self, f_GHz, scale=1.0, skin_scale=1.0, diel_scale=1.0,
                    offset=0.0):
        a, b, c = self.popt_alpha
        base = skin_scale * a * np.sqrt(f_GHz) + diel_scale * b * f_GHz + c
        return scale * base + offset

    def Zc(self, f_GHz, offset=0.0):
        re = fit_impedance_physical(f_GHz, *self.popt_zre) + offset
        im = fit_impedance_imag(f_GHz, *self.popt_zim)
        return re + 1j * im

    def nm(self, f_GHz, offset=0.0):
        f = np.asarray(f_GHz, dtype=float)
        if self.nm_model == "cubic-beta" or self.popt_nm is None:
            f_Hz = f * 1e9
            return (C0 * fit_beta(f_Hz, *self.popt_beta)) / (2 * np.pi * f_Hz) + offset
        return fit_nm_saturating(f, *self.popt_nm) + offset

    # -- convenience ---------------------------------------------------
    def summary_at(self, f_GHz: float, **pert) -> dict:
        f = np.atleast_1d(float(f_GHz))
        return {
            "f_GHz": float(f_GHz),
            "alpha_dB_cm": float(self.alpha_dB_cm(f, **{k: v for k, v in pert.items()
                                                        if k in ("scale", "skin_scale",
                                                                 "diel_scale", "offset")})[0]),
            "Zc_re": float(np.real(self.Zc(f, offset=pert.get("zc_offset", 0.0)))[0]),
            "Zc_im": float(np.imag(self.Zc(f, offset=pert.get("zc_offset", 0.0)))[0]),
            "nm": float(self.nm(f, offset=pert.get("nm_offset", 0.0))[0]),
        }


# =====================================================================
# 3. Source / load impedance networks
# =====================================================================
def rlc_impedance(f_GHz, R, L_pH=0.0, C_fF=0.0):
    """
    Series R + jwL, shunted by a pad capacitance C.

        Z(f) = (R + jwL)  ||  1/(jwC)

    With L = C = 0 this returns exactly the scalar R, so the historic
    purely-resistive behaviour is untouched.
    """
    f = np.asarray(f_GHz, dtype=float)
    if L_pH == 0.0 and C_fF == 0.0:
        return np.full(f.shape, complex(R)) if f.shape else complex(R)

    w = 2 * np.pi * f * 1e9
    z_series = R + 1j * w * (L_pH * 1e-12)
    if C_fF == 0.0:
        return z_series
    y_c = 1j * w * (C_fF * 1e-15)
    z_series = np.where(np.abs(z_series) < 1e-12, 1e-12 + 0j, z_series)
    return 1.0 / (y_c + 1.0 / z_series)


# =====================================================================
# 4. The traveling-wave EO transfer function
# =====================================================================
def eo_transfer(f_GHz, alpha_dB_cm, nm, Zc, L_device_m, ng, Zs, Zt):
    """
    Complex, un-normalised EO transfer function of a traveling-wave electrode.

    Parameters
    ----------
    f_GHz : array          modulation frequency grid
    alpha_dB_cm : array    microwave attenuation on that grid
    nm : array             microwave effective index on that grid
    Zc : complex array     characteristic impedance on that grid
    L_device_m : float     electrode length
    ng : float             optical group index
    Zs, Zt : complex       source and terminating impedance (scalar or array)

    Returns
    -------
    (H, zin) : complex arrays
        H   -- the transfer function (take abs for magnitude response)
        zin -- input impedance looking into the loaded line, for return loss
    """
    f_GHz = np.asarray(f_GHz, dtype=float)
    f_Hz = f_GHz * 1e9
    omega = 2 * np.pi * f_Hz

    beta_opt = ng * omega / C0
    beta_rf = nm * omega / C0
    alpha_Np_m = np.asarray(alpha_dB_cm) * 100.0 * NP_PER_DB
    gamma = alpha_Np_m + 1j * beta_rf

    gL = gamma * L_device_m
    tanh_gL = np.tanh(gL)
    zin = Zc * ((Zt + Zc * tanh_gL) / (Zc + Zt * tanh_gL))

    M = (Zs + zin) * (Zt + Zc)
    N = (Zs + zin) * (Zt - Zc)
    p1 = zin / (M * np.exp(gL) + N * np.exp(-gL))

    up = L_device_m * (alpha_Np_m + 1j * (beta_rf - beta_opt))
    un = L_device_m * (-alpha_Np_m + 1j * (-beta_rf - beta_opt))
    up = np.where(np.abs(up) < 1e-12, 1e-12, up)
    un = np.where(np.abs(un) < 1e-12, 1e-12, un)

    p2 = (Zt + Zc) * ((1 - np.exp(up)) / up) + (Zt - Zc) * ((1 - np.exp(un)) / un)
    return p1 * p2, zin


# ---------------------------------------------------------------------
# 4b. Segmented electrode: modulating sections joined by non-modulating bends
# ---------------------------------------------------------------------
MAX_BENDS = 4


def bend_optical_length_m(p: dict) -> float:
    """Optical path through one bend, from the bend optical delay: the light
    crosses it in bend_opt_delay_ps at the nominal group index n_g. The layout
    stores lengths (the cascade and the INTERCONNECT element multiply them by
    each arm's n_g), so an arm at n_g + d sees the delay scaled by (n_g + d)/n_g."""
    return float(p.get("bend_opt_delay_ps", 5.0)) * 1e-12 * C0 / float(p.get("ng", 2.27))


BEND_F_REF_GHZ = 60.0       # where the bend's Z0 and n_m are quoted, matched and used for its length


def bend_from_cross_section(p: dict) -> bool:
    return str(p.get("bend_model", "cross-section")) == "cross-section"


def bend_ref(p: dict, f_GHz: float = BEND_F_REF_GHZ) -> dict:
    """The bend line at one frequency: alpha (dB/cm), n_m, Z0 = |Zc| and where
    they come from."""
    if bend_from_cross_section(p):
        from .bend_cpw import geometry_from_params, line_model
        g = geometry_from_params(p)
        r = line_model(g).at_ref(f_GHz)
        return dict(alpha_dB_cm=r["alpha_dB_cm"], nm=r["n_m"], Z=r["Z0"], Zc=r["Zc"],
                    source=(f"cross-section S {g.S_um:g} / W {g.W_um:g} / Wg {g.Wg_um:g} / "
                            f"t {g.t_um:g} um"))
    a, b, src = bend_loss_coefficients(p)
    f = max(float(f_GHz), 0.0)
    Z = float(p.get("bend_Z_ohm", 60.0))
    return dict(alpha_dB_cm=a * np.sqrt(f) + b * f, nm=float(p.get("bend_nm", 1.7)), Z=Z, Zc=complex(Z),
                source=f"fitted values ({src})")


def bend_index(p: dict) -> float:
    """Microwave index that sets the RF transit through a bend: the bend line's
    n_m at 60 GHz (cross-section), or the flat index (fitted values)."""
    if bend_from_cross_section(p):
        return float(bend_ref(p)["nm"])
    return float(p.get("bend_nm", 1.7))


def bend_summary(p: dict) -> str:
    """One line for logs and plot notes."""
    r = bend_ref(p)
    return (f"{r['source']}: Z0 {r['Z']:.1f} ohm, n_m {r['nm']:.3f}, alpha "
            f"{r['alpha_dB_cm']:.2f} dB/cm at {BEND_F_REF_GHZ:g} GHz")


def bend_matched_length_mm(p: dict) -> float:
    """RF length of a bend whose RF transit n_b.L_b/c equals the bend optical
    delay: the length compensation that makes the bend skew-free."""
    return float(p.get("bend_opt_delay_ps", 5.0)) * 1e-12 * C0 / bend_index(p) * 1e3


def bend_skew_ps(p: dict) -> float:
    """RF transit minus optical delay through one bend (ps): positive means the RF
    reaches the next electrode after the light. Transit at the bend's microwave
    index (at 60 GHz for a cross-section bend); reflections at the bend's ends
    add a little phase on top, which the cascade includes."""
    sk = (bend_index(p) * float(p.get("bend_len_mm", 0.0)) * 1e-3 / C0 * 1e12
          - float(p.get("bend_opt_delay_ps", 5.0)))
    return round(sk, 6) + 0.0          # no "-0.00 ps" at the matched length


def bend_walkoff_skew_ps(fit, p: dict, f_ref_GHz: float) -> float:
    """Bend skew (RF minus light, ps) that best re-aligns the electrode when the
    sections themselves walk off. Inside a section the RF drifts from the light
    by (n_m - n_g).L/c; a section's contribution is centred on its middle, so
    consecutive sections are aligned when the bend makes up the drift between
    their centres: skew = -(n_m - n_g).(L_k + L_k+1)/2 / c, averaged over the
    bends (all bends share one length). n_m is taken at f_ref (the -3 dB
    frequency is the natural choice: that is where the alignment matters).
    Zero when n_m = n_g; reflections and loss weighting move the true optimum a
    little further, which the cascade includes."""
    lay = electrode_layout(p)
    secs = [x["L_rf"] for x in lay if x["kind"] == "mod"]
    if len(secs) < 2:
        return 0.0
    dn = float(fit.nm(np.array([float(f_ref_GHz)]), offset=float(p.get("nm_offset", 0.0)))[0]) \
        - float(p.get("ng", 2.27))
    lbar = float(np.mean([(a + b) / 2 for a, b in zip(secs[:-1], secs[1:])]))
    return -dn * lbar / C0 * 1e12


def bend_walkoff_length_mm(fit, p: dict, f_ref_GHz: float) -> float:
    """Bend length giving bend_walkoff_skew_ps: (tau + skew) . c / n_b."""
    tau = float(p.get("bend_opt_delay_ps", 5.0)) + bend_walkoff_skew_ps(fit, p, f_ref_GHz)
    return max(tau, 0.0) * 1e-12 * C0 / bend_index(p) * 1e3


def electrode_layout(p: dict) -> list:
    """
    The electrode as an ordered list of pieces, from the RF input to the load.

    Each piece is a dict with ``kind`` ('mod' or 'bend'), ``L_rf`` (m, length
    along the electrode) and ``L_opt`` (m, optical path length through it).
    With n_bends = 0 this is one modulating piece of length L.
    """
    nb = max(0, min(int(p.get("n_bends", 0)), MAX_BENDS))
    L = float(p["L_target_mm"]) * 1e-3
    if nb == 0:
        return [dict(kind="mod", L_rf=L, L_opt=L)]
    auto = L / (nb + 1)
    secs = []
    for k in range(1, nb + 2):
        Lk = float(p.get(f"tw_len_{k}_mm", 0.0)) * 1e-3
        secs.append(Lk if Lk > 0 else auto)
    Lb = float(p.get("bend_len_mm", 0.0)) * 1e-3
    Lbo = bend_optical_length_m(p)
    out = []
    for k, Lk in enumerate(secs):
        out.append(dict(kind="mod", L_rf=Lk, L_opt=Lk))
        if k < nb:
            out.append(dict(kind="bend", L_rf=Lb, L_opt=Lbo))
    return out


def modulating_length_m(p: dict) -> float:
    return sum(x["L_rf"] for x in electrode_layout(p) if x["kind"] == "mod")


def rf_length_m(p: dict) -> float:
    return sum(x["L_rf"] for x in electrode_layout(p))


def _int_exp(x, L):
    """(1 - exp(-x L)) / x, with the x -> 0 limit L."""
    xL = x * L
    small = np.abs(xL) < 1e-9
    safe = np.where(small, 1.0, x)
    return np.where(small, L * (1 - xL / 2), (1 - np.exp(-xL)) / safe)


@dataclass
class SegmentedLine:
    """What the cascade knows about each modulating section (for export)."""
    H: np.ndarray                  # same convention as eo_transfer
    zin: np.ndarray                # input impedance of the whole electrode
    z_source: list                 # per mod section: impedance looking back to the source
    z_load: list                   # per mod section: impedance looking into the rest
    v_thevenin: list               # per mod section: open-circuit voltage / source voltage
    t_optical: list                # per mod section: optical delay to its start (s)


def segmented_transfer(f_GHz, alpha_dB_cm, nm, Zc, layout, ng, Zs, Zt,
                       bend_alpha_dB_cm=0.0, bend_nm=None, bend_Z=None) -> SegmentedLine:
    """
    EO transfer function of an electrode made of several line pieces.

    Exact transmission-line cascade: input impedances are found from the load
    backwards, voltages from the source forwards, so every reflection -- at the
    source, at each impedance step into and out of a bend, at the load -- is
    included to all orders. On piece i the voltage is

        V_i(z) = V_i+ ( e^{-g z} + G_i e^{-2 g L_i} e^{g z} ),   G_i = (Z_L,i - Zc_i)/(Z_L,i + Zc_i)

    and the light, which reaches the start of modulating piece i after the
    optical transit s_i of everything before it (bends included), sees

        H = (1/L_mod) sum_i e^{j bo s_i} int_0^{L_i} V_i(z) e^{j bo z} dz

    with bo = n_g w / c. Bends carry the RF (loss, delay, impedance) but add
    nothing to the sum. One piece reproduces eo_transfer up to a pure delay
    (eo_transfer references the optical exit, this the entry), which the phase
    factor at the end removes.
    """
    f = np.asarray(f_GHz, dtype=float)
    w = 2 * np.pi * f * 1e9
    bo = ng * w / C0
    n = f.size

    def as_arr(x):
        return np.broadcast_to(np.asarray(x, dtype=complex), (n,)).copy()

    g_line = np.asarray(alpha_dB_cm) * 100.0 * NP_PER_DB + 1j * np.asarray(nm) * w / C0
    nm_b = nm if bend_nm is None else bend_nm
    g_bend = bend_alpha_dB_cm * 100.0 * NP_PER_DB + 1j * np.asarray(nm_b) * w / C0
    Zc = as_arr(Zc)
    Zb = Zc if bend_Z is None else as_arr(bend_Z)
    Zs, Zt = as_arr(Zs), as_arr(Zt)

    pieces = [(as_arr(g_line), Zc, x) if x["kind"] == "mod" else (as_arr(g_bend), Zb, x)
              for x in layout]

    # load -> source: impedance looking into each piece, and each piece's load
    z_load = [None] * len(pieces)
    zl = Zt
    for i in range(len(pieces) - 1, -1, -1):
        g, Z, x = pieces[i]
        z_load[i] = zl
        th = np.tanh(g * x["L_rf"])
        zl = Z * (zl + Z * th) / (Z + zl * th)
    zin = zl

    # source -> load: voltages, Thevenin equivalents, optical positions
    v_in = zin / (Zs + zin)
    z_back = Zs
    s_opt = 0.0
    L_mod = sum(x["L_rf"] for x in layout if x["kind"] == "mod") or 1.0
    acc = np.zeros(n, dtype=complex)
    out_zs, out_zl, out_vth, out_t = [], [], [], []
    for i, (g, Z, x) in enumerate(pieces):
        L = x["L_rf"]
        G = (z_load[i] - Z) / (z_load[i] + Z)
        e2 = np.exp(-2 * g * L)
        vp = v_in / (1 + G * e2)
        if x["kind"] == "mod":
            fwd = _int_exp(g - 1j * bo, L)
            bwd = np.exp(-g * L + 1j * bo * L) * _int_exp(g + 1j * bo, L)
            acc += np.exp(1j * bo * s_opt) * vp * (fwd + G * bwd)
            out_zs.append(z_back.copy())
            out_zl.append(z_load[i].copy())
            zin_i = _zin_of(g, Z, L, z_load[i])
            out_vth.append(v_in * (z_back + zin_i) / zin_i)
            out_t.append(ng * s_opt / C0)
        th = np.tanh(g * L)
        z_back = Z * (z_back + Z * th) / (Z + z_back * th)
        v_in = vp * np.exp(-g * L) * (1 + G)
        s_opt += x["L_opt"]

    H = acc / L_mod * np.exp(-1j * bo * s_opt)
    return SegmentedLine(H=H, zin=zin, z_source=out_zs, z_load=out_zl,
                         v_thevenin=out_vth, t_optical=out_t)


def _zin_of(g, Z, L, zl):
    th = np.tanh(g * L)
    return Z * (zl + Z * th) / (Z + zl * th)


def line_transfer(f_GHz, alpha, nm, Zc, p: dict, ng: float, Zs, Zt):
    """(H, zin) of the electrode described by *p*: the closed-form uniform line
    when there are no bends (unchanged, validated path), the cascade otherwise."""
    if int(p.get("n_bends", 0)) <= 0:
        return eo_transfer(f_GHz, alpha, nm, Zc, float(p["L_target_mm"]) * 1e-3, ng, Zs, Zt)
    seg = segmented_transfer(f_GHz, alpha, nm, Zc, electrode_layout(p), ng, Zs, Zt,
                             **bend_line(p, f_GHz))
    return seg.H, seg.zin


# ---------------------------------------------------------------------
# The bend as a line of its own
# ---------------------------------------------------------------------
_BEND_FIT_CACHE: dict = {}


def fit_bend_loss(path: str, length_mm: float) -> tuple:
    """
    Fit alpha(f) = a.sqrt(f) + b.f  [dB/cm, f in GHz] to a simulated bend S21.

    The file holds f (GHz) and S21 (dB) of one bend of *length_mm*. It may be
    normalised at some frequency (BEND200GHZ.csv is 0 dB at 1 GHz), so the fit
    is on differences: S21(f) - S21(f_ref) = -(A(f) - A(f_ref)) with
    A = (a.sqrt(f) + b.f).L. The form has zero loss at DC, which is what a
    conductor-plus-dielectric line does, and it is what lets the loss be
    scaled to any bend length. Returns (a, b, rms_residual_dB).
    """
    key = (os.path.abspath(path), os.path.getmtime(path), float(length_mm))
    if key in _BEND_FIT_CACHE:
        return _BEND_FIT_CACHE[key]
    d = np.genfromtxt(path, delimiter=",", skip_header=1, invalid_raise=False)
    d = d[np.all(np.isfinite(d[:, :2]), axis=1)]
    f, s21 = d[:, 0], d[:, 1]
    i_ref = int(np.argmin(np.abs(s21)))              # where the file is normalised
    M = np.column_stack([np.sqrt(f) - np.sqrt(f[i_ref]), f - f[i_ref]])
    (aL, bL), *_ = np.linalg.lstsq(M, -(s21 - s21[i_ref]), rcond=None)
    rms = float(np.sqrt(np.mean((s21 - s21[i_ref] + M @ [aL, bL]) ** 2)))
    L_cm = float(length_mm) / 10.0
    out = (float(aL / L_cm), float(bL / L_cm), rms)
    _BEND_FIT_CACHE[key] = out
    return out


def bend_loss_coefficients(p: dict) -> tuple:
    """(a, b, source) of the bend attenuation alpha(f) = a.sqrt(f) + b.f."""
    path = str(p.get("bend_loss_file", "") or "")
    if path and os.path.isfile(path):
        a, b, _ = fit_bend_loss(path, float(p.get("bend_loss_file_len_mm", 0.8)))
        return a, b, os.path.basename(path)
    return float(p.get("bend_alpha_sqrt", 0.0)), float(p.get("bend_alpha_lin", 0.0)), "coefficients"


def bend_line(p: dict, f_GHz) -> dict:
    """
    The bend's own transmission-line properties on the frequency grid. Nothing
    here comes from the electrode's Touchstone: the bend is a different line.
    Keyword arguments for segmented_transfer.
    """
    f = np.maximum(np.asarray(f_GHz, dtype=float), 0.0)
    if bend_from_cross_section(p):
        # the analytical line model of the bend cross-section (bend_cpw): loss,
        # index and complex impedance at every frequency
        from .bend_cpw import geometry_from_params, line_constants
        lc = line_constants(geometry_from_params(p), f)
        return dict(bend_alpha_dB_cm=lc["alpha_dB_cm"], bend_nm=lc["n_m"], bend_Z=lc["Zc"])
    a, b, _ = bend_loss_coefficients(p)
    return dict(bend_alpha_dB_cm=a * np.sqrt(f) + b * f,
                bend_nm=float(p.get("bend_nm", 1.7)),
                bend_Z=float(p.get("bend_Z_ohm", 60.0)))


def straight_reference_transfer(f_GHz, alpha, nm, Zc, p: dict, ng: float, Zs, Zt):
    """The same device without bends: one straight electrode of the same total
    MODULATING length, same source and load. It is the yardstick for what the
    bends cost, because V_pi.L is a property of the modulating cross-section --
    a bend adds RF path and loss, never modulation."""
    L = modulating_length_m(p)
    return segmented_transfer(f_GHz, alpha, nm, Zc, [dict(kind="mod", L_rf=L, L_opt=L)],
                              ng, Zs, Zt).H


def bend_efficiency_dB(fit: "LineFit", p: dict) -> float:
    """Low-frequency modulation of the bent electrode relative to the straight
    one (0 dB without bends). The normalised S21 cannot show this: a bend loss
    that is flat in frequency scales the whole curve and normalises away."""
    if int(p.get("n_bends", 0)) <= 0:
        return 0.0
    f = np.array([fit.f_min_sim_GHz])
    alpha = fit.alpha_dB_cm(f, scale=float(p["alpha_scale"]),
                            skin_scale=float(p["alpha_skin_scale"]),
                            diel_scale=float(p["alpha_diel_scale"]),
                            offset=float(p["alpha_offset_dB_cm"]))
    nm = fit.nm(f, offset=float(p["nm_offset"]))
    Zc = fit.Zc(f, offset=float(p["zc_offset_ohm"]))
    Zs = rlc_impedance(f, float(p["Zs_R"]), float(p["Zs_L_pH"]), float(p["Zs_C_fF"]))
    Zt = rlc_impedance(f, float(p["Rt_R"]), float(p["Rt_L_pH"]), float(p["Rt_C_fF"]))
    ng = float(p["ng"])
    Hb, _ = line_transfer(f, alpha, nm, Zc, p, ng, Zs, Zt)
    Hs = straight_reference_transfer(f, alpha, nm, Zc, p, ng, Zs, Zt)
    return float(20 * np.log10(abs(Hb[0]) / abs(Hs[0])))


# =====================================================================
# 5. Bandwidth extraction
# =====================================================================
def first_crossing(f, y, level, f_start=0.0):
    """
    First frequency at which *y* drops to *level*, linearly interpolated.

    The search starts at *f_start*. Bandwidth means the roll-off crossing, so
    the search has to begin above the reference region: a strongly
    under-terminated line peaks with frequency, which leaves its own DC value
    more than 3 dB below the reference and would otherwise be reported as a
    bandwidth of 0 GHz.
    """
    y = np.where(np.isfinite(y), y, np.inf)     # a NaN is not a crossing
    mask = np.asarray(f) >= f_start
    below = np.where((y <= level) & mask)[0]
    if below.size == 0:
        return None
    i = below[0]
    if i == 0:
        return float(f[0])
    f1, f2 = f[i - 1], f[i]
    y1, y2 = y[i - 1], y[i]
    if y2 == y1:
        return float(f2)
    return float(f1 + (f2 - f1) * (level - y1) / (y2 - y1))


def reference_dB(f_GHz, raw_dB, window) -> float:
    """
    The 0 dB reference of a response curve, given a frequency window.

    A window with f_hi > f_lo is averaged (that is plateau normalisation --
    spanning whole standing-wave periods cancels the mismatch ripple instead of
    sampling a random phase of it). A degenerate window is read as a single
    point. Both the closed-form model and the INTERCONNECT read-back go through
    here, which is the only way to guarantee they cannot drift apart.
    """
    f = np.asarray(f_GHz, dtype=float)
    raw = np.asarray(raw_dB, dtype=float)
    f_lo, f_hi = float(window[0]), float(window[1])
    if f_hi > f_lo:
        win = (f >= f_lo) & (f <= f_hi) & np.isfinite(raw)
        if win.any():
            return float(np.mean(raw[win]))
    i = int(np.argmin(np.abs(f - f_lo)))
    return float(raw[i])


def normalise_and_measure(f_GHz, raw_dB, window, level):
    """
    Normalise a raw response and read its bandwidth off, one single way.

    Returns (s21_dB, bw_GHz, ref_dB, clipped).

    This exists because the two halves of the toolkit used to disagree here
    while agreeing perfectly on the physics. The closed-form model averaged
    over a plateau and searched for the crossing above the reference window;
    the INTERCONNECT read-back anchored on one frequency and took the first
    sample below the threshold anywhere in the sweep. On identical transfer
    functions that is worth a few tenths of a dB of reference, which on a
    shallow roll-off is worth tens of GHz of "bandwidth" -- the divergence was
    entirely in the book-keeping.
    """
    f = np.asarray(f_GHz, dtype=float)
    ref = reference_dB(f, raw_dB, window)
    s21 = np.asarray(raw_dB, dtype=float) - ref
    bw = first_crossing(f, s21, float(level), f_start=float(window[1]))
    clipped = bw is None
    return s21, (float(f[-1]) if clipped else float(bw)), ref, clipped


# =====================================================================
# 6. The single entry point the rest of the toolkit uses
# =====================================================================
def ripple_period_GHz(nm_ref: float, L_m: float) -> float:
    """
    Spacing of the standing-wave resonances of a mismatched electrode.

    The forward and backward microwave waves interfere, so a line whose Zc does
    not match the source and load rings with period c/(2 n_m L). On a 16.5 mm
    line at n_m = 2.29 that is 3.96 GHz, with about half a dB peak-to-peak at
    low frequency -- which is why picking one frequency as the 0 dB reference
    is picking a random phase of that ripple.
    """
    return C0 / (2.0 * nm_ref * L_m) / 1e9


PLATEAU_ROLLOFF_FRACTION = 0.15


def plateau_window(fit: "LineFit", p: dict, bw_hint: float) -> tuple:
    """
    Low-frequency averaging window: one standing-wave period.

    Averaging over a whole period cancels the ripple instead of sampling it,
    which is what makes the reported bandwidth independent of where the
    reference is taken. One period is the least that does so. Every further
    period only extends the window into the response's own low-frequency slope
    (skin effect, Zc dispersion), which drags the reference down and inflates
    the bandwidth.

    The window must also stay inside the flat part of the response, so it is
    capped at a fraction of the bandwidth (hence the *bw_hint* from a first
    pass). When a whole period does not fit below that cap -- a short line,
    whose ripple period is comparable to its bandwidth -- the window is
    shortened to the cap rather than collapsed to one point.

    The window is a continuous function of the line and its terminations.
    It used to be 1, 2 or 3 whole periods, or a single point when not even one
    fitted. Those steps turned small changes of Rt or of the frequency grid into
    jumps of the bandwidth: 29.6 vs 56.6 GHz for the same 16.5 mm line on two
    grids, and 65.9 -> 58.8 GHz between Rt = 35 and 40 ohm.

    Returns (f_lo, f_hi, period_GHz, periods_covered); periods_covered <= 1,
    0 when there is no room at all.
    """
    L_m = rf_length_m(p)
    nm_ref = float(np.atleast_1d(fit.nm(np.array([min(60.0, fit.f_max_sim_GHz)])))[0])
    period = ripple_period_GHz(nm_ref, L_m)
    f_lo = max(fit.f_min_sim_GHz, 0.0)
    ceiling = PLATEAU_ROLLOFF_FRACTION * float(bw_hint)
    if period <= 0 or ceiling <= f_lo:
        return f_lo, f_lo, period, 0.0
    f_hi = f_lo + min(period, ceiling - f_lo)
    return f_lo, f_hi, period, (f_hi - f_lo) / period


@dataclass
class EOResult:
    f_GHz: np.ndarray
    s21_dB: np.ndarray            # normalised to the low-frequency reference
    bw_GHz: float                 # -3 dB (or whatever level was asked for)
    bw_clipped: bool              # True if the response never crossed the level
    s21_at_probe_dB: float
    s11_dB: np.ndarray            # electrical input return loss vs f_sys
    s11_worst_dB: float
    zin: np.ndarray
    alpha_dB_cm: np.ndarray
    nm: np.ndarray
    Zc: np.ndarray
    walkoff_at_bw: float          # |n_m - n_g| evaluated at the -3 dB point
    # Complex, un-normalised. eo_transfer is complex throughout -- both the
    # reflection term p1 and the walk-off term p2 carry phase -- so the EO phase
    # is a real result of the model, not something the maths threw away. Its
    # group delay comes out at the optical transit time n_g.L/c.
    H: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=complex))
    gamma_in: np.ndarray = field(default_factory=lambda: np.empty(0, dtype=complex))
    ref_dB: float = 0.0            # what was subtracted to normalise the magnitude
    norm_mode: str = "plateau"
    norm_window_GHz: tuple = (0.0, 0.0)
    ripple_period_GHz: float = 0.0
    ripple_pp_dB: float = 0.0     # peak-to-peak of the low-frequency ripple
    # Filled by ``device_response``: the bare electrode (both arms at the
    # nominal n_g), kept alongside the whole-modulator curve for comparison.
    bw_electrode_GHz: float = float("nan")
    s21_electrode_dB: np.ndarray = field(default_factory=lambda: np.empty(0))


def eo_response(fit: LineFit, p: dict) -> EOResult:
    """
    Evaluate the full EO response for one parameter set.

    *p* is a normalised parameter dictionary (see ``parameters.normalise``).
    Only the "circuit" parameters are read here; link-level parameters such as
    V_pi or arm imbalance are handled by :func:`link_metrics`.
    """
    f_norm = float(p["f_norm_GHz"])
    f_max = float(p["f_max_GHz"])
    n_pts = int(p["n_points"])
    level = float(p["bw_level_dB"])
    norm_mode = str(p.get("norm_mode", "plateau"))

    # The grid runs from DC. The fitted forms carry 1/sqrt(f) and 1/f terms that
    # blow up below the measured band -- Zc reached 282 + 610j ohm at 10 MHz and
    # was infinite at f = 0, which turned the whole curve into NaN -- so the fits
    # are held at their lowest measured value below that point rather than being
    # extrapolated into a singularity.
    f = np.linspace(0.0, f_max, n_pts)
    f_eval = np.maximum(f, fit.f_min_sim_GHz)

    alpha = fit.alpha_dB_cm(f_eval,
                            scale=float(p["alpha_scale"]),
                            skin_scale=float(p["alpha_skin_scale"]),
                            diel_scale=float(p["alpha_diel_scale"]),
                            offset=float(p["alpha_offset_dB_cm"]))
    nm = fit.nm(f_eval, offset=float(p["nm_offset"]))
    Zc = fit.Zc(f_eval, offset=float(p["zc_offset_ohm"]))

    Zs = rlc_impedance(f_eval, float(p["Zs_R"]), float(p["Zs_L_pH"]), float(p["Zs_C_fF"]))
    Zt = rlc_impedance(f_eval, float(p["Rt_R"]), float(p["Rt_L_pH"]), float(p["Rt_C_fF"]))

    ng = float(p["ng"])

    H, zin = line_transfer(f, alpha, nm, Zc, p, ng, Zs, Zt)

    mag = np.abs(H)
    mag = np.where(np.isfinite(mag) & (mag > 0), mag, 1e-300)
    raw_dB = 20.0 * np.log10(mag)

    # First pass: locate the roll-off, so the averaging window can be kept
    # inside the flat region. The anchor is the mean over the first ripple
    # period, not the lowest measured sample: that sample sits on a random
    # phase of the ripple (or on the fit's low-frequency bump) and moved the
    # hint enough to change the window.
    i_lo = int(np.argmin(np.abs(f - max(fit.f_min_sim_GHz, 0.0))))
    _, _, period0, _ = plateau_window(fit, p, float("inf"))
    first = (f >= f[i_lo]) & (f <= f[i_lo] + period0) & np.isfinite(raw_dB)
    anchor = float(np.mean(raw_dB[first])) if first.sum() >= 2 else float(raw_dB[i_lo])
    bw_hint = first_crossing(f, raw_dB - anchor, level,
                             f_start=float(f[i_lo])) or float(f[-1])

    f_lo, f_hi, period, n_per = plateau_window(fit, p, bw_hint)
    win = (f >= f_lo) & (f <= f_hi) & np.isfinite(raw_dB)
    ripple_pp = float(raw_dB[win].max() - raw_dB[win].min()) if win.any() else 0.0

    if norm_mode == "plateau" and n_per > 0 and win.sum() >= 2:
        norm_window = (float(f_lo), float(f_hi))
    elif norm_mode == "plateau":
        norm_window = (float(f[i_lo]), float(f[i_lo]))   # no room at all
    else:
        i_norm = int(np.argmin(np.abs(f - f_norm)))
        norm_window = (float(f[i_norm]), float(f[i_norm]))

    s21_dB, bw, ref, clipped = normalise_and_measure(f, raw_dB, norm_window, level)

    # electrical input match, referenced to the system impedance
    z_ref = float(p["z0_sys_ohm"])
    gamma_in = (zin - z_ref) / (zin + z_ref)
    s11_dB = 20.0 * np.log10(np.clip(np.abs(gamma_in), 1e-12, None))

    f_probe = float(p["f_probe_GHz"])
    i_probe = int(np.argmin(np.abs(f - f_probe)))

    i_bw = int(np.argmin(np.abs(f - bw)))
    walkoff = float(abs(nm[i_bw] - ng))

    return EOResult(
        f_GHz=f, s21_dB=s21_dB, bw_GHz=float(bw), bw_clipped=clipped,
        s21_at_probe_dB=float(s21_dB[i_probe]),
        s11_dB=s11_dB, s11_worst_dB=float(np.max(s11_dB)),
        zin=zin, alpha_dB_cm=alpha, nm=nm, Zc=Zc, walkoff_at_bw=walkoff,
        H=H, gamma_in=gamma_in, ref_dB=float(ref),
        norm_mode=norm_mode, norm_window_GHz=norm_window,
        ripple_period_GHz=float(period), ripple_pp_dB=ripple_pp,
    )


# =====================================================================
# 7. Static link metrics (V_pi, extinction ratio, chirp)
# =====================================================================
@dataclass
class LinkMetrics:
    vpi_eff_V: float          # device half-wave voltage seen by the driver
    vpi_L_Vcm: float          # the figure of merit people actually compare
    er_dB: float              # static extinction ratio ceiling
    chirp_alpha: float        # Henry chirp parameter at quadrature
    imbalance_note: str = ""


def link_metrics(p: dict) -> LinkMetrics:
    """
    Static (DC) figures of merit of the interferometer.

    Push-pull with two arms of half-wave voltage Vpi1, Vpi2 driven with
    opposite sign produces a differential phase

        dphi = pi*V*(1/Vpi1 + 1/Vpi2)      ->  Vpi_eff = 1/(1/Vpi1 + 1/Vpi2)

    so a perfectly balanced device has Vpi_eff = Vpi_arm/2. Driving one arm
    only gives Vpi_eff = Vpi_arm and a chirp parameter of 1.

    The chirp parameter is alpha = (g1 + g2)/(g1 - g2) with g_i the per-arm
    phase-modulation efficiency; it is exactly 0 for ideal push-pull and grows
    with the arm-to-arm V_pi mismatch.
    """
    vpi = float(p["Vpi_V"])
    d = float(p["vpi_imbalance_frac"])
    config = str(p["drive_config"])

    g1 = 1.0 / vpi
    if config == "push-pull":
        g2 = -1.0 / (vpi * (1.0 + d))
    else:                                   # single-arm drive
        g2 = 0.0

    denom = g1 - g2
    vpi_eff = 1.0 / abs(denom) if denom != 0 else float("inf")
    chirp = (g1 + g2) / denom if denom != 0 else float("inf")

    # --- static extinction ratio from amplitude imbalance -------------
    rho = 0.5 + float(p["split_err"])
    rho = min(max(rho, 1e-6), 1 - 1e-6)
    a1 = np.sqrt(rho)
    a2 = np.sqrt(1.0 - rho) * 10 ** (-float(p["arm_loss_imbalance_dB"]) / 20.0)
    num, den = a1 + a2, abs(a1 - a2)
    er_dB = 20.0 * np.log10(num / den) if den > 1e-12 else float("inf")

    note = ""
    if float(p["arm_phase_imbalance_deg"]) != 0.0:
        note = (f"static arm phase error {float(p['arm_phase_imbalance_deg']):.1f} deg "
                f"-> bias offset, wavelength dependent")

    return LinkMetrics(
        vpi_eff_V=float(vpi_eff),
        vpi_L_Vcm=float(vpi_eff * modulating_length_m(p) * 100.0),
        er_dB=float(er_dB),
        chirp_alpha=float(chirp),
        imbalance_note=note,
    )


# =====================================================================
# 8. Per-arm interferometer model
# =====================================================================
@dataclass
class ArmModel:
    """Everything that can differ between the two arms of the interferometer.

    ``a``    field amplitude weight: splitter ratio and propagation loss.
    ``phi0`` static phase: bias point plus any optical path-length error.
    ``g``    phase-modulation efficiency in rad/V, *signed*. Push-pull means
             the two arms have opposite signs because the two waveguides sit
             in the two gaps of the G-S-G and see opposite E-field.
    ``ng``   optical group index of this arm, which sets its own walk-off
             against the microwave.
    """
    a: float
    phi0: float
    g: float
    ng: float


def arm_models(p: dict) -> tuple:
    """
    Turn the imbalance knobs into two concrete arms.

    The four mechanisms are independent and physically distinct, even though a
    single fabrication error (an asymmetric rib over-etch, say) drives several
    of them at once:

      split_err               power split away from 50:50      -> amplitude
      arm_loss_imbalance_dB   excess propagation loss of arm 2 -> amplitude
      arm_phase_imbalance_deg static optical path error        -> bias offset
      vpi_imbalance_frac      overlap-integral mismatch        -> efficiency
      ng_imbalance            group-index mismatch             -> walk-off

    Only the last of these can change the *shape* of the electro-optic
    response; the first four are frequency-flat and therefore move the eye
    around without moving the bandwidth. See ``link_response``.
    """
    rho = min(max(0.5 + float(p["split_err"]), 1e-6), 1 - 1e-6)
    a1 = np.sqrt(rho)
    a2 = np.sqrt(1.0 - rho) * 10 ** (-float(p["arm_loss_imbalance_dB"]) / 20.0)

    phi0_1 = 0.0
    phi0_2 = np.deg2rad(float(p["bias_phase_deg"]) + float(p["arm_phase_imbalance_deg"]))

    vpi = float(p["Vpi_V"])
    d = float(p["vpi_imbalance_frac"])
    g1 = np.pi / vpi
    g2 = -np.pi / (vpi * (1.0 + d)) if str(p["drive_config"]) == "push-pull" else 0.0

    ng = float(p["ng"])
    dn = float(p.get("ng_imbalance", 0.0))
    return (ArmModel(a1, phi0_1, g1, ng * (1.0 + dn / 2.0)),
            ArmModel(a2, phi0_2, g2, ng * (1.0 - dn / 2.0)))


def electrode_transfer(fit: LineFit, p: dict, f_GHz, ng: float, straight: bool = False):
    """The electrode's complex EO transfer function on an arbitrary grid.

    Shared by the small-signal response and the time-domain eye so the two can
    never be driven by different physics. The fits carry 1/sqrt(f) and 1/f
    terms that are singular below the measured band, so they are held at their
    lowest measured value there -- the same clamp ``eo_response`` uses.
    """
    f = np.asarray(f_GHz, dtype=float)
    f_eval = np.maximum(f, fit.f_min_sim_GHz)
    alpha = fit.alpha_dB_cm(f_eval,
                            scale=float(p["alpha_scale"]),
                            skin_scale=float(p["alpha_skin_scale"]),
                            diel_scale=float(p["alpha_diel_scale"]),
                            offset=float(p["alpha_offset_dB_cm"]))
    nm = fit.nm(f_eval, offset=float(p["nm_offset"]))
    Zc = fit.Zc(f_eval, offset=float(p["zc_offset_ohm"]))
    Zs = rlc_impedance(f_eval, float(p["Zs_R"]), float(p["Zs_L_pH"]), float(p["Zs_C_fF"]))
    Zt = rlc_impedance(f_eval, float(p["Rt_R"]), float(p["Rt_L_pH"]), float(p["Rt_C_fF"]))
    if straight:
        return straight_reference_transfer(f, alpha, nm, Zc, p, ng, Zs, Zt)
    H, _ = line_transfer(f, alpha, nm, Zc, p, ng, Zs, Zt)
    return H


@dataclass
class LinkResult:
    """Small-signal response of the whole interferometer, not just the electrode."""
    f_GHz: np.ndarray
    s21_dB: np.ndarray            # normalised, the curve you would measure
    bw_GHz: float
    bw_clipped: bool
    bw_electrode_GHz: float       # the same electrode with balanced arms
    H: np.ndarray                 # complex link response, un-normalised
    slope_efficiency: float       # |dP/dV| at the bias point, relative to ideal
    ref_dB: float = 0.0
    norm_window_GHz: tuple = (0.0, 0.0)


def link_response(fit: LineFit, p: dict, res: Optional[EOResult] = None) -> LinkResult:
    """
    Electro-optic response of the two-arm interferometer, arm by arm.

    Starting from the two-beam interference at the output combiner,

        P  = a1^2 + a2^2 + 2 a1 a2 cos(dphi0 + m1 - m2)

    a small drive v gives

        dP = -2 a1 a2 sin(dphi0) [ g1 H1(f) - g2 H2(f) ] V(f)

    with H_i the travelling-wave transfer function seen by arm i. Everything
    outside the bracket is frequency-flat, so it scales the response without
    reshaping it. That is the whole story of arm imbalance and bandwidth:

      * amplitude imbalance (loss, splitter) enters only through 2 a1 a2,
      * bias error enters only through sin(dphi0),
      * V_pi imbalance enters only through the weights g1 and g2,

    and none of the three can move the -3 dB point. Only a group-index
    mismatch does, because that makes H1 and H2 genuinely different functions
    of frequency -- and for any realistic over-etch it is a very small effect.
    This is a prediction worth checking rather than a claim to take on trust,
    which is why ``bw_electrode_GHz`` is reported alongside.
    """
    arm1, arm2 = arm_models(p)
    f = np.linspace(0.0, float(p["f_max_GHz"]), int(p["n_points"]))
    level = float(p["bw_level_dB"])

    H1 = electrode_transfer(fit, p, f, arm1.ng)
    H2 = H1 if arm1.ng == arm2.ng else electrode_transfer(fit, p, f, arm2.ng)

    dphi0 = arm2.phi0 - arm1.phi0
    prefactor = -2.0 * arm1.a * arm2.a * np.sin(dphi0)
    bracket = arm1.g * H1 - arm2.g * H2
    H = prefactor * bracket

    if res is None:
        res = eo_response(fit, p)
    window = res.norm_window_GHz

    # The shape comes from the bracket alone; the prefactor is flat and is
    # zero at a null bias, where it would otherwise wipe out the curve.
    mag = np.abs(bracket)
    mag = np.where(np.isfinite(mag) & (mag > 0), mag, 1e-300)
    s21, bw, ref, clipped = normalise_and_measure(f, 20.0 * np.log10(mag), window, level)

    # How much modulation slope survives, against a perfectly balanced device
    # biased at quadrature and driven with the same single-arm V_pi.
    ideal = 2.0 * 0.5 * (2.0 * np.pi / float(p["Vpi_V"]))
    slope = abs(prefactor * (arm1.g - arm2.g)) / ideal if ideal else float("nan")

    return LinkResult(
        f_GHz=f, s21_dB=s21, bw_GHz=bw, bw_clipped=clipped,
        bw_electrode_GHz=float(res.bw_GHz), H=H, slope_efficiency=float(slope),
        ref_dB=float(ref), norm_window_GHz=window,
    )


def device_response(fit: LineFit, p: dict) -> EOResult:
    """
    The EO response of the whole modulator: what the GUI, the sweep, the
    command line and the exported Touchstone report as "the" EO response.

    ``eo_response`` models one electrode seen by light at the nominal n_g.
    That is the whole device only while both arms share that n_g. With a
    group-index imbalance each arm walks off differently, and the modulator
    responds to the weighted difference of two electrode responses:

        H_dev(f) = (g1 H1(f) - g2 H2(f)) / (g1 - g2)

    (the bracket of ``link_response``, divided by its DC value so that with
    equal n_g it is exactly H1). This returns the electrode result with H,
    S21 and bandwidth replaced by the whole-modulator ones, normalised in the
    same window, and keeps the bare electrode's in ``bw_electrode_GHz`` /
    ``s21_electrode_dB``. Every other imbalance is frequency-flat, so with
    ng_imbalance = 0 nothing changes.
    """
    res = eo_response(fit, p)
    arm1, arm2 = arm_models(p)
    f = res.f_GHz
    if arm1.ng == float(p["ng"]) and arm2.ng == float(p["ng"]):
        return replace(res, bw_electrode_GHz=float(res.bw_GHz),
                       s21_electrode_dB=res.s21_dB)
    H1 = electrode_transfer(fit, p, f, arm1.ng)
    H2 = electrode_transfer(fit, p, f, arm2.ng) if arm2.g != 0 else 0.0
    H = (arm1.g * H1 - arm2.g * H2) / (arm1.g - arm2.g)
    mag = np.abs(H)
    mag = np.where(np.isfinite(mag) & (mag > 0), mag, 1e-300)
    s21, bw, ref, clipped = normalise_and_measure(
        f, 20.0 * np.log10(mag), res.norm_window_GHz, float(p["bw_level_dB"]))
    i_probe = int(np.argmin(np.abs(f - float(p["f_probe_GHz"]))))
    i_bw = int(np.argmin(np.abs(f - bw)))
    return replace(
        res, H=H, s21_dB=s21, bw_GHz=float(bw), bw_clipped=bool(clipped),
        ref_dB=float(ref), s21_at_probe_dB=float(s21[i_probe]),
        walkoff_at_bw=float(abs(res.nm[i_bw] - float(p["ng"]))),
        bw_electrode_GHz=float(res.bw_GHz), s21_electrode_dB=res.s21_dB,
    )
