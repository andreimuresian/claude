"""L+S run (single straight line, EL_L = 3.24 mm): line parameters from the touchstone and from the gap fields.

Touchstone route: ABCD extraction (mzm_interconnect.extractor.extract_line_fit) -> alpha(f), n_m(f), Zc(f).
Field route: gap voltage V(z) ~ GAP * E_y at the gap centre (push-pull mean of the two gaps, sign so both are
signal -> ground), smoothed over one Tee pitch (0.18 mm) to remove the periodic loading ripple, then fitted with
two waves V(z) = A exp(-gamma z) + B exp(+gamma z) on the inner part of the line (0.18 mm cut at each end).
gamma from the fields does not see the ports: it is the propagation constant of the line itself.
EO response (n_g = 2.27, velocity-matched optics): H = (1/L) int V(z) exp(j w n_g z / c) dz,
fields vs line formula with the touchstone parameters, 50 ohm source and load (the CST ports).
Outputs: ls_extraction.png, ls_extraction.csv, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, ROOT)
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import eo_transfer, C0

D = os.path.join(HERE, "..", "L+S"); L = 3.24e-3; GAP = 4.45e-6; NG = 2.27; PITCH = 0.18e-3; CUT = 0.18e-3

def load_gap(fn):
    a = np.loadtxt(os.path.join(D, fn), comments="#", skiprows=2)
    fs = np.unique(a[:, 0]); out = {}
    for f in fs:
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3])
        out[f] = (b[o, 3] * 1e-3, b[o, 6] + 1j * b[o, 7])          # z (m), E_y
    return out

Gp, Gm = load_gap("L1_gap+.txt"), load_gap("L1_gap-.txt")
F = np.array(sorted(Gp)); z = Gp[F[0]][0]; dz = z[1] - z[0]
V = np.array([0.5 * GAP * (Gp[f][1] - Gm[f][1]) for f in F])        # push-pull mean gap voltage, signal -> ground
k = int(round(PITCH / dz)); ker = np.ones(k) / k
zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in V])
m = (zs >= CUT) & (zs <= L - CUT)

# touchstone extraction
fit = extract_line_fit(os.path.join(D, "BASELINE_LS.s2p"), L * 1e3)
fr = fit.raw_f_GHz
a_ts = np.interp(F, fr, fit.raw_alpha_dB_cm); n_ts = np.interp(F, fr, fit.raw_nm)

# field two-wave fit
def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]
    return c, M @ c - vv
a_f, n_f, rho, res = [], [], [], []
for i, f in enumerate(F):
    w = 2 * np.pi * f * 1e9
    g0 = [a_ts[i] * 100 / 8.686, n_ts[i] * w / C0]
    def r(p):
        _, e = two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m]); return np.concatenate([e.real, e.imag])
    p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x
    c, e = two_wave(p[0] + 1j * p[1], zs[m], Vs[i][m])
    a_f.append(p[0] * 8.686 / 100); n_f.append(p[1] * C0 / w)
    rho.append(abs(c[1] * np.exp(p[0] * L + 1j * p[1] * L) / (c[0] * np.exp(-(p[0] * L + 1j * p[1] * L)))))   # |B/A| at z = L
    res.append(np.linalg.norm(e) / np.linalg.norm(Vs[i][m]))
a_f, n_f, rho, res = map(np.array, (a_f, n_f, rho, res))

# EO response
w = 2 * np.pi * F * 1e9
H_f = np.array([np.trapezoid(V[i] * np.exp(1j * w[i] * NG * z / C0), z) / L for i in range(len(F))])
H_t, _ = eo_transfer(F, fit.alpha_dB_cm(F), fit.nm(F), fit.Zc(F), L, NG, 50.0, 50.0)
H_r, _ = eo_transfer(F, a_ts, n_ts, np.interp(F, fr, fit.raw_Zc.real) + 1j * np.interp(F, fr, fit.raw_Zc.imag), L, NG, 50.0, 50.0)
db = lambda h: 20 * np.log10(abs(h) / abs(h[0]))
eo_f, eo_t, eo_r = db(H_f), db(H_t), db(H_r)

print("f GHz | alpha dB/cm: touchstone / fields | n_m: touchstone / fields | Re Zc (ts) | |refl| at far end (fields) | fit residual")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F - q))
    print(f"{F[i]:5.0f} | {a_ts[i]:.2f} / {a_f[i]:.2f} | {n_ts[i]:.3f} / {n_f[i]:.3f} | "
          f"{np.interp(F[i], fr, fit.raw_Zc.real):.1f} | {rho[i]:.3f} | {res[i]*100:.1f} %")
for lab, y in (("fitted", eo_t), ("raw", eo_r)):
    d = eo_f - y; print(f"EO fields - touchstone ({lab} params): rms {np.sqrt(np.mean(d**2)):.2f} dB, max {abs(d).max():.2f} dB")
print("EO at 20/40/60 GHz (re 1 GHz), fields:", " ".join(f"{eo_f[np.argmin(abs(F-q))]:+.2f}" for q in (20, 40, 60)),
      "| touchstone:", " ".join(f"{eo_t[np.argmin(abs(F-q))]:+.2f}" for q in (20, 40, 60)))

np.savetxt(os.path.join(HERE, "ls_extraction.csv"),
           np.column_stack([F, a_ts, a_f, n_ts, n_f, rho, eo_f, eo_t]), delimiter=",", fmt="%.5g",
           header="f_GHz,alpha_ts_dB_cm,alpha_fields_dB_cm,nm_ts,nm_fields,refl_far_end_fields,EO_fields_dB,EO_touchstone_dB", comments="")

fig, ax = plt.subplots(1, 3, figsize=(13, 4))
ax[0].plot(F, a_ts, "k-", label="touchstone"); ax[0].plot(F, a_f, "o", ms=3, color="#eb6834", label="fields")
ax[0].set_ylabel("α (dB/cm)")
ax[1].plot(F, n_ts, "k-", label="touchstone"); ax[1].plot(F, n_f, "o", ms=3, color="#eb6834", label="fields")
ax[1].set_ylabel("n_m")
ax[2].plot(F, eo_t, "k-", label="touchstone (line formula)"); ax[2].plot(F, eo_f, "o", ms=3, color="#eb6834", label="fields")
ax[2].set_ylabel("EO response re 1 GHz (dB)"); ax[2].set_ylim(top=0.5)
for a_ in ax: a_.set_xlabel("frequency (GHz)"); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=8)
fig.suptitle("L+S run, 3.24 mm straight line: touchstone vs gap fields", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "ls_extraction.png"), dpi=200)
