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

from dataclasses import dataclass, field
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


PLATEAU_MAX_PERIODS = 3
PLATEAU_ROLLOFF_FRACTION = 0.15


def plateau_window(fit: "LineFit", p: dict, bw_hint: float) -> tuple:
    """
    Low-frequency averaging window, spanning whole standing-wave periods.

    Averaging over an integer number of periods cancels the ripple instead of
    sampling it, which is what makes the reported bandwidth independent of
    where the reference is taken.

    The window must also stay inside the flat part of the response: a window
    that reaches into the roll-off drags the reference down and inflates the
    bandwidth. So it is capped at a fraction of the bandwidth itself (hence the
    *bw_hint* from a first pass), and if not even one whole period fits below
    that cap -- a short line, whose ripple period is comparable to its
    bandwidth -- this returns n_per = 0 and the caller falls back to anchoring
    on the lowest measured frequency.

    Returns (f_lo, f_hi, period_GHz, n_periods).
    """
    L_m = float(p["L_target_mm"]) * 1e-3
    nm_ref = float(np.atleast_1d(fit.nm(np.array([min(60.0, fit.f_max_sim_GHz)])))[0])
    period = ripple_period_GHz(nm_ref, L_m)
    f_lo = max(fit.f_min_sim_GHz, 0.0)
    ceiling = PLATEAU_ROLLOFF_FRACTION * float(bw_hint)
    if period <= 0 or ceiling <= f_lo:
        return f_lo, f_lo, period, 0
    n_per = min(PLATEAU_MAX_PERIODS, int((ceiling - f_lo) / period))
    if n_per < 1:
        return f_lo, f_lo, period, 0
    return f_lo, f_lo + n_per * period, period, n_per


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

    L_m = float(p["L_target_mm"]) * 1e-3
    ng = float(p["ng"])

    H, zin = eo_transfer(f, alpha, nm, Zc, L_m, ng, Zs, Zt)

    mag = np.abs(H)
    mag = np.where(np.isfinite(mag) & (mag > 0), mag, 1e-300)
    raw_dB = 20.0 * np.log10(mag)

    # First pass: anchor on the lowest measured frequency just to locate the
    # roll-off, so the averaging window can be kept inside the flat region.
    i_lo = int(np.argmin(np.abs(f - max(fit.f_min_sim_GHz, 0.0))))
    bw_hint = first_crossing(f, raw_dB - raw_dB[i_lo], level,
                             f_start=float(f[i_lo])) or float(f[-1])

    f_lo, f_hi, period, n_per = plateau_window(fit, p, bw_hint)
    win = (f >= f_lo) & (f <= f_hi) & np.isfinite(raw_dB)
    ripple_pp = float(raw_dB[win].max() - raw_dB[win].min()) if win.any() else 0.0

    if norm_mode == "plateau" and n_per >= 1 and win.any():
        ref = float(np.mean(raw_dB[win]))
        norm_window = (float(f_lo), float(f_hi))
    elif norm_mode == "plateau":
        ref = float(raw_dB[i_lo])           # no room to average a whole period
        norm_window = (float(f[i_lo]), float(f[i_lo]))
    else:
        i_norm = int(np.argmin(np.abs(f - f_norm)))
        ref = float(raw_dB[i_norm])
        norm_window = (float(f[i_norm]), float(f[i_norm]))
    s21_dB = raw_dB - ref

    bw = first_crossing(f, s21_dB, level, f_start=float(norm_window[1]))
    clipped = bw is None
    if clipped:
        bw = float(f[-1])

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
        vpi_L_Vcm=float(vpi_eff * float(p["L_target_mm"]) * 0.1),
        er_dB=float(er_dB),
        chirp_alpha=float(chirp),
        imbalance_note=note,
    )
