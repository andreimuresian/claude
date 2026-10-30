"""30 GHz: (1) amplitudes of the five modes plus the free wave (n 2.475, 3 dB/cm) in the narrow and
the widened run; (2) matrix pencil of the difference wide - narrow of B's CPW pattern (one sample
per cell at each non-stem cell position): which waves did widening change?"""
import os, sys, subprocess, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../cordoba_8mm/modefit"))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../..")))
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); NAR = os.path.realpath(os.path.join(HERE, "../cordoba_8mm"))
if len(sys.argv) > 1:                                    # child: amplitudes for one run
    import io, contextlib
    with contextlib.redirect_stdout(io.StringIO()):
        import avsb_scan as S
    o = S.run(2.475, 3.0); ref = o["x"]["e_cpw+"]
    print(json.dumps({k: [abs(v / ref), float(np.angle(v / ref, deg=True))] for k, v in o["x"].items()}))
    sys.exit()
amp = {}
for k, dd in (("narrow", NAR), ("wide", HERE)):
    out = subprocess.run([sys.executable, __file__, "child"], env={**os.environ, "FIELDS": dd}, capture_output=True, text=True).stdout
    amp[k] = json.loads(out.strip().splitlines()[-1])
print("amplitude / e_cpw+ (o_AvsB = free wave n 2.475, 3 dB/cm) | narrow | wide")
for m in amp["narrow"]:
    print(f"  {m:8s} | {amp['narrow'][m][0]:.3e} {amp['narrow'][m][1]:+7.1f} deg | {amp['wide'][m][0]:.3e} {amp['wide'][m][1]:+7.1f} deg")
from mzm_interconnect.xtalk_fields import load_field_dir
fn, fw = load_field_dir(NAR), load_field_dir(HERE); z = fn["z"]
cpw = lambda F: F["B"][0] - F["B"][1]
D = cpw(fw["ports"][30.0][1]) - cpw(fn["ports"][30.0][1]); N0 = cpw(fn["ports"][30.0][1])
sel = (z >= 0.31e-3 - 1e-9) & (z <= 7.69e-3 + 1e-9); zz = z[sel] * 1e3; D = D[sel]; N0 = N0[sel]
print("\n z (mm): |wide - narrow| / rms(narrow), B CPW pattern:",
      " ".join(f"{a:.1f}:{np.sqrt(np.mean(abs(D[abs(zz-a)<0.25])**2))/np.sqrt(np.mean(abs(N0)**2)):.2f}" for a in np.arange(0.5, 7.6, 1.0)))
idx = np.round(((zz - 0.04) % 0.18) / 0.005).astype(int) % 36
keep = ~((idx >= 13) & (idx <= 23))
X = np.array([D[keep & (idx == p)][:40] for p in sorted(set(idx[keep]))]); X = X / abs(X).max()
k0 = 2 * np.pi * 30e9 / 2.99792458e8; Nn = X.shape[1]; Lp = Nn // 2
Hk = np.vstack([np.array([v[i:i + Lp + 1] for i in range(Nn - Lp)]) for v in X])
_, Sv, Vh = np.linalg.svd(Hk, full_matrices=False)
print("pencil of the difference, SV:", " ".join(f"{s/Sv[0]:.2e}" for s in Sv[:8]))
for M in (2, 3, 4, 5):
    V = Vh[:M].T; q = np.linalg.eigvals(np.linalg.pinv(V[:-1]) @ V[1:])
    Z = q[None, :] ** np.arange(Nn)[:, None]; Am, *_ = np.linalg.lstsq(Z, X.T, rcond=None)
    err = np.linalg.norm(Z @ Am - X.T) / np.linalg.norm(X)
    g = -np.log(q) / 0.18e-3; n = g.imag / k0; a = g.real * 8.686 / 100
    am = np.sqrt(np.mean(abs(Am) ** 2, axis=1)); o_ = np.argsort(-am)
    print(f" M={M} resid {err:.2f}: " + "; ".join(f"n {n[i]:+.3f} a {a[i]:6.1f} dB/cm amp {am[i]:.2f}" for i in o_))
