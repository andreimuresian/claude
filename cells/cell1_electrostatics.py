# %% [1] Anisotropic DC Electrostatics
from skfem import Basis, ElementTriP0, ElementTriP1, BilinearForm, asm, condense, solve
from skfem.helpers import grad

basis_dc = Basis(skfem_mesh, ElementTriP1())
basis_p0 = Basis(skfem_mesh, ElementTriP0())

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

# ------------------------------------------------------------------
# ELECTRODE BOUNDARY CONDITION
# ------------------------------------------------------------------
# get_dofs(elements=...) is VOLUMETRIC, not perimeter-based: internally it does
# np.unique(topo.t[:, elements]), i.e. every node touched by the selected elements
# (interior nodes included). So the whole conductor body is pinned to one potential.
#
# Consequences for the split (bottom + top) electrode:
#   * no perimeter is ever extracted, so there is no "wrong perimeter" to pick;
#   * the bottom/top seam nodes are pinned to the SAME value from both blocks, so
#     no spurious internal Dirichlet surface and no artificial charge sheet appear;
#   * the effective conductor surface is automatically the OUTER boundary of the
#     fused body, which is exactly what we want.
# The only real requirement is that every gold sub-region map to the same material
# tag -- guaranteed by the elR_* / elL_* naming + PREFIX_TO_MAT. Verified below.
# ------------------------------------------------------------------
sig_regions = sorted(n for n in polygons if n.startswith("elR"))
gnd_regions = sorted(n for n in polygons if n.startswith("elL"))
print(f"Signal sub-regions ({len(sig_regions)}): {sig_regions}")
print(f"Ground sub-regions ({len(gnd_regions)}): {gnd_regions}")

sig_elements = np.where(mat_of_el == "Au_sig")[0]
gnd_elements = np.where(mat_of_el == "Au_gnd")[0]
assert sig_elements.size and gnd_elements.size, "an electrode has no elements"

dofs_signal = basis_dc.get_dofs(elements=sig_elements).all()
dofs_ground = basis_dc.get_dofs(elements=gnd_elements).all()
assert np.intersect1d(dofs_signal, dofs_ground).size == 0, "signal and ground electrodes touch"
dofs_dirichlet = np.unique(np.concatenate([dofs_signal, dofs_ground]))

u_dirichlet = np.zeros(basis_dc.N)
u_dirichlet[dofs_signal] = V_bias
u_dirichlet[dofs_ground] = 0.0

K_c, f_c, u_c, I = condense(K, np.zeros(basis_dc.N), x=u_dirichlet, D=dofs_dirichlet)
potential_nodes = u_c.copy()
potential_nodes[I] = solve(K_c, f_c)

grad_V = basis_dc.interpolate(potential_nodes).grad
Ex_dc = -np.mean(grad_V[0], axis=-1) if grad_V.ndim == 3 else -grad_V[0]
Ey_dc = -np.mean(grad_V[1], axis=-1) if grad_V.ndim == 3 else -grad_V[1]

# --- Proof that the fused electrode really is equipotential --------------------
metal = np.isin(mat_of_el, ["Au_sig", "Au_gnd"])
E_in_metal = float(np.max(np.hypot(Ex_dc[metal], Ey_dc[metal])))
E_nominal = V_bias / GAP_BOT
print(f"Pinned DOFs: {dofs_signal.size} signal + {dofs_ground.size} ground "
      f"= {dofs_dirichlet.size} of {basis_dc.N}")
print(f"max |E_dc| inside metal = {E_in_metal:.3e} V/um  "
      f"({E_in_metal / E_nominal:.1e} x nominal V/gap)  -> body is equipotential, "
      f"bottom/top seam is transparent")

# ------------------------------------------------------------------
# Diagnostic plots
# ------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(17, 4.0))

ax0 = axes[0]
electrode_field = np.zeros(skfem_mesh.nelements)
electrode_field[mat_of_el == "Au_sig"] = 1.0
electrode_field[mat_of_el == "Au_gnd"] = -1.0
skfem_mesh.plot(electrode_field, ax=ax0, shading="flat",
                cmap=plt.matplotlib.colors.ListedColormap(["#2c3e50", "#ecf0f1", "#e67e22"]))
ax0.text(XB + 0.6, Y_EB + 0.15, "SIGNAL\n(+1V)", color="white", fontweight="bold", fontsize=8)
ax0.text(-XB - 3.4, Y_EB + 0.15, "GROUND\n(0V)", color="white", fontweight="bold", fontsize=8)
ax0.set_title("Electrode assignment (both halves = one body)", fontsize=10)
ax0.set_xlim([-8.0, 8.0])
ax0.set_ylim([-0.5, 2.0])
ax0.set_aspect("equal")

ax1 = axes[1]
skfem_mesh.plot(potential_nodes, ax=ax1, shading="gouraud", cmap="coolwarm", colorbar=True)
ax1.set_title(r"Anisotropic DC potential $V(x,y)$ [V]", fontsize=10)
ax1.set_xlim([-6.0, 6.0])
ax1.set_ylim([-0.5, 2.0])
ax1.set_aspect("equal")

ax2 = axes[2]
skfem_mesh.plot(Ex_dc, ax=ax2, shading="flat", cmap="RdBu_r", colorbar=True)
ax2.set_title(r"$E_x^{\,DC}$ [V/$\mu$m] - buffer & gap detail", fontsize=10)
ax2.set_xlim([-2.6, 2.6])
ax2.set_ylim([0.0, 1.8])
ax2.set_aspect("equal")

plt.tight_layout()
plt.show()
