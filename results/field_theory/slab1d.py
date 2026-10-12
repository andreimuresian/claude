"""1D multilayer slab-mode solver (TE / TM w.r.t. the layer normal y), complex beta.

Layers are listed bottom -> top: [(eps_inplane_tangent, eps_normal, thickness_um), ...];
the first and last entries are half-spaces (thickness ignored).
TE  (E along the layers, transverse to propagation): field U = E_t, ky^2 = eps_t k0^2 - b^2
TM  (H along the layers): U = H_t, ky^2 = (eps_s/eps_y)(eps_y k0^2 - b^2), V = (1/eps_s) dU/dy
Time convention exp(+jwt), fields ~ exp(-j b s); Im(n) < 0 is loss (same as femwell run).
"""
import numpy as np
from scipy.optimize import newton


def _ky2(pol, es, ey, k0, b):
    return es * k0**2 - b**2 if pol == "TE" else (es / ey) * (ey * k0**2 - b**2)


def _q(pol, es):
    return 1.0 if pol == "TE" else 1.0 / es


def _gamma(pol, es, ey, k0, b):
    g = np.sqrt(-_ky2(pol, es, ey, k0, b) + 0j)
    return g if g.real >= 0 else -g


def char(n, layers, k0, pol):
    b = n * k0
    es, ey, _ = layers[0]
    g = _gamma(pol, es, ey, k0, b)
    U, V = 1.0 + 0j, _q(pol, es) * g
    for es, ey, d in layers[1:-1]:
        ky = np.sqrt(_ky2(pol, es, ey, k0, b) + 0j)
        q = _q(pol, es)
        c, s = np.cos(ky * d), np.sin(ky * d)
        U, V = c * U + s / (q * ky) * V, -q * ky * s * U + c * V
    es, ey, _ = layers[-1]
    return V + _q(pol, es) * _gamma(pol, es, ey, k0, b) * U


def solve(layers, k0, pol, n0):
    return complex(newton(lambda n: char(n, layers, k0, pol), n0 + 0j, tol=1e-12, maxiter=200))


def profile(n, layers, k0, pol, y):
    """U(y) and V(y) on points y (y = 0 at the bottom of the first finite layer)."""
    b = n * k0
    tops = np.cumsum([0.0] + [d for _, _, d in layers[1:-1]])
    U = np.zeros_like(y, dtype=complex); V = np.zeros_like(y, dtype=complex)
    es, ey, _ = layers[0]
    g = _gamma(pol, es, ey, k0, b); q = _q(pol, es)
    m = y < 0
    U[m] = np.exp(g * y[m]); V[m] = q * g * np.exp(g * y[m])
    Ui, Vi = 1.0 + 0j, q * g
    for i, (es, ey, d) in enumerate(layers[1:-1]):
        ky = np.sqrt(_ky2(pol, es, ey, k0, b) + 0j); q = _q(pol, es)
        m = (y >= tops[i]) & (y < tops[i + 1]); t = y[m] - tops[i]
        c, s = np.cos(ky * t), np.sin(ky * t)
        U[m] = c * Ui + s / (q * ky) * Vi; V[m] = -q * ky * s * Ui + c * Vi
        c, s = np.cos(ky * d), np.sin(ky * d)
        Ui, Vi = c * Ui + s / (q * ky) * Vi, -q * ky * s * Ui + c * Vi
    es, ey, _ = layers[-1]
    g = _gamma(pol, es, ey, k0, b); m = y >= tops[-1]
    U[m] = Ui * np.exp(-g * (y[m] - tops[-1])); V[m] = -_q(pol, es) * g * U[m]
    return U, V, tops
