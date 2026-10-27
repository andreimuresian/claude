# %% [4] Selected mode: PEC quantities and dielectric loss
#   The mode solve treats the gold as a perfect conductor: it gives the external
#   inductance L_ext and the capacitance (n_m_pec, Z0_pec).  The gold itself (R' and
#   the internal inductance L_int) is handled volumetrically in cell [5].
i_sel  = fundamental["index"]
x_sel  = xs[:, i_sel]
beta_m = fundamental["beta_m"]
P_sel  = fundamental["P"]

fields = basis_rf.interpolate(x_sel)
P_diel = float(np.real(f_dielectric.assemble(basis_rf, et=fields[0], ez=fields[1],
                                             sig=basis_eps.interpolate(sigma))))
n_m_pec = fundamental["neff"].real
Z0_pec  = fundamental["Z_PI"]
L_ext   = Z0_pec * n_m_pec / C0                   # H/m
alpha_d = P_diel / (2.0 * P_sel)                  # Np/m, dielectric loss (LN, SiO2, ALD tan d)

print(f"selected mode {i_sel}: n_m (PEC) {n_m_pec:.5f}, Z0 (PEC) {Z0_pec:.4f} ohm, "
      f"Mode_Score {fundamental['score']:.4f}, quasi-TEM divergence {fundamental['div']*100:.2f} %")

fig, ax = plt.subplots(figsize=(8, 4))
_Ex = np.mean(np.abs(np.asarray(fields[0])[0]) ** 2, axis=-1)
mesh.plot(np.sqrt(_Ex / _Ex.max()), ax=ax, shading="flat", cmap="inferno", colorbar=True)
ax.set_xlim([-x_gi - 10, x_gi + 10]); ax.set_ylim([-3, au_h + 4]); ax.set_aspect("equal")
ax.set_title(r"selected CPW mode $|E_x|$"); ax.set_xlabel(r"$x$ ($\mu$m)"); ax.set_ylabel(r"$y$ ($\mu$m)")
plt.tight_layout(); plt.show()
