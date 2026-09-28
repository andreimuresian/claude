"""Touchstone -> (gamma, Zc) extraction and travelling-wave EO response.

Everything here is closed-form; no fitting.

Extraction (same as thesis App. B): S -> ABCD, cosh(gamma*L) = (A+D)/2,
Zc = sqrt(B/C).  The branch of the complex acosh is fixed by picking the
root e^{-gamma L} closest to S21 (the forward wave) and unwrapping its phase
over frequency, so beta*L is continuous from 0 even for a 14 mm line
(beta*L ~ 50 rad at 80 GHz).

EO response (thesis Eq. 1.3 / predictor 5.10.4), written here as the
explicit overlap integral so every sign is visible:

    V(z)  = V+ e^{-gz} + V- e^{+gz},  V+ + V- = V0 = Vs Zin / (Zs + Zin)
    V+    = V0 (Rt + Zc) e^{+gL} / D,  V- = V0 (Rt - Zc) e^{-gL} / D
    D     = (Rt + Zc) e^{+gL} + (Rt - Zc) e^{-gL}
    m(f)  = (1/L) int_0^L V(z) e^{+j k_o z} dz,   k_o = w n_g / c

(e^{+jwt} convention: the optical wave launched at t0 sees the RF phasor
at time t0 + n_g z / c.)
"""
import numpy as np

C0 = 299792458.0


def read_s2p(path):
    """CST 'GHz S MA R 50' Touchstone -> f [Hz], S [nf,2,2] complex, Zref."""
    rows, zref = [], 50.0
    with open(path) as fh:
        for line in fh:
            s = line.strip()
            if not s or s.startswith('!'):
                continue
            if s.startswith('#'):
                tok = s.upper().split()
                assert tok[1:4] == ['GHZ', 'S', 'MA'], s
                zref = float(tok[tok.index('R') + 1])
                continue
            rows.append([float(x) for x in s.split()])
    d = np.array(rows)
    f = d[:, 0] * 1e9
    ma = lambda m, a: m * np.exp(1j * np.deg2rad(a))
    S = np.empty((len(f), 2, 2), complex)
    S[:, 0, 0] = ma(d[:, 1], d[:, 2])
    S[:, 1, 0] = ma(d[:, 3], d[:, 4])
    S[:, 0, 1] = ma(d[:, 5], d[:, 6])
    S[:, 1, 1] = ma(d[:, 7], d[:, 8])
    return f, S, zref


def s_to_abcd(S, z0):
    s11, s12, s21, s22 = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]
    A = ((1 + s11) * (1 - s22) + s12 * s21) / (2 * s21)
    B = z0 * ((1 + s11) * (1 + s22) - s12 * s21) / (2 * s21)
    C = ((1 - s11) * (1 - s22) - s12 * s21) / (2 * s21 * z0)
    D = ((1 - s11) * (1 + s22) + s12 * s21) / (2 * s21)
    return A, B, C, D


def abcd_to_s(A, B, C, D, z0):
    den = A + B / z0 + C * z0 + D
    S = np.empty((len(A), 2, 2), complex)
    S[:, 0, 0] = (A + B / z0 - C * z0 - D) / den
    S[:, 0, 1] = 2 * (A * D - B * C) / den
    S[:, 1, 0] = 2 / den
    S[:, 1, 1] = (-A + B / z0 - C * z0 + D) / den
    return S


def gamma_L(S, z0):
    """Unwrapped gamma*L (complex, per frequency) and Zc from one 2-port."""
    A, B, C, D = s_to_abcd(S, z0)
    x = 0.5 * (A + D)
    r = np.sqrt(x * x - 1 + 0j)
    mu1, mu2 = x - r, x + r                       # the two roots, mu1*mu2 = 1
    s21 = S[:, 1, 0]
    mu = np.where(np.abs(mu1 - s21) <= np.abs(mu2 - s21), mu1, mu2)  # e^{-gL}
    gl = -np.log(np.abs(mu)) - 1j * np.unwrap(np.angle(mu))
    # Zc = sqrt(B/C), sign with Re > 0; cross-check B / sinh(gL)
    zc = np.sqrt(B / C)
    zc = np.where(zc.real < 0, -zc, zc)
    return gl, zc


def per_length(f, gl, L):
    """alpha [dB/cm], n_m from gamma*L of a line of length L [m]."""
    alpha_dbcm = 20 / np.log(10) * gl.real / L / 100
    nm = gl.imag * C0 / (2 * np.pi * f * L)
    return alpha_dbcm, nm


def line_s(gamma, zc, L, z0):
    """S-parameters of a uniform line (gamma per m, Zc) of length L."""
    gl = gamma * L
    return abcd_to_s(np.cosh(gl), zc * np.sinh(gl), np.sinh(gl) / zc,
                     np.cosh(gl), z0)


def _int_exp(a, L):
    """int_0^L e^{a z / L} dz = L (e^a - 1)/a, stable for a -> 0."""
    small = np.abs(a) < 1e-9
    a_safe = np.where(small, 1.0, a)
    return np.where(small, L * (1 + a / 2), L * np.expm1(a_safe) / a_safe)


def eo_response(f, gamma, zc, L, ng, Rt, Zs):
    """Complex EO response m(f) (un-normalised) for device length L."""
    gl = gamma * L
    ko = 2 * np.pi * f * ng / C0
    zin = zc * (Rt + zc * np.tanh(gl)) / (zc + Rt * np.tanh(gl))
    v0 = zin / (Zs + zin)
    D = (Rt + zc) * np.exp(gl) + (Rt - zc) * np.exp(-gl)
    vp = v0 * (Rt + zc) * np.exp(gl) / D
    vm = v0 * (Rt - zc) * np.exp(-gl) / D
    Ip = _int_exp((-gamma + 1j * ko) * L, L)
    Im = _int_exp((+gamma + 1j * ko) * L, L)
    return (vp * Ip + vm * Im) / L


def eo_db(m):
    """20 log10 |m| normalised to the lowest frequency point."""
    return 20 * np.log10(np.abs(m) / np.abs(m[0]))


def bw3db(f, db):
    """First -3 dB crossing (linear interpolation); nan if never crossed."""
    k = np.where(db <= -3.0)[0]
    if len(k) == 0:
        return np.nan
    i = k[0]
    return f[i - 1] + (f[i] - f[i - 1]) * (-3.0 - db[i - 1]) / (db[i] - db[i - 1])
