"""Offline optimiser: L1 = 10 mm (+), L2 (+), L3 (-), two-mode bend model (validated on the full run), 1-130 GHz.
Grid L2, L3 = 0.5 .. 10 mm (0.5 mm steps). 50 ohm ports, n_g 2.27, light matched to the RF in the bends.
Metrics (EO = 20 log|H|):
  normalised (re own 1 GHz): bandwidth f_-3dB (> 130 if not reached), peaking = max over 1-130 GHz, worst level 10-130 GHz
  absolute (re the standalone 10 mm line at 1 GHz, same ports): low-frequency efficiency (1 GHz) and level at 130 GHz
Also the standalone 10 mm line (L+S model) as reference. Validity: 1-130 GHz only (no extrapolation of the bend).
Outputs: optimiser_L1_10mm.npz, printed tables."""
import os, io, contextlib, runpy, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    tm = runpy.run_path(os.path.join(HERE, "two_mode_cascade.py")); sl = runpy.run_path(os.path.join(HERE, "standalone_line_eo_130.py"))
solve, SM, F, RHO = tm["solve"], tm["SM"], tm["F"], tm["RHO"]
H10, _ = sl["model_eo"](10e-3); ref = abs(H10[0])
def cross(y, lev=-3.0):
    k = np.where(y[1:] <= lev)[0]
    if not len(k): return np.inf
    i = k[0] + 1; return F[i - 1] + (lev - y[i - 1]) * (F[i] - F[i - 1]) / (y[i] - y[i - 1])
e10 = 20 * np.log10(abs(H10) / abs(H10[0])); m10 = F >= 10
print(f"standalone 10 mm: f-3dB {cross(e10):.1f} GHz, worst 10-130 GHz {e10[m10].min():+.2f} dB, at 130 GHz {e10[-1]:+.2f} dB")
L2s = np.arange(0.5, 10.01, 0.5); L3s = np.arange(0.5, 10.01, 0.5)
R = {k: np.full((len(L2s), len(L3s)), np.nan) for k in ("bw", "peak", "worst", "e130", "abs1", "abs130", "absworst")}
EO = np.zeros((len(L2s), len(L3s), len(F)))
for a, L2 in enumerate(L2s):
    for b, L3 in enumerate(L3s):
        _, _, H, _ = solve(SM, RHO, ds=10e-6, LEN=[10e-3, L2 * 1e-3, L3 * 1e-3])
        e = 20 * np.log10(abs(H) / abs(H[0])); ea = 20 * np.log10(abs(H) / ref); EO[a, b] = ea
        R["bw"][a, b], R["peak"][a, b], R["worst"][a, b], R["e130"][a, b] = cross(e), e.max(), e[m10].min(), e[-1]
        R["abs1"][a, b], R["abs130"][a, b], R["absworst"][a, b] = ea[0], ea[-1], ea[m10].min()
np.savez(os.path.join(HERE, "optimiser_L1_10mm.npz"), F=F, L2s=L2s, L3s=L3s, EO_abs=EO, e10=e10, **R)
print("done")
