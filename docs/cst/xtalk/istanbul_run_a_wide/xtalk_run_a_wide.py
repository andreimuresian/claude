"""Istanbul run (a, wide): run (a) bare line pair with the substrate widened to 625 um lateral padding on both sides
(was 391 / 474 um); open boundaries still on the substrate edges. Everything else as run (a): 50 ohm ports at both
ends, port 1 = A near (excited), 2 = A far, 3 = B near, 4 = B far. NEXT = |S31|, FEXT = |S41|.
EO crosstalk from the gap fields (A y +-0.005, B y -0.62/-0.63; z 0.3025..9.0525, last point dropped), 50 ohm
source, push-pull, n_g 2.27. The uploaded zips had swapped names (fixed on placement). Compared with run (a)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); RA = os.path.join(HERE, "../istanbul_run_a")
sys.path.insert(0, RA); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
dB = lambda s: 20 * np.log10(np.maximum(abs(s), 1e-12))
Xw = XF.eo_crosstalk_fields(p, load(base=HERE, a_zip="e-field (f=1) [1]_lineA.zip")); f = Xw["f_GHz"]
Xa = XF.eo_crosstalk_fields(p, load()); assert np.allclose(Xa["f_GHz"], f)
eow, eoa = dB(Xw["X"]), dB(Xa["X"])
nw = rf.Network(os.path.join(HERE, "v0_istanbul_rf_line_625.s4p")); na = rf.Network(os.path.join(RA, "v0_istanbul_rf_line.s4p"))
fw, fa = nw.f / 1e9, na.f / 1e9
S = {f"{q} {r}": (ff, dB(n.s[:, i, 0])) for r, n, ff in (("a", na, fa), ("w", nw, fw)) for q, i in (("S11", 0), ("S21", 1), ("NEXT", 2), ("FEXT", 3))}
I = {k: np.interp(f, *v) for k, v in S.items()}
np.savetxt(os.path.join(HERE, "xtalk_run_a_wide.csv"), np.c_[f, I["NEXT w"], I["FEXT w"], eow, eoa], delimiter=",", fmt="%.3f",
           header="f_GHz,NEXT_dB_wide,FEXT_dB_wide,EO_dB_wide,EO_dB_run_a", comments="")
k = f >= 5
print("f | NEXT a w | FEXT a w | EO a w | S11 a w (dB)")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - q))
    print(f"{q:2d} | {I['NEXT a'][i]:6.1f} {I['NEXT w'][i]:6.1f} | {I['FEXT a'][i]:6.1f} {I['FEXT w'][i]:6.1f} | {eoa[i]:6.1f} {eow[i]:6.1f} | {I['S11 a'][i]:6.1f} {I['S11 w'][i]:6.1f}")
for lab, y in (("NEXT a", I["NEXT a"]), ("NEXT w", I["NEXT w"]), ("FEXT a", I["FEXT a"]), ("FEXT w", I["FEXT w"]), ("EO a", eoa), ("EO w", eow)):
    j = np.argmax(np.where(k, y, -999)); print(f"max {lab} 5-60 GHz: {y[j]:.1f} dB at {f[j]:.0f} GHz; median {np.median(y[k]):.1f}")
for lab, y, r in (("EO w - a", eow, eoa), ("NEXT w - a", I["NEXT w"], I["NEXT a"]), ("FEXT w - a", I["FEXT w"], I["FEXT a"]),
                  ("S11 w - a", I["S11 w"], I["S11 a"]), ("S21 w - a", I["S21 w"], I["S21 a"])):
    d = y - r; print("%s, 5-60 GHz: median %+.2f dB, 5-95%% %+.1f .. %+.1f, max|d| %.1f; corr %.2f" % (lab, np.median(d[k]), *np.percentile(d[k], [5, 95]), abs(d[k]).max(), np.corrcoef(y[k], r[k])[0, 1]))
C = {"a": "#eb6834", "w": "#2a78d6"}
fig, ax = plt.subplots(1, 2, figsize=(13, 4.6))
ax[0].plot(f, eoa, "o-", color=C["a"], ms=3, lw=1.3, label="run (a): lateral padding 391 / 474 um")
ax[0].plot(f, eow, "o-", color=C["w"], ms=3, lw=1.3, label="run (a, wide): lateral padding 625 / 625 um")
ax[0].set_ylabel("EO crosstalk B/A (dB)"); ax[0].set_title("EO crosstalk (gap fields)", fontsize=10)
for r, ls in (("a", "-"), ("w", "-")):
    ax[1].plot(*S[f"NEXT {r}"], ls, color=C[r], lw=1.2, label=f"NEXT ({'a' if r == 'a' else 'a, wide'})")
    ax[1].plot(*S[f"FEXT {r}"], "--", color=C[r], lw=1.2, label=f"FEXT ({'a' if r == 'a' else 'a, wide'})")
ax[1].set_ylabel("dB"); ax[1].set_title("NEXT |S31| (solid), FEXT |S41| (dashed)", fontsize=10)
for a in ax:
    a.set_xlim(0, 60); a.set_ylim(-110, -15); a.set_xlabel("frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=8, loc="lower right")
fig.suptitle("Istanbul 8.75 mm bare line pair: effect of lateral padding (open boundary on the substrate edge)", fontsize=11)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "padding_a_vs_wide.png"), dpi=150)
