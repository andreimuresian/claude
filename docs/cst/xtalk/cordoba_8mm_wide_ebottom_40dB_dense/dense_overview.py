"""Dense -40 dB run: (1) subvolume monitors vs the full-volume reference monitors at 5 and 10 GHz (same run);
(2) convergence at 5..60 GHz across -27, -40, -44.5 dB (B CPW pattern differences, EO); test of 'truncation error
scales with the tail amplitude' (amplitude ratios: -27 -> -40 dB 4.47, -40 -> -44.5 dB 1.68);
(3) dense EO 1-60 GHz (full line, 50/50 ohm, push-pull, n_g 2.27) with the other two runs; dense_eo.png."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
dn = XF.load_field_dir(os.path.join(HERE, "unpacked")); fv = XF.load_field_dir(os.path.join(HERE, "unpacked_fullvol"))
d27 = XF.load_field_dir(os.path.join(HERE, "../cordoba_8mm_wide_ebottom"))
d45 = XF.load_field_dir(os.path.join(HERE, "../cordoba_8mm_wide_ebottom_60dB"))
cpw = lambda v: (v[0] - v[1]) / 2; rms = lambda v: np.sqrt(np.mean(abs(v) ** 2))
def pat(fd, f, line):
    F = fd["ports"][f][1]; v = np.stack(F[line]); return cpw(v if line == "A" else np.stack([-v[1], -v[0]]))
print("(1) subvolume vs full-volume monitor, same run: |diff|/|field|")
for f in (5.0, 10.0):
    print(f"  {f:4.0f} GHz  A CPW {rms(pat(dn,f,'A')-pat(fv,f,'A'))/rms(pat(dn,f,'A')):.2e}   B CPW {rms(pat(dn,f,'B')-pat(fv,f,'B'))/rms(pat(dn,f,'B')):.2e}")
print("\n(2) B CPW pattern differences between accuracy levels, relative to B(-44.5):")
print("  f  | |B40-B27| | |B45-B40| | ratio (expected 4.47-1)/(1.68-1) = 5.1 if error ~ amplitude | |B45-B27|")
F12 = d27["f_GHz"]
for f in F12:
    b27, b40, b45 = pat(d27, f, "B"), pat(dn, f, "B"), pat(d45, f, "B"); r = rms(b45)
    a, b = rms(b40 - b27) / r, rms(b45 - b40) / r
    print(f"  {f:3.0f} | {a:6.3f} | {b:6.3f} | {a/b:5.1f} | {rms(b45-b27)/r:6.3f}")
Xd = XF.eo_crosstalk_fields(p, dn); X27 = XF.eo_crosstalk_fields(p, d27)["X"]; X45 = XF.eo_crosstalk_fields(p, d45)["X"]
fD = Xd["f_GHz"]; yD = 20 * np.log10(abs(Xd["X"]))
print("\n(3) EO (dB) at 5..60 GHz:  -27: " + " ".join(f"{20*np.log10(abs(x)):6.1f}" for x in X27))
print("                          -40: " + " ".join(f"{yD[np.argmin(abs(fD-f))]:6.1f}" for f in F12))
print("                        -44.5: " + " ".join(f"{20*np.log10(abs(x)):6.1f}" for x in X45))
np.savetxt(os.path.join(HERE, "dense_eo.csv"), np.c_[fD, Xd["X"].real, Xd["X"].imag, yD], delimiter=",",
           header="f_GHz,ReX,ImX,X_dB  (EO B/A, full line, 50/50 ohm, push-pull, n_g 2.27; -40 dB run)")
fig, ax = plt.subplots(figsize=(8, 4.4))
ax.plot(fD, yD, "-o", color="#2a78d6", ms=3, lw=1.3, label="-40 dB run, monitors every 1 GHz")
ax.plot(F12, 20*np.log10(abs(X45)), "s", color="#1a9e5c", ms=7, mec="white", label="-44.5 dB run (stopped)")
ax.plot(F12, 20*np.log10(abs(X27)), "o", color="#eb6834", ms=7, mec="white", label="-27 dB run")
ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk B/A (dB)"); ax.grid(alpha=0.3)
ax.set_title("CORDOBA 8 mm, widened, electric bottom: EO crosstalk from the gap fields", fontsize=10)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "dense_eo.png"), dpi=150)
