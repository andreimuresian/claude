"""
Smoothness test of the six-mode fit across the 12 monitor frequencies (this run, -44.5 dB).

Coefficients made comparable across frequency:
* each eigen pattern is aligned (complex scale) to its family's 15 deg pattern, so a pattern switch between
  eigen points does not change the amplitude's phase reference;
* every amplitude is divided by A's forward CPW amplitude a_A = (e_cpw+ + o_cpw+)/2 (removes the source spectrum
  and the port phase);
* backward waves (referenced at z = L) are further divided by exp(-gamma_cpw L): they become conversion
  coefficients at the far end of the forward CPW wave that arrives there.
Then each coefficient should vary slowly with f if it describes end physics.

Tests: (1) coefficient table and a plot; (2) leave-one-out: each interior frequency predicted from the others
(cubic spline on Re and Im of the coefficients, the eigen dispersion evaluated at the held-out f), EO of the
predicted model vs the data EO on the fitted samples; compared with interpolating the data EO directly.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["TDDIR"] = HERE
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/eigen_w2mm_mag_ebottom_sweep"))
import numpy as np
from scipy.interpolate import CubicSpline
import sweepfit as S

# --- consistent pattern phase reference per family (15 deg pattern) ---
REF = {fam: S.pattern_raw(D.files[int(np.where(D.ph == 15)[0][0])]) for fam, D in S.DISP.items()}
_orig = S.pattern_at
def pattern_at(fam, f, mode):
    u, src = _orig(fam, f, mode)
    u = S.align(u, REF[fam]); return u / np.linalg.norm(u), src
S.pattern_at = pattern_at

E = ("e_cpw", "e_slot", "e_sb"); O = ("o_cpw", "o_slot", "o_AvsB")
F = np.array(S.FTD, float)
TD = {f: S.TDData(int(f)) for f in F}
fits = {f: S.fit(int(f), TD[f]) for f in F}
labels = list(fits[F[0]]["x"].keys())


def gamma(fam, f):
    D = S.DISP[fam]; n = float(D.n_of(f)); a = float(D.alpha(f))
    if fam.endswith("cpw"):
        nm = 0.5 * (float(S.DISP["e_cpw"].n_of(f)) + float(S.DISP["o_cpw"].n_of(f)))
        n = nm + (0.5 if fam.startswith("e") else -0.5) * float(S.split_cpw(f))
    return a + 1j * 2 * np.pi * f * 1e9 * n / S.C0


def coeffs(x, f):
    aA = 0.5 * (x["e_cpw+"] + x["o_cpw+"])
    g = 0.5 * (gamma("e_cpw", f) + gamma("o_cpw", f))
    return {k: v / aA / (np.exp(-g * S.L) if k.endswith("-") else 1.0) for k, v in x.items()}


C = {f: coeffs(fits[f]["x"], f) for f in F}
print("Normalised coefficients |c| (phase deg); forward / a_A, backward / (a_A exp(-gamma L)):")
print("  f   " + " ".join(f"{k:>17s}" for k in labels))
for f in F:
    print(f"{f:4.0f}  " + " ".join(f"{abs(C[f][k]):8.2e}({np.degrees(np.angle(C[f][k])):+5.0f})" for k in labels))
# B-side combinations of the pairs (what B sees): (e - o)/2 for cpw and slot
print("\nB-side pair combinations (e - o)/2 and A-side (e + o)/2, normalised:")
for pr in ("cpw+", "cpw-", "slot+", "slot-"):
    row = [0.5 * (C[f]["e_" + pr] - C[f]["o_" + pr]) for f in F]
    print(f"  B {pr:6s} " + " ".join(f"{abs(v):.1e}({np.degrees(np.angle(v)):+4.0f})" for v in row))


def model_X(xn, f, td):
    """EO B/A on the fitted samples from normalised coefficients xn at frequency f."""
    g = 0.5 * (gamma("e_cpw", f) + gamma("o_cpw", f)); aA = 1.0
    x = {k: v * (np.exp(-g * S.L) if k.endswith("-") else 1.0) for k, v in xn.items()}
    ce, le, _ = S.basis(E, f, td); co, lo, _ = S.basis(O, f, td)
    v = np.array([x[k] for k in le + lo])
    colsA = [0.5 * c for c in ce] + [0.5 * c for c in co]; colsB = [0.5 * c for c in ce] + [-0.5 * c for c in co]
    mA = np.array([S.cpw(c) for c in colsA]).T @ v; mB = np.array([S.cpw(c) for c in colsB]).T @ v
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(mB * w) / np.mean(mA * w)


def data_X(f, td):
    bo = 2 * np.pi * f * 1e9 * S.NG_OPT / S.C0; w = np.exp(1j * bo * (td.zz - S.L))
    return np.mean(S.cpw(td.Bp) * w) / np.mean(S.cpw(td.A) * w)


Xd = np.array([data_X(f, TD[f]) for f in F]); Xm = np.array([model_X(C[f], f, TD[f]) for f in F])
print("\nEO on the fitted samples (dB): data " + " ".join(f"{20*np.log10(abs(v)):6.1f}" for v in Xd))
print("                         model fit " + " ".join(f"{20*np.log10(abs(v)):6.1f}" for v in Xm))

print("\nLeave-one-out (interior frequencies): EO error of the modal interpolation vs direct interpolation of X")
print("  f  | modal: err dB  |dX|/|X| | direct spline on Re/Im X: err dB |dX|/|X|")
lo_m, lo_d = [], []
for i in range(1, len(F) - 1):
    keep = np.arange(len(F)) != i; f = F[i]
    cn = {k: CubicSpline(F[keep], [C[g][k] for g in F[keep]])(f) for k in labels}
    xm = model_X(cn, f, TD[f])
    xd = CubicSpline(F[keep], Xd[keep])(f)
    em, ed = abs(xm - Xd[i]) / abs(Xd[i]), abs(xd - Xd[i]) / abs(Xd[i]); lo_m.append(em); lo_d.append(ed)
    print(f"  {f:3.0f} | {20*np.log10(abs(xm/Xd[i])):+6.2f}  {em:5.2f}   | {20*np.log10(abs(xd/Xd[i])):+6.2f}  {ed:5.2f}")
print(f"  median |dX|/|X|: modal {np.median(lo_m):.2f}, direct {np.median(lo_d):.2f}")

import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
groups = {"CPW fwd (B side)": lambda c: 0.5 * (c["e_cpw+"] - c["o_cpw+"]),
          "CPW bwd (B side)": lambda c: 0.5 * (c["e_cpw-"] - c["o_cpw-"]),
          "slot fwd (B side)": lambda c: 0.5 * (c["e_slot+"] - c["o_slot+"]),
          "strips-bottom fwd": lambda c: c["e_sb+"], "strips-bottom bwd": lambda c: c["e_sb-"],
          "A vs B fwd": lambda c: c["o_AvsB+"], "A vs B bwd": lambda c: c["o_AvsB-"]}
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for i, (nm, fn) in enumerate(groups.items()):
    v = np.array([fn(C[f]) for f in F]); col = plt.cm.tab10(i)
    ax[0].semilogy(F, abs(v), "o-", color=col, label=nm, ms=4)
    ax[1].plot(F, np.degrees(np.unwrap(np.angle(v))), "o-", color=col, ms=4)
ax[0].set_xlabel("f (GHz)"); ax[0].set_ylabel("|coefficient| (re A forward CPW)"); ax[0].legend(fontsize=7, frameon=False)
ax[1].set_xlabel("f (GHz)"); ax[1].set_ylabel("phase, unwrapped (deg)")
for a in ax: a.grid(alpha=0.3); a.axvspan(37.5, 62, color="0.9", zorder=0)
ax[0].set_title("six-mode fit coefficients (shaded: B fit residual > 0.2)", fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "smoothness_coeffs.png"), dpi=150)
