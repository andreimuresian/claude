"""Bend block of the L+B+S run, 0-130 GHz: two-port from the touchstone and from the gap fields.

Bend block = everything between the ends of the buried electrodes (z = 2.16 mm on line 1 and on line 2):
rise onto the cladding, raised straight, U-bend, raised straight, descent.
Line model (from L+S, ls_extraction_130.py): gamma = physical fit of the FIELD alpha and n_m (1-130 GHz);
Zc = smooth fit of the touchstone Zc with the bands |f - m*20.8 GHz| < 2.5 GHz excluded
(Re Zc = z0 + k1/sqrt f + k2/f + k3 f, Im Zc = k1/sqrt f + k2/f + k3 f, linear least squares).
Port block P (each port): series Ls then shunt Cp, fitted on the L+S touchstone with this line model.

(A) touchstone route:  T_LBS = P1 T(2.16) B T(1.08) P2   ->   B = T(2.16)^-1 P1^-1 T_LBS P2^-1 T(1.08)^-1
(B) field route: two-wave fits of the gap voltage on line 1 (z 0..2.16) and line 2 (z 1.08..2.16), gamma fixed to the
    line value, pitch average, 0.18 mm cut at each end. Waves at the planes z = 2.16:
      line 1: a1 = V1+ e^{-gamma 2.16} (towards the bend), b1 = V1- e^{+gamma 2.16} (away from it)
      line 2 (coordinate s = 2.16 - z, 0 at the plane): b2 = V2+ (away), a2 = V2- (towards)
    symmetric reciprocal block: b1 = S11 a1 + S21 a2, b2 = S21 a1 + S11 a2  -> S11, S21 (referenced to Zc).
Both routes are expressed as S-parameters referenced to the line Zc. Outputs: lbs_bend_130.npz, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf
from scipy.optimize import least_squares, curve_fit
from mzm_interconnect.physics import C0, fit_alpha_scaled, fit_nm_saturating
E = os.path.join(HERE, ".."); R = os.path.join(E, "L+B+S", "130 GHz")
GAP, PITCH, CUT = 4.45e-6, 0.18e-3, 0.18e-3
LS = np.load(os.path.join(HERE, "ls_extraction_130.npz"))

# ---- line model
pa = curve_fit(fit_alpha_scaled, LS["F"], LS["aF"], maxfev=40000)[0]
pn = curve_fit(fit_nm_saturating, LS["F"], LS["nF"], p0=(2.3, -0.1, 3), bounds=([1, -1, 1e-3], [10, 1, 130]), maxfev=80000)[0]
fT, ZT = LS["fT"], LS["ZT"]; ok = (fT >= 1) & (np.min([abs(fT - m * 20.8) for m in range(1, 7)], 0) > 2.5)
Mr = np.stack([np.ones(ok.sum()), fT[ok] ** -0.5, 1 / fT[ok], fT[ok]], 1); cr = np.linalg.lstsq(Mr, ZT[ok].real, rcond=None)[0]
Mi = Mr[:, 1:]; ci = np.linalg.lstsq(Mi, ZT[ok].imag, rcond=None)[0]
def line(f):
    w = 2 * np.pi * f * 1e9
    g = fit_alpha_scaled(f, *pa) * 100 / 8.686 + 1j * fit_nm_saturating(f, *pn) * w / C0
    Z = cr[0] + cr[1] * f ** -0.5 + cr[2] / f + cr[3] * f + 1j * (ci[0] * f ** -0.5 + ci[1] / f + ci[2] * f)
    return g, Z
def T(g, Z, L):
    return np.array([[np.cosh(g * L), Z * np.sinh(g * L)], [np.sinh(g * L) / Z, np.cosh(g * L)]]).transpose(2, 0, 1)
def ports(f, Ls, Cp):
    w = 2 * np.pi * f * 1e9; o, n = np.ones_like(f), np.zeros_like(f)
    Ps = np.array([[o, 1j * w * Ls], [n, o]]).transpose(2, 0, 1); Pc = np.array([[o, n], [1j * w * Cp, o]]).transpose(2, 0, 1)
    return Ps @ Pc, Pc @ Ps                       # port 1 (outside -> line), port 2 (line -> outside)
inv = np.linalg.inv

# ---- port block fitted on L+S
nLS = rf.Network(os.path.join(E, "L+S", "130 GHz", "BASELINE - L+S - 130 GHz.s2p")); k = nLS.f / 1e9 >= 1
f = nLS.f[k] / 1e9; g, Z = line(f); SLS = nLS.s[k]
def res(p):
    P1, P2 = ports(f, p[0] * 1e-12, p[1] * 1e-15); S = rf.network.a2s(P1 @ T(g, Z, 3.24e-3) @ P2, 50.0)
    e = np.r_[S[:, 0, 0] - SLS[:, 0, 0], S[:, 1, 0] - SLS[:, 1, 0]]; return np.r_[e.real, e.imag]
pp = least_squares(res, [2.5, 1.7]).x
print(f"line fits: alpha a,b,c {np.round(pa,4)}, n_m n0,dn,fc {np.round(pn,4)}; port block Ls {pp[0]:.2f} pH, Cp {pp[1]:.2f} fF, "
      f"L+S S rms error {np.sqrt(np.mean(res(pp)**2)):.4f} (without ports {np.sqrt(np.mean(res([0,0])**2)):.4f})")

# ---- (A) touchstone route
nLBS = rf.Network(os.path.join(R, "BASELINE - L+B+S - 130 GHz.s2p")); assert np.allclose(nLBS.f[k] / 1e9, f)
P1, P2 = ports(f, pp[0] * 1e-12, pp[1] * 1e-15)
B = inv(T(g, Z, 2.16e-3)) @ inv(P1) @ rf.network.s2a(nLBS.s[k], 50.0) @ inv(P2) @ inv(T(g, Z, 1.08e-3))
B_np = inv(T(g, Z, 2.16e-3)) @ rf.network.s2a(nLBS.s[k], 50.0) @ inv(T(g, Z, 1.08e-3))          # without port blocks
def a2s_Z(A, Zc):
    return np.array([rf.network.a2s(A[i:i + 1], Zc[i])[0] for i in range(len(Zc))])
SA, SA_np = a2s_Z(B, Z), a2s_Z(B_np, Z)

# ---- (B) field route
def load(fn):
    d = np.loadtxt(os.path.join(R, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
def waves(name, z0, z1):
    F, z, Ep = load(f"{name}_gap+.txt"); _, _, Em = load(f"{name}_gap-.txt")
    V = GAP / 2 * (Ep - Em); kk = int(round(PITCH / (z[1] - z[0]))); ker = np.ones(kk) / kk
    zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in V]); m = (zs >= z0 + CUT) & (zs <= z1 - CUT)
    return F, zs[m], Vs[:, m]
F, z1, V1 = waves("L1", 0, 2.16e-3); _, z2, V2 = waves("L2", 1.08e-3, 2.16e-3); s2 = 2.16e-3 - z2
gF, ZF = line(F); SB = np.zeros((len(F), 2, 2), complex); resid = []
for i in range(len(F)):
    g_ = gF[i]
    M1 = np.stack([np.exp(-g_ * z1), np.exp(g_ * z1)], 1); c1 = np.linalg.lstsq(M1, V1[i], rcond=None)[0]
    M2 = np.stack([np.exp(-g_ * s2), np.exp(g_ * s2)], 1); c2 = np.linalg.lstsq(M2, V2[i], rcond=None)[0]
    resid.append(max(np.linalg.norm(M1 @ c1 - V1[i]) / np.linalg.norm(V1[i]), np.linalg.norm(M2 @ c2 - V2[i]) / np.linalg.norm(V2[i])))
    a1, b1 = c1[0] * np.exp(-g_ * 2.16e-3), c1[1] * np.exp(g_ * 2.16e-3); b2, a2 = c2[0], c2[1]
    s11, s21 = np.linalg.solve([[a1, a2], [a2, a1]], [b1, b2]); SB[i] = [[s11, s21], [s21, s11]]
resid = np.array(resid)

# ---- compare on the field frequencies
ia = [np.argmin(abs(f - x)) for x in F]; w = 2 * np.pi * F * 1e9
dB = lambda s: 20 * np.log10(abs(s))
def tau(S21, ff):            # group delay from the unwrapped phase, ps
    ph = np.unwrap(np.angle(S21)); return -np.gradient(ph, 2 * np.pi * ff * 1e9) * 1e12
tA = tau(SA[:, 1, 0], f); tB = tau(SB[:, 1, 0], F)
phA = np.unwrap(np.angle(SA[:, 1, 0])); phB = np.unwrap(np.angle(SB[:, 1, 0]))
tpA, tpB = -phA / (2 * np.pi * f * 1e9) * 1e12, -phB / w * 1e12           # phase delay, ps
print(f"field two-wave residual: median {100*np.median(resid):.2f} %, max {100*resid.max():.2f} % at {F[np.argmax(resid)]:.0f} GHz")
print(" f GHz | |S21| dB  ts / fields / ts no ports | phase delay ps  ts / fields | |S11|  ts / fields")
for q in (2, 5, 10, 16, 20, 30, 31, 40, 47, 50, 60, 63, 70, 79, 80, 90, 100, 110, 120, 130):
    i = np.argmin(abs(F - q)); j = ia[i]
    print(f"{F[i]:5.0f} | {dB(SA[j,1,0]):+.3f} / {dB(SB[i,1,0]):+.3f} / {dB(SA_np[j,1,0]):+.3f} | {tpA[j]:.3f} / {tpB[i]:.3f} | {abs(SA[j,0,0]):.3f} / {abs(SB[i,0,0]):.3f}")
np.savez(os.path.join(HERE, "lbs_bend_130.npz"), f=f, SA=SA, SA_np=SA_np, F=F, SB=SB, resid=resid, tpA=tpA, tpB=tpB, Zf=Z, ZF=ZF, pp=pp, pa=pa, pn=pn, cr=cr, ci=ci)
