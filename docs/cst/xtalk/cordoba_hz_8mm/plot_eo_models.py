"""CORDOBA HZ, 8 mm: FEXT |S41| (s4p), EO crosstalk B/A from the gap fields (12 monitor points, exact for
the TD model) and EO crosstalk from the two-CPW-mode equivalent line extracted from the same s4p
(pair-even/pair-odd lines, the GUI's "Crosstalk from s4p" model; variants "Ze = Zo (forward waves)" and
"exact terminals"). All at 50 ohm source and load, push-pull, optical n_g 2.27."""
import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
import numpy as np, skrf, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_s4p as X, xtalk_fields as XF
HERE = os.path.dirname(os.path.abspath(__file__))
S4P = os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_NARROW.s4p")
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6a64", "#e4e3de", "#fcfcfb"
C_FEXT, C_FIELD, C_EQ, C_FULL = "#eb6834", "#1f1f1e", "#2a78d6", "#1baf7a"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.facecolor": SURF, "figure.facecolor": SURF, "axes.grid": True,
                     "grid.color": GRID, "grid.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False})
d = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0; p["f_max_GHz"] = 60.0
pair = X.load_pair(S4P, 8.0)
net = skrf.Network(S4P)
fld = XF.eo_crosstalk_fields(p, XF.load_field_dir(HERE), pair)
dev = X.device_crosstalk_s4p(p, pair)
fm = dev["f_GHz"]
xeq = dev["eq"]["resp"]["H_B"] / dev["eq"]["resp"]["H_A"]
xfu = dev["full"]["resp"]["H_B"] / dev["full"]["resp"]["H_A"]
fig, a = plt.subplots(figsize=(10, 5.5))
a.plot(net.f / 1e9, d(net.s[:, 3, 0]), color=C_FEXT, lw=2, label="FEXT |S41| (s4p)")
a.plot(fm, d(xeq), color=C_EQ, lw=2, label="EO, two-CPW-mode line from the s4p: Ze = Zo (forward waves)")
a.plot(fm, d(xfu), color=C_FULL, lw=2, label="EO, two-CPW-mode line from the s4p: exact terminals")
a.plot(fld["f_GHz"], d(fld["X"]), "o", color=C_FIELD, ms=8, mec=SURF, mew=2, label="EO from the CST gap fields (exact, monitor points)")
a.set_xlim(0, 60); a.set_ylim(-85, -20)
a.set_xlabel("Frequency (GHz)"); a.set_ylabel("dB (amplitude ratio)")
a.set_title("CORDOBA high impedance, 8 mm (signal 10 µm, grounds 25 µm): EO crosstalk B/A and FEXT\n"
            "(50 Ω source and load, push-pull, optical n_g 2.27)", loc="left", color=INK, fontsize=10)
a.legend(frameon=False, loc="lower right", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_models_hz.png"), dpi=150)
print(" f GHz | fields | Ze=Zo  (diff) | exact terminals (diff) | FEXT")
for i, g in enumerate(fld["f_GHz"]):
    j = np.argmin(abs(fm - g)); k = np.argmin(abs(net.f / 1e9 - g))
    F = d(fld["X"][i]); E = d(xeq[j]); U = d(xfu[j])
    print(f" {g:5.0f} | {F:6.1f} | {E:6.1f} ({E-F:+5.1f}) | {U:6.1f} ({U-F:+5.1f})          | {d(net.s[k,3,0]):6.1f}")
