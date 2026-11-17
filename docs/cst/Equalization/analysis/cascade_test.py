"""Full equalizer rebuilt as a 2-port cascade: T = T_line(2.70) B T_line(1.44) B T_line(1.44), 50 ohm ports.
Line: L+S touchstone extraction (raw alpha, n_m, Zc). Bend B: 2-port from L+B+S, B = T(2.16)^-1 T_LBS T(1.08)^-1
(route (c) of lbs_bend.py), (i) as measured, dips included; (ii) smoothed: |S21| dB, delay and S11 of B
replaced by a cubic fit in f over the bands outside the dips (14-18, 29-33, 44-50, 60-67, >75 GHz excluded: resonances of the ground-to-ground mode at 16, 31, 47, 63, 79 GHz).
Compared with the full-equalizer touchstone. Outputs: cascade_test.png, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0
E = os.path.join(HERE, "..")
net = lambda p: rf.Network(os.path.join(E, p))
nLBS, nLS, nFULL = net("L+B+S/BASELINE_LBS.s2p"), net("L+S/BASELINE_LS.s2p"), net("full equalizer/BASELINE_FULL_EQUALIZER.s2p")
f = nLBS.f / 1e9; k = f >= 0.5; f = f[k]
fit = extract_line_fit(os.path.join(E, "L+S/BASELINE_LS.s2p"), 3.24)
g = np.interp(f, fit.raw_f_GHz, fit.raw_alpha_dB_cm) * 100 / 8.686 + 1j * np.interp(f, fit.raw_f_GHz, fit.raw_nm) * 2 * np.pi * f * 1e9 / C0
Z = np.interp(f, fit.raw_f_GHz, fit.raw_Zc.real) + 1j * np.interp(f, fit.raw_f_GHz, fit.raw_Zc.imag)
def T(Lm):
    gl = g * Lm; t = np.empty((len(f), 2, 2), complex)
    t[:, 0, 0] = np.cosh(gl); t[:, 0, 1] = Z * np.sinh(gl); t[:, 1, 0] = np.sinh(gl) / Z; t[:, 1, 1] = np.cosh(gl); return t
inv = np.linalg.inv; A = lambda n: rf.network.s2a(n.s[k], 50.0)
B = inv(T(2.16e-3)) @ A(nLBS) @ inv(T(1.08e-3))
# smoothed bend: S-params of B referenced to Zc, fit outside the dips
S = np.array([rf.network.a2s(B[i:i+1], Z[i])[0] for i in range(len(f))])
ok = ~(((f > 14) & (f < 18)) | ((f > 29) & (f < 33)) | ((f > 44) & (f < 50)) | ((f > 60) & (f < 67)) | (f > 75))
def sm(y): return np.polyval(np.polyfit(f[ok], y[ok], 3), f)
mag = 10 ** (sm(20 * np.log10(abs(S[:, 1, 0]))) / 20); ph = sm(np.unwrap(np.angle(S[:, 1, 0])))
s11 = sm(S[:, 0, 0].real) + 1j * sm(S[:, 0, 0].imag)
Ss = np.zeros_like(S); Ss[:, 0, 0] = Ss[:, 1, 1] = s11; Ss[:, 1, 0] = Ss[:, 0, 1] = mag * np.exp(1j * ph)
Bs = np.array([rf.network.s2a(Ss[i:i+1], Z[i])[0] for i in range(len(f))])
def s21(TT): return rf.network.a2s(TT, 50.0)[:, 1, 0], rf.network.a2s(TT, 50.0)[:, 0, 0]
Tl1, Tl2 = T(2.70e-3), T(1.44e-3)
c_raw = s21(Tl1 @ B @ Tl2 @ B @ Tl2); c_sm = s21(Tl1 @ Bs @ Tl2 @ Bs @ Tl2)
ref = nFULL.s[k][:, 1, 0], nFULL.s[k][:, 0, 0]
dB = lambda x: 20 * np.log10(abs(x))
print(" f GHz | |S21| dB: full run / cascade, bend as measured / cascade, smoothed bend")
for q in (10, 16, 20, 31, 40, 47, 55, 60, 70, 80):
    i = np.argmin(abs(f - q)); print(f"{f[i]:5.1f}  | {dB(ref[0][i]):+.3f} / {dB(c_raw[0][i]):+.3f} / {dB(c_sm[0][i]):+.3f}")
for lab, c in (("as measured", c_raw), ("smoothed", c_sm)):
    m = f <= 60; d = dB(c[0]) - dB(ref[0]); dp = np.degrees(np.angle(c[0] / ref[0]))
    print(f"cascade ({lab}) - full run, 0.5-60 GHz: |S21| max {abs(d[m]).max():.3f} dB, rms {np.sqrt(np.mean(d[m]**2)):.3f} dB; "
          f"phase max {abs(dp[m]).max():.1f} deg; |S11| max diff {abs(abs(c[1][m]) - abs(ref[1][m])).max():.3f}")
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
ax[0].plot(f, dB(ref[0]), "k-", lw=1.6, label="full equalizer run (CST)")
ax[0].plot(f, dB(c_raw[0]), "-", color="#eb6834", lw=1, label="cascade, L+B+S bend as measured")
ax[0].plot(f, dB(c_sm[0]), "--", color="#2a78d6", lw=1.2, label="cascade, L+B+S bend smoothed")
ax[0].set_ylabel("|S21| (dB)")
ax[1].plot(f, dB(ref[1]), "k-", lw=1.6, label="full run"); ax[1].plot(f, dB(c_raw[1]), "-", color="#eb6834", lw=1, label="cascade, as measured")
ax[1].plot(f, dB(c_sm[1]), "--", color="#2a78d6", lw=1.2, label="cascade, smoothed"); ax[1].set_ylabel("|S11| (dB)")
for a_ in ax: a_.set_xlabel("frequency (GHz)"); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle("Full equalizer: CST vs 2-port cascade (L+S line + L+B+S bend, two bends)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "cascade_test.png"), dpi=200)
