"""EO response of line A (driven line) from the gap fields of the Istanbul crosstalk runs (a)-(d), 8.75 mm line.
H_A(f) = (1/L) * integral of the push-pull gap voltage * exp(j beta_o z) dz, beta_o = w n_g / c, n_g = 2.27
(xtalk_fields.eo_crosstalk_fields, I_A: the same integral as the EO crosstalk, on line A). Source and termination are
the CST ports of each run (50 ohm; run b: real far-end termination; run d: driver-trace waveguide port).
Normalisation: |H_A| / mean |H_A| over 3-10.7 GHz (one mismatch-ripple period, c / (2 n_m L) = 7.7 GHz),
and, for reference, / |H_A(1 GHz)|. 1 GHz of run c and 2, 15 GHz of runs a-c are corrupted exports and left out.
Check: run (a) fields vs the closed-form line formula with alpha, n_m, Zc extracted from the run (a) s4p (line A
two-port, 50/50 ohm). Outputs: eo_bandwidth_fields.png, eo_bandwidth_fields.csv, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(X, "istanbul_run_a")); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, tempfile, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from mzm_interconnect.physics import eo_transfer
from mzm_interconnect.extractor import extract_line_fit
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
LA, BAD = "e-field (f=1) [1]_lineA.zip", (2.0, 15.0)
RUNS = {"a": ("(a) bare line, 50 Ω ports", load(skip_f=BAD)),
        "b": ("(b) real far-end termination", load(base=os.path.join(X, "istanbul_run_b"), a_zip=LA, skip_f=BAD)),
        "c": ("(c) launch pads", load(base=os.path.join(X, "istanbul_run_c"), a_zip=LA, drop="first", skip_f=BAD + (1.0,))),
        "d": ("(d) full module (driver trace, wires, pads)", load(base=os.path.join(X, "istanbul_run_d"), a_zip=LA, drop="first"))}
REF = (3.0, 10.7)
def cross(f, y, lev=-3.0):
    k = np.where(y <= lev)[0]
    if not len(k): return None
    i = k[0]; return f[i - 1] + (lev - y[i - 1]) * (f[i] - f[i - 1]) / (y[i] - y[i - 1])
out = {}
for r, (lab, fd) in RUNS.items():
    o = XF.eo_crosstalk_fields(p, fd); f = o["f_GHz"]; h = abs(o["I_A"])
    ref = np.mean(h[(f >= REF[0]) & (f <= REF[1])]); out[r] = (f, 20 * np.log10(h / ref), 20 * np.log10(h / h[0]) if f[0] == 1 else None)
# check against the S-parameter route (run a)
n = rf.Network(os.path.join(X, "istanbul_run_a", "v0_istanbul_rf_line.s4p")).subnetwork([0, 1])
tmp = os.path.join(tempfile.mkdtemp(), "runa_A"); n.write_touchstone(tmp); fit = extract_line_fit(tmp + ".s2p", 8.75)
f = out["a"][0]; fr = fit.raw_f_GHz
H, _ = eo_transfer(f, np.interp(f, fr, fit.raw_alpha_dB_cm), np.interp(f, fr, fit.raw_nm),
                   np.interp(f, fr, fit.raw_Zc.real) + 1j * np.interp(f, fr, fit.raw_Zc.imag), 8.75e-3, 2.27, 50.0, 50.0)
hm = abs(H); yM = 20 * np.log10(hm / np.mean(hm[(f >= REF[0]) & (f <= REF[1])]))
d = out["a"][1] - yM
print(f"check run (a), fields - line formula from the s4p: median {np.median(d):+.2f} dB, max abs {abs(d).max():.2f} dB")
print("run | EO response at 20/40/60 GHz (dB, plateau ref) | -3 dB crossing: plateau ref | 1 GHz ref")
for r, (f, y, y1) in out.items():
    v = " ".join(f"{y[np.argmin(abs(f - q))]:+.2f}" for q in (20, 40, 60))
    c1 = cross(f, y1) if y1 is not None else None
    print(f" {r}  | {v} | {cross(f, y) or '> 60'} | {c1 if c1 else ('> 60' if y1 is not None else 'n/a (1 GHz corrupted)')}")
with open(os.path.join(HERE, "eo_bandwidth_fields.csv"), "w") as fh:
    fh.write("f_GHz," + ",".join(f"EO_run_{r}_dB" for r in out) + ",line_formula_run_a_dB\n")
    for i, q in enumerate(out["a"][0]):
        vals = [out[r][1][np.argmin(abs(out[r][0] - q))] if np.min(abs(out[r][0] - q)) < 1e-6 else np.nan for r in out]
        fh.write(f"{q:g}," + ",".join(f"{v:.3f}" for v in vals) + f",{yM[i]:.3f}\n")
C = {"a": "#eb6834", "b": "#2a78d6", "c": "#1baa7d", "d": "#7a4bd1"}
fig, ax = plt.subplots(figsize=(8.5, 4.8))
for r, (f, y, _) in out.items(): ax.plot(f, y, "o-", ms=3, lw=1.3, color=C[r], label=RUNS[r][0])
ax.plot(out["a"][0], yM, "k--", lw=1.2, label="(a) line formula with α, n_m, Z_c from the s4p (check)")
ax.axhline(-3, color="0.4", lw=0.9, ls=":"); ax.set_xlim(0, 60); ax.set_ylim(-4, 1)
ax.set_xlabel("frequency (GHz)"); ax.set_ylabel("EO response, line A (dB)"); ax.grid(alpha=0.3); ax.legend(frameon=False, fontsize=8, loc="lower left")
ax.set_title("Istanbul 8.75 mm, EO response from the CST gap fields (n_g 2.27, push-pull; ref: mean 3–10.7 GHz)", fontsize=9.5)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_bandwidth_fields.png"), dpi=200)
