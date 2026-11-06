"""Istanbul run (c): line pair + input launch pads (on oxide) at the near end, 50 ohm discrete ports at both ends.
Touchstone ports: 1 = A near pad (excited), 2 = A far (z 9.05), 3 = B near pad, 4 = B far (history; far-end assignment
confirmed by port_check_c.py). NEXT = |S31|, FEXT = |S41|.
EO crosstalk from the gap fields as in runs (a), (b): both lines sampled 5 um from their centre, 50 ohm source,
push-pull, n_g 2.27. Field grid z 0.300..9.050 (runs a, b: 0.3025..9.0525); the z = 0.300 point (zero in line A, at the
line/pad boundary) is dropped. Line B exports at 2 and 15 GHz are corrupted (15: all zero; 2: only Ex) -> left out."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RA, RB = os.path.join(HERE, "../istanbul_run_a"), os.path.join(HERE, "../istanbul_run_b")
sys.path.insert(0, RA); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
dB = lambda s: 20 * np.log10(np.maximum(abs(s), 1e-12))
BAD = (2.0, 15.0)
Xc = XF.eo_crosstalk_fields(p, load(base=HERE, a_zip="e-field (f=1) [1]_lineA.zip", drop="first", skip_f=BAD)); f = Xc["f_GHz"]
Xa = XF.eo_crosstalk_fields(p, load(skip_f=BAD)); Xb = XF.eo_crosstalk_fields(p, load(base=RB, a_zip="e-field (f=1) [1]_lineA.zip", skip_f=BAD))
assert np.allclose(Xa["f_GHz"], f) and np.allclose(Xb["f_GHz"], f)
eoa, eob, eoc = dB(Xa["X"]), dB(Xb["X"]), dB(Xc["X"])
nc = rf.Network(os.path.join(HERE, "v0_istanbul_rf_lineLaunch.s4p")); fc = nc.f / 1e9
na = rf.Network(os.path.join(RA, "v0_istanbul_rf_line.s4p")); fa = na.f / 1e9
nb = rf.Network(os.path.join(RB, "v0_istanbul_rf_lineZload.s2p")); fb = nb.f / 1e9
S = {"NEXT a": (fa, dB(na.s[:, 2, 0])), "NEXT b": (fb, dB(nb.s[:, 1, 0])), "NEXT c": (fc, dB(nc.s[:, 2, 0])),
     "FEXT a": (fa, dB(na.s[:, 3, 0])), "FEXT c": (fc, dB(nc.s[:, 3, 0])),
     "S11 a": (fa, dB(na.s[:, 0, 0])), "S11 c": (fc, dB(nc.s[:, 0, 0])), "S21 a": (fa, dB(na.s[:, 1, 0])), "S21 c": (fc, dB(nc.s[:, 1, 0]))}
I = {k: np.interp(f, *v) for k, v in S.items()}
np.savetxt(os.path.join(HERE, "xtalk_run_c.csv"), np.c_[f, I["NEXT c"], I["FEXT c"], eoc, eoa, eob], delimiter=",", fmt="%.3f",
           header="f_GHz,NEXT_dB_run_c,FEXT_dB_run_c,EO_dB_run_c,EO_dB_run_a,EO_dB_run_b", comments="")
k = f >= 5
print("f | NEXT a b c | FEXT a c | EO a b c | S11 a c | S21 a c (dB)")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - q))
    print(f"{q:2d} | {I['NEXT a'][i]:6.1f} {I['NEXT b'][i]:6.1f} {I['NEXT c'][i]:6.1f} | {I['FEXT a'][i]:6.1f} {I['FEXT c'][i]:6.1f} | "
          f"{eoa[i]:6.1f} {eob[i]:6.1f} {eoc[i]:6.1f} | {I['S11 a'][i]:6.1f} {I['S11 c'][i]:6.1f} | {I['S21 a'][i]:5.1f} {I['S21 c'][i]:5.1f}")
for lab, y in (("NEXT a", I["NEXT a"]), ("NEXT b", I["NEXT b"]), ("NEXT c", I["NEXT c"]), ("FEXT a", I["FEXT a"]),
               ("FEXT c", I["FEXT c"]), ("EO a", eoa), ("EO b", eob), ("EO c", eoc)):
    j = np.argmax(np.where(k, y, -999)); print(f"max {lab} 5-60 GHz: {y[j]:.1f} dB at {f[j]:.0f} GHz; median {np.median(y[k]):.1f}")
for lab, y, r in (("EO c - EO a", eoc, eoa), ("EO c - EO b", eoc, eob), ("NEXT c - NEXT a", I["NEXT c"], I["NEXT a"]),
                  ("FEXT c - FEXT a", I["FEXT c"], I["FEXT a"]), ("S11 c - S11 a", I["S11 c"], I["S11 a"])):
    d = y - r; print("%s, 5-60 GHz: median %+.1f dB, 5-95%% %+.1f .. %+.1f; corr %.2f" % (lab, np.median(d[k]), *np.percentile(d[k], [5, 95]), np.corrcoef(y[k], r[k])[0, 1]))
print("corr(EO c, FEXT c) %.2f, corr(EO c, NEXT c) %.2f" % (np.corrcoef(eoc[k], I["FEXT c"][k])[0, 1], np.corrcoef(eoc[k], I["NEXT c"][k])[0, 1]))
m = (fc >= 1) & (fc <= 60); ma = (fa >= 1) & (fa <= 60)
print(f"|S11| 1-60 GHz median: a {np.median(dB(na.s[ma,0,0])):.1f}, c {np.median(dB(nc.s[m,0,0])):.1f} dB; max a {dB(na.s[ma,0,0]).max():.1f}, c {dB(nc.s[m,0,0]).max():.1f}")
C = {"a": "#eb6834", "b": "#2a78d6", "c": "#1baa7d"}
def fig_(name, title, ylab, curves):
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for x, y, c, ls, lab in curves: ax.plot(x, y, ls, color=c, ms=3, lw=1.3, label=lab)
    ax.set_xlim(0, 60); ax.set_ylim(-110, -15); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(ylab); ax.grid(alpha=0.3)
    ax.set_title(title, fontsize=9.5); ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout()
    fig.savefig(os.path.join(HERE, name), dpi=150)
fig_("xtalk_run_c.png", "Istanbul run (c), 8.75 mm line + launch pads, 50 ohm ports: NEXT, FEXT and EO crosstalk", "dB",
     [(*S["NEXT c"], "0.55", "-", "NEXT |S31|"), (*S["FEXT c"], "0.2", "-", "FEXT |S41|"), (f, eoc, C["c"], "o-", "EO crosstalk B/A (gap fields)")])
fig_("eo_runs_abc.png", "Istanbul 8.75 mm, EO crosstalk B/A: runs (a), (b), (c) (2 and 15 GHz left out)", "EO crosstalk (dB)",
     [(f, eoa, C["a"], "o-", "(a) bare line, 50 ohm ports"), (f, eob, C["b"], "o-", "(b) real far-end terminations"),
      (f, eoc, C["c"], "o-", "(c) launch pads, 50 ohm ports")])
fig_("next_fext_runs_abc.png", "Istanbul 8.75 mm: NEXT (solid) and FEXT (dashed), runs (a), (b), (c)", "dB",
     [(*S["NEXT a"], C["a"], "-", "NEXT (a)"), (*S["NEXT b"], C["b"], "-", "NEXT (b)"), (*S["NEXT c"], C["c"], "-", "NEXT (c)"),
      (*S["FEXT a"], C["a"], "--", "FEXT (a)"), (*S["FEXT c"], C["c"], "--", "FEXT (c)")])
