"""Istanbul line A (ports 1, 2; line B ports in 50 ohm): extrapolation to 10 mm.
Two-line method (5 + 8.75 mm): with identical ends E, the ABCD matrices are T_L = E1 Tline(L) E2, so
M = T_8.75 T_5^-1 = E1 Tline(3.75) E1^-1 and T_10 = M^(1/3) T_8.75 = E1 Tline(10) E2: the CST ends appear once, the line
is exact, no line model or Zc needed. Eigenvalues of M = exp(-+gamma 3.75 mm) give gamma free of end effects.
Single-line method (GUI): alpha, n_m, Zc from one length (extract_line_fit), uniform line of 10 mm between 50 ohm.
Check of the two-line method: (3 + 5) -> 8.75 mm against the simulated 8.75 mm.
Caveats: 3/5 mm and 1/8.75 mm are two mesh/port families (four_lengths_results.md); 5 + 8.75 mixes them.
The two-line result is singular where the length difference is a multiple of half a wavelength (19, 38, 57 GHz for
3.75 mm): spikes there are the method, not the line. Two-line alpha is noisy point to point; smoothed for the EO."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import eo_transfer, C0
FILES = {1.0: "ISTANBUL_SW_1p00mm.s4p", 3.0: "TEST0_XTALK_SW__3p00mm.s4p", 5.0: "TEST0_XTALK_SW_5mm.s4p", 8.75: "ISTANBUL_SW_8p75mm.s4p"}
Z0 = 50.0; tmp = tempfile.mkdtemp()
net = {L: rf.Network(os.path.join(HERE, fn)).subnetwork([0, 1]) for L, fn in FILES.items()}
F = net[5.0].f / 1e9; k = (F >= 1) & (F <= 60); f = F[k]
def s2a(s):
    s11, s12, s21, s22 = s[:, 0, 0], s[:, 0, 1], s[:, 1, 0], s[:, 1, 1]
    A = ((1 + s11) * (1 - s22) + s12 * s21) / (2 * s21); B = Z0 * ((1 + s11) * (1 + s22) - s12 * s21) / (2 * s21)
    C = ((1 - s11) * (1 - s22) - s12 * s21) / (2 * s21 * Z0); D = ((1 - s11) * (1 + s22) + s12 * s21) / (2 * s21)
    return np.stack([np.stack([A, B], -1), np.stack([C, D], -1)], -2)
def a2s(T):
    A, B, C, D = T[:, 0, 0], T[:, 0, 1], T[:, 1, 0], T[:, 1, 1]; d = A + B / Z0 + C * Z0 + D
    return np.stack([np.stack([(A + B / Z0 - C * Z0 - D) / d, 2 * (A * D - B * C) / d], -1), np.stack([2 / d, (-A + B / Z0 - C * Z0 + D) / d], -1)], -2)
T = {L: s2a(n.s[k]) for L, n in net.items()}
def two_line(La, Lb, Lt):
    """gamma from (La < Lb) and T at Lt = M^p T_Lb, p = (Lt - Lb)/(Lb - La)."""
    M = T[Lb] @ np.linalg.inv(T[La]); dL = (Lb - La) * 1e-3
    w, V = np.linalg.eig(M)
    g = -np.log(w) / dL                         # two eigenvalues: exp(-gamma dL), exp(+gamma dL)
    i = np.argmax(g.real, axis=1); j = 1 - i     # forward wave: Re(gamma) > 0
    gf = g[np.arange(len(f)), i]
    beta = np.unwrap(-np.angle(w[np.arange(len(f)), i])) / dL  # unwrap the phase over frequency
    beta += 2 * np.pi * np.round((2 * np.pi * f * 1e9 * 2.1 / C0 - beta)[0] / (2 * np.pi / dL)) / dL * 0
    gam = gf.real + 1j * beta
    p = (Lt - Lb) / (Lb - La)
    lam = np.zeros((len(f), 2), complex)
    lam[np.arange(len(f)), i] = np.exp(-gam * dL * p); lam[np.arange(len(f)), j] = np.exp(gam * dL * p)
    Mp = V @ (lam[:, :, None] * np.linalg.inv(V))
    return gam, a2s(Mp @ T[Lb])
def single(L, Lt, ff=None):
    n = net[L]; p = os.path.join(tmp, f"A{int(L*100)}"); n.write_touchstone(p); fit = extract_line_fit(p + ".s2p", L)
    ff = f if ff is None else ff
    g = fit.alpha_dB_cm(ff) * 100 / 8.686 + 1j * 2 * np.pi * ff * 1e9 * fit.nm(ff) / C0; zc = fit.Zc(ff); gl = g * Lt * 1e-3
    den = 2 * zc * Z0 * np.cosh(gl) + (zc ** 2 + Z0 ** 2) * np.sinh(gl)
    return fit, (zc ** 2 - Z0 ** 2) * np.sinh(gl) / den, 2 * zc * Z0 / den
dB = lambda x: 20 * np.log10(abs(x)); ph = lambda x: np.degrees(np.unwrap(np.angle(x)))
at = lambda y, q: y[np.argmin(abs(f - q))]
# check of the two-line method on a simulated length
g35, S875 = two_line(3.0, 5.0, 8.75); s = net[8.75].s[k]
print("check (3+5 -> 8.75 vs simulated 8.75): |S21| err at 30/60 GHz %+.3f %+.3f dB, phase err %+.1f %+.1f deg, |S11| rms %.2f dB" % (
      at(dB(S875[:, 1, 0]) - dB(s[:, 1, 0]), 30), at(dB(S875[:, 1, 0]) - dB(s[:, 1, 0]), 60),
      at(ph(S875[:, 1, 0]) - ph(s[:, 1, 0]), 30), at(ph(S875[:, 1, 0]) - ph(s[:, 1, 0]), 60), np.sqrt(np.mean((dB(S875[:, 0, 0]) - dB(s[:, 0, 0])) ** 2))))
g58, S10 = two_line(5.0, 8.75, 10.0)
nm2 = lambda g: g.imag * C0 / (2 * np.pi * f * 1e9); al2 = lambda g: g.real * 8.686 / 100
print("\nline parameters at 30 / 60 GHz:   n_m            alpha (dB/cm)")
print("  two-line 5 + 8.75 mm     %.4f %.4f   %.3f %.3f" % (at(nm2(g58), 30), at(nm2(g58), 60), at(al2(g58), 30), at(al2(g58), 60)))
print("  two-line 3 + 5 mm        %.4f %.4f   %.3f %.3f" % (at(nm2(g35), 30), at(nm2(g35), 60), at(al2(g35), 30), at(al2(g35), 60)))
fits = {}
for L in (3.0, 5.0, 8.75):
    fit, s11, s21 = single(L, 10.0); fits[L] = (fit, s11, s21)
    print("  single %5.2f mm (fit)    %.4f %.4f   %.3f %.3f   Re Zc %.1f %.1f" % (L, *fit.nm(np.array([30., 60.])), *fit.alpha_dB_cm(np.array([30., 60.])), *fit.Zc(np.array([30., 60.])).real))
print("\n10 mm, single-line extrapolation minus two-line (5 + 8.75):")
print("  from    |S21| at 30/60 GHz (dB)   S21 phase at 30/60 (deg)   |S11| rms 1-60 (dB)   EO at 30/60 (dB)")
fe = np.arange(1.0, 60.01, 0.25); REF = (fe >= 3) & (fe <= 10.7)
zref = fits[8.75][0].Zc(fe)
def eo(al, nm):
    H, _ = eo_transfer(fe, al, nm, zref, 10e-3, 2.27, 50.0, 50.0); return 20 * np.log10(abs(H) / np.mean(abs(H[REF])))
from scipy.signal import savgol_filter
def smooth(g):
    """two-line alpha is noisy point to point (the loss over 3.75 mm is ~1-2 dB): least-squares a sqrt f + b f + c;
    n_m: Savitzky-Golay, 81 points (6.4 GHz), order 2."""
    A = np.c_[np.sqrt(f), f, np.ones_like(f)]; c, *_ = np.linalg.lstsq(A, al2(g), rcond=None)
    return np.interp(fe, f, A @ c), np.interp(fe, f, savgol_filter(nm2(g), 81, 2))
eo2 = eo(*smooth(g58))
print("two-line pairs, medians over 25-35 GHz (alpha dB/cm +- std point to point, n_m): " + "; ".join(
    f"{a:g}+{b:g}: {np.median(al2(two_line(a, b, 10.0)[0])[(f >= 25) & (f < 35)]):.2f} +- {np.std(al2(two_line(a, b, 10.0)[0])[(f >= 25) & (f < 35)]):.2f}, "
    f"{np.median(nm2(two_line(a, b, 10.0)[0])[(f >= 25) & (f < 35)]):.4f}" for a, b in ((5.0, 8.75), (3.0, 5.0), (1.0, 8.75), (3.0, 8.75))))
ae = lambda y, q: y[np.argmin(abs(fe - q))]
out = {}
for L, (fit, s11, s21) in fits.items():
    e1 = eo(fit.alpha_dB_cm(fe), fit.nm(fe)) - eo2; out[L] = (s21, s11, e1)
    print(f"  {L:5.2f}   {at(dB(s21) - dB(S10[:, 1, 0]), 30):+.3f} {at(dB(s21) - dB(S10[:, 1, 0]), 60):+.3f}          "
          f"{at(ph(s21) - ph(S10[:, 1, 0]), 30):+6.1f} {at(ph(s21) - ph(S10[:, 1, 0]), 60):+6.1f}              "
          f"{np.sqrt(np.mean((dB(s11) - dB(S10[:, 0, 0])) ** 2)):.2f}                {ae(e1, 30):+.3f} {ae(e1, 60):+.3f}")
print("  (EO: same Zc, 50/50 ohm, n_g 2.27; only alpha and n_m differ)")
fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
ax[0].plot(f, dB(S10[:, 1, 0]), "k", lw=2.2, label="two-line (5 + 8.75 mm)"); ax[1].plot(f, dB(S10[:, 0, 0]), "k", lw=1.6, label="two-line (5 + 8.75 mm)")
C = {3.0: "#1baa7d", 5.0: "#7a4bd1", 8.75: "#2a78d6"}
for L, (s21, s11, e1) in out.items():
    ax[0].plot(f, dB(s21), color=C[L], lw=1.2, label=f"single line {L:g} mm"); ax[1].plot(f, dB(s11), color=C[L], lw=1.0, label=f"single line {L:g} mm")
    ax[2].plot(f, ph(s21) - ph(S10[:, 1, 0]), color=C[L], lw=1.4, label=f"single line {L:g} mm")
ax[0].set_ylim(-6, 0); ax[1].set_ylim(-50, 0); ax[2].axhline(0, color="k", lw=0.8)
for a_, t in zip(ax, ("|S21| at 10 mm (dB)", "|S11| at 10 mm (dB)", "S21 phase error vs two-line (deg)")):
    a_.set_xlim(0, 60); a_.set_xlabel("frequency (GHz)"); a_.set_ylabel(t); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle("Istanbul line A extrapolated to 10 mm: two-line de-embedding (5 + 8.75 mm) vs single-line extraction", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "two_line_vs_single.png"), dpi=170)
