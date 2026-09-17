"""Full-wave 2D mode analysis of the cross-section (femwell / scikit-fem).

This is the direct analogue of the COMSOL `emw` Mode Analysis study: it solves
the vector wave equation on the cross-section and returns complex effective
indices.  It is used for the RF baseline attenuation and, at optical
frequencies, for n_eff / n_g / alpha_opt.

LIMITATION (see README): femwell's `compute_modes` takes a *scalar* relative
permittivity per element, so lithium niobate is currently entered as an
isotropic stand-in.  Anisotropic support requires a tensor-valued weak form.
"""

import numpy as np
from femwell.maxwell.waveguide import compute_modes
from skfem import Basis, ElementTriP0

from .materials import (C0, LN_RF_EXTRAORDINARY, SIO2_RF, gold_epsilon,
                        silicon_epsilon)
from .mesh import build_mesh


def rf_permittivity(cs, mesh, f_hz=60e9, eps_ln=LN_RF_EXTRAORDINARY):
    """Complex relative permittivity per element at RF."""
    basis0 = Basis(mesh, ElementTriP0())
    eps = basis0.zeros(dtype=complex) + 1.0

    values = {"slab": eps_ln, "oxide": SIO2_RF,
              "silicon": silicon_epsilon(f_hz), "air": 1.0}
    for name in cs.rib_names():
        values[name] = eps_ln
    for i in range(len(cs.rib_centres())):
        values[f"cap_{i}"] = SIO2_RF
    for metal in cs.metal_names():
        values[metal] = gold_epsilon(f_hz)

    for name, value in values.items():
        if name in mesh.subdomains:
            eps[basis0.get_dofs(elements=name)] = value
    return basis0, eps


def rf_modes(cs, f_hz=60e9, num_modes=8, n_guess=2.0, resolution=0.5,
             mesh=None, eps_ln=LN_RF_EXTRAORDINARY):
    """Compute RF eigenmodes of the cross-section."""
    if mesh is None:
        mesh = build_mesh(cs, resolution=resolution)
    basis0, eps = rf_permittivity(cs, mesh, f_hz=f_hz, eps_ln=eps_ln)
    wavelength_um = C0 / f_hz * 1e6
    return mesh, compute_modes(basis0, eps, wavelength=wavelength_um,
                               num_modes=num_modes, order=1, n_guess=n_guess)


def attenuation_db_per_cm(n_eff, f_hz):
    """alpha = 20 log10(e) * (2 pi f / c) * |Im(n_eff)|, in dB/cm."""
    return 20 * np.log10(np.e) * (2 * np.pi * f_hz / C0) * abs(n_eff.imag) / 100


def pick_quasi_tem(modes, f_hz, n_m_reference, tol=0.25):
    """Select the fundamental quasi-TEM mode.

    The COMSOL pipeline filtered 40 eigenmodes with an impedance bound, a
    current-symmetry sieve and a TEM-purity deduplication.  Here we use the
    quasi-static n_m as the discriminator, which is cheap and unambiguous as
    long as the quasi-static solve is trustworthy.
    """
    best, best_err = None, np.inf
    for mode in modes:
        err = abs(mode.n_eff.real - n_m_reference)
        if err < best_err:
            best, best_err = mode, err
    if best_err > tol * n_m_reference:
        return None
    return best
