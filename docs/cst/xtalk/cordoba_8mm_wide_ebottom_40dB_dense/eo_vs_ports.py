"""EO crosstalk (gap fields, 50/50 ohm, push-pull, n_g 2.27) of the dense -40 dB run vs its FEXT (S41) and NEXT (S31),
and FEXT/2 (velocity-matched forward coupling growing linearly along the line: the EO average of B is half its end value)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
fd = XF.load_field_dir(os.path.join(HERE, "unpacked")); X = XF.eo_crosstalk_fields(p, fd); f = X["f_GHz"]
n = rf.Network(os.path.join(HERE, "LINEA_8MM_625UM_PITCH_CORDOBA_OAD_1port_E-fondo -minus 40 dB.s4p"))
fs = n.f / 1e9; s41 = n.s[:, 3, 0]; s31 = n.s[:, 2, 0]
eo = 20 * np.log10(abs(X["X"])); fx = np.interp(f, fs, 20 * np.log10(abs(s41))); nx = np.interp(f, fs, 20 * np.log10(abs(s31)))
d = eo - fx
print("EO - FEXT (dB): median %.1f, 5-95%% range %.1f .. %.1f; correlation of dB curves 5-60 GHz: %.2f; NEXT: %.2f"
      % (np.median(d[f >= 5]), *np.percentile(d[f >= 5], [5, 95]), np.corrcoef(eo[f >= 5], fx[f >= 5])[0, 1], np.corrcoef(eo[f >= 5], nx[f >= 5])[0, 1]))
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(fs, 20 * np.log10(abs(s41)), color="#eb6834", lw=1.2, label="FEXT |S41| (port data)")
ax.plot(fs, 20 * np.log10(abs(s41)) - 6.02, color="#eb6834", lw=0.9, ls=":", label="FEXT - 6 dB")
ax.plot(fs, 20 * np.log10(abs(s31)), color="0.55", lw=1.0, label="NEXT |S31| (port data)")
ax.plot(f, eo, "o-", color="#2a78d6", ms=3, lw=1.4, label="EO crosstalk B/A (gap fields)")
ax.set_xlim(0, 60); ax.set_ylim(-110, -40); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("dB"); ax.grid(alpha=0.3)
ax.set_title("CORDOBA 8 mm widened, electric bottom, -40 dB run: EO crosstalk vs FEXT and NEXT", fontsize=10)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_vs_fext_next.png"), dpi=150)
