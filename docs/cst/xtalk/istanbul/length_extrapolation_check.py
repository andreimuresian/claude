"""How good is the GUI's length extrapolation? Istanbul line A (ports 1 near, 2 far of the 4-port; line B ports in 50 ohm).
Extract alpha, n_m, Zc (extract_line_fit, the GUI's extraction) from each simulated length (1, 3, 5, 8.75 mm) and
extrapolate to 8.75 mm with the uniform-line formula. Compare with:
  - the simulated 8.75 mm S21, S11 (ISTANBUL_SW_8p75mm.s4p, fine mesh family as the 1 mm run);
  - the EO response (50/50 ohm, n_g 2.27, normalised to 3-10.7 GHz) of the line model extracted from the 8.75 mm run
    itself (no length extrapolation). The run (a) gap fields are NOT usable as reference: run (a) is a different structure
    (n_m 2.23 at 30 GHz against 2.11 for these SW files).
Note: 3 and 5 mm are the coarse mesh/port family (four_lengths_results.md), 1 and 8.75 mm the fine one."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import eo_transfer, C0
FILES = {1.0: "ISTANBUL_SW_1p00mm.s4p", 3.0: "TEST0_XTALK_SW__3p00mm.s4p", 5.0: "TEST0_XTALK_SW_5mm.s4p", 8.75: "ISTANBUL_SW_8p75mm.s4p"}
LT, ZR = 8.75, 50.0
tmp = tempfile.mkdtemp()
def two_port(L):
    n = rf.Network(os.path.join(HERE, FILES[L])).subnetwork([0, 1]); p = os.path.join(tmp, f"A_{int(L*100)}"); n.write_touchstone(p); return n, p + ".s2p"
def line_s(fit, f, L):
    g = fit.alpha_dB_cm(f) * 100 / 8.686 + 1j * 2 * np.pi * f * 1e9 * fit.nm(f) / C0; zc = fit.Zc(f); gl = g * L * 1e-3
    den = 2 * zc * ZR * np.cosh(gl) + (zc ** 2 + ZR ** 2) * np.sinh(gl)
    return (zc ** 2 - ZR ** 2) * np.sinh(gl) / den, 2 * zc * ZR / den
dB = lambda x: 20 * np.log10(abs(x))
ref_net, _ = two_port(LT); fs = ref_net.f / 1e9; k = (fs >= 1) & (fs <= 60); fs = fs[k]
S21_true, S11_true = dB(ref_net.s[k, 1, 0]), dB(ref_net.s[k, 0, 0])
fe = np.arange(1.0, 60.01, 0.25); REF = (fe >= 3) & (fe <= 10.7)
ph_true = np.unwrap(np.angle(ref_net.s[k, 1, 0]))
_, p_ = two_port(LT); f_ = extract_line_fit(p_, LT)
H_, _ = eo_transfer(fe, f_.alpha_dB_cm(fe), f_.nm(fe), f_.Zc(fe), LT * 1e-3, 2.27, 50.0, 50.0); eo_true = 20 * np.log10(abs(H_) / np.mean(abs(H_[REF])))
res = {}
print("from L | |S21| err 30/60 GHz (dB) | |S21| rms | S21 phase err 30/60 (deg) | |S11| rms (dB) | EO err 30/60 vs 8.75 own model | -3 dB bw | alpha@30 dB/cm n_m@30 ReZc@30")
for L in FILES:
    _, path = two_port(L); fit = extract_line_fit(path, L)
    s11, s21 = line_s(fit, fs, LT)
    H, _ = eo_transfer(fe, fit.alpha_dB_cm(fe), fit.nm(fe), fit.Zc(fe), LT * 1e-3, 2.27, 50.0, 50.0)
    eo = 20 * np.log10(abs(H) / np.mean(abs(H[REF])))
    d21, d11, de = dB(s21) - S21_true, dB(s11) - S11_true, eo - eo_true
    dph = np.degrees(np.unwrap(np.angle(s21)) - ph_true); dph -= 360 * np.round(dph[0] / 360)
    c3 = np.where(eo < -3)[0]; bw = f"{fe[c3[0]]:.1f}" if len(c3) else "> 60"
    res[L] = (dB(s21), dB(s11), eo)
    i30, i60 = np.argmin(abs(fs - 30)), np.argmin(abs(fs - 60)); j30, j60 = np.argmin(abs(fe - 30)), np.argmin(abs(fe - 60))
    a30 = fit.alpha_dB_cm(np.array([30.0]))[0]; n30 = fit.nm(np.array([30.0]))[0]; z30 = fit.Zc(np.array([30.0]))[0].real
    print(f"{L:5.2f}  | {d21[i30]:+.2f} {d21[i60]:+.2f} | {np.sqrt(np.mean(d21**2)):.2f} | {dph[i30]:+.0f} {dph[i60]:+.0f} | {np.sqrt(np.mean(d11**2)):.1f} | "
          f"{de[j30]:+.2f} {de[j60]:+.2f} | {bw} | {a30:.3f} {n30:.4f} {z30:.1f}")
C = {1.0: "#eb6834", 3.0: "#1baa7d", 5.0: "#7a4bd1", 8.75: "#2a78d6"}
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
ax[0].plot(fs, S21_true, "k", lw=2.2, label="simulated 8.75 mm"); ax[1].plot(fs, S11_true, "k", lw=1.2, label="simulated 8.75 mm")

for L, (a, b, c) in res.items():
    lab = f"extrapolated from {L:g} mm" if L != LT else "line model of 8.75 mm itself"
    ax[0].plot(fs, a, color=C[L], lw=1.2, label=lab); ax[1].plot(fs, b, color=C[L], lw=1.0, label=lab); ax[2].plot(fe, c, color=C[L], lw=1.3, label=lab)
ax[0].set_ylim(-6, 0); ax[1].set_ylim(-50, 0); ax[2].set_ylim(-6, 1)
for a_, t in zip(ax, ("|S21| (dB)", "|S11| (dB)", "EO response (dB, ref 3-10.7 GHz)")):
    a_.set_xlim(0, 60); a_.set_xlabel("frequency (GHz)"); a_.set_ylabel(t); a_.grid(alpha=0.3)
ax[0].legend(frameon=False, fontsize=8); fig.suptitle("Istanbul line A: length extrapolation to 8.75 mm from each simulated length", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "length_extrapolation_check.png"), dpi=170)
