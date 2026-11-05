"""
One measured CORDOBA 8 mm line, before and after the 40 nm Al2O3 (ALD) layer: RF index n_m, characteristic impedance
Z0 (real part) and attenuation, de-embedded with the MZM Studio extractor (mzm_interconnect.extractor.extract_line_fit:
ABCD -> gamma, Zc; per-unit-length values divided by the measured length).

Usage: python3 compare_line.py <no_ALD.s2p> <ALD.s2p> [label] [L_mm]
Assumption: line length 8 mm (pads included in the measured 2-port; they bias n_m, Z0 and alpha in the same way before
and after ALD, so the differences are what this script reports with confidence).
Output: <label>_compare.png and a table of values at 10..50 GHz and band averages of the differences.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.extractor import extract_line_fit

f_no, f_ald = sys.argv[1], sys.argv[2]
label = sys.argv[3] if len(sys.argv) > 3 else "line"
L_mm = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0
fits = {"no ALD": extract_line_fit(f_no, L_mm), "ALD": extract_line_fit(f_ald, L_mm)}
nets = {"no ALD": rf.Network(f_no), "ALD": rf.Network(f_ald)}
col = {"no ALD": "#2a78d6", "ALD": "#eb6834"}

raw = {k: (v.raw_f_GHz, v.raw_nm, np.real(v.raw_Zc), v.raw_alpha_dB_cm) for k, v in fits.items()}
f = raw["no ALD"][0]
assert np.allclose(f, raw["ALD"][0]), "frequency grids differ"
names = ("n_m", "Re Z0 (ohm)", "alpha (dB/cm)")
print(f"{label}: L = {L_mm} mm, {len(f)} points {f[0]:.2f}-{f[-1]:.1f} GHz")
print("   f GHz | " + " | ".join(f"{n:>13s} noALD / ALD / diff" for n in names))
for fq in (10, 20, 30, 40, 50):
    i = np.argmin(abs(f - fq)); row = []
    for j in range(3):
        a, b = raw["no ALD"][j + 1][i], raw["ALD"][j + 1][i]; row.append(f"{a:8.3f} {b:8.3f} {b - a:+7.3f}")
    print(f"   {fq:5d} | " + " | ".join(row))
band = (f >= 5) & (f <= 50)
print("band 5-50 GHz, median difference ALD - no ALD: " + ", ".join(
    f"{n} {np.median(raw['ALD'][j + 1][band] - raw['no ALD'][j + 1][band]):+.4f}" for j, n in enumerate(names)))

fig, ax = plt.subplots(4, 2, figsize=(11, 12), sharex=True)
for k, n in nets.items():
    fn = n.f / 1e9
    ax[0, 0].plot(fn, 20 * np.log10(abs(n.s[:, 1, 0])), color=col[k], lw=1.2, label=k)
    ax[0, 1].plot(fn, 20 * np.log10(abs(n.s[:, 0, 0])), color=col[k], lw=1.2, label=k)
ax[0, 0].set_ylabel("|S21| (dB)"); ax[0, 1].set_ylabel("|S11| (dB)")
for j, n in enumerate(names):
    a = ax[j + 1, 0]; d = ax[j + 1, 1]
    for k in raw:
        a.plot(f, raw[k][j + 1], color=col[k], lw=1.1, label=k)
    d.plot(f, raw["ALD"][j + 1] - raw["no ALD"][j + 1], color="0.25", lw=1.0)
    d.axhline(0, color="0.6", lw=0.8)
    a.set_ylabel(n); d.set_ylabel("ALD - no ALD: " + n)
ax[1, 0].set_ylim(np.percentile(raw["no ALD"][1][band], 1) - 0.1, np.percentile(raw["no ALD"][1][band], 99) + 0.1)
for a in ax.ravel():
    a.grid(alpha=0.3)
ax[0, 0].legend(frameon=False); ax[-1, 0].set_xlabel("frequency (GHz)"); ax[-1, 1].set_xlabel("frequency (GHz)")
fig.suptitle(f"CORDOBA 8 mm, {label}: before vs after 40 nm Al2O3 (de-embedded per unit length, L = {L_mm} mm)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, f"{label}_compare.png"), dpi=150)
