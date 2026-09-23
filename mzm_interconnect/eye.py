"""
Time-domain link simulation and eye diagram.

The frequency-domain half of the toolkit answers "what is the -3 dB
bandwidth?". That number is a single point on a curve, and it is deliberately
blind to everything the bandwidth is not: extinction ratio, bias error, chirp,
pattern-dependent distortion. The eye is where those show up.

Nothing here re-derives any physics. The electrode transfer function is the
same ``eo_transfer`` the response plot and INTERCONNECT both use, evaluated on
the FFT grid instead of a plot grid, so an eye and a bandwidth computed from
the same settings are guaranteed to be describing the same device.

Signal chain:

    PRBS -> NRZ/PAM4 -> driver Bessel -> electrode H_i(f) -> per-arm phase
         -> two-beam interference -> optional SSMF dispersion
         -> photodiode (+ shot and thermal noise) -> receiver Bessel -> eye
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.signal import bessel

from .physics import C0, LineFit, arm_models, electrode_transfer

# Above this the fitted alpha(f) is extrapolated far outside anything that was
# measured, and the response is a hundred dB down anyway. Holding the transfer
# function constant up there keeps the FFT well behaved without shaping the
# part of the spectrum that carries the signal.
F_MODEL_CEIL_GHz = 2000.0

# LFSR feedback taps (1-based positions) for maximal-length sequences.
PRBS_TAPS = {7: (7, 6), 9: (9, 5), 11: (11, 9), 15: (15, 14), 23: (23, 18)}


def prbs_bits(order: int, n_bits: int) -> np.ndarray:
    """Maximal-length PRBS of the requested order, repeated to *n_bits*."""
    taps = PRBS_TAPS.get(int(order))
    if taps is None:
        raise ValueError(f"PRBS order {order} not available; "
                         f"choose from {sorted(PRBS_TAPS)}")
    state = (1 << int(order)) - 1
    period = (1 << int(order)) - 1
    seq = np.empty(period, dtype=np.uint8)
    for i in range(period):
        seq[i] = state & 1
        fb = 0
        for t in taps:
            fb ^= (state >> (t - 1)) & 1
        state = ((state << 1) | fb) & ((1 << int(order)) - 1)
    return np.resize(seq, int(n_bits))


def _bessel4(f_GHz, f3dB_GHz):
    """4th-order Bessel-Thomson response, -3 dB at *f3dB_GHz*.

    Bessel rather than Butterworth because it is what both driver amplifiers
    and reference receivers approximate: near-constant group delay, so the
    filter does not add its own intersymbol interference on top of the
    modulator's.
    """
    if f3dB_GHz <= 0:
        return np.ones_like(np.asarray(f_GHz, dtype=float))
    b, a = bessel(4, 1.0, norm="mag", analog=True)
    s = 1j * np.asarray(f_GHz, dtype=float) / float(f3dB_GHz)
    return np.polyval(b, s) / np.polyval(a, s)


@dataclass
class EyeResult:
    t_ps: np.ndarray              # time axis of one 2-UI eye window
    traces: np.ndarray            # (n_traces, n_samples) photocurrent, A
    bitrate_Gbps: float
    symbol_rate_GBd: float
    levels: int                   # 2 for NRZ, 4 for PAM4
    er_dB: float                  # dynamic extinction ratio measured on the eye
    eye_height_A: float
    eye_opening_dB: float
    crossing_pct: float
    jitter_rms_ps: float
    q_factor: float
    oma_A: float
    mean_power_W: float
    sample_index: int             # where in the window the eye was sampled
    # what went in, so a figure can label itself
    drive_bw_GHz: float = 0.0
    rx_bw_GHz: float = 0.0
    fibre_km: float = 0.0
    notes: list = field(default_factory=list)


def _auto(value, fallback):
    v = float(value)
    return v if v > 0 else fallback


# A filter corner this close to the sample grid's Nyquist frequency cannot be
# represented: the stopband has nowhere to live, so a sharp edge rings instead
# of settling, and the ringing shows up as photocurrent below zero and rails
# past the static transfer curve. Anything above this is clamped and said so.
NYQUIST_SAFE_FRACTION = 0.4


def _clamp_bw(name, value, fs_GHz, notes):
    """Hold a filter corner inside what the sample grid can represent."""
    ceiling = NYQUIST_SAFE_FRACTION * fs_GHz
    if value <= ceiling:
        return value
    notes.append(
        f"{name} {value:.1f} GHz is past what this grid can represent "
        f"(sample rate {fs_GHz:.0f} GHz); clamped to {ceiling:.1f} GHz. "
        f"Raise 'Samples per symbol' to model a faster filter.")
    return ceiling


def simulate_eye(fit: LineFit, p: dict, seed: int = 12345) -> EyeResult:
    """
    Run the link in the time domain and fold the result into an eye.

    The drive is filtered by the electrode's own complex transfer function,
    normalised so that a static drive of V_pi gives exactly pi radians -- which
    is how V_pi is defined and measured. Everything the frequency-domain model
    knows about walk-off, microwave loss and mismatch ripple therefore reaches
    the eye automatically, as intersymbol interference rather than as a number.
    """
    levels = 4 if str(p.get("mod_format", "NRZ")).upper() == "PAM4" else 2
    bits_per_sym = 1 if levels == 2 else 2
    bitrate = float(p["bitrate_Gbps"])
    sym_rate = bitrate / bits_per_sym                      # GBd
    sps = int(p["samples_per_symbol"])
    order = int(p["prbs_order"])

    n_sym = (1 << order) - 1
    if n_sym * sps > 1 << 21:                              # keep the FFT sane
        n_sym = (1 << 21) // sps
    n_bits = n_sym * bits_per_sym
    bits = prbs_bits(order, n_bits)

    # ---- symbols ----------------------------------------------------
    if levels == 2:
        symbols = bits.astype(float)
    else:                                                  # Gray-coded PAM4
        pairs = bits[: 2 * n_sym].reshape(-1, 2)
        gray = {(0, 0): 0.0, (0, 1): 1.0, (1, 1): 2.0, (1, 0): 3.0}
        symbols = np.array([gray[(int(a), int(b))] for a, b in pairs]) / 3.0
    n_sym = symbols.size

    fs_GHz = sym_rate * sps
    n = n_sym * sps
    t_s = np.arange(n) / (fs_GHz * 1e9)

    # ---- drive waveform, centred on zero ----------------------------
    Vpp = float(p["drive_Vpp_V"])
    v = np.repeat(symbols - 0.5, sps) * Vpp
    f_GHz = np.fft.rfftfreq(n, d=1.0 / (fs_GHz * 1e9)) / 1e9

    notes = []
    drive_bw = _clamp_bw("Driver bandwidth",
                         _auto(p["drive_bw_GHz"], 0.7 * sym_rate), fs_GHz, notes)
    V = np.fft.rfft(v) * _bessel4(f_GHz, drive_bw)

    # ---- per-arm electrode response ---------------------------------
    arm1, arm2 = arm_models(p)
    f_model = np.minimum(f_GHz, F_MODEL_CEIL_GHz)
    if f_GHz[-1] > F_MODEL_CEIL_GHz:
        notes.append(f"electrode response held constant above "
                     f"{F_MODEL_CEIL_GHz:.0f} GHz (it is ~100 dB down there)")

    def arm_phase(arm):
        H = electrode_transfer(fit, p, f_model, arm.ng)
        # Normalise so a DC drive of V_pi gives pi radians: that is what makes
        # V_pi mean what it means. H[0] carries the low-frequency gain.
        h0 = H[0] if np.isfinite(H[0]) and abs(H[0]) > 0 else 1.0
        m = np.fft.irfft(V * (H / h0) * arm.g, n=n)
        return m

    m1 = arm_phase(arm1)
    m2 = m1 * (arm2.g / arm1.g) if (arm1.ng == arm2.ng and arm1.g != 0) \
        else (arm_phase(arm2) if arm2.g != 0 else np.zeros(n))

    # ---- two-beam interference --------------------------------------
    P_laser = 10 ** (float(p["P_laser_dBm"]) / 10) / 1000.0
    E0 = np.sqrt(P_laser)
    E = E0 * (arm1.a * np.exp(1j * (arm1.phi0 + m1))
              + arm2.a * np.exp(1j * (arm2.phi0 + m2)))

    # ---- optional fibre ---------------------------------------------
    z_km = float(p["fibre_km"])
    if z_km > 0:
        lam = float(p["lambda_nm"]) * 1e-9
        D = float(p["fibre_D_ps_nm_km"]) * 1e-6            # s/m/m
        beta2 = -D * lam ** 2 / (2 * np.pi * C0)           # s^2/m
        w = 2 * np.pi * np.fft.fftfreq(n, d=1.0 / (fs_GHz * 1e9))
        E = np.fft.ifft(np.fft.fft(E) * np.exp(1j * beta2 / 2 * w ** 2 * (z_km * 1e3)))

    # ---- photodiode --------------------------------------------------
    R = 1.0                                                # A/W, matches PIN_1
    i_t = R * np.abs(E) ** 2

    rx_bw = _clamp_bw("Receiver bandwidth",
                      _auto(p["rx_bw_GHz"], 0.75 * sym_rate), fs_GHz, notes)
    if bool(p["eye_noise"]):
        rng = np.random.default_rng(seed)
        q = 1.602176634e-19
        psd = 2 * q * float(np.mean(i_t)) \
            + (float(p["rx_thermal_pA_rtHz"]) * 1e-12) ** 2      # A^2/Hz
        sigma = np.sqrt(max(psd, 0.0) * (fs_GHz * 1e9) / 2.0)
        i_t = i_t + rng.normal(0.0, sigma, n)

    i_t = np.fft.irfft(np.fft.rfft(i_t) * _bessel4(f_GHz, rx_bw), n=n)

    # ---- fold into an eye --------------------------------------------
    win = 2 * sps
    n_tr = (n - win) // sps
    traces = np.empty((n_tr, win))
    for k in range(n_tr):
        traces[k] = i_t[k * sps: k * sps + win]

    # The whole chain -- driver filter, electrode transit (n_g.L/c is already
    # several UI at these rates), receiver filter -- delays the waveform, so the
    # received samples have to be realigned with the symbols that produced them
    # before anything can be labelled. One cross-correlation finds that delay.
    # The PRBS occupies exactly one period of the FFT, so the circular
    # convolution the filtering performs is the correct one and there are no
    # edge effects to work around.
    ref = np.repeat(symbols - symbols.mean(), sps)
    xc = np.fft.irfft(np.fft.rfft(i_t - i_t.mean()) * np.conj(np.fft.rfft(ref)), n=n)
    lag = int(np.argmax(np.abs(xc)))

    def labels_at(j):
        return ((np.arange(n_tr) * sps + j - lag) // sps) % n_sym

    # The transmitted symbols are known, so every trace can be labelled exactly
    # instead of being thresholded -- which matters for PAM4, where a single
    # threshold is meaningless, and for a badly closed NRZ eye, where it is
    # simply wrong.
    uniq = np.unique(symbols)

    def opening_at(j):
        lab = symbols[labels_at(j)]
        col_ = traces[:, j]
        gaps = []
        for a, b in zip(uniq[:-1], uniq[1:]):
            lo_, hi_ = col_[lab == b], col_[lab == a]
            if lo_.size and hi_.size:
                gaps.append(lo_.min() - hi_.max())
        return min(gaps) if gaps else -np.inf

    j0 = max(range(win), key=opening_at)

    labels = symbols[labels_at(j0)]
    col = traces[:, j0]
    mu = np.array([col[labels == u].mean() if (labels == u).any() else np.nan
                   for u in uniq])
    sd = np.array([col[labels == u].std() if (labels == u).sum() > 1 else 0.0
                   for u in uniq])

    mu0, mu1 = float(mu[0]), float(mu[-1])
    oma = mu1 - mu0
    er = 10 * np.log10(mu1 / mu0) if mu0 > 0 else float("inf")

    # Worst of the sub-eyes: for NRZ there is only one, for PAM4 there are three
    # and the link is only as good as the tightest of them.
    heights, qs = [], []
    for i in range(len(uniq) - 1):
        heights.append((mu[i + 1] - 3 * sd[i + 1]) - (mu[i] + 3 * sd[i]))
        denom = sd[i] + sd[i + 1]
        qs.append((mu[i + 1] - mu[i]) / denom if denom > 0 else float("inf"))
    eye_h = float(min(heights)) if heights else float("nan")
    q_fac = float(min(qs)) if qs else float("nan")

    # Crossing point: where the traces of the outer rails bunch together.
    cross_level = 0.5 * (mu1 + mu0)
    tol = 0.05 * max(abs(oma), 1e-18)
    spread = np.array([float(np.sum(np.abs(traces[:, j] - cross_level) < tol))
                       for j in range(win)])
    j_cross = int(np.argmax(spread))
    crossing_pct = 100.0 * (float(np.median(traces[:, j_cross])) - mu0) / oma \
        if oma > 0 else float("nan")

    # Jitter: spread of the times at which traces cross that level, kept to the
    # crossing nearest the eye edge so the two edges are not pooled together.
    t_ps = np.arange(win) / (fs_GHz * 1e9) * 1e12
    ui_ps = 1e3 / sym_rate
    cross_times = []
    for k in range(n_tr):
        y = traces[k] - cross_level
        for i in np.where(np.diff(np.sign(y)) != 0)[0]:
            if y[i + 1] == y[i]:
                continue
            tt = t_ps[i] + (-y[i] / (y[i + 1] - y[i])) * (t_ps[i + 1] - t_ps[i])
            if abs(tt - t_ps[j_cross]) < 0.25 * ui_ps:
                cross_times.append(tt)
    jitter = float(np.std(cross_times)) if len(cross_times) > 2 else 0.0

    return EyeResult(
        t_ps=t_ps, traces=traces, bitrate_Gbps=bitrate, symbol_rate_GBd=sym_rate,
        levels=levels, er_dB=float(er), eye_height_A=float(eye_h),
        eye_opening_dB=float(10 * np.log10(eye_h / oma)) if (eye_h > 0 and oma > 0)
        else float("-inf"),
        crossing_pct=float(crossing_pct), jitter_rms_ps=jitter,
        q_factor=float(q_fac), oma_A=float(oma),
        mean_power_W=float(np.mean(i_t) / R), sample_index=j0,
        drive_bw_GHz=drive_bw, rx_bw_GHz=rx_bw, fibre_km=z_km, notes=notes,
    )
