"""Capacitance per cell -> the lumped reactive penalties dL and dC.

The T-stub is centred in the cell, so both z-faces are mirror planes of the
static problem and natural (Neumann) conditions there are exact.  Metal
volumes stay in the mesh and are pinned to a constant potential, which makes
their interior energy identically zero.
"""

import time
from dataclasses import dataclass

import meshio
import numpy as np
import pyamg
from skfem import (Basis, BilinearForm, ElementTetP0, ElementTetP1, Functional,
                   condense)
from skfem.helpers import dot, grad
from skfem.io.meshio import from_meshio

EPS0 = 8.8541878128e-12
C0 = 299792458.0

EPS_RF = {"ln": 28.0, "ox": 3.9, "si": 11.7, "air": 1.0,
          "signal": 1.0, "ground": 1.0}
EPS_VACUUM = {k: 1.0 for k in EPS_RF}


@BilinearForm
def _laplace(u, v, w):
    return w["eps"] * dot(grad(u), grad(v))


@Functional
def _energy(w):
    return w["eps"] * dot(grad(w["u"]), grad(w["u"]))


@dataclass
class Penalties:
    """Lumped penalties of one 200 um cell, and the baselines they came from."""
    dC: float      # F per cell
    dL: float      # H per cell
    C_unetched: float   # F/m
    L_unetched: float   # H/m
    C_etched: float     # F/m
    L_etched: float     # H/m
    seconds: float


def capacitance(mshfile, eps_map, pitch=200.0, tol=1e-10, verbose=False):
    """Capacitance per metre of a unit cell mesh (mesh in micrometres)."""
    mesh = from_meshio(meshio.read(mshfile))
    basis = Basis(mesh, ElementTetP1())
    basis0 = basis.with_element(ElementTetP0())

    eps = basis0.zeros() + 1.0
    for name, value in eps_map.items():
        if name in mesh.subdomains:
            eps[basis0.get_dofs(elements=name)] = value

    A = _laplace.assemble(basis, eps=basis0.interpolate(eps))
    u = basis.zeros()
    d_sig = basis.get_dofs(elements="signal")
    d_gnd = basis.get_dofs(elements="ground")
    u[d_sig] = 1.0
    D = np.unique(np.concatenate([d_sig.flatten(), d_gnd.flatten()]))

    Ac, bc, _, I = condense(A, basis.zeros(), x=u, D=D)
    ml = pyamg.smoothed_aggregation_solver(Ac.tocsr())
    u[I] = ml.solve(bc, tol=tol, accel="cg", maxiter=800)

    W = _energy.assemble(basis, u=basis.interpolate(u),
                         eps=basis0.interpolate(eps))
    if verbose:
        print(f"    dofs={basis.N}  C={EPS0 * W / pitch * 1e12:.4f} pF/m")
    return EPS0 * W / pitch


def penalties(etched_msh, unetched_msh, pitch=200.0):
    """dL and dC for one geometry, from four scalar solves."""
    t0 = time.time()
    C_e = capacitance(etched_msh, EPS_RF, pitch)
    Ca_e = capacitance(etched_msh, EPS_VACUUM, pitch)
    C_u = capacitance(unetched_msh, EPS_RF, pitch)
    Ca_u = capacitance(unetched_msh, EPS_VACUUM, pitch)

    L_e = 1.0 / (C0 ** 2 * Ca_e)
    L_u = 1.0 / (C0 ** 2 * Ca_u)
    cell_m = pitch * 1e-6
    return Penalties(dC=(C_e - C_u) * cell_m, dL=(L_e - L_u) * cell_m,
                     C_unetched=C_u, L_unetched=L_u,
                     C_etched=C_e, L_etched=L_e,
                     seconds=time.time() - t0)
