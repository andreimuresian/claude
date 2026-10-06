"""
(Production copy of tools/bend_cpw/cpw_galerkin.py.)

Capacitance of a CPW on a layered substrate by the spectral-domain Galerkin
method (charge basis on the strips), plus the thickness of the electrodes from
the boundary-element solution in air.

Zero-thickness strips at the interface y = 0: signal (-a, a), grounds (b, c)
and (-c, -b), FINITE grounds. Unknown: the charge density, expanded on each
strip in Chebyshev polynomials with the 1/sqrt edge singularity,

    signal:       T_2n(x/a) / sqrt(1 - (x/a)^2)                    (even in x)
    ground pair:  T_m(u) / sqrt(1 - u^2) on (b, c), mirrored on (-c, -b),
                  u = (x - x0)/w,  x0 = (b + c)/2,  w = (c - b)/2.

Potential of a charge sheet over the layered half-space below and air above,
in the spectral domain: phi(beta) = rho(beta) / (eps0 (|beta| + Y(beta))),
Y from the transmission-line recursion of the layers (anisotropy exact). The
kernel is split into the uniform-medium part 1/(eps0 eps_s |beta|), eps_s =
1 + eps of the first layer, whose matrix is evaluated in space (closed form on
the same strip, Gauss-Chebyshev between strips), and the remainder, which decays
as exp(-2 |beta| h1) and is integrated in beta. The charge is neutral (TEM),
signal at 1 V, grounds at 0 V.

Electrode thickness: C = C_thin(layers) + [C_air,thick(BEM) - C_thin(air)],
i.e. the thickness adds what it adds in air (the gaps are air-filled).
"""
import numpy as np
from scipy.special import jv

EPS0 = 8.8541878128e-12


def _strips(S, W, Wg):
    a = S / 2.0
    b = a + W
    c = b + Wg
    return a, (b + c) / 2.0, (c - b) / 2.0


def _uniform_matrix(S, W, Wg, ns, ng, m_quad=400):
    """Galerkin matrix of -ln|x - x'| (no 1/(pi eps0 eps_s) factor)."""
    a, x0, w = _strips(S, W, Wg)
    N = ns + ng
    P = np.zeros((N, N))
    # same strip: int ln|u - v| T_n(v)/sqrt(1-v^2) dv = -pi ln2 (n=0), -(pi/n) T_n(u) (n>=1)
    def self_block(width, orders):
        B = np.zeros((len(orders), len(orders)))
        for i, m in enumerate(orders):
            for j, n in enumerate(orders):
                if m != n:
                    continue
                if n == 0:
                    B[i, j] = -width ** 2 * np.pi ** 2 * (np.log(width) - np.log(2.0))
                else:
                    B[i, j] = width ** 2 * np.pi ** 2 / (2.0 * n)
        return B                                    # this is the matrix of -ln|x-x'|
    so = [2 * n for n in range(ns)]
    go = list(range(ng))
    P[:ns, :ns] = self_block(a, so)
    # Gauss-Chebyshev nodes: int f(u)/sqrt(1-u^2) du ~ (pi/M) sum f(u_k)
    th = (np.arange(m_quad) + 0.5) * np.pi / m_quad
    u = np.cos(th)
    Ts = np.array([np.cos(n * th) for n in so])                 # T_n(cos th) = cos(n th)
    Tg = np.array([np.cos(n * th) for n in go])
    xs = a * u
    xg = x0 + w * u
    ws, wg = a * np.pi / m_quad, w * np.pi / m_quad
    # signal - ground pair (pair = right + mirrored left; the signal is even, so 2 x right)
    Ksr = -np.log(np.abs(xs[:, None] - xg[None, :]))
    P[:ns, ns:] = 2 * ws * wg * Ts @ Ksr @ Tg.T
    P[ns:, :ns] = P[:ns, ns:].T
    # pair - pair: 2 (right-right + right-left)
    Krl = -np.log(np.abs(xg[:, None] + xg[None, :]))
    # left strip basis: T_m(u') with u' = (-x - x0)/w, i.e. the mirror image; at
    # x = -(x0 + w u) its value is T_m(u), so the same node values apply
    P[ns:, ns:] = 2 * self_block(w, go) + 2 * wg * wg * Tg @ Krl @ Tg.T
    return P


def _spectra(beta, S, W, Wg, ns, ng):
    a, x0, w = _strips(S, W, Wg)
    F = [np.pi * a * (-1) ** n * jv(2 * n, beta * a) for n in range(ns)]
    F += [2 * np.pi * w * jv(m, beta * w) * np.cos(beta * x0 + m * np.pi / 2) for m in range(ng)]
    return np.array(F)


def layered_Y(beta, layers, below="air"):
    """D_y/(eps0 phi) looking down from y = 0 into [(h, eps_h, eps_v), ...];
    below the last layer: air (below='air') or a magnetic wall ('open')."""
    bt = np.abs(beta)
    Y = bt.copy() if below == "air" else np.zeros_like(bt)
    for h, eh, ev in reversed(layers):
        Yi = np.sqrt(eh * ev) * bt
        if not np.isfinite(h):
            Y = Yi
            continue
        th = np.tanh(np.sqrt(eh / ev) * bt * h)
        Y = Yi * (Y + Yi * th) / (Yi + Y * th)
    return Y


def c_thin(S, W, Wg, layers, ns=6, ng=8, below="air", n_beta=4000):
    """C (F/m) of the zero-thickness CPW at the top of *layers*, air above."""
    h1, eh1, ev1 = layers[0]
    eps_s = 1.0 + np.sqrt(eh1 * ev1)
    P = _uniform_matrix(S, W, Wg, ns, ng) / (np.pi * EPS0 * eps_s)
    # remainder of the kernel: 1/(eps0(|b| + Y)) - 1/(eps0 eps_s |b|); it decays
    # as exp(-2 b h1 sqrt(eh/ev)) and has a 1/b tail at b -> 0 that only acts on
    # the net charge (zero), so a small lower cut-off is harmless
    hz = h1 * np.sqrt(eh1 / ev1)
    beta = np.geomspace(1e-3 / (Wg + S + W), 40.0 / hz, n_beta)
    dG = 1.0 / (EPS0 * (beta + layered_Y(beta, layers, below))) - 1.0 / (EPS0 * eps_s * beta)
    F = _spectra(beta, S, W, Wg, ns, ng)
    wq = np.gradient(np.log(beta)) * beta          # d beta on the log grid
    P += (F * (dG * wq)) @ F.T / np.pi
    # neutral charge, signal 1 V, grounds 0 V, common offset K:
    #   P c - K q = v,  q^T c = 0
    N = ns + ng
    q = np.zeros(N)
    a, x0, w = _strips(S, W, Wg)
    q[0], q[ns] = np.pi * a, 2 * np.pi * w
    v = np.zeros(N)
    v[:ns] = q[:ns]
    A = np.zeros((N + 1, N + 1))
    A[:N, :N], A[:N, N], A[N, :N] = P, -q, q
    sol = np.linalg.solve(A, np.concatenate([v, [0.0]]))
    return float(q[:ns] @ sol[:ns])


def capacitance(S, W, Wg, t, layers, C_air_thick=None, **kw):
    """(C_eps, C_air) of the thick CPW: thin-strip Galerkin on the layers, plus the
    thickness increment from the BEM air solution."""
    if C_air_thick is None:
        from .bem import solve
        C_air_thick = solve(S, W, Wg, t)["C_air"]
    air = [(h, 1.0, 1.0) for h, _, _ in layers]
    Ct = c_thin(S, W, Wg, layers, **kw)
    Ca = c_thin(S, W, Wg, air, **kw)
    return Ct + C_air_thick - Ca, C_air_thick
