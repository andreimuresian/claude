"""EO crosstalk from the gap fields: -27 dB run vs the run stopped at -44.5 dB (same model), and how much each line's
CPW gap pattern changed between them, absolute (in units of A's CPW rms) and relative to the line's own level."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from mzm_interconnect import parameters as P, xtalk_fields as XF
old, new = XF.load_field_dir(os.path.join(HERE, "../cordoba_8mm_wide_ebottom")), XF.load_field_dir(HERE)
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
f = old["f_GHz"]; Xo = XF.eo_crosstalk_fields(p, old)["X"]; Xn = XF.eo_crosstalk_fields(p, new)["X"]
cpw = lambda v: (v[0] - v[1]) / 2; rms = lambda v: np.sqrt(np.mean(abs(v) ** 2))
def pat(fd, ff, line):
    F = fd["ports"][ff][1]; return cpw(np.stack(F[line]))
chA, chB, absA, absB, levB = [], [], [], [], []
for ff in f:
    a0, a1, b0, b1 = pat(old, ff, "A"), pat(new, ff, "A"), pat(old, ff, "B"), pat(new, ff, "B")
    ref = rms(a1)
    chA.append(rms(a1 - a0) / rms(a1)); chB.append(rms(b1 - b0) / rms(b1))
    absA.append(20*np.log10(rms(a1 - a0) / ref)); absB.append(20*np.log10(rms(b1 - b0) / ref)); levB.append(20*np.log10(rms(b1) / ref))
print("f:", " ".join(f"{v:6.0f}" for v in f))
print("|dA|/|A| rel     :", " ".join(f"{v:6.3f}" for v in chA))
print("|dB|/|B| rel     :", " ".join(f"{v:6.2f}" for v in chB))
print("|dA| re A (dB)   :", " ".join(f"{v:6.1f}" for v in absA))
print("|dB| re A (dB)   :", " ".join(f"{v:6.1f}" for v in absB))
print("|B| re A (dB)    :", " ".join(f"{v:6.1f}" for v in levB))
fig, ax = plt.subplots(2, 1, figsize=(7.5, 7.2), sharex=True, gridspec_kw={"height_ratios": [1.3, 1]})
ff = np.linspace(f[0], f[-1], 400)
for X, lab, c in ((Xo, "accuracy -27 dB", "#eb6834"), (Xn, "accuracy target -60 dB, stopped at -44.5 dB", "#2a78d6")):
    y = 20 * np.log10(abs(X)); ax[0].plot(ff, PchipInterpolator(f, y)(ff), "--", color=c, lw=1.1)
    ax[0].plot(f, y, "o", color=c, ms=7, mec="white", mew=1.5, label=lab)
for x, y0, y1 in zip(f, 20*np.log10(abs(Xo)), 20*np.log10(abs(Xn))):
    ax[0].annotate(f"{y1-y0:+.0f}", (x, max(y0, y1) + 1.5), ha="center", fontsize=7.5, color="0.3")
ax[0].set_ylabel("EO crosstalk B/A (dB)"); ax[0].grid(alpha=0.3); ax[0].legend(frameon=False, loc="lower right", fontsize=8)
ax[0].set_title("Same CST model, two solver accuracies: EO crosstalk from the gap fields\n(numbers: change in dB; dashed: guide through the points only)", fontsize=9.5)
ax[1].semilogy(f, chA, "s-", color="#2a78d6", ms=5, label="line A (driven): change / own level")
ax[1].semilogy(f, chB, "o-", color="#eb6834", ms=5, label="line B (victim): change / own level")
ax[1].axhline(1, color="0.5", lw=0.8, ls=":")
ax[1].set_ylabel("|field(-44.5 dB) - field(-27 dB)| / |field|"); ax[1].set_xlabel("frequency (GHz)")
ax[1].grid(alpha=0.3, which="both"); ax[1].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "accuracy_eo_comparison.png"), dpi=150)
