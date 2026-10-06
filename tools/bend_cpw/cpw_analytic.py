"""
Coplanar waveguide (CPW) model for the electrode bend: geometry and materials
in, Z0, n_m and alpha(f) out. No FEM mesh, no Touchstone. Use bend_cpw().

Capacitance (quasi-TEM):
  * air above: conformal map with finite grounds, C = 2 eps0 K(k)/K(k');
  * gaps between the sidewalls: a parallel plate each, eps0 t / W;
  * layers below: spectral-domain variational method (layered admittance by
    transmission-line recursion, LN anisotropy exact, conformal-map slot field
    as trial function), scaled by the finite-ground factor of the map;
  * the air-filled capacitance C_air (it sets L_ext = 1/(c^2 C_air)) is taken
    from the boundary-element solution of the real thick electrodes
    (bem_pec.py); the difference to the conformal C_air is a thickness error
    common to both C and C_air, so C is corrected by the same amount.

Conductor resistance (conductor_impedance):
  * DC: 1/(sigma S t) + 1/(2 sigma Wg t)  (signal + two grounds in parallel);
  * skin effect: the exact surface current of the thick electrodes, top,
    bottom AND sidewalls, from the boundary-element solution of the PEC
    problem (bem_pec.py), with two finite-skin-depth corrections:
      - receding wall (Wheeler): the current flows ~delta/2 inside the metal,
        so the surface current is taken on the electrodes shrunk by delta/2;
      - corners: the PEC current is singular there (J/I = K r^-1/3); the real
        current spreads over a skin depth, which removes c K^2 delta^(1/3) per
        corner, c = 0.70 for a right-angle corner (corner_constant.py: from an
        isolated square bar, not from the CPW validation set);
    R = sqrt(R_dc^2 + R_hf^2); L_int = R_hf / omega in the skin-effect regime,
    blended to the exact uniform-current L_dc towards DC.
  * G_ghione() (thin-strip closed form, Ghione 1993) is kept for comparison.

Dielectric loss: G = sum_i sigma_i dC/d(eps0 eps_i) + omega tan(delta) terms,
alpha_d = G Z0 / 2.
"""
import numpy as np
from scipy.special import ellipk

C0 = 299792458.0
EPS0 = 8.8541878128e-12
MU0 = 4e-7 * np.pi
DB_PER_NEPER = 20.0 * np.log10(np.e)


def KK(k):
    """K(k)/K(k'), k the modulus (scipy's ellipk takes m = k^2)."""
    k = float(k)
    return float(ellipk(k * k) / ellipk(1.0 - k * k))


def k_air(a, b, c):
    if c is None or not np.isfinite(c):
        return a / b
    return (a / b) * np.sqrt((1 - b * b / (c * c)) / (1 - a * a / (c * c)))


def k_layer(a, b, c, H):
    """Modulus of a layer of depth H below the metal (magnetic wall at its bottom)."""
    x = np.pi / (2.0 * H)
    if x * b > 300:                     # very thin layer: sinh ratio underflows
        return None
    sa, sb = np.sinh(x * a), np.sinh(x * b)
    k = sa / sb
    if c is not None and np.isfinite(c):
        sc = np.sinh(x * c)
        k *= np.sqrt((1 - sb * sb / (sc * sc)) / (1 - sa * sa / (sc * sc)))
    return k


def capacitance(S, W, Wg, t, layers, eps_gap=1.0, eps_above=1.0):
    """C per unit length (F/m) of the CPW. *layers*: list of (thickness_m,
    eps_h, eps_v) from the metal downward; the last may be np.inf. Returns
    (C, parts) where parts lists each term (for filling factors)."""
    a, b = S / 2.0, S / 2.0 + W
    c = b + Wg if Wg is not None else None
    k0 = k_air(a, b, c)
    C_up = 2 * EPS0 * eps_above * KK(k0)                # upper half-space
    C_down_air = 2 * EPS0 * KK(k0)                      # lower half-space, all air
    C_wall = 2 * EPS0 * eps_gap * t / W                 # two gaps, sidewall parallel plates
    iso = []
    for h, eh, ev in layers:
        eps = np.sqrt(eh * ev)
        hh = h * np.sqrt(eh / ev) if np.isfinite(h) else np.inf
        iso.append((hh, eps))
    parts = []
    C_lay = 0.0
    H = 0.0
    for i, (hh, eps) in enumerate(iso):
        H = H + hh
        eps_next = iso[i + 1][1] if i + 1 < len(iso) else 1.0
        kk = k0 if not np.isfinite(H) else k_layer(a, b, c, H)
        q = 0.0 if kk is None else 2 * EPS0 * KK(kk)
        C_lay += (eps - eps_next) * q
        parts.append(q)
    C = C_up + C_down_air + C_wall + C_lay
    return C, dict(C_up=C_up, C_down_air=C_down_air, C_wall=C_wall, C_layers=C_lay, q=parts, iso=iso)


def cpw(f_Hz, S, W, Wg, t, layers, sigma_metal=4.56e7, layer_sigma=None, layer_tand=None,
        thin_metal_correction=False):
    """Z0 (ohm), n_m, alpha (dB/cm) and its conductor / dielectric parts at f_Hz
    (scalar or array). Lengths in metres."""
    f = np.atleast_1d(np.asarray(f_Hz, float))
    C_eps, parts = capacitance(S, W, Wg, t, layers)
    air_layers = [(h, 1.0, 1.0) for h, _eh, _ev in layers]
    C_air, _ = capacitance(S, W, Wg, t, air_layers)
    L_ext = 1.0 / (C0 ** 2 * C_air)

    # Wheeler: every surface recedes by n
    def L_of(n):
        Ca, _ = capacitance(S - 2 * n, W + 2 * n, (Wg - 2 * n) if Wg is not None else None,
                            t - 2 * n, air_layers)
        return 1.0 / (C0 ** 2 * Ca)
    dn = 1e-3 * min(W, t)
    dL_dn = (L_of(dn) - L_of(-dn)) / (2 * dn)

    w = 2 * np.pi * f
    delta = np.sqrt(2.0 / (w * MU0 * sigma_metal))
    Rs = 1.0 / (sigma_metal * delta)
    if thin_metal_correction:
        # field on both faces of a metal of thickness t: each face sees
        # Zs coth((1+j) t / (2 delta)); the DC limit is the sheet resistance 1/(sigma t)
        g = (1 + 1j) * t / (2 * delta)
        Zs = (1 + 1j) * Rs / np.tanh(g)
    else:
        Zs = (1 + 1j) * Rs
    Zp = Zs * dL_dn / MU0                    # series impedance from the conductors, ohm/m
    R = Zp.real
    L_int = Zp.imag / w
    L = L_ext + L_int
    n_m = C0 * np.sqrt(L * C_eps)
    Z0 = np.sqrt(L / C_eps)

    # dielectric conductance: G = sum sigma_i dC/d(eps_abs_i) (+ omega tan d terms)
    G = np.zeros_like(f)
    nl = len(layers)
    for i in range(nl):
        sig = 0.0 if layer_sigma is None else float(layer_sigma[i])
        tdl = 0.0 if layer_tand is None else float(layer_tand[i])
        if sig == 0.0 and tdl == 0.0:
            continue
        h, eh, ev = layers[i]
        d = 1e-6
        lay_p = list(layers)
        lay_p[i] = (h, eh * (1 + d), ev * (1 + d))
        Cp, _ = capacitance(S, W, Wg, t, lay_p)
        dC_deps = (Cp - C_eps) / (d * np.sqrt(eh * ev))       # dC/d(eps_r of layer i), F/m
        G = G + (sig / EPS0 + w * tdl * np.sqrt(eh * ev)) * dC_deps
    a_c = R / (2 * Z0)
    a_d = G * Z0 / 2
    out = dict(f_GHz=f / 1e9, Z0=Z0, n_m=n_m, alpha_dB_cm=DB_PER_NEPER * (a_c + a_d) / 100,
               alpha_c_dB_cm=DB_PER_NEPER * a_c / 100, alpha_d_dB_cm=DB_PER_NEPER * a_d / 100,
               R_per_m=R, L_ext=L_ext, L_int=L_int, C_eps=C_eps, C_air=C_air,
               n_qs=C0 * np.sqrt(L_ext * C_eps), Z_qs=np.sqrt(L_ext / C_eps), parts=parts)
    return out


UM = 1e-6
BEND_LAYERS = [(3.6 * UM, 3.9, 3.9), (0.275 * UM, 28.0, 44.0), (4.7 * UM, 3.9, 3.9), (550 * UM, 11.7, 11.7)]
BEND_SIGMA = [1e-13, 1e-3, 1e-13, 1e-12]


def bend(f_Hz, S=35 * UM, W=4.15 * UM, Wg=50 * UM, t=2 * UM, layers=None, **kw):
    return cpw(f_Hz, S, W, Wg, t, layers or BEND_LAYERS, layer_sigma=BEND_SIGMA, **kw)


if __name__ == "__main__":
    r = bend(60e9)
    print({k: (np.round(v, 5) if not isinstance(v, dict) else "") for k, v in r.items()})


# ---------------------------------------------------------------------------
# Lower half-space by the spectral-domain variational method
# ---------------------------------------------------------------------------
def _slot_trial(a, b, n=600):
    """Gauss-Chebyshev nodes over the slot (a, b) for the conformal-mapping trial
    field E(x) = A / sqrt((x^2 - a^2)(b^2 - x^2)), normalised to 1 V across the
    slot. Returns (x_nodes, weights) such that int_a^b E(x) g(x) dx ~ sum w g(x)."""
    th = (np.arange(n) + 0.5) * np.pi / n
    x = (a + b) / 2 + (b - a) / 2 * np.cos(th)
    wgt = (np.pi / n) / np.sqrt((x + a) * (x + b))
    return x, wgt / wgt.sum()


def layered_admittance(beta, layers, bottom_eps=None):
    """Spectral 'admittance' D_y / (eps0 phi) looking DOWN into the layer stack
    from the metal plane: TL recursion with Y_i = sqrt(eps_h eps_v) |beta| and
    electrical length sqrt(eps_h/eps_v) |beta| h. The last layer may be infinite."""
    bt = np.abs(beta)
    Y = None
    for h, eh, ev in reversed(layers):
        Yi = np.sqrt(eh * ev) * bt
        if Y is None and not np.isfinite(h):
            Y = Yi
            continue
        if Y is None:                         # finite bottom layer on air
            Y = 1.0 * bt
        th = np.tanh(np.sqrt(eh / ev) * bt * h)
        Y = Yi * (Y + Yi * th) / (Yi + Y * th)
    return Y


def C_lower_spectral(S, W, layers, n_beta=6000):
    """Capacitance (F/m) of the half-space below a zero-thickness CPW with
    infinite grounds, signal at 1 V: C = (4 eps0 / pi) int_0^inf Y(b) S(b)^2 / b^2 db,
    S(b) = int_slot E(x) sin(b x) dx. Variational in E (an upper bound)."""
    a, b = S / 2.0, S / 2.0 + W
    x, wq = _slot_trial(a, b)
    beta = np.logspace(np.log10(1e-4 / b), np.log10(2e3 / W), n_beta)
    Sb = np.array([np.dot(wq, np.sin(bb * x)) for bb in beta])
    Y = layered_admittance(beta, layers)
    integrand = Y * Sb ** 2 / beta ** 2
    return 4 * EPS0 / np.pi * np.trapezoid(integrand * beta, np.log(beta))


def capacitance_sd(S, W, Wg, t, layers, eps_gap=1.0, eps_above=1.0):
    """C (F/m): air above (conformal, finite grounds) + sidewall parallel plates
    + layered half-space below (spectral variational, infinite grounds, scaled
    by the finite-ground factor of the conformal map)."""
    a, b = S / 2.0, S / 2.0 + W
    c = b + Wg if Wg is not None else None
    k_fin, k_inf = k_air(a, b, c), a / b
    fg = KK(k_fin) / KK(k_inf)
    C_up = 2 * EPS0 * eps_above * KK(k_fin)
    C_wall = 2 * EPS0 * eps_gap * t / W
    C_low = C_lower_spectral(S, W, layers) * fg
    return C_up + C_wall + C_low, dict(C_up=C_up, C_wall=C_wall, C_low=C_low, fg=fg)


# ---------------------------------------------------------------------------
# Final model
# ---------------------------------------------------------------------------
def G_ghione(S, W, t):
    """Geometric factor of the CPW conductor resistance, R = Rs * G (1/m):
    Ghione's closed form for coplanar lines (current crowding at the strip
    edges, cut off at a stopping distance set by the metal thickness),
    written for R rather than alpha so that its thin-strip Z0 drops out:
        alpha = Rs sqrt(eps_eff) / (480 pi K K' (1 - k^2)) * B,
        B = (1/a)[pi + ln(8 pi a (1-k)/(t (1+k)))] + (1/b)[pi + ln(8 pi b (1-k)/(t (1+k)))]
    with Z0 = 30 pi K'/(K sqrt(eps_eff)) and R = 2 Z0 alpha. Infinite grounds."""
    a, b = S / 2.0, S / 2.0 + W
    k = a / b
    K, Kp = ellipk(k * k), ellipk(1 - k * k)
    B = (1 / a) * (np.pi + np.log(8 * np.pi * a * (1 - k) / (t * (1 + k)))) + \
        (1 / b) * (np.pi + np.log(8 * np.pi * b * (1 - k) / (t * (1 + k))))
    return 2 * 30 * np.pi * Kp / K / (480 * np.pi * K * Kp * (1 - k * k)) * B


C_CORNER = 0.70      # right-angle corner constant, from corner_constant.py


def conductor_impedance(f_Hz, S, W, Wg, t, sigma_metal=4.56e7, c_corner=C_CORNER, L_ext=None):
    """R (ohm/m) and L_int (H/m) of a CPW with thick electrodes, from DC to the
    strong skin effect. The boundary-element solve is done at a few receding
    depths and interpolated, so many frequencies cost no more than one."""
    import bem_pec
    f = np.atleast_1d(np.asarray(f_Hz, float))
    w = 2 * np.pi * f
    delta = np.sqrt(2.0 / (w * MU0 * sigma_metal))
    Rs = 1.0 / (sigma_metal * delta)
    d_eff = np.minimum(delta, 0.45 * t)                 # the receded metal keeps a core
    dg = np.unique(np.geomspace(d_eff.min(), d_eff.max(), 7 if d_eff.max() > d_eff.min() * 1.01 else 1))
    Gs, Ks = [], []
    for d in dg:
        b = bem_pec.solve(S - d, W + d, Wg - d, t - d)
        Gs.append(b["G_pec"]); Ks.append(4 * sum(k * k for k in b["K_corners"]))
    G = np.interp(np.log(d_eff), np.log(dg), Gs)
    Ksum = np.interp(np.log(d_eff), np.log(dg), Ks)
    R_dc = 1.0 / (sigma_metal * S * t) + 0.5 / (sigma_metal * Wg * t)
    R_hf = Rs * (G - c_corner * Ksum * delta ** (1.0 / 3.0))
    R = np.sqrt(R_dc ** 2 + R_hf ** 2)
    # internal inductance: R_hf / w in the skin-effect regime; towards DC the
    # current spreads uniformly over each electrode and L tends to L_dc (exact
    # for uniform current), so the excess over L_ext is blended as
    #   L_int = (1/dL_dc^2 + 1/(R_hf/w)^2)^(-1/2),  dL_dc = L_dc - L_ext
    L_hf = R_hf / w
    if L_ext is not None:
        dL = max(inductance_dc(S, W, Wg, t) - L_ext, 1e-30)
        L_int = 1.0 / np.sqrt(1.0 / dL ** 2 + 1.0 / L_hf ** 2)
    else:
        L_int = L_hf
    return R, L_int, dict(R_dc=R_dc, R_hf=R_hf, G=G, Ksum=Ksum)


def inductance_dc(S, W, Wg, t):
    """Loop inductance (H/m) with uniform current in each electrode (signal +1,
    grounds -1/2 each), from the exact mean log-distance between rectangles."""
    from peec2d import mean_log
    xs, xgi = S / 2, S / 2 + W
    rects = [(-xs, xs, 0.0, t), (xgi, xgi + Wg, 0.0, t), (-xgi - Wg, -xgi, 0.0, t)]
    cur = (1.0, -0.5, -0.5)
    return sum(cur[a] * cur[b] * (-MU0 / (2 * np.pi)) * float(mean_log(rects[a], rects[b]))
               for a in range(3) for b in range(3))


def bend_cpw(f_Hz, S, W, Wg, t, layers, sigma_metal=4.56e7, layer_sigma=None, layer_tand=None,
             conductor="thick", capacitance_model="galerkin"):
    """Z0, n_m, alpha(f) of a CPW (signal S, gaps W, grounds Wg, metal t; SI units)
    on the layer stack *layers* [(h, eps_h, eps_v), ... from the metal down],
    air above and in the gaps. Closed form + one 1D spectral integral."""
    f = np.atleast_1d(np.asarray(f_Hz, float))
    w = 2 * np.pi * f
    air = [(h, 1.0, 1.0) for h, _eh, _ev in layers]
    if conductor == "thick" and capacitance_model == "galerkin":
        import cpw_galerkin
        C_eps, C_air = cpw_galerkin.capacitance(S, W, Wg, t, layers)

        def C_of(lay):
            return cpw_galerkin.capacitance(S, W, Wg, t, lay, C_air_thick=C_air)[0]
    else:
        C_eps, parts = capacitance_sd(S, W, Wg, t, layers)
        C_air, _ = capacitance_sd(S, W, Wg, t, air)

        def C_of(lay):
            return capacitance_sd(S, W, Wg, t, lay)[0]
        if conductor == "thick":
            import bem_pec
            C_air_bem = bem_pec.solve(S, W, Wg, t)["C_air"]
            C_eps = C_eps + (C_air_bem - C_air)          # same thickness error in both
            C_air = C_air_bem
    L_ext = 1.0 / (C0 ** 2 * C_air)
    if conductor == "thick":
        R, L_int, cinfo = conductor_impedance(f, S, W, Wg, t, sigma_metal, L_ext=L_ext)
        R_dc, G = cinfo["R_dc"], cinfo["G"]
    else:
        delta = np.sqrt(2.0 / (w * MU0 * sigma_metal))
        Rs = 1.0 / (sigma_metal * delta)
        G = G_ghione(S, W, t)
        R_dc = 1.0 / (sigma_metal * S * t) + 0.5 / (sigma_metal * Wg * t)
        R_hf = Rs * G
        R = np.sqrt(R_dc ** 2 + R_hf ** 2)
        f_x = (R_dc / G) ** 2 * sigma_metal / (np.pi * MU0)
        L_int = np.where(f >= f_x, R_hf / w, R_dc / (2 * np.pi * f_x))
    L = L_ext + L_int
    # dielectric conductance from the capacitance's sensitivity to each layer
    G_d = np.zeros_like(f)
    for i, (h, eh, ev) in enumerate(layers):
        sg = 0.0 if layer_sigma is None else float(layer_sigma[i])
        td = 0.0 if layer_tand is None else float(layer_tand[i])
        if sg == 0.0 and td == 0.0:
            continue
        lay = list(layers)
        lay[i] = (h, eh * 1.001, ev * 1.001)
        dC = (C_of(lay) - C_eps) / (0.001 * np.sqrt(eh * ev))
        G_d = G_d + (sg / EPS0 + w * td * np.sqrt(eh * ev)) * dC
    # exact line constants (R is not small against w L below ~1 GHz)
    gamma = np.sqrt((R + 1j * w * L) * (G_d + 1j * w * C_eps))
    Zc = np.sqrt((R + 1j * w * L) / (G_d + 1j * w * C_eps))
    Z0 = np.abs(Zc)
    n_m = gamma.imag / w * C0
    # split of alpha into conductor and dielectric parts (low-loss expressions,
    # scaled so that they add up to Re(gamma))
    a_c0, a_d0 = R / (2 * Z0), G_d * Z0 / 2
    a_c = gamma.real * a_c0 / (a_c0 + a_d0)
    a_d = gamma.real * a_d0 / (a_c0 + a_d0)
    return dict(f_GHz=f / 1e9, Z0=Z0, Zc=Zc, n_m=n_m, alpha_dB_cm=DB_PER_NEPER * gamma.real / 100,
                alpha_c_dB_cm=DB_PER_NEPER * a_c / 100, alpha_d_dB_cm=DB_PER_NEPER * a_d / 100,
                R=R, L=L, C=C_eps, C_air=C_air, L_ext=L_ext, R_dc=R_dc, G_geo=G)
