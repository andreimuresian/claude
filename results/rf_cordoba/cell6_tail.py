t_mqs = time.time()
R_mqs, L_mqs, L_ext_box, mqs_info = conductor_impedance(f0)
L_int_mqs = L_mqs - L_ext_box
t_mqs = time.time() - t_mqs

# figures of merit with the volumetric gold: n_m and Z0 scale with sqrt(L_ext + L_int)
kappa_m   = np.sqrt(1.0 + L_int_mqs / L_ext)
n_m_c     = n_m_pec * kappa_m
Z0_c      = Z0_pec * kappa_m
Z_VP_c    = fundamental["Z_VP"] * kappa_m
alpha_c_c = R_mqs / (2.0 * Z0_c)
alpha_db_cm_c = DB_PER_NEPER * (alpha_c_c + alpha_d) / 100.0
S21_db_c  = -DB_PER_NEPER * (alpha_c_c + alpha_d) * device_l

print("=" * 66)
print(f"  RF FIGURES OF MERIT @ {f0/1e9:.0f} GHz  (volumetric gold)")
print(f"  buffer {BUFFER_H*1e3:.0f} nm | ALD {T_ALD*1e3:.0f} nm (eps {EPS_ALD}, tan d {TAN_ALD}) | padding {lat_pad:.0f} um")
print("=" * 66)
print(f"  microwave index   n_m              {n_m_c:>14.5f}")
print(f"  Z0              (power-current)    {Z0_c:>14.4f} ohm")
print(f"  Z0_voltage      (voltage-power)    {Z_VP_c:>14.4f} ohm")
print(f"  conductor loss                     {DB_PER_NEPER * alpha_c_c / 100:>14.4f} dB/cm")
print(f"  dielectric loss                    {DB_PER_NEPER * alpha_d / 100:>14.4f} dB/cm")
print(f"  Attenuation                        {alpha_db_cm_c:>14.4f} dB/cm")
print(f"  S21 over {device_l*1e3:>4.1f} mm                    {S21_db_c:>14.4f} dB")
print("-" * 66)
print(f"  R'                                 {R_mqs:>14.2f} ohm/m")
print(f"  L_ext / L_int                      {L_ext*1e9:>8.2f} / {L_int_mqs*1e9:.2f} nH/m")
print(f"  conductor solve: {mqs_info['n_el']} triangles, {mqs_info['ndof']} P2 DOF, {t_mqs:.1f} s")
print("=" * 66)
