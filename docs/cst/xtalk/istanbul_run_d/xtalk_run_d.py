"""Istanbul run (d): full module. Driver carrier (alumina) with GS traces, 8 bond wires (PEC, 17 um) to the launch pads,
line pair 8.75 mm. Port 1 = waveguide port on the driver trace of line A (aggressor, y = 0, excited); port 5 = same on
line B (not excited); ports 2, 4 = far-end discrete ports (assumed: 2 = A far, 4 = B far).
S-parameters exported as ASCII magnitudes (dB) only: S11, S21, S41 (FEXT), S51 (NEXT, at the driver port of B).
EO crosstalk from the gap fields as in runs (a)-(c): both lines 5 um from their centre, push-pull, n_g 2.27.
Field grid z 0.300..9.050, the z = 0.300 point dropped (as run c). All 60 frequencies are valid.
Runs (a)-(c) leave out 2 and 15 GHz (corrupted in run c), so the comparison uses the common set."""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
RA, RB, RC = (os.path.join(HERE, f"../istanbul_run_{r}") for r in "abc")
sys.path.insert(0, RA); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
dB = lambda s: 20 * np.log10(np.maximum(abs(s), 1e-12))
BAD = (2.0, 15.0)
LA = "e-field (f=1) [1]_lineA.zip"

def read_ascii(path):
    out, key = {}, None
    for ln in open(path):
        m = re.search(r'"(S\d,\d) \[Magnitude / dB\]"', ln)
        if m: key = m.group(1); out[key] = []; continue
        if ln.startswith("#") or not ln.strip(): continue
        out[key].append([float(v) for v in ln.split()])
    return {k: np.array(v) for k, v in out.items()}

Xd_all = XF.eo_crosstalk_fields(p, load(base=HERE, a_zip=LA, drop="first"))
Xd = XF.eo_crosstalk_fields(p, load(base=HERE, a_zip=LA, drop="first", skip_f=BAD)); f = Xd["f_GHz"]
Xa = XF.eo_crosstalk_fields(p, load(skip_f=BAD))
Xb = XF.eo_crosstalk_fields(p, load(base=RB, a_zip=LA, skip_f=BAD))
Xc = XF.eo_crosstalk_fields(p, load(base=RC, a_zip=LA, drop="first", skip_f=BAD))
for X in (Xa, Xb, Xc): assert np.allclose(X["f_GHz"], f)
eo = {r: dB(X["X"]) for r, X in zip("abcd", (Xa, Xb, Xc, Xd))}
Sd = read_ascii(os.path.join(HERE, "v0_istanbul_rf_module_allS.txt"))
na = rf.Network(os.path.join(RA, "v0_istanbul_rf_line.s4p")); nc = rf.Network(os.path.join(RC, "v0_istanbul_rf_lineLaunch.s4p"))
S = {"NEXT a": (na.f / 1e9, dB(na.s[:, 2, 0])), "NEXT c": (nc.f / 1e9, dB(nc.s[:, 2, 0])), "NEXT d": tuple(Sd["S5,1"].T),
     "FEXT a": (na.f / 1e9, dB(na.s[:, 3, 0])), "FEXT c": (nc.f / 1e9, dB(nc.s[:, 3, 0])), "FEXT d": tuple(Sd["S4,1"].T),
     "S11 c": (nc.f / 1e9, dB(nc.s[:, 0, 0])), "S11 d": tuple(Sd["S1,1"].T),
     "S21 c": (nc.f / 1e9, dB(nc.s[:, 1, 0])), "S21 d": tuple(Sd["S2,1"].T)}
I = {k: np.interp(f, *v) for k, v in S.items()}
np.savetxt(os.path.join(HERE, "xtalk_run_d.csv"), np.c_[f, I["NEXT d"], I["FEXT d"], eo["d"], eo["a"], eo["b"], eo["c"]],
           delimiter=",", fmt="%.3f", header="f_GHz,NEXT_dB_run_d,FEXT_dB_run_d,EO_dB_run_d,EO_dB_run_a,EO_dB_run_b,EO_dB_run_c", comments="")
k = f >= 5
print("f | NEXT a c d | FEXT a c d | EO a b c d | S11 c d | S21 c d (dB)")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(f - q))
    print(f"{q:2d} | " + " ".join(f"{I['NEXT '+r][i]:6.1f}" for r in "acd") + " | " + " ".join(f"{I['FEXT '+r][i]:6.1f}" for r in "acd")
          + " | " + " ".join(f"{eo[r][i]:6.1f}" for r in "abcd") + f" | {I['S11 c'][i]:6.1f} {I['S11 d'][i]:6.1f} | {I['S21 c'][i]:5.1f} {I['S21 d'][i]:5.1f}")
for lab, y in [(f"NEXT {r}", I[f"NEXT {r}"]) for r in "acd"] + [(f"FEXT {r}", I[f"FEXT {r}"]) for r in "acd"] + [(f"EO {r}", eo[r]) for r in "abcd"]:
    j = np.argmax(np.where(k, y, -999)); print(f"max {lab} 5-60 GHz: {y[j]:.1f} dB at {f[j]:.0f} GHz; median {np.median(y[k]):.1f}")
for lab, y, r in (("EO d - EO c", eo["d"], eo["c"]), ("EO d - EO a", eo["d"], eo["a"]), ("NEXT d - NEXT c", I["NEXT d"], I["NEXT c"]),
                  ("FEXT d - FEXT c", I["FEXT d"], I["FEXT c"]), ("S21 d - S21 c", I["S21 d"], I["S21 c"])):
    d = y - r; print("%s, 5-60 GHz: median %+.1f dB, 5-95%% %+.1f .. %+.1f; corr %.2f" % (lab, np.median(d[k]), *np.percentile(d[k], [5, 95]), np.corrcoef(y[k], r[k])[0, 1]))
print("corr(EO d, FEXT d) %.2f, corr(EO d, NEXT d) %.2f" % (np.corrcoef(eo["d"][k], I["FEXT d"][k])[0, 1], np.corrcoef(eo["d"][k], I["NEXT d"][k])[0, 1]))
fa = Xd_all["f_GHz"]; ea = dB(Xd_all["X"])
print("run d at 2, 15 GHz (left out of the comparison): " + ", ".join(f"{ea[np.argmin(abs(fa-q))]:.1f}" for q in (2, 15)) + " dB")
C = {"a": "#eb6834", "b": "#2a78d6", "c": "#1baa7d", "d": "#7a4bd1"}
def fig_(name, title, ylab, curves, ylim=(-110, -10)):
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    for x, y, c, ls, lab in curves: ax.plot(x, y, ls, color=c, ms=3, lw=1.3, label=lab)
    ax.set_xlim(0, 60); ax.set_ylim(*ylim); ax.set_xlabel("frequency (GHz)"); ax.set_ylabel(ylab); ax.grid(alpha=0.3)
    ax.set_title(title, fontsize=9.5); ax.legend(frameon=False, fontsize=8, loc="lower right"); fig.tight_layout()
    fig.savefig(os.path.join(HERE, name), dpi=150)
fig_("xtalk_run_d.png", "Istanbul run (d), full module (driver + wires + pads + line): NEXT, FEXT and EO crosstalk", "dB",
     [(*S["NEXT d"], "0.55", "-", "NEXT |S51| (driver port of B)"), (*S["FEXT d"], "0.2", "-", "FEXT |S41|"),
      (fa, ea, C["d"], "o-", "EO crosstalk B/A (gap fields)")])
fig_("eo_runs_abcd.png", "Istanbul 8.75 mm, EO crosstalk B/A: runs (a)-(d) (2 and 15 GHz left out)", "EO crosstalk (dB)",
     [(f, eo["a"], C["a"], "o-", "(a) bare line"), (f, eo["b"], C["b"], "o-", "(b) real far-end terminations"),
      (f, eo["c"], C["c"], "o-", "(c) launch pads"), (f, eo["d"], C["d"], "o-", "(d) full module")], ylim=(-70, -10))
fig_("next_fext_runs_acd.png", "Istanbul 8.75 mm: NEXT (solid) and FEXT (dashed), runs (a), (c), (d)", "dB",
     [(*S[f"NEXT {r}"], C[r], "-", f"NEXT ({r})") for r in "acd"] + [(*S[f"FEXT {r}"], C[r], "--", f"FEXT ({r})") for r in "acd"])
