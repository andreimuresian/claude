"""Figures for report topic 1 (field-based EO crosstalk), from the CORDOBA 8 mm TD fields."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(HERE, "../../cst/xtalk")
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"; B1, B2, B3 = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False})
C0 = 2.99792458e8
fd = XF.load_field_dir(os.path.join(X, "cordoba_8mm")); z = fd["z"]; F = fd["ports"][30.0][1]
# V+ ~ Ey(+ side), V- ~ -Ey(- side); CPW pattern drives push-pull: (V+ + V-)/2
VA = (F["A"][0] - F["A"][1]) / 2; VB = (F["B"][0] - F["B"][1]) / 2
ref = np.max(abs(VA))
# Fig 2: push-pull gap field (E_y at the sample point) along the line, A and B
fig, a = plt.subplots(figsize=(8, 3.6))
a.plot(z * 1e3, 20 * np.log10(abs(VA) / ref), color=B1, lw=1.2, label="line A (driven)")
a.plot(z * 1e3, 20 * np.log10(abs(VB) / ref + 1e-12), color=B2, lw=1.2, label="line B (victim)")
a.set_xlabel("z along the line (mm)"); a.set_ylabel("|E+ + E-| at sample point\n(dB re max of A)"); a.set_xlim(0, 8); a.set_ylim(-110, 5)
a.legend(frameon=False, loc="lower left"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "f2_voltage.png"), dpi=150)
# Fig 3: running EO integral, synthetic forward / backward / mismatched waves (8 mm, 30 GHz)
L = 8e-3; zz = np.linspace(0, L, 2000); k0 = 2 * np.pi * 30e9 / C0; bo = k0 * 2.27
cases = [("forward wave, same speed as the light (n = 2.27)", np.exp(-1j * bo * zz), B1),
         ("forward wave, slower than the light (n = 3.0)", np.exp(-1j * k0 * 3.0 * zz), B3),
         ("backward wave (n = 2.27, travelling toward z = 0)", np.exp(+1j * bo * zz), B2)]
fig, a = plt.subplots(figsize=(8, 3.6))
for lab, v, c in cases:
    run = np.concatenate([[0], np.cumsum((v[1:] * np.exp(1j * bo * zz[1:]) + v[:-1] * np.exp(1j * bo * zz[:-1])) / 2 * np.diff(zz))]) / L
    a.plot(zz * 1e3, abs(run), color=c, lw=2, label=lab)
a.set_xlabel("distance travelled by the light (mm)"); a.set_ylabel("accumulated modulation\n(1 = full field, whole line)")
a.set_xlim(0, 8); a.set_ylim(0, 1.05); a.legend(frameon=False, loc="upper left", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "f3_matching.png"), dpi=150)
# Fig 4: EO crosstalk vs f, both CORDOBA runs
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
fig, a = plt.subplots(figsize=(8, 3.6))
for lab, path, c in (("CORDOBA (signal 35 µm)", "cordoba_8mm", B1), ("CORDOBA high impedance (signal 10 µm)", "cordoba_hz_8mm", B2)):
    r = XF.eo_crosstalk_fields(p, XF.load_field_dir(os.path.join(X, path)))
    y = 20 * np.log10(abs(r["X"]))
    a.plot(r["f_GHz"], y, "o", color=c, ms=7, mec=SURF, mew=1.5, label=lab); a.plot(r["f_GHz"], y, ":", color=c, lw=1)
a.set_xlabel("frequency (GHz)"); a.set_ylabel("EO crosstalk B/A (dB)"); a.set_xlim(0, 62)
a.legend(frameon=False, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "f4_xtalk.png"), dpi=150)
# numbers quoted in the text
def H(v, ng): return np.trapezoid(v * np.exp(1j * 2 * np.pi * 30e9 * ng / C0 * (z - z[-1])), z) / (z[-1] - z[0])
print("30 GHz: |H_A|/ref", abs(H(VA, 2.27)) / ref, " |H_B|/|H_A| dB", 20 * np.log10(abs(H(VB, 2.27)) / abs(H(VA, 2.27))))
print("max|V_B|/max|V_A| dB", 20 * np.log10(np.max(abs(VB)) / ref))
print("backward wave rel. modulation", abs(2 / ((bo + bo) * L)))
