"""Physical model of the bend block (raised taper + arc + raised taper), fitted to the L+B+S 2-port outside the
ground-mode resonances. The block is a uniform line section with its own impedance Zb and propagation
    theta(f) = [a sqrt(f/GHz) + b (f/GHz)] / 8.686  +  j w tau        (conductor + dielectric loss, constant delay)
referenced to the line impedance Zc(f) of the L+S run on both sides:
    S21 = 2 Zb Zc / D,  S11 = (Zb^2 - Zc^2) sinh(theta) / D,  D = 2 Zb Zc cosh(theta) + (Zb^2 + Zc^2) sinh(theta).
Four real parameters (a, b, tau, Zb), least squares on complex S21 and S11 over 1-80 GHz, resonance bands excluded.
Compared with the cubic-polynomial smoothing of cascade_test.py.
Outputs: bend_physical.npz (model S on the touchstone grid), bend_physical.png, printed parameters."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
with contextlib.redirect_stdout(io.StringIO()):
    ct = runpy.run_path(os.path.join(HERE, "cascade_test.py"))
f, S, Ss, Z, ok = ct["f"], ct["S"], ct["Ss"], ct["Z"], ct["ok"]
w = 2 * np.pi * f * 1e9
def model(p, ff=f, ZZ=Z):
    a, b, tau, Zb = p; th = (a * np.sqrt(ff) + b * ff) / 8.686 + 1j * 2 * np.pi * ff * 1e9 * tau * 1e-12
    D = 2 * Zb * ZZ * np.cosh(th) + (Zb**2 + ZZ**2) * np.sinh(th)
    return 2 * Zb * ZZ / D, (Zb**2 - ZZ**2) * np.sinh(th) / D
m = ok & (f >= 1.0)
def res(p):
    s21, s11 = model(p); return np.concatenate([(s21[m] - S[m, 1, 0]).real, (s21[m] - S[m, 1, 0]).imag,
                                                (s11[m] - S[m, 0, 0]).real, (s11[m] - S[m, 0, 0]).imag])
p = least_squares(res, [0.01, 0.003, 5.05, 44.0]).x
s21p, s11p = model(p)
print(f"bend model: loss = {p[0]:.4f} sqrt(f) + {p[1]:.5f} f dB (f in GHz) -> {p[0]*np.sqrt(20)+p[1]*20:.3f} / {p[0]*np.sqrt(60)+p[1]*60:.3f} dB at 20 / 60 GHz;"
      f" delay {p[2]:.3f} ps; Zb = {p[3]:.2f} ohm (line Zc ~ {Z[np.argmin(abs(f-30))].real:.1f} ohm)")
dB = lambda x: 20 * np.log10(abs(x))
for lab, s21, s11 in (("polynomial", Ss[:, 1, 0], Ss[:, 0, 0]), ("physical", s21p, s11p)):
    print(f"{lab:10s} fit vs measured bend outside resonances: |S21| rms {np.sqrt(np.mean((dB(s21[m]) - dB(S[m,1,0]))**2)):.4f} dB,"
          f" |S11| rms {np.sqrt(np.mean((abs(s11[m]) - abs(S[m,0,0]))**2)):.4f}, complex S11 rms {np.sqrt(np.mean(abs(s11[m] - S[m,0,0])**2)):.4f}")
Sp = np.zeros_like(S); Sp[:, 0, 0] = Sp[:, 1, 1] = s11p; Sp[:, 1, 0] = Sp[:, 0, 1] = s21p
np.savez(os.path.join(HERE, "bend_physical.npz"), f=f, S=Sp, params=p)
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
ax[0].plot(f, dB(S[:, 1, 0]), color="0.6", lw=1, label="L+B+S bend, measured"); ax[0].plot(f, dB(Ss[:, 1, 0]), "--", color="#2a78d6", label="polynomial")
ax[0].plot(f, dB(s21p), "-", color="#eb6834", lw=1.4, label="physical model"); ax[0].set_ylabel("|S21| (dB)"); ax[0].set_ylim(-0.9, 0.1)
ax[1].plot(f, abs(S[:, 0, 0]), color="0.6", lw=1, label="measured"); ax[1].plot(f, abs(Ss[:, 0, 0]), "--", color="#2a78d6", label="polynomial")
ax[1].plot(f, abs(s11p), "-", color="#eb6834", lw=1.4, label="physical model"); ax[1].set_ylabel("|S11|"); ax[1].set_ylim(0, 0.08)
ax[2].plot(S[m, 0, 0].real, S[m, 0, 0].imag, ".", ms=2, color="0.6", label="measured (outside resonances)")
ax[2].plot(Ss[:, 0, 0].real, Ss[:, 0, 0].imag, "--", color="#2a78d6", label="polynomial"); ax[2].plot(s11p.real, s11p.imag, "-", color="#eb6834", label="physical model")
ax[2].set_xlabel("Re S11"); ax[2].set_ylabel("Im S11"); ax[2].set_aspect("equal")
for a_ in ax[:2]: a_.set_xlabel("frequency (GHz)")
for a_ in ax: a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle(f"Bend block: physical model (line section, Zb = {p[3]:.1f} Ω, delay {p[2]:.2f} ps) vs polynomial smoothing", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "bend_physical.png"), dpi=200)
