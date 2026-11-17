"""EO validation of the offline equaliser model against the full CST run.

Model: 50 ohm source -> line 2.70 mm (+) -> bend -> line 1.44 mm (+) -> bend -> line 1.44 mm (-) -> 50 ohm load.
  line  : alpha, n_m, Zc from the L+S run. Two variants: (i) all from the touchstone extraction (pure S-parameter
          tool); (ii) alpha and n_m from the L+S gap fields (port-free), Zc from the touchstone.
  bend  : 2-port from L+B+S (B = T(2.16)^-1 T_LBS T(1.08)^-1), smoothed outside the ground-mode resonances
          (cascade_test.py); interpolated to 1..60 GHz.
  V, I propagated through the chain with the ABCD matrices: [V(s); I(s)] = T(s)^-1 [V0; I0] inside a line,
  [V; I]_after = B^-1 [V; I]_before across a bend.
  EO: H = sum_k p_k int V_k(s) exp(j w t_opt(s)) ds, p = (+1, +1, -1), n_g = 2.27, light matched to the RF delay
  of each bend (delay of the bend model), as in the field reference.
Reference: EO response of the full run from its gap fields (full_eq_fields.csv). Both normalised at 1 GHz.
Also: complex V(z) of the model vs the pitch-averaged field V(z) of the full run, after one complex scale factor
per frequency (same for the three lines): rms relative error over the buried metal.
Outputs: eo_validation.png, eo_validation.csv, printed table."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect.physics import C0

with contextlib.redirect_stdout(io.StringIO()):
    ct = runpy.run_path(os.path.join(HERE, "cascade_test.py"))
    fe = runpy.run_path(os.path.join(HERE, "full_eq_fields.py"))
LS = np.genfromtxt(os.path.join(HERE, "ls_extraction.csv"), delimiter=",", names=True)
NG = 2.27; F = fe["F"]; w = 2 * np.pi * F * 1e9; fit = ct["fit"]

# bend model on the 1..60 GHz grid
fT, Ss = ct["f"], ct["Ss"]
mag = np.interp(F, fT, 20 * np.log10(abs(Ss[:, 1, 0]))); ph = np.interp(F, fT, np.unwrap(np.angle(Ss[:, 1, 0])))
s11 = np.interp(F, fT, Ss[:, 0, 0].real) + 1j * np.interp(F, fT, Ss[:, 0, 0].imag)
Zc = np.interp(F, fit.raw_f_GHz, fit.raw_Zc.real) + 1j * np.interp(F, fit.raw_f_GHz, fit.raw_Zc.imag)
SB = np.zeros((len(F), 2, 2), complex); SB[:, 0, 0] = SB[:, 1, 1] = s11; SB[:, 1, 0] = SB[:, 0, 1] = 10 ** (mag / 20) * np.exp(1j * ph)
BB = np.array([rf.network.s2a(SB[i:i+1], Zc[i])[0] for i in range(len(F))])
tauB_poly = -ph / w
# physical bend (bend_physical.py): uniform section, impedance Zb, theta = loss + j w tau -> ABCD independent of Zc
pb = np.load(os.path.join(HERE, "bend_physical.npz"))["params"]
thb = (pb[0] * np.sqrt(F) + pb[1] * F) / 8.686 + 1j * w * pb[2] * 1e-12
BB_phys = np.array([[[np.cosh(t), pb[3] * np.sinh(t)], [np.sinh(t) / pb[3], np.cosh(t)]] for t in thb])
BENDS = {"polynomial": (BB, tauB_poly), "physical": (BB_phys, np.full(len(F), pb[2] * 1e-12))}

def gamma(variant):
    if variant == "touchstone":
        a = np.interp(F, fit.raw_f_GHz, fit.raw_alpha_dB_cm); n = np.interp(F, fit.raw_f_GHz, fit.raw_nm)
    else:
        a = np.interp(F, LS["f_GHz"], LS["alpha_fields_dB_cm"]); n = np.interp(F, LS["f_GHz"], LS["nm_fields"])
    return a * 100 / 8.686 + 1j * n * w / C0
def Tl(g, Z, s):
    gl = g * s; return np.array([[np.cosh(gl), Z * np.sinh(gl)], [np.sinh(gl) / Z, np.cosh(gl)]])
SECT = [("L1", 2.70e-3, +1), ("L2", 1.44e-3, +1), ("L3", 1.44e-3, -1)]
def model(variant, bend="polynomial", ds=5e-6):
    BB, tauB = BENDS[bend]; g = gamma(variant); H = np.zeros(len(F), complex); prof = []
    for i in range(len(F)):
        # whole-chain ABCD and input voltage with 50 ohm source (1 V EMF) and 50 ohm load
        Ttot = np.eye(2, dtype=complex)
        for j, (_, L, _) in enumerate(SECT):
            Ttot = Ttot @ Tl(g[i], Zc[i], L)
            if j < 2: Ttot = Ttot @ BB[i]
        Zin = (Ttot[0, 0] * 50 + Ttot[0, 1]) / (Ttot[1, 0] * 50 + Ttot[1, 1])
        V0 = Zin / (Zin + 50); VI = np.array([V0, V0 / Zin]); t0 = 0.0; p_i = {}
        for j, (nm, L, pol) in enumerate(SECT):
            s = np.arange(0, L + ds / 2, ds)
            V = np.array([np.linalg.solve(Tl(g[i], Zc[i], x), VI)[0] for x in s])
            H[i] += pol * np.trapezoid(V * np.exp(1j * w[i] * (t0 + NG * s / C0)), s); p_i[nm] = (s, V)
            VI = np.linalg.solve(Tl(g[i], Zc[i], L), VI); t0 += NG * L / C0
            if j < 2: VI = np.linalg.solve(BB[i], VI); t0 += tauB[i]
        prof.append(p_i)
    return H, prof
db = lambda h: 20 * np.log10(abs(h) / abs(h[0]))
ref = fe["db"](fe["H_full"])
res = {}
import skrf as _rf
full = _rf.Network(os.path.join(HERE, "..", "full equalizer", "BASELINE_FULL_EQUALIZER.s2p"))
fS = full.f / 1e9; S21ref = np.interp(F, fS, abs(full.s[:, 1, 0])); S11ref = np.interp(F, fS, abs(full.s[:, 0, 0]))
for v in ("touchstone", "fields"):
  for bnd in ("polynomial", "physical"):
    H, prof = model(v, bnd); y = db(H); d = y - ref
    BBx = BENDS[bnd][0]; g = gamma(v); s21m, s11m = [], []
    for i in range(len(F)):
        Tt = Tl(g[i], Zc[i], 2.70e-3) @ BBx[i] @ Tl(g[i], Zc[i], 1.44e-3) @ BBx[i] @ Tl(g[i], Zc[i], 1.44e-3)
        Sx = rf.network.a2s(Tt[None], 50.0)[0]; s21m.append(abs(Sx[1, 0])); s11m.append(abs(Sx[0, 0]))
    dS21 = 20 * np.log10(np.array(s21m) / S21ref); dS11 = np.array(s11m) - S11ref
    err = []
    for i in range(len(F)):
        mv, fv = [], []
        for nm, L, _ in SECT:
            z, Vf = fe["data"][nm]; z0, z1, dr = fe["LINES"][nm]
            k = int(round(0.18e-3 / (z[1] - z[0]))); ker = np.ones(k) / k
            zs = np.convolve(z, ker, "valid"); vs = np.convolve(Vf[i], ker, "valid"); m = (zs >= z0 + 0.09e-3) & (zs <= z1 - 0.09e-3)
            sf = (zs[m] - z0) if dr > 0 else (z1 - zs[m]); s_, Vm = prof[i][nm]
            mv.append(np.interp(sf, s_, Vm.real) + 1j * np.interp(sf, s_, Vm.imag)); fv.append(vs[m])
        mv, fv = np.concatenate(mv), np.concatenate(fv); c = np.vdot(mv, fv) / np.vdot(mv, mv)
        err.append(np.linalg.norm(c * mv - fv) / np.linalg.norm(fv))
    res[(v, bnd)] = (y, d, np.array(err))
    print(f"line {v:10s} bend {bnd:10s}: EO rms {np.sqrt(np.mean(d**2)):.3f} max {abs(d).max():.3f} dB | V(z) median {100*np.median(err):.1f} % max {100*max(err):.1f} %"
          f" | S21 rms {np.sqrt(np.mean(dS21**2)):.3f} max {abs(dS21).max():.3f} dB | |S11| max diff {abs(dS11).max():.3f}")
print(" f GHz | EO re 1 GHz (dB): fields (CST) | model, polynomial bend | model, physical bend   (touchstone line)")
for q in (5, 7, 10, 15, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F - q)); print(f"{F[i]:5.0f}  | {ref[i]:+.2f} | {res[('touchstone','polynomial')][0][i]:+.2f} | {res[('touchstone','physical')][0][i]:+.2f}")
np.savetxt(os.path.join(HERE, "eo_validation.csv"),
           np.column_stack([F, ref] + [res[k][0] for k in res] + [res[k][2] for k in res]),
           delimiter=",", fmt="%.5g", comments="", header="f_GHz,EO_fields_CST_dB," + ",".join(f"EO_{a}_{b}_dB" for a, b in res) + "," + ",".join(f"Vz_err_{a}_{b}" for a, b in res))
fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
ax[0].plot(F, ref, "o", ms=3.5, color="#eb6834", label="full run, from the CST gap fields (reference)")
ax[0].plot(F, res[("touchstone", "polynomial")][0], "k-", lw=1.4, label="model, touchstone line, polynomial bend")
ax[0].plot(F, res[("touchstone", "physical")][0], "--", color="#2a78d6", lw=1.4, label="model, touchstone line, physical bend")
ax[0].axhline(-3, color="0.4", lw=0.8, ls=":"); ax[0].set_ylim(-3.5, 0.5); ax[0].set_ylabel("EO response re 1 GHz (dB)")
ax[1].plot(F, res[("touchstone", "polynomial")][1], "k-", lw=1.4, label="polynomial bend − fields")
ax[1].plot(F, res[("touchstone", "physical")][1], "--", color="#2a78d6", lw=1.4, label="physical bend − fields")
ax[1].axhline(0, color="0.4", lw=0.8); ax[1].set_ylabel("EO difference (dB)"); ax[1].set_ylim(-0.5, 0.5)
for a_ in ax: a_.set_xlabel("frequency (GHz)"); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle("Equaliser EO response: offline model (L+S line + L+B+S bend) vs full CST run (n_g 2.27, + + −, 50 Ω ports)", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "eo_validation.png"), dpi=200)
