"""Far-end voltage of SRC -> EL_1 -> LOAD: wave solution vs the textbook line formula."""
import numpy as np
c0 = 299792458.0
f = np.linspace(0.0, 100e9, 501); w = 2*np.pi*f
L, nm = 14e-3, 2.25
g = 0.5*np.sqrt(f/1e9)*100*np.log(10)/20 + 1j*w*nm/c0     # gamma = alpha + j beta
Zc, Zs, Zt, R0, Vemf = 45.0 - 1.0j, 60.0, 55.0, 50.0, 1.0
G = (Zc-R0)/(Zc+R0); e1 = np.exp(-g*L)
S11 = G*(1-e1**2)/(1-G**2*e1**2); S21 = (1-G**2)*e1/(1-G**2*e1**2)
Gs, GL, Tf = (Zs-R0)/(Zs+R0), (Zt-R0)/(Zt+R0), 2*R0/(Zs+R0)
a_drv = Vemf/2
Gin = S11 + S21**2*GL/(1-S11*GL)                      # step 4
a1 = Tf*a_drv/(1-Gs*Gin)                              # step 5
b2 = S21*a1/(1-S11*GL)                                # step 3
VL_waves = (1+GL)*b2                                  # step 6
# textbook: V(0) from the Thevenin divider on Zin, then V(L) = V(0)/(cosh + Zc/Zt sinh)
th = np.tanh(g*L); Zin = Zc*(Zt+Zc*th)/(Zc+Zt*th)
V0 = Vemf*Zin/(Zs+Zin)
VL_text = V0/(np.cosh(g*L) + Zc/Zt*np.sinh(g*L))
print("max relative difference:", np.max(abs(VL_waves[1:]/VL_text[1:]-1)))
print("DC value (wave solution):", abs(VL_waves[0]), " Zt/(Zs+Zt) =", Zt/(Zs+Zt))
for R0b in (20.0, 100.0):    # change the bookkeeping impedance: result must not move
    G2 = (Zc-R0b)/(Zc+R0b); s11 = G2*(1-e1**2)/(1-G2**2*e1**2); s21 = (1-G2**2)*e1/(1-G2**2*e1**2)
    gs, gl, tf = (Zs-R0b)/(Zs+R0b), (Zt-R0b)/(Zt+R0b), 2*R0b/(Zs+R0b)
    gin = s11 + s21**2*gl/(1-s11*gl); A1 = tf*a_drv/(1-gs*gin)
    print(f"R0 = {R0b:5.1f} ohm: max change in V(L)", np.max(abs((1+gl)*s21*A1/(1-s11*gl)/VL_waves-1)))
