# %% [2] Optical Eigensolver (N1 x P1 Elements)
import scipy.constants
from skfem import ElementTriN1, ElementTriP0, ElementTriP1, BilinearForm, solve, condense
from skfem.helpers import curl, dot, grad
from skfem.utils import solver_eigen_scipy
from femwell.maxwell.waveguide import Mode, Modes, calculate_hfield, calculate_overlap


def compute_modes_anisotropic(
    basis_epsilon_r,
    eps_xx,
    eps_yy,
    eps_zz,
    wavelength,
    num_modes=8,
    n_guess=1.8755,
):
    c0 = scipy.constants.speed_of_light
    k0_val = 2.0 * np.pi / wavelength
    element = ElementTriN1() * ElementTriP1()
    basis = basis_epsilon_r.with_element(element)
    basis_eps = basis.with_element(basis_epsilon_r.elem)

    @BilinearForm(dtype=complex)
    def aform(e_t, e_z, v_t, v_z, w):
        return (
            curl(e_t) * curl(v_t) / k0_val**2
            - (w.eps_xx * e_t[0] * v_t[0] + w.eps_yy * e_t[1] * v_t[1])
            + dot(grad(e_z), v_t)
            + (w.eps_xx * e_t[0] * grad(v_z)[0] + w.eps_yy * e_t[1] * grad(v_z)[1])
            - w.eps_zz * e_z * v_z * k0_val**2
        )

    @BilinearForm(dtype=complex)
    def bform(e_t, e_z, v_t, v_z, w):
        return -dot(e_t, v_t) / k0_val**2

    A = aform.assemble(
        basis,
        eps_xx=basis_eps.interpolate(eps_xx),
        eps_yy=basis_eps.interpolate(eps_yy),
        eps_zz=basis_eps.interpolate(eps_zz),
    )
    B = bform.assemble(basis)

    bnd_dofs = basis.get_dofs(facets=skfem_mesh.boundary_facets())
    lams, xs = solve(
        *condense(-A, -B, D=bnd_dofs, x=basis.zeros(dtype=complex)),
        solver=solver_eigen_scipy(k=num_modes, sigma=k0_val**2 * n_guess**2),
    )

    xs[basis.split_indices()[1], :] /= 1j * np.sqrt(lams[np.newaxis, :] / k0_val**4)

    hs = []
    omega = k0_val * (c0 * 1e6)
    for i, lam in enumerate(lams):
        H = calculate_hfield(basis, xs[:, i], np.sqrt(lam), omega=omega)
        power = calculate_overlap(basis, xs[:, i], H, basis, xs[:, i], H)
        xs[:, i] /= np.sqrt(power)
        H /= np.sqrt(power)
        hs.append(H)

    return Modes(
        modes=[
            Mode(
                frequency=(c0 * 1e6) / wavelength,
                k=np.sqrt(lams[i]),
                basis_epsilon_r=basis_epsilon_r,
                epsilon_r=eps_xx,
                basis=basis,
                E=xs[:, i],
                H=hs[i],
            )
            for i in range(num_modes)
        ]
    )


eps_xx = np.array([MATERIALS[m]["eps_opt"][0] for m in mat_of_el], dtype=complex)
eps_yy = np.array([MATERIALS[m]["eps_opt"][1] for m in mat_of_el], dtype=complex)
eps_zz = np.array([MATERIALS[m]["eps_opt"][2] for m in mat_of_el], dtype=complex)

# intorder=4 is REQUIRED, not cosmetic.
#   with_element() inherits the quadrature rule of the basis it is called on.
#   Basis(mesh, ElementTriP0()) defaults to a 3-point rule, so the N1 x P1
#   eigenproblem would be assembled with 3 points, while skfem's native rule for
#   N1 x P1 is 6 points (intorder 4). That under-integrates the curl-curl and mass
#   forms; it bites hardest on the thin, high-aspect-ratio buffer/skin elements.
basis_epsilon_r = Basis(skfem_mesh, ElementTriP0(), intorder=4)

import time
t_eig0 = time.time()
modes = compute_modes_anisotropic(
    basis_epsilon_r,
    eps_xx,
    eps_yy,
    eps_zz,
    wavelength=wl,
    num_modes=num_modes_search,
    n_guess=n_guess,
)
print(f"Eigensolver complete in {time.time() - t_eig0:.1f}s: computed {len(modes)} optical modes around n_guess = {n_guess}.")
