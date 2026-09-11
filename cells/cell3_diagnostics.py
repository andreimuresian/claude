# %% [3] High-Precision Diagnostics & Mode Gallery
from skfem import Functional

core_ids = [s_id for name, s_id in name_to_id.items() if name.split("___")[0] == "core"]
is_core = np.zeros(skfem_mesh.nelements, dtype=float)
is_core[np.isin(tri_subdomains, core_ids)] = 1.0
is_core_field = basis_p0.interpolate(is_core)

@Functional(dtype=complex)
def _px(w):
    return np.abs(w["E"][0][0]) ** 2

@Functional(dtype=complex)
def _ptot(w):
    return (
        np.abs(w["E"][0][0]) ** 2
        + np.abs(w["E"][0][1]) ** 2
        + np.abs(w["E"][1]) ** 2
    )

@Functional(dtype=complex)
def _p_core(w):
    return w["is_core"] * (
        np.abs(w["E"][0][0]) ** 2
        + np.abs(w["E"][0][1]) ** 2
        + np.abs(w["E"][1]) ** 2
    )

@Functional(dtype=complex)
def _ex_core_signed(w):
    return w["is_core"] * np.real(w["E"][0][0])

@Functional(dtype=complex)
def _ex_core_abs(w):
    return w["is_core"] * np.abs(np.real(w["E"][0][0]))

mode_diagnostics = []

print("=" * 82)
print(f"{'Idx':<4} | {'Re(neff)':<10} | {'Im(neff)':<12} | {'TE %':<8} | {'Core Pwr %':<10} | {'Unipolarity':<12}")
print("-" * 82)

for idx, mode in enumerate(modes):
    E_interp = mode.basis.interpolate(mode.E)

    P_x = np.real(_px.assemble(mode.basis, E=E_interp))
    P_tot = np.real(_ptot.assemble(mode.basis, E=E_interp))
    P_core = np.real(_p_core.assemble(mode.basis, E=E_interp, is_core=is_core_field))

    te_ratio = P_x / P_tot
    core_confinement = P_core / P_tot

    signed = np.real(_ex_core_signed.assemble(mode.basis, E=E_interp, is_core=is_core_field))
    absval = np.real(_ex_core_abs.assemble(mode.basis, E=E_interp, is_core=is_core_field))

    unipolarity = 0.0000 if absval < 1e-12 else np.abs(signed) / absval

    neff_val = complex(mode.k / k0)

    mode_diagnostics.append({
        "index": idx,
        "mode": mode,
        "neff": neff_val,
        "te_ratio": te_ratio,
        "core_conf": core_confinement,
        "unipolarity": unipolarity,
    })

    print(
        f"{idx:<4} | "
        f"{neff_val.real:<10.5f} | "
        f"{neff_val.imag:<12.2e} | "
        f"{te_ratio * 100:<7.2f}% | "
        f"{core_confinement * 100:<9.2f}% | "
        f"{unipolarity:<12.4f}"
    )

print("=" * 82)

# Full Mode Gallery Plot
cols = 4
rows = int(np.ceil(len(modes) / cols))
fig, axes = plt.subplots(rows, cols, figsize=(16, 3.4 * rows))
axes = np.array(axes).flatten()

for idx, diag in enumerate(mode_diagnostics):
    ax = axes[idx]
    E_interp = diag["mode"].basis.interpolate(diag["mode"].E)
    Ex_elem = np.mean(np.abs(E_interp[0].value[0]) ** 2, axis=-1)

    skfem_mesh.plot(Ex_elem, ax=ax, shading="flat", cmap="inferno")
    title_str = (
        f"Mode {idx}: n={diag['neff'].real:.4f}\n"
        f"TE={diag['te_ratio']*100:.1f}% | Conf={diag['core_conf']*100:.1f}%\n"
        f"Uni={diag['unipolarity']:.4f}"
    )
    ax.set_title(title_str, fontsize=9)
    ax.set_xlim([-4.0, 4.0])
    ax.set_ylim([-0.5, 1.8])   # taller window: cap now reaches y=1.675
    ax.set_aspect("equal")

for j in range(len(modes), len(axes)):
    fig.delaxes(axes[j])

plt.tight_layout()
plt.show()