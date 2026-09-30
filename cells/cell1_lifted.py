# %% [1] Anisotropic DC Electrostatics
from skfem import Basis, ElementTriP0, ElementTriP1, BilinearForm, asm, condense, solve
from skfem.helpers import grad

basis_dc = Basis(skfem_mesh, ElementTriP1(), intorder=4)
basis_p0 = Basis(skfem_mesh, ElementTriP0(), intorder=4)

eps_dc_x = np.array([MATERIALS[m]["eps_dc"][0] for m in mat_of_el], dtype=float)
eps_dc_y = np.array([MATERIALS[m]["eps_dc"][1] for m in mat_of_el], dtype=float)

@BilinearForm
def laplace_aniso(u, v, w):
    return w.eps_x * grad(u)[0] * grad(v)[0] + w.eps_y * grad(u)[1] * grad(v)[1]

K = asm(
    laplace_aniso,
    basis_dc,
    eps_x=basis_p0.interpolate(eps_dc_x),
    eps_y=basis_p0.interpolate(eps_dc_y),
)

sig_elements = np.where(mat_of_el == "Au_sig")[0]
gnd_elements = np.where(mat_of_el == "Au_gnd")[0]

dofs_signal = basis_dc.get_dofs(elements=sig_elements).all()
dofs_ground = basis_dc.get_dofs(elements=gnd_elements).all()
dofs_dirichlet = np.unique(np.concatenate([dofs_signal, dofs_ground]))

u_dirichlet = np.zeros(basis_dc.N)
u_dirichlet[dofs_signal] = V_bias
u_dirichlet[dofs_ground] = 0.0

K_c, f_c, u_c, I = condense(K, np.zeros(basis_dc.N), x=u_dirichlet, D=dofs_dirichlet)
potential_nodes = u_c.copy()
potential_nodes[I] = solve(K_c, f_c)

grad_V = basis_dc.interpolate(potential_nodes).grad
Ex_dc = -np.mean(grad_V[0], axis=-1) if grad_V.ndim == 3 else -grad_V[0]

# Diagnostic plots
fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))

ax0 = axes[0]
electrode_field = np.zeros(skfem_mesh.nelements)
electrode_field[mat_of_el == "Au_sig"] = 1.0
electrode_field[mat_of_el == "Au_gnd"] = -1.0

skfem_mesh.plot(electrode_field, ax=ax0, shading="flat", cmap=plt.matplotlib.colors.ListedColormap(["#2c3e50", "#ecf0f1", "#e67e22"]))
ax0.text(GAP_TOP / 2 + 1.0, SLAB_H + BUFFER_H + 0.8, "SIGNAL (+1V)", color="white", fontweight="bold")
ax0.text(-GAP_TOP / 2 - 6.5, SLAB_H + BUFFER_H + 0.8, "GROUND (0V)", color="white", fontweight="bold")
ax0.set_title("Equipotential Electrodes: Signal (+1V) vs Ground (0V)")
ax0.set_xlim([-14.0, 14.0])
ax0.set_ylim([-0.5, 6.5])
ax0.set_aspect("equal")

ax1 = axes[1]
skfem_mesh.plot(potential_nodes, ax=ax1, shading="gouraud", cmap="coolwarm", colorbar=True)
ax1.set_title(r"Anisotropic DC Potential $V(x, y)$ [V]")
ax1.set_xlim([-14.0, 14.0])
ax1.set_ylim([-0.5, 6.5])
ax1.set_aspect("equal")

plt.tight_layout()
plt.show()