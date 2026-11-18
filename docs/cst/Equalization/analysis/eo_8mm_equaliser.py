"""EO -3 dB bandwidth: straight 8 mm line vs equaliser 8 (+) | bend | 4 (+) | bend | 4 (-).
Line: alpha, n_m, Zc from the L+S touchstone extraction (physical fits, so the curves extend past the 80 GHz of
the touchstone; above 80 GHz = extrapolation). Bend: physical block of bend_physical.py (a, b, tau, Zb).
50 ohm source and load, n_g 2.27, light delay in each bend matched to the RF bend delay tau.
EO: H = sum_k p_k int V_k(s) exp(j w t_opt(s)) ds. Two normalisations: each curve re its own 1 GHz value, and
both re the straight line at 1 GHz (absolute efficiency; at DC the equaliser is 8 + 4 - 4 = 8 mm, as the line).
Outputs: eo_8mm_equaliser.png, .csv, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0, fit_alpha_scaled, fit_impedance_physical, fit_impedance_imag, fit_nm_saturating
fit = extract_line_fit(os.path.join(HERE, "../L+S/BASELINE_LS.s2p"), 3.24)
NG, ZS, ZL = 2.27, 50.0, 50.0
F = np.arange(0.5, 130.01, 0.5); w = 2 * np.pi * F * 1e9
g = fit_alpha_scaled(F, *fit.popt_alpha) * 100 / 8.686 + 1j * fit_nm_saturating(F, *fit.popt_nm) * w / C0
Z = fit_impedance_physical(F, *fit.popt_zre) + 1j * fit_impedance_imag(F, *fit.popt_zim)
a, b, tau, Zb = np.load(os.path.join(HERE, "bend_physical.npz"))["params"][:4]
thb = (a * np.sqrt(F) + b * F) / 8.686 + 1j * w * tau * 1e-12
def T(gl, Zc):
    return np.array([[np.cosh(gl), Zc * np.sinh(gl)], [np.sinh(gl) / Zc, np.cosh(gl)]]).transpose(2, 0, 1)
BEND = T(thb, np.full(len(F), Zb + 0j))

def eo(sections, ds=10e-6):
    """sections: list of (length m, polarity); a bend between consecutive sections."""
    Tt = np.broadcast_to(np.eye(2, dtype=complex), (len(F), 2, 2)).copy()
    for j, (L, _) in enumerate(sections):
        Tt = Tt @ T(g * L, Z)
        if j < len(sections) - 1: Tt = Tt @ BEND
    Zin = (Tt[:, 0, 0] * ZL + Tt[:, 0, 1]) / (Tt[:, 1, 0] * ZL + Tt[:, 1, 1])
    V, I = Zin / (Zin + ZS), 1 / (Zin + ZS); t0 = np.zeros(len(F)); H = np.zeros(len(F), complex)
    for j, (L, p) in enumerate(sections):
        s = np.arange(0, L + ds / 2, ds)[:, None]
        Vs = V * np.cosh(g * s) - Z * I * np.sinh(g * s)          # inverse ABCD of a line of length s
        H += p * np.trapezoid(Vs * np.exp(1j * w * (t0 + NG * s[:, 0, None] / C0)), s[:, 0], axis=0)
        V, I = (V * np.cosh(g * L) - Z * I * np.sinh(g * L), -V * np.sinh(g * L) / Z + I * np.cosh(g * L)); t0 += NG * L / C0
        if j < len(sections) - 1:
            V, I = (V * np.cosh(thb) - Zb * I * np.sinh(thb), -V * np.sinh(thb) / Zb + I * np.cosh(thb)); t0 += tau * 1e-12
    return H
i1 = np.argmin(abs(F - 1.0))
CASES = {"straight 8 mm": [(8e-3, +1)], "equaliser 8 (+) | 4 (+) | 4 (−)": [(8e-3, +1), (4e-3, +1), (4e-3, -1)]}
H = {k: eo(v) for k, v in CASES.items()}; ref = abs(H["straight 8 mm"][i1])
own = {k: 20 * np.log10(abs(h) / abs(h[i1])) for k, h in H.items()}
absd = {k: 20 * np.log10(abs(h) / ref) for k, h in H.items()}
def bw(y):
    k = np.where(y[i1:] < -3)[0]; return F[i1 + k[0]] if len(k) else np.nan
print(f"line fit: n_m(1 GHz) {fit_nm_saturating(1, *fit.popt_nm):.3f}, alpha(60) {fit_alpha_scaled(60, *fit.popt_alpha):.2f} dB/cm, Re Zc(60) {fit_impedance_physical(60, *fit.popt_zre):.1f} ohm")
for k in H:
    print(f"{k:34s}: -3 dB re own 1 GHz {bw(own[k]):6.1f} GHz | re straight line 1 GHz {bw(absd[k]):6.1f} GHz | 1 GHz level re straight {absd[k][i1]:+.2f} dB")
print(" f GHz |" + " | ".join(f"{k} own / abs" for k in H))
for q in (10, 20, 30, 40, 50, 60, 70, 80, 100, 120):
    i = np.argmin(abs(F - q)); print(f"{q:5d}  | " + " | ".join(f"{own[k][i]:+.2f} / {absd[k][i]:+.2f}" for k in H))
np.savetxt(os.path.join(HERE, "eo_8mm_equaliser.csv"), np.column_stack([F] + [own[k] for k in H] + [absd[k] for k in H]),
           delimiter=",", fmt="%.5g", comments="", header="f_GHz,straight_own_dB,equaliser_own_dB,straight_abs_dB,equaliser_abs_dB")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.3)); col = {"straight 8 mm": "k", "equaliser 8 (+) | 4 (+) | 4 (−)": "#eb6834"}
for j, (dat, tt) in enumerate(((own, "re own 1 GHz value"), (absd, "re straight 8 mm line at 1 GHz"))):
    for k in H: ax[j].plot(F, dat[k], color=col[k], lw=1.5, label=f"{k}  (−3 dB at " + (f"{bw(dat[k]):.0f} GHz)" if bw(dat[k]) == bw(dat[k]) else "> 130 GHz)"))
    ax[j].axhline(-3, color="0.4", lw=0.8, ls=":"); ax[j].axvspan(80, 130, color="0.9", zorder=0)
    ax[j].text(82, 0.3, "extrapolated\n(touchstone ends at 80 GHz)", fontsize=7, va="top")
    ax[j].set_ylim(-8, 0.5); ax[j].set_xlim(0, 130); ax[j].set_title(f"EO response {tt}", fontsize=9)
    ax[j].set_xlabel("frequency (GHz)"); ax[j].set_ylabel("EO response (dB)"); ax[j].grid(alpha=0.3); ax[j].legend(frameon=False, fontsize=8, loc="lower left")
fig.suptitle("Straight 8 mm line vs equaliser 8 + 4 − 4 mm (L+S line model, physical bend, 50 Ω ports, n_g 2.27, light matched in the bends)", fontsize=9.5)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_8mm_equaliser.png"), dpi=200)
