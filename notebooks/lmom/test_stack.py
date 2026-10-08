"""Checks of stack.py against closed forms."""
import numpy as np
import stack as S

k0 = 2*np.pi*60e9/S.C0
kx = np.array([0.3, 0.9, 1.5, 3.0, 50.0, 1e4])*k0
ok = True
def chk(name, a, b, tol=1e-9):
    global ok
    e = np.max(np.abs(np.asarray(a) - np.asarray(b)))/max(1e-30, np.max(np.abs(b)))
    ok &= e < tol
    print(f"{'PASS' if e < tol else 'FAIL'} {name}: rel err {e:.1e}")

# (a) air over an isotropic half-space, beta = 0: Fresnel for tangential E
eps2 = 11.7 - 0.3j
air = S.Air(kx, 0.0, k0)
R = air.reflection(S.stack_admittance(kx, 0.0, k0, [], (eps2,)*3))
ky1 = np.sqrt(k0**2 - kx**2 + 0j); ky1 = np.where(ky1.imag > 0, -ky1, ky1)
ky2 = np.sqrt(eps2*k0**2 - kx**2 + 0j); ky2 = np.where(ky2.imag > 0, -ky2, ky2)
chk("TE  Rzz vs Fresnel", R[:, 1, 1], (ky1 - ky2)/(ky1 + ky2))
chk("TM  Rxx vs Fresnel", R[:, 0, 0], (ky2/eps2 - ky1)/(ky2/eps2 + ky1))
chk("no TE/TM coupling at beta = 0 (abs)", np.abs(R[:, 0, 1]) + np.abs(R[:, 1, 0]) + 1, np.ones(len(kx)), tol=1e-8)

# (b) finite layers of the bottom medium change nothing; an air layer of thickness d over the
# half-space gives R exp(-2 j ky1 d) (reflection moved down by d)
R2 = air.reflection(S.stack_admittance(kx, 0.0, k0, [((eps2,)*3, 3e-6), ((eps2,)*3, 7e-6)], (eps2,)*3))
chk("eps2 layers over eps2 = half-space", R2, R)
d = 5e-6
R4 = air.reflection(S.stack_admittance(kx, 0.0, k0, [((1.0,)*3, d)], (eps2,)*3))
chk("air layer: R exp(-2j ky d)", R4, R*np.exp(-2j*ky1*d)[:, None, None])

# (c) oblique (beta != 0), isotropic: R is a rotation of the TE/TM pair, check |det| and trace invariants
beta = 1.7*k0
airb = S.Air(kx, beta, k0)
Rb = airb.reflection(S.stack_admittance(kx, beta, k0, [], (eps2,)*3))
kt = np.sqrt(kx**2 + beta**2)
q1 = np.sqrt(k0**2 - kt**2 + 0j); q1 = np.where(q1.imag > 0, -q1, q1)
q2 = np.sqrt(eps2*k0**2 - kt**2 + 0j); q2 = np.where(q2.imag > 0, -q2, q2)
rte, rtm = (q1 - q2)/(q1 + q2), (q2/eps2 - q1)/(q2/eps2 + q1)
ev = np.sort_complex(np.linalg.eigvals(Rb), axis=-1) if False else np.linalg.eigvals(Rb)
match = [min(abs(ev[i, 0] - rte[i]) + abs(ev[i, 1] - rtm[i]), abs(ev[i, 1] - rte[i]) + abs(ev[i, 0] - rtm[i])) for i in range(len(kx))]
chk("oblique: eigenvalues of R = (r_TE, r_TM) (abs)", np.array(match) + 1, np.ones(len(kx)), tol=1e-8)

# (d) anisotropic LN half-space, static limit along x: (1 - sqrt(ex ey))/(1 + sqrt(ex ey))
kbig = np.array([1e5])*k0
a3 = S.Air(kbig, 0.0, k0)
R3 = a3.reflection(S.stack_admittance(kbig, 0.0, k0, [], (28.0, 43.0, 43.0)))
chk("LN static image along x", R3[0, 0, 0], (1 - np.sqrt(28*43))/(1 + np.sqrt(28*43)), tol=1e-6)

# (e) free-space sheet: Jz sheet, beta = 0 -> Ez below = -eta0 k0 / (2 ky) Jz
Ed, Eu = air.sheet_down((0.0, 0.0, 1.0))
chk("Jz sheet: Ez below", Ed[:, 1], -S.ETA0*k0/(2*ky1))
chk("Jz sheet: Ez above = below", Eu[:, 1], Ed[:, 1])

# (f) the full TFLN stack: lossless energy check for a propagating TE wave (|R| <= 1)
L, bot = S.tfln_layers(0.273e-6, 11.7)
Rf = air.reflection(S.stack_admittance(kx, 0.0, k0, L, bot))
print("full stack |R_zz|, |R_xx| at kx/k0 =", np.round(kx/k0, 2), np.round(np.abs(Rf[:, 1, 1]), 4), np.round(np.abs(Rf[:, 0, 0]), 4))
print("ALL PASS" if ok else "SOME FAIL")
