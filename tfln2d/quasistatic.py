"""Quasi-static (L, C) extraction of the CPW cross-section.

For a quasi-TEM line the kinematics follow from two electrostatic solves:

    C       from the real dielectric stack
    C_air   from the same geometry with every dielectric replaced by vacuum
    L     = 1 / (c0^2 C_air)
    n_m   = sqrt(C / C_air)
    Z0    = 1 / (c0 sqrt(C C_air))

These are exactly the distributed parameters that the composite predictor
superposes the MoM lumped penalties (dL, dC) onto.
"""

from dataclasses import dataclass

import numpy as np
from femwell.coulomb import solve_coulomb
from skfem import (Basis, ElementTriP0, ElementTriP1, Functional,
                   InteriorFacetBasis)
from skfem.helpers import dot, grad

from .materials import C0, EPS0, LN_RF_EXTRAORDINARY, SI_RF_EPS, SIO2_RF
from .materials import surface_resistance
from .mesh import build_mesh, metal_facets


@dataclass
class QuasiStatic:
    """Result of one cross-section extraction."""
    C: float           # F/m
    C_air: float       # F/m
    L: float           # H/m
    n_m: float
    Z0: float          # ohm
    R: float = float("nan")      # ohm/m, conductor series resistance
    alpha_c: float = float("nan")  # dB/cm, conductor attenuation


@Functional
def _energy(w):
    return w["eps"] * dot(grad(w["u"]), grad(w["u"]))


@Functional
def _js_squared(w):
    # rho_s = eps0 |dV/dn| ; mesh is in um so the gradient carries 1e6 V/m
    return (EPS0 * np.abs(dot(w["gu"], w.n)) * 1e6 / w["C_air"]) ** 2


def _rf_permittivity(cs, eps_ln=LN_RF_EXTRAORDINARY):
    """Relative permittivity per named region, at RF."""
    eps = {"slab": eps_ln, "oxide": SIO2_RF, "silicon": SI_RF_EPS, "air": 1.0}
    for name in cs.rib_names():
        eps[name] = eps_ln
    for i in range(len(cs.rib_centres())):
        eps[f"cap_{i}"] = SIO2_RF
    # metal interiors are bounded by Dirichlet facets; their filling is inert
    for metal in cs.metal_names():
        eps[metal] = 1.0
    return eps


def _solve(mesh, cs, eps_map):
    basis0 = Basis(mesh, ElementTriP0())
    eps = basis0.zeros() + 1.0
    for name, value in eps_map.items():
        if name in mesh.subdomains:
            eps[basis0.get_dofs(elements=name)] = value

    facets = metal_facets(cs, mesh)
    fixed = {}
    for name in facets["signal"]:
        fixed[name] = 1.0
    for metal in ("ground_l", "ground_r"):
        for name in facets[metal]:
            fixed[name] = 0.0

    basis_u, u = solve_coulomb(basis0, eps, fixed)
    cap = EPS0 * _energy.assemble(basis_u, u=basis_u.interpolate(u),
                                  eps=basis0.interpolate(eps))
    return basis_u, u, cap


def _conductor_loss(mesh, cs, u_air, C_air, Z0, f_hz):
    """Perturbative surface-resistance loss from the air-filled solution.

    NOTE: for ideally sharp electrode corners this integral does not converge
    under mesh refinement (the edge current density is singular).  Use it for
    trends; use the full-wave impedance-boundary solver for absolute values.
    """
    metal_elements = np.unique(np.concatenate(
        [mesh.subdomains[m] for m in cs.metal_names()]))
    facets = metal_facets(cs, mesh)

    total = 0.0
    for names in facets.values():
        for name in names:
            for side in (0, 1):
                fb = InteriorFacetBasis(mesh, ElementTriP1(),
                                        facets=mesh.boundaries[name], side=side)
                if np.isin(fb.tind, metal_elements).all():
                    continue  # this is the metal side; we want the dielectric
                total += _js_squared.assemble(
                    fb, gu=fb.interpolate(u_air).grad, C_air=C_air) * 1e-6

    R = surface_resistance(f_hz) * total
    alpha_np_m = R / (2 * Z0)
    return R, alpha_np_m * 8.686 / 100.0


def extract(cs, resolution=0.25, f_hz=60e9, eps_ln=LN_RF_EXTRAORDINARY,
            with_loss=True, mesh=None):
    """Full quasi-static extraction for one cross-section."""
    if mesh is None:
        mesh = build_mesh(cs, resolution=resolution)

    eps_map = _rf_permittivity(cs, eps_ln=eps_ln)
    _, _, C = _solve(mesh, cs, eps_map)
    _, u_air, C_air = _solve(mesh, cs, {k: 1.0 for k in eps_map})

    L = 1.0 / (C0 ** 2 * C_air)
    n_m = np.sqrt(C / C_air)
    Z0 = 1.0 / (C0 * np.sqrt(C * C_air))

    result = QuasiStatic(C=C, C_air=C_air, L=L, n_m=n_m, Z0=Z0)
    if with_loss:
        result.R, result.alpha_c = _conductor_loss(
            mesh, cs, u_air, C_air, Z0, f_hz)
    return result
