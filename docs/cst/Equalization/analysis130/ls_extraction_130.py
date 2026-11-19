"""L+S run 0-130 GHz (straight line, EL_L = 3.24 mm): gamma = alpha + j beta (beta = n_m w / c) and Zc from the
touchstone and from the gap fields; agreement of the two routes; quality of the old extrapolation.

Touchstone route: S (50 ohm) -> ABCD -> Zc = sqrt(B/C), exp(gamma L) = A + B/Zc (mzm_interconnect.extractor).
Field route: V(z) = (GAP/2)(Ey+ - Ey-) at the two gap centres (x = 0.001 mm), averaged over one pitch (0.18 mm),
fitted with V(z) = A exp(-gamma z) + B exp(+gamma z) on 0.18 .. 3.06 mm  -> gamma.
  Zc from the reflection at port 2 (plane z = L, 50 ohm):  Gamma_L = B exp(gamma L) / (A exp(-gamma L)),
  Zc = 50 (1 - Gamma_L) / (1 + Gamma_L). The pitch average multiplies both waves by the same factor, so Gamma_L is
  unaffected. Gamma_L includes whatever the port transition adds at z = L (seen as a Zc error).
Extrapolation check (field route only): physical fits of the OLD 1-60 GHz field data (formulas in the code below)
Outputs: ls_extraction_130.png, ls_extraction_130.csv, printed table."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0, fit_alpha_scaled, fit_nm_saturating, fit_impedance_physical, fit_impedance_imag
E = os.path.join(HERE, ".."); D = os.path.join(E, "L+S", "130 GHz")
L, GAP, PITCH, CUT = 3.24e-3, 4.45e-6, 0.18e-3, 0.18e-3

# ---- touchstone route (new data)
ts = extract_line_fit(os.path.join(D, "BASELINE - L+S - 130 GHz.s2p"), L * 1e3)
fT, aT, nT, ZT = ts.raw_f_GHz, ts.raw_alpha_dB_cm, ts.raw_nm, ts.raw_Zc

# ---- field route (function: used for the new 0-130 GHz and the old 0-60 GHz exports)
def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
def field_route(folder):
    def load(fn):
        d = np.loadtxt(os.path.join(folder, fn), skiprows=2); f = np.unique(d[:, 0]); z = d[d[:, 0] == f[0], 3] * 1e-3
        return f, z, (d[:, 6] + 1j * d[:, 7]).reshape(len(f), len(z))
    F, z, Ep = load("L1_gap+.txt"); _, _, Em = load("L1_gap-.txt")
    V = GAP / 2 * (Ep - Em); k = int(round(PITCH / (z[1] - z[0]))); ker = np.ones(k) / k
    zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in V]); m = (zs >= CUT) & (zs <= L - CUT)
    w = 2 * np.pi * F * 1e9; out = []
    for i, f in enumerate(F):
        g0 = [np.interp(f, fT, aT) * 100 / 8.686, np.interp(f, fT, nT) * w[i] / C0]
        r = lambda p: np.concatenate([(e := two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m])[1]).real, e.imag])
        p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]
        c, e = two_wave(g, zs[m], Vs[i][m]); GL = c[1] * np.exp(g * L) / (c[0] * np.exp(-g * L))
        out.append((p[0] * 8.686 / 100, p[1] * C0 / w[i], 50 * (1 - GL) / (1 + GL), np.linalg.norm(e) / np.linalg.norm(Vs[i][m])))
    a, n, Z, res = (np.array(x) for x in zip(*out)); return F, a, n, Z, res
F, aF, nF, ZF, res = field_route(D); w = 2 * np.pi * F * 1e9
aTi, nTi = np.interp(F, fT, aT), np.interp(F, fT, nT); ZTi = np.interp(F, fT, ZT.real) + 1j * np.interp(F, fT, ZT.imag)

# ---- extrapolation check, field route only: physical fits of the OLD 1-60 GHz field data, compared with the new
#      62-130 GHz field data.  alpha = a sqrt(f) + b f + c   (conductor skin loss + dielectric loss + offset, dB/cm)
#      n_m = n0 + dn f / (fc + f)   (bounded dispersion, corner fc kept inside the fitted band)
#      Re Zc = z_inf + k1 / sqrt(f) + k2 / f,   Im Zc = k1 / sqrt(f) + k2 / f      (f in GHz)
from scipy.optimize import curve_fit
Fo, aFo, nFo, ZFo, _ = field_route(os.path.join(E, "L+S"))
pa = curve_fit(fit_alpha_scaled, Fo, aFo, maxfev=40000)[0]
pn = curve_fit(fit_nm_saturating, Fo, nFo, p0=(np.median(nFo), 0.01, 30), bounds=([1, -1, 1e-3], [10, 1, Fo.max()]), maxfev=80000)[0]
pz = curve_fit(fit_impedance_physical, Fo, ZFo.real, maxfev=40000)[0]; pzi = curve_fit(fit_impedance_imag, Fo, ZFo.imag, maxfev=40000)[0]
EXT = lambda ff: (fit_alpha_scaled(ff, *pa), fit_nm_saturating(ff, *pn), fit_impedance_physical(ff, *pz) + 1j * fit_impedance_imag(ff, *pzi))
print("fit of old field data 1-60 GHz: alpha a,b,c =", np.round(pa, 4), "| n_m n0,dn,fc =", np.round(pn, 4), "| Re Zc z_inf,k1,k2 =", np.round(pz, 3), "| Im Zc k1,k2 =", np.round(pzi, 3))
oldnew = np.isin(F, Fo); i_o = np.searchsorted(Fo, F[oldnew])
print(f"old vs new field data over 1-60 GHz: alpha max diff {abs(aF[oldnew]-aFo[i_o]).max():.3f} dB/cm, n_m {abs(nF[oldnew]-nFo[i_o]).max():.4f}, Re Zc {abs(ZF.real[oldnew]-ZFo.real[i_o]).max():.2f} ohm")
e = EXT(F); b = F > 60
print(f"extrapolation error vs new field data, 62-130 GHz: alpha max {abs(e[0]-aF)[b].max():.3f} dB/cm ({100*(abs(e[0]-aF)/aF)[b].max():.1f} %), "
      f"n_m max {abs(e[1]-nF)[b].max():.4f} ({100*(abs(e[1]-nF)/nF)[b].max():.2f} %), Re Zc max {abs(e[2].real-ZF.real)[b].max():.2f} ohm ({100*(abs(e[2].real-ZF.real)/ZF.real)[b].max():.1f} %), "
      f"Im Zc max {abs(e[2].imag-ZF.imag)[b].max():.2f} ohm")
# ---- report
band = lambda lo, hi: (F >= lo) & (F <= hi)
print("Agreement fields vs touchstone (differences fields - touchstone):")
for lo, hi in ((1, 60), (62, 130)):
    b = band(lo, hi)
    print(f"  {lo:3d}-{hi:3d} GHz: alpha rms {np.sqrt(np.mean((aF-aTi)[b]**2)):.3f} dB/cm (rel median {100*np.median(abs(aF-aTi)[b]/aTi[b]):.1f} %), "
          f"n_m mean {np.mean((nF-nTi)[b]):+.4f} rms {np.sqrt(np.mean((nF-nTi)[b]**2)):.4f}, Re Zc mean {np.mean((ZF-ZTi).real[b]):+.2f} ohm, "
          f"Im Zc mean {np.mean((ZF-ZTi).imag[b]):+.2f} ohm, field fit residual max {100*res[b].max():.1f} %")
np.savetxt(os.path.join(HERE, "ls_extraction_130.csv"),
           np.column_stack([F, aTi, aF, nTi, nF, ZTi.real, ZF.real, ZTi.imag, ZF.imag, res]), delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,alpha_ts_dB_cm,alpha_fields_dB_cm,nm_ts,nm_fields,ReZc_ts,ReZc_fields,ImZc_ts,ImZc_fields,field_fit_residual")

np.savez(os.path.join(HERE, "ls_extraction_130.npz"), fT=fT, aT=aT, nT=nT, ZT=ZT, F=F, aF=aF, nF=nF, ZF=ZF,
         Fo=Fo, aFo=aFo, nFo=nFo, ZFo=ZFo, ext=np.array(EXT(F)), pa=pa, pn=pn, pz=pz, pzi=pzi)
