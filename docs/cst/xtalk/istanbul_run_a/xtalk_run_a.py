"""Istanbul run (a): NEXT |S31|, FEXT |S41| (port data) and EO crosstalk B/A from the gap fields (50 ohm source and
load, push-pull, n_g 2.27: the same settings as the CORDOBA dense run, eo_vs_ports.py). Port 3 = line B near end
(z = 0.3), port 4 = far end: port_check.py. Caveat: line B gap fields sampled 5 um from the line centre, line A 7.5 um
(see load_fields.py), so the EO level may carry a sampling bias."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
X = XF.eo_crosstalk_fields(p, load()); f = X["f_GHz"]; eo = 20 * np.log10(abs(X["X"]))
n = rf.Network(os.path.join(HERE, "v0_istanbul_rf_line.s4p")); fs = n.f / 1e9
dB = lambda s: 20 * np.log10(np.maximum(abs(s), 1e-12))
nx_s, fx_s = dB(n.s[:, 2, 0]), dB(n.s[:, 3, 0])
nx, fx = np.interp(f, fs, nx_s), np.interp(f, fs, fx_s)
cor = np.loadtxt(os.path.join(HERE, "../cordoba_8mm_wide_ebottom_40dB_dense/dense_eo.csv"), delimiter=",", skiprows=1)
np.savetxt(os.path.join(HERE, "xtalk_run_a.csv"), np.c_[f, nx, fx, eo], delimiter=",", fmt="%.3f",
           header="f_GHz,NEXT_S31_dB,FEXT_S41_dB,EO_dB", comments="")
m = f >= 5; d = eo - fx
print("f (GHz) | NEXT | FEXT | EO   (dB)")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - q)); print(f"{q:3d} | {nx[i]:6.1f} | {fx[i]:6.1f} | {eo[i]:6.1f}")
for lab, y in (("NEXT", nx), ("FEXT", fx), ("EO", eo)):
    k = np.argmax(np.where(m, y, -999)); print(f"max {lab} 5-60 GHz: {y[k]:.1f} dB at {f[k]:.0f} GHz")
print("EO - FEXT (dB), 5-60 GHz: median %.1f, 5-95%% %.1f .. %.1f; corr(EO, FEXT) %.2f, corr(EO, NEXT) %.2f"
      % (np.median(d[m]), *np.percentile(d[m], [5, 95]), np.corrcoef(eo[m], fx[m])[0, 1], np.corrcoef(eo[m], nx[m])[0, 1]))
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(fs, nx_s, color="0.55", lw=1.0, label="NEXT |S31|")
ax.plot(fs, fx_s, color="#eb6834", lw=1.2, label="FEXT |S41|")
ax.plot(f, eo, "o-", color="#2a78d6", ms=3, lw=1.4, label="EO crosstalk B/A (gap fields)")
ax.plot(cor[:, 0], cor[:, 3], color="#2a78d6", lw=0.9, ls=":", label="EO, CORDOBA 8 mm dense run (reference)")
ax.set_xlim(0, 60); ax.set_ylim(-110, -20); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("dB"); ax.grid(alpha=0.3)
ax.set_title("Istanbul run (a), 8.75 mm, 625 um pitch, -40 dB: NEXT, FEXT and EO crosstalk", fontsize=10)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout()
fig.savefig(os.path.join(HERE, "xtalk_run_a.png"), dpi=150)
