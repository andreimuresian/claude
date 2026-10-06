"""
Inverse design of the bend line.

Free: signal width S, gap W, ground width Wg, each inside a range the user sets.
Fixed: gold thickness, conductivity, layer stack.

    find      (S, W, Wg) in the ranges
    such that |Zc(f_ref)| = Z_target                    (impedance matching)
    minimise  bend loss = alpha(f_ref) x L_b,  L_b = c tau / n_m(f_ref)

L_b is the bend length that gives the RF transit time tau through the bend
(tau = the bend optical delay, or the walk-off compensated delay: chosen by
the caller). Since tau does not depend on the geometry, the objective is
alpha / n_m: a slower line needs a shorter bend for the same delay.

Method: the line model at f_ref on a 3 x 3 x 3 grid over the ranges, full
quadratic response surfaces for |Zc|, n_m and alpha (checked against the grid
nodes), a dense search of the surfaces on the constraint |Zc| = Z_target, then
a polish of the best point with the line model itself (secant on the matching
variable), so the reported geometry, Z0, n_m and alpha are the model's, not the
surface's.
"""
from __future__ import annotations

import itertools
import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

import numpy as np

from .model import C0, F_REF_GHZ, BendGeometry, line_model

VARS = ("S_um", "W_um", "Wg_um")
LABELS = {"S_um": "signal S", "W_um": "gap W", "Wg_um": "ground Wg"}


@dataclass
class DesignResult:
    geometry: BendGeometry
    Z0: float                     # |Zc| at f_ref (ohm)
    n_m: float
    alpha_dB_cm: float
    L_b_mm: float                 # bend length for the RF delay tau
    loss_dB: float                # alpha x L_b at f_ref
    feasible: bool                # Z_target reached inside the ranges
    message: str
    Z_range: tuple = (np.nan, np.nan)          # |Zc| reachable in the ranges (from the grid)
    surface_check: dict = field(default_factory=dict)
    grid: list = field(default_factory=list)   # [(S, W, Wg, Z0, n_m, alpha), ...]


def _basis(x):
    """Full quadratic in 3 variables, x shape (..., 3) in [-1, 1]."""
    a, b, c = x[..., 0], x[..., 1], x[..., 2]
    one = np.ones_like(a)
    return np.stack([one, a, b, c, a * a, b * b, c * c, a * b, a * c, b * c], axis=-1)


def _evaluate(base: BendGeometry, xs, f_ref_GHz):
    g = base.with_(**dict(zip(VARS, map(float, xs))))
    r = line_model(g).at_ref(f_ref_GHz, dielectric=False)
    return r["Z0"], r["n_m"], r["alpha_dB_cm"]


def optimise(base: BendGeometry, ranges: dict, Z_target: float, tau_ps: float,
             f_ref_GHz: float = F_REF_GHZ, progress: Optional[Callable[[str, float], None]] = None,
             cancel: Optional[threading.Event] = None, z_tol: float = 0.01) -> DesignResult:
    """*ranges*: {"S_um": (lo, hi), "W_um": (lo, hi), "Wg_um": (lo, hi)} (um)."""
    lo = np.array([float(ranges[k][0]) for k in VARS])
    hi = np.array([float(ranges[k][1]) for k in VARS])
    if np.any(hi < lo) or np.any(lo <= 0):
        raise ValueError("each range needs 0 < min <= max")
    if not tau_ps > 0:
        raise ValueError(f"the RF delay through the bend must be positive (got {tau_ps:.3f} ps)")
    mid, half = (lo + hi) / 2, np.maximum((hi - lo) / 2, 1e-12)

    def to_x(u):
        return (np.asarray(u) - mid) / half

    def to_u(x):
        return mid + np.asarray(x) * half

    def say(msg, frac):
        if progress:
            progress(msg, frac)
        if cancel is not None and cancel.is_set():
            raise RuntimeError("cancelled")

    # 1. the line model on a 3 x 3 x 3 grid (fewer nodes along a fixed variable)
    levels = [np.array([-1.0, 0.0, 1.0]) if hi[i] > lo[i] else np.array([0.0]) for i in range(3)]
    nodes = np.array(list(itertools.product(*levels)))
    vals = []
    for k, x in enumerate(nodes):
        say(f"line model on the design grid: {k + 1}/{len(nodes)}", 0.8 * k / len(nodes))
        vals.append(_evaluate(base, to_u(x), f_ref_GHz))
    vals = np.array(vals)
    grid = [tuple(to_u(x)) + tuple(v) for x, v in zip(nodes, vals)]
    Zmin, Zmax = float(vals[:, 0].min()), float(vals[:, 0].max())

    # 2. response surfaces (least squares; exact interpolation on a full 3^3 grid
    #    is not possible with 10 terms, so the node residual is a real check)
    B = _basis(nodes)
    coef = {}
    resid = {}
    for j, name in enumerate(("Z0", "n_m", "alpha")):
        c, *_ = np.linalg.lstsq(B, vals[:, j], rcond=None)
        coef[name] = c
        resid[name] = float(np.max(np.abs(B @ c / vals[:, j] - 1)) * 100)

    def surf(name, x):
        return _basis(x) @ coef[name]

    # 3. dense search on |Zc| = Z_target: for each pair of the other two
    #    variables, solve the (quadratic) surface for the third
    say("searching the response surfaces", 0.82)
    cands = []
    g1 = np.linspace(-1, 1, 61)
    for j in range(3):                        # the variable solved for
        if hi[j] <= lo[j]:
            continue
        o = [i for i in range(3) if i != j]
        ga = g1 if hi[o[0]] > lo[o[0]] else np.array([0.0])
        gb = g1 if hi[o[1]] > lo[o[1]] else np.array([0.0])
        A_, B_ = np.meshgrid(ga, gb, indexing="ij")
        pts = np.zeros(A_.shape + (3,))
        pts[..., o[0]], pts[..., o[1]] = A_, B_
        # Z(xj) = q0 + q1 xj + q2 xj^2 along the line: sample 3 points and solve
        zs = []
        for v in (-1.0, 0.0, 1.0):
            p = pts.copy(); p[..., j] = v
            zs.append(surf("Z0", p))
        zm, z0, zp = zs
        q2 = (zp + zm) / 2 - z0
        q1 = (zp - zm) / 2
        q0 = z0 - Z_target
        for sgn in (1.0, -1.0):
            with np.errstate(invalid="ignore", divide="ignore"):
                disc = q1 * q1 - 4 * q2 * q0
                lin = np.abs(q2) < 1e-12 * (np.abs(q1) + 1e-30)
                root = np.where(lin, -q0 / np.where(q1 == 0, np.nan, q1),
                                (-q1 + sgn * np.sqrt(disc)) / (2 * np.where(lin, 1.0, q2)))
            ok = np.isfinite(root) & (np.abs(root) <= 1.0)
            if not ok.any():
                continue
            p = pts[ok].copy()
            p[:, j] = root[ok]
            obj = surf("alpha", p) / surf("n_m", p)
            k = int(np.argmin(obj))
            cands.append((float(obj[k]), p[k], j))
    feasible = bool(cands)
    if feasible:
        cands.sort(key=lambda c: c[0])
        _obj, x_best, j_solve = cands[0]
    else:
        # closest reachable impedance: corner/edge of the box nearest the target
        dense = np.array(list(itertools.product(*(g1 if hi[i] > lo[i] else [0.0] for i in range(3)))))
        zd = surf("Z0", dense)
        k = int(np.argmin(np.abs(zd - Z_target) + 1e-6 * surf("alpha", dense) / surf("n_m", dense)))
        x_best, j_solve = dense[k], 1

    # 4. polish with the line model: secant on the matching variable
    u = to_u(x_best)
    say("polishing with the line model", 0.88)
    Z, n, a = _evaluate(base, u, f_ref_GHz)
    if feasible:
        u_prev, Z_prev = None, None
        for it in range(8):
            if abs(Z - Z_target) <= z_tol:
                break
            if u_prev is None:
                du = 0.01 * half[j_solve] + 1e-3
                u_try = u.copy(); u_try[j_solve] = min(max(u[j_solve] + du, lo[j_solve]), hi[j_solve])
                if u_try[j_solve] == u[j_solve]:
                    u_try[j_solve] = u[j_solve] - du
                Z_try, _n, _a = _evaluate(base, u_try, f_ref_GHz)
                u_prev, Z_prev = u_try, Z_try
            slope = (Z - Z_prev) / (u[j_solve] - u_prev[j_solve])
            if slope == 0:
                break
            u_new = u.copy()
            u_new[j_solve] = min(max(u[j_solve] - (Z - Z_target) / slope, lo[j_solve]), hi[j_solve])
            u_prev, Z_prev = u.copy(), Z
            u = u_new
            say(f"polishing with the line model ({it + 1})", 0.88 + 0.01 * it)
            Z, n, a = _evaluate(base, u, f_ref_GHz)
    g = base.with_(**dict(zip(VARS, map(float, u))))
    full = line_model(g).at_ref(f_ref_GHz, dielectric=True)
    xb = to_x(u)
    check = {"node residual % (Z0, n_m, alpha)": (resid["Z0"], resid["n_m"], resid["alpha"]),
             "surface vs model at the result, %": (
                 float((surf("Z0", xb) / full["Z0"] - 1) * 100),
                 float((surf("n_m", xb) / full["n_m"] - 1) * 100),
                 float((surf("alpha", xb) / full["alpha_dB_cm"] - 1) * 100))}
    L_b_mm = C0 * tau_ps * 1e-12 / full["n_m"] * 1e3
    loss = full["alpha_dB_cm"] * L_b_mm / 10.0
    if feasible and abs(full["Z0"] - Z_target) <= 5 * z_tol:
        msg = (f"Z0 = {full['Z0']:.2f} ohm matched; bend loss {loss:.3f} dB at {f_ref_GHz:g} GHz "
               f"over {L_b_mm:.3f} mm")
    else:
        feasible = False
        msg = (f"Z0 = {Z_target:.2f} ohm is not reachable in these ranges (reachable "
               f"{Zmin:.1f}-{Zmax:.1f} ohm at the grid nodes); closest: {full['Z0']:.2f} ohm")
    say("done", 1.0)
    return DesignResult(geometry=g, Z0=full["Z0"], n_m=full["n_m"], alpha_dB_cm=full["alpha_dB_cm"],
                        L_b_mm=L_b_mm, loss_dB=loss, feasible=feasible, message=msg,
                        Z_range=(Zmin, Zmax), surface_check=check, grid=grid)
