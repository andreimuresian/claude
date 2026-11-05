"""Istanbul run (b): line pair with the real far-end terminations (RS 25 ohm, RG 50 ohm, per line), ports only at the
near end: CST port 1 = line A (y = 0), CST port 3 = line B (y = -0.625), both z = 0.3 (touchstone ports 1, 2).
NEXT = |S21| of the s2p (CST S31). EO crosstalk from the gap fields as in run (a): both lines sampled 5 um from their
centre (A y +-0.005, B y -0.62/-0.63), 50 ohm source, push-pull, n_g 2.27. The fields already contain the
terminations, so no renormalisation. Compared with run (a) (50 ohm ports at both ends of both lines)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RA = os.path.join(HERE, "../istanbul_run_a")
sys.path.insert(0, RA); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
dB = lambda s: 20 * np.log10(np.maximum(abs(s), 1e-12))
Xb = XF.eo_crosstalk_fields(p, load(base=HERE, a_zip="e-field (f=1) [1]_lineA.zip")); f = Xb["f_GHz"]
Xa = XF.eo_crosstalk_fields(p, load()); assert np.allclose(Xa["f_GHz"], f)
eob, eoa = dB(Xb["X"]), dB(Xa["X"])
nb = rf.Network(os.path.join(HERE, "v0_istanbul_rf_lineZload.s2p")); fb = nb.f / 1e9
na = rf.Network(os.path.join(RA, "v0_istanbul_rf_line.s4p")); fa = na.f / 1e9
nxb_s, nxa_s = dB(nb.s[:, 1, 0]), dB(na.s[:, 2, 0])
nxb = np.interp(f, fb, nxb_s)
# termination check: DC load seen at port 1 (line resistance included)
s0 = nb.s[0, 0, 0].real; print(f"S11 at DC {s0:+.4f} -> input resistance {50 * (1 + s0) / (1 - s0):.1f} ohm (load + line series R)")
m = (fb >= 1) & (fb <= 60); ma = (fa >= 1) & (fa <= 60)
print(f"|S11| 1-60 GHz: run b median {np.median(dB(nb.s[m, 0, 0])):.1f} dB, max {dB(nb.s[m, 0, 0]).max():.1f}; "
      f"run a median {np.median(dB(na.s[ma, 0, 0])):.1f}, max {dB(na.s[ma, 0, 0]).max():.1f} dB")
np.savetxt(os.path.join(HERE, "xtalk_run_b.csv"), np.c_[f, nxb, eob, eoa], delimiter=",", fmt="%.3f",
           header="f_GHz,NEXT_dB_run_b,EO_dB_run_b,EO_dB_run_a", comments="")
k = f >= 5; d = eob - eoa
print("f (GHz) | NEXT b | EO b | EO a | EO b - a (dB)")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - q)); print(f"{q:3d} | {nxb[i]:6.1f} | {eob[i]:6.1f} | {eoa[i]:6.1f} | {d[i]:+5.1f}")
for lab, y in (("NEXT b", nxb), ("EO b", eob), ("EO a", eoa)):
    j = np.argmax(np.where(k, y, -999)); print(f"max {lab} 5-60 GHz: {y[j]:.1f} dB at {f[j]:.0f} GHz")
print("EO b - EO a, 5-60 GHz: median %+.1f dB, 5-95%% %+.1f .. %+.1f; correlation of dB curves %.2f"
      % (np.median(d[k]), *np.percentile(d[k], [5, 95]), np.corrcoef(eob[k], eoa[k])[0, 1]))
print("corr(EO b, NEXT b) 5-60 GHz: %.2f" % np.corrcoef(eob[k], nxb[k])[0, 1])
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(fb, nxb_s, color="0.55", lw=1.0, label="NEXT |S31| (port data)")
ax.plot(f, eob, "o-", color="#2a78d6", ms=3, lw=1.4, label="EO crosstalk B/A (gap fields)")
ax.set_xlim(0, 60); ax.set_ylim(-110, -20); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("dB"); ax.grid(alpha=0.3)
ax.set_title("Istanbul run (b), 8.75 mm, 625 um pitch, real terminations (RS 25, RG 50 ohm): NEXT and EO crosstalk", fontsize=9.5)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "xtalk_run_b.png"), dpi=150)
fig, ax = plt.subplots(figsize=(8.5, 4.6))
ax.plot(f, eoa, "o-", color="#eb6834", ms=3, lw=1.3, label="run (a): 50 ohm ports at both ends")
ax.plot(f, eob, "o-", color="#2a78d6", ms=3, lw=1.3, label="run (b): real terminations at the far end")
ax.set_xlim(0, 60); ax.set_ylim(-110, -20); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO crosstalk B/A (dB)"); ax.grid(alpha=0.3)
ax.set_title("Istanbul 8.75 mm, EO crosstalk: run (a) vs run (b) (gap fields, both lines sampled at +-5 um)", fontsize=9.5)
ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_run_a_vs_b.png"), dpi=150)
