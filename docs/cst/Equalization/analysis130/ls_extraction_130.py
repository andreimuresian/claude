"""L+S run 0-130 GHz (straight line, EL_L = 3.24 mm): gamma = alpha + j beta (beta = n_m w / c) and Zc from the
touchstone and from the gap fields; agreement of the two routes; quality of the old extrapolation.

Touchstone route: S (50 ohm) -> ABCD -> Zc = sqrt(B/C), exp(gamma L) = A + B/Zc (mzm_interconnect.extractor).
Field route: V(z) = (GAP/2)(Ey+ - Ey-) at the two gap centres (x = 0.001 mm), averaged over one pitch (0.18 mm),
fitted with V(z) = A exp(-gamma z) + B exp(+gamma z) on 0.18 .. 3.06 mm  -> gamma.
  Zc from the reflection at port 2 (plane z = L, 50 ohm):  Gamma_L = B exp(gamma L) / (A exp(-gamma L)),
  Zc = 50 (1 - Gamma_L) / (1 + Gamma_L). The pitch average multiplies both waves by the same factor, so Gamma_L is
  unaffected. Gamma_L includes whatever the port transition adds at z = L (seen as a Zc error).
Extrapolation check: physical fits (alpha = a sqrt f + b f + c, saturating n_m, Re Zc = z_inf + k1/sqrt f + k2/f,
Im Zc = k1/sqrt f + k2/f) of the OLD touchstone, fitted (i) on 0.5-60 GHz and (ii) on 0.5-80 GHz (the model used
for the 8 mm prediction), compared with the new 0-130 GHz touchstone data.
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

# ---- field route
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); f = np.unique(d[:, 0]); z = d[d[:, 0] == f[0], 3] * 1e-3
    return f, z, (d[:, 6] + 1j * d[:, 7]).reshape(len(f), len(z))
F, z, Ep = load("L1_gap+.txt"); _, _, Em = load("L1_gap-.txt")
V = GAP / 2 * (Ep - Em); k = int(round(PITCH / (z[1] - z[0]))); ker = np.ones(k) / k
zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in V]); m = (zs >= CUT) & (zs <= L - CUT)
w = 2 * np.pi * F * 1e9
def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
aF, nF, ZF, res = [], [], [], []
for i, f in enumerate(F):
    g0 = [np.interp(f, fT, aT) * 100 / 8.686, np.interp(f, fT, nT) * w[i] / C0]
    r = lambda p: np.concatenate([(e := two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m])[1]).real, e.imag])
    p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]
    c, e = two_wave(g, zs[m], Vs[i][m]); GL = c[1] * np.exp(g * L) / (c[0] * np.exp(-g * L))
    aF.append(p[0] * 8.686 / 100); nF.append(p[1] * C0 / w[i]); ZF.append(50 * (1 - GL) / (1 + GL)); res.append(np.linalg.norm(e) / np.linalg.norm(Vs[i][m]))
aF, nF, ZF, res = map(np.array, (aF, nF, ZF, res))
aTi, nTi = np.interp(F, fT, aT), np.interp(F, fT, nT); ZTi = np.interp(F, fT, ZT.real) + 1j * np.interp(F, fT, ZT.imag)

# ---- old-data extrapolations (fits on 0.5-60 and 0.5-80 GHz of the old touchstone)
old = rf.Network(os.path.join(E, "L+S", "BASELINE_LS.s2p")); EXT = {}
for fmax in (60, 80):
    p = os.path.join(tempfile.mkdtemp(), f"old_{fmax}.s2p"); old[f"0-{fmax}ghz"].write_touchstone(p)
    fo = extract_line_fit(p, L * 1e3)
    EXT[fmax] = (lambda ff, fo=fo: (fit_alpha_scaled(ff, *fo.popt_alpha), fit_nm_saturating(ff, *fo.popt_nm),
                                     fit_impedance_physical(ff, *fo.popt_zre) + 1j * fit_impedance_imag(ff, *fo.popt_zim)))

# ---- report
band = lambda lo, hi: (F >= lo) & (F <= hi)
print("Agreement fields vs touchstone (differences fields - touchstone):")
for lo, hi in ((1, 60), (62, 130)):
    b = band(lo, hi)
    print(f"  {lo:3d}-{hi:3d} GHz: alpha rms {np.sqrt(np.mean((aF-aTi)[b]**2)):.3f} dB/cm (rel median {100*np.median(abs(aF-aTi)[b]/aTi[b]):.1f} %), "
          f"n_m mean {np.mean((nF-nTi)[b]):+.4f} rms {np.sqrt(np.mean((nF-nTi)[b]**2)):.4f}, Re Zc mean {np.mean((ZF-ZTi).real[b]):+.2f} ohm, "
          f"Im Zc mean {np.mean((ZF-ZTi).imag[b]):+.2f} ohm, field fit residual max {100*res[b].max():.1f} %")
print(" f GHz | alpha dB/cm ts / fields / ext60 / ext80 | n_m ts / fields / ext60 / ext80 | Re Zc ts / fields / ext60 / ext80 | Im Zc ts / fields")
for q in (1, 10, 30, 60, 80, 100, 130):
    i = np.argmin(abs(F - q)); e6, e8 = EXT[60](F[i]), EXT[80](F[i])
    print(f"{F[i]:5.0f} | {aTi[i]:.2f} / {aF[i]:.2f} / {e6[0]:.2f} / {e8[0]:.2f} | {nTi[i]:.3f} / {nF[i]:.3f} / {e6[1]:.3f} / {e8[1]:.3f} | "
          f"{ZTi[i].real:.1f} / {ZF[i].real:.1f} / {e6[2].real:.1f} / {e8[2].real:.1f} | {ZTi[i].imag:+.1f} / {ZF[i].imag:+.1f}")
for fmax in (60, 80):
    e = EXT[fmax](fT); b = fT > fmax
    print(f"extrapolation of the 0.5-{fmax} GHz fit over {fmax}-130 GHz vs new touchstone: alpha max err {abs(e[0]-aT)[b].max():.2f} dB/cm "
          f"(at 130: {e[0][-1]-aT[-1]:+.2f}), n_m max err {abs(e[1]-nT)[b].max():.4f}, Re Zc max err {abs(e[2].real-ZT.real)[b].max():.2f} ohm")
np.savetxt(os.path.join(HERE, "ls_extraction_130.csv"),
           np.column_stack([F, aTi, aF, nTi, nF, ZTi.real, ZF.real, ZTi.imag, ZF.imag, res]), delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,alpha_ts_dB_cm,alpha_fields_dB_cm,nm_ts,nm_fields,ReZc_ts,ReZc_fields,ImZc_ts,ImZc_fields,field_fit_residual")

# ---- figure: 2 x 3 (top: ts vs fields; bottom: extrapolation)
OR, BL, GR = "#eb6834", "#2a78d6", "0.45"
fig, ax = plt.subplots(2, 3, figsize=(13, 7.2), sharex=True)
for j, (yt, yf, lab) in enumerate(((aT, aF, "α (dB/cm)"), (nT, nF, "$n_m$"), (ZT.real, ZF.real, "Re $Z_c$ (Ω)"))):
    ax[0, j].plot(fT, yt, "k-", lw=1.2, label="touchstone"); ax[0, j].plot(F, yf, "o", ms=3, color=OR, label="fields")
    ax[1, j].plot(fT, yt, "k-", lw=1.2, label="new touchstone (0–130 GHz)")
    for fmax, st, cl in ((60, "--", BL), (80, ":", OR)):
        ax[1, j].plot(fT, EXT[fmax](fT)[j].real, st, color=cl, lw=1.6, label=f"fit of old data 0.5–{fmax} GHz")
    ax[0, j].set_ylabel(lab); ax[1, j].set_ylabel(lab); ax[1, j].set_xlabel("frequency (GHz)")
ax[0, 2].plot(fT, ZT.imag, "-", color=GR, lw=1, label="Im $Z_c$ touchstone"); ax[0, 2].plot(F, ZF.imag, "s", ms=2.5, color=BL, label="Im $Z_c$ fields")
ax[1, 0].axvspan(60, 130, color="0.93", zorder=0)
for a_ in ax.flat: a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=7.5)
ax[0, 1].set_title("Touchstone vs fields", fontsize=10); ax[1, 1].set_title("Old-data fits extrapolated vs new data", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "ls_extraction_130.png"), dpi=200)
for fmax in (60, 80):
    e = EXT[fmax](F); b = F > fmax
    print(f"0.5-{fmax} GHz fit vs FIELD route over {fmax}-130 GHz: alpha max err {abs(e[0]-aF)[b].max():.2f} dB/cm ({100*(abs(e[0]-aF)/aF)[b].max():.1f} %), "
          f"Re Zc max err {abs(e[2].real-ZF.real)[b].max():.2f} ohm")
print("ripple period expected for beta L = m pi:", round(C0 / (2 * np.interp(60, fT, nT) * L) / 1e9, 1), "GHz")
np.savez(os.path.join(HERE, "ls_extraction_130.npz"), fT=fT, aT=aT, nT=nT, ZT=ZT, F=F, aF=aF, nF=nF, ZF=ZF,
         **{f"ext{k}": np.array(EXT[k](fT)) for k in EXT})
