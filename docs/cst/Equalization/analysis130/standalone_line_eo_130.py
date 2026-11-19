"""EO response of a standalone straight line of any length, built from the L+S run (0-130 GHz), compared with the
full equaliser (fields). No bends, no other sections.

Line model (as in lbs_bend_130.py): gamma = physical fit of the L+S FIELD alpha and n_m; Zc = smooth fit of the L+S
touchstone Zc (beta L = m pi bands excluded). Ports: the L+S port block at each end (series Ls + shunt Cp, fitted on
the L+S touchstone: the same 50 ohm ports with PEC ground bridge as in all runs). Source: 1 V behind 50 ohm; load 50 ohm.
Voltage along the line from the ABCD chain: [V(s); I(s)] = T(s)^-1 [V(0); I(0)], V(s) = V0 cosh(gs) - Zc I0 sinh(gs).
EO: H = int_0^L V(s) exp(j w n_g s / c) ds, n_g = 2.27, normalised to 1 GHz.
Check: the model at L = 3.24 mm against the EO computed directly from the L+S gap fields (same 1 GHz normalisation).
Outputs: standalone_line_eo_130.png, standalone_line_eo_130.csv, printed table."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C0, NG, GAP = 299792458.0, 2.27, 4.45e-6
with contextlib.redirect_stdout(io.StringIO()):
    lb = runpy.run_path(os.path.join(HERE, "lbs_bend_130.py"))
line, ports, pp = lb["line"], lb["ports"], lb["pp"]
F = np.r_[np.arange(1, 61), np.arange(62, 131, 2)].astype(float); w = 2 * np.pi * F * 1e9
def model_eo(L, with_ports=True, ds=5e-6):
    g, Z = line(F); P1, P2 = ports(F, pp[0] * 1e-12 * with_ports, pp[1] * 1e-15 * with_ports)
    T = np.array([[np.cosh(g * L), Z * np.sinh(g * L)], [np.sinh(g * L) / Z, np.cosh(g * L)]]).transpose(2, 0, 1)
    Tt = P1 @ T @ P2; Zin = (Tt[:, 0, 0] * 50 + Tt[:, 0, 1]) / (Tt[:, 1, 0] * 50 + Tt[:, 1, 1])
    Vin, Iin = Zin / (Zin + 50), 1 / (Zin + 50)
    VI = np.linalg.solve(P1, np.stack([Vin, Iin], 1)[:, :, None])[:, :, 0]       # at the line input, after the port block
    s = np.arange(0, L + ds / 2, ds)[None, :]; V = VI[:, :1] * np.cosh(g[:, None] * s) - Z[:, None] * VI[:, 1:] * np.sinh(g[:, None] * s)
    H = np.trapezoid(V * np.exp(1j * w[:, None] * NG * s / C0), s[0], axis=1)
    S21 = 2 / (Tt[:, 0, 0] + Tt[:, 0, 1] / 50 + Tt[:, 1, 0] * 50 + Tt[:, 1, 1])
    return H, S21
# check against the L+S fields at 3.24 mm
D = os.path.join(HERE, "..", "L+S", "130 GHz")
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
Ff, z, Ep = load("L1_gap+.txt"); _, _, Em = load("L1_gap-.txt"); assert np.allclose(Ff, F)
Hf = np.trapezoid(GAP / 2 * (Ep - Em) * np.exp(1j * w[:, None] * NG * z[None, :] / C0), z, axis=1)
dB0 = lambda h: 20 * np.log10(abs(h) / abs(h[0]))
Hm324, _ = model_eo(3.24e-3); d = dB0(Hm324) - dB0(Hf)
print(f"check, 3.24 mm: model - L+S fields EO: rms {np.sqrt(np.mean(d**2)):.3f} dB, max {abs(d).max():.3f} dB (1-130 GHz)")
H27, S27 = model_eo(2.70e-3); H27n, _ = model_eo(2.70e-3, with_ports=False)
eq = np.loadtxt(os.path.join(HERE, "full_eq_eo_130.csv"), delimiter=",", skiprows=1)
assert np.allclose(eq[:, 0], F)
e27, e27n, eeq, eL1in = dB0(H27), dB0(H27n), eq[:, 4], eq[:, 2] - eq[0, 2]
def cross(y, lev=-3.0):
    k = np.where(y <= lev)[0]
    if not len(k): return "> 130"
    i = k[0]; return f"{F[i-1] + (lev - y[i-1]) * (F[i] - F[i-1]) / (y[i] - y[i-1]):.1f}"
print(" f GHz | standalone 2.70 mm (ports / no ports) | L1 inside the full run | full equaliser + + -   [dB re own 1 GHz]")
for q in (10, 20, 30, 40, 60, 80, 100, 120, 130):
    i = np.argmin(abs(F - q)); print(f"{q:5d}  | {e27[i]:+.2f} / {e27n[i]:+.2f} | {eL1in[i]:+.2f} | {eeq[i]:+.2f}")
print("-3 dB: standalone 2.70 mm", cross(e27), "GHz | full equaliser", cross(eeq), "GHz | standalone electrical |S21| at 130 GHz", f"{20*np.log10(abs(S27[-1])):.2f} dB")
for L in (2.7e-3, 4.0e-3, 5.0e-3, 6.0e-3, 8.0e-3):
    print(f"   standalone {L*1e3:.1f} mm: EO -3 dB at {cross(dB0(model_eo(L)[0]))} GHz")
np.savetxt(os.path.join(HERE, "standalone_line_eo_130.csv"), np.column_stack([F, e27, e27n, eL1in, eeq, dB0(Hm324), dB0(Hf)]), delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,EO_standalone_2p70mm_dB,EO_standalone_2p70mm_noports_dB,EO_L1_inside_full_dB,EO_full_equaliser_dB,EO_model_3p24mm_dB,EO_LS_fields_3p24mm_dB")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 2, figsize=(13, 4.4))
ax[0].plot(F, dB0(Hf), "o", ms=3, color="#EB6834", label="L+S fields (CST)"); ax[0].plot(F, dB0(Hm324), "-", color="#0E2268", lw=1.5, label="line model from L+S")
ax[0].set_title("Check: 3.24 mm line (L+S run)", fontsize=11)
ax[1].plot(F, e27, "-", color="#0E2268", lw=1.6, label="standalone 2.70 mm line (L+S model)")
ax[1].plot(F, eeq, "o-", ms=3, lw=1, color="#EB6834", label="full equaliser + + − (fields)")
ax[1].plot(F, eL1in, ":", color="#9AA0AC", lw=1.6, label="L1 inside the full run (fields)")
ax[1].set_title("EO response, n$_g$ = 2.27, 50 Ω ports", fontsize=11)
for a in ax:
    a.axhline(-3, color="0.4", lw=0.8, ls=":"); a.set_ylim(-4, 0.5); a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.set_ylabel("EO response re 1 GHz (dB)")
    a.grid(alpha=0.3); a.legend(frameon=False, fontsize=10.5, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "standalone_line_eo_130.png"), dpi=200)
