# %% [4] Overlap Integral, Vpi*L & Optical Attenuation
from skfem import Functional

# Fundamental TE mode identification (highest index matching modal filters)
guided_cands = [
    d for d in mode_diagnostics
    if d["te_ratio"] >= 0.75 and d["core_conf"] >= 0.20 and d["unipolarity"] >= 0.85
]

if not guided_cands:
    raise RuntimeError("Fundamental TE rib mode not found. Check n_guess or eigensolver outputs.")

guided_cands.sort(key=lambda x: x["neff"].real, reverse=True)
fund_diag = guided_cands[0]
chosen_idx = fund_diag["index"]
fund_mode = fund_diag["mode"]
n_eff = fund_diag["neff"]

# 1. Optical Attenuation (Ohmic Metal Loss matching COMSOL Att_Opt)
att_opt_dB_m = np.abs(20.0 * np.log10(np.e) * k0_m * np.imag(n_eff))
att_opt_dB_cm = att_opt_dB_m / 100.0

# 2. Electro-Optic Overlap Integral (Gamma)
ln_mask = (mat_of_el == "LN")
Ex_dc_ln = np.zeros(skfem_mesh.nelements, dtype=float)
Ex_dc_ln[ln_mask] = Ex_dc[ln_mask]
Ex_dc_ln_field = basis_p0.interpolate(Ex_dc_ln)

E_fund_interp = fund_mode.basis.interpolate(fund_mode.E)

@Functional(dtype=complex)
def _num(w): 
    return w["Ex_dc_ln"] * np.abs(w["E"][0][0]) ** 2

@Functional(dtype=complex)
def _den(w): 
    return np.abs(w["E"][0][0]) ** 2

num = np.real(_num.assemble(fund_mode.basis, E=E_fund_interp, Ex_dc_ln=Ex_dc_ln_field))
den = np.real(_den.assemble(fund_mode.basis, E=E_fund_interp))

# GAP_EO only normalises the reported Gamma: it appears in both the overlap
# definition and in Vpi*L, so it cancels exactly and does NOT affect Vpi*L.
# GAP_BOT is the honest choice (it is the gap the DC field actually drops across).
GAP_EO = GAP_BOT
overlap = (GAP_EO / V_bias) * (num / den)
Vpi_L_m = (GAP_EO * 1e-6 * wl_m) / (r33 * np.abs(overlap) * (ne**3) * 2.0)
Vpi_L_Vcm = Vpi_L_m * 100.0
Vpi = Vpi_L_Vcm / L_cm

# 3. Formatted Simulation Summary
print("=" * 55)
print("             ELECTRO-OPTIC SIMULATION RESULTS")
print("=" * 55)
print(f"Selected Mode Index:         {chosen_idx}")
print(f"Effective Index (neff):      {n_eff.real:.6f} + {n_eff.imag:.2e}j")
print(f"Optical Attenuation:         {att_opt_dB_cm:.4e} dB/cm  ({att_opt_dB_m:.4e} dB/m)")
print(f"Overlap Integral (Gamma):    {overlap:.4f}   (normalised to GAP_EO = {GAP_EO} um)")
print(f"|Vpi * L|:                   {Vpi_L_Vcm:.4f} V*cm")
print(f"|Vpi| (for L = {L_cm} cm):        {Vpi:.4f} V")
print("=" * 55)