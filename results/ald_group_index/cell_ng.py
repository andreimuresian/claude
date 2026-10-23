# %% [5] Group index: central finite difference of n_eff(lambda) on the SAME mesh
#
#   ng = n_eff - lambda * d n_eff / d lambda.  Only the material permittivities change
#   between the solves (all dispersive: LN Zelmon, SiO2 Malitson, Au Johnson & Christy,
#   ALD Al2O3 Sellmeier), so the discretisation error cancels in the differences.
#   The fundamental TE mode at each wavelength is the one with the largest overlap
#   with the mode selected in cell 4.
NG_DL = (0.001, 0.002)              # um: half-steps of the central differences (+-1 nm, +-2 nm)

def _eps_tensors(lam):
    ne_l, no_l = n_LN(lam); ns_l = n_SiO2(lam); ea_l = eps_Au_JC(lam); na_l = n_ALD(lam)
    tab = {"LN": (ne_l**2, no_l**2, no_l**2), "SiO2": (ns_l**2,) * 3, "air": (1.0,) * 3,
           "Au_sig": (ea_l,) * 3, "Au_gnd": (ea_l,) * 3, "Al2O3": (na_l**2,) * 3}
    return [np.array([tab[m][i] for m in mat_of_el], dtype=complex) for i in range(3)]

def _neff_at(lam):
    exx, eyy, ezz = _eps_tensors(lam)
    ms = compute_modes_anisotropic(basis_epsilon_r, exx, eyy, ezz, wavelength=lam,
                                   num_modes=num_modes_search, n_guess=n_eff.real)
    ov = [abs(calculate_overlap(fund_mode.basis, fund_mode.E, fund_mode.H, m.basis, m.E, m.H)) for m in ms]
    best = ms[int(np.argmax(ov))]
    return complex(best.k / (2.0 * np.pi / lam)), float(max(ov))

ng_rows = {0.0: (n_eff, 1.0)}
for dl in NG_DL:
    for sgn in (-1, 1):
        ng_rows[sgn * dl] = _neff_at(wl + sgn * dl)
ng_results = {}
for dl in NG_DL:
    dn = (ng_rows[dl][0].real - ng_rows[-dl][0].real) / (2.0 * dl)
    ng_results[dl] = n_eff.real - wl * dn
print("=" * 70)
print(f"GROUP INDEX @ {wl*1e3:.1f} nm   (T_ALD = {T_ALD*1e3:.0f} nm, ALD model '{ALD_MODEL}', n_ALD = {n_ALD(wl):.4f})")
for k in sorted(ng_rows):
    print(f"  lambda {(wl + k)*1e3:8.1f} nm   n_eff = {ng_rows[k][0].real:.7f}   overlap with ref = {ng_rows[k][1]:.4f}")
for dl, v in ng_results.items():
    print(f"  ng (central, +-{dl*1e3:.0f} nm) = {v:.5f}")
print("=" * 70)
