"""
Six-mode fit (2 mm electric-bottom eigenmodes, nearest eigen pattern aligned to the family's 15 deg pattern, A slot x10)
at all 60 monitor frequencies of the dense -40 dB run. Then the frequency behaviour of the coefficients, normalised
as in ../cordoba_8mm_wide_ebottom_60dB/smoothness.py (by A's forward CPW amplitude; backward ones also by
exp(-gamma_cpw L)): phase step between neighbouring 1 GHz points, and the group delay tau = -dphi/domega of each
B-side coefficient. A coefficient set by end physics plus propagation has a near-constant delay (phase linear in f).
Frequencies below the lowest eigen point (~7.4 GHz) use extrapolated dispersion. Outputs: dense_modefit.log,
dense_modefit.png.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); UNP = os.path.join(HERE, "unpacked")
os.environ["TDDIR"] = UNP
sys.path.insert(0, os.path.join(HERE, "../cordoba_8mm/eigen_w2mm_mag_ebottom_sweep"))
import numpy as np
import sweepfit as S
S.FTD = list(range(1, 61))
REF = {fam: S.pattern_raw(D.files[int(np.where(D.ph == 15)[0][0])]) for fam, D in S.DISP.items()}
_orig = S.pattern_at
def pattern_at(fam, f, mode):
    u, src = _orig(fam, f, mode); u = S.align(u, REF[fam]); return u / np.linalg.norm(u), src
S.pattern_at = pattern_at


def gamma(fam, f):
    D = S.DISP[fam]; n = float(D.n_of(f)); a = float(D.alpha(f))
    if fam.endswith("cpw"):
        nm = 0.5 * (float(S.DISP["e_cpw"].n_of(f)) + float(S.DISP["o_cpw"].n_of(f)))
        n = nm + (0.5 if fam.startswith("e") else -0.5) * float(S.split_cpw(f))
    return a + 1j * 2 * np.pi * f * 1e9 * n / S.C0


F = np.array(S.FTD, float); res = {}; C = {}
for f in F:
    td = S.TDData(int(f)); o = S.fit(int(f), td); x = o["x"]
    aA = 0.5 * (x["e_cpw+"] + x["o_cpw+"]); g = 0.5 * (gamma("e_cpw", f) + gamma("o_cpw", f))
    C[f] = {k: v / aA / (np.exp(-g * S.L) if k.endswith("-") else 1.0) for k, v in x.items()}
    res[f] = o["res"]
print(" f  | A CPW | B CPW | B slot")
for f in F:
    r = res[f]; print(f"{f:3.0f} | {r['A CPW']:.3f} | {r['B CPW']:.3f} | {r['B slot']:.3f}")
grp = {"CPW fwd (B)": lambda c: 0.5 * (c["e_cpw+"] - c["o_cpw+"]), "CPW bwd (B)": lambda c: 0.5 * (c["e_cpw-"] - c["o_cpw-"]),
       "CPW bwd (A, far-end refl.)": lambda c: 0.5 * (c["e_cpw-"] + c["o_cpw-"]),
       "slot fwd (B)": lambda c: 0.5 * (c["e_slot+"] - c["o_slot+"]), "slot bwd (B)": lambda c: 0.5 * (c["e_slot-"] - c["o_slot-"]),
       "strips-bottom fwd": lambda c: c["e_sb+"], "strips-bottom bwd": lambda c: c["e_sb-"],
       "A vs B fwd": lambda c: c["o_AvsB+"], "A vs B bwd": lambda c: c["o_AvsB-"]}
print("\nPhase step between neighbouring 1 GHz points (deg): median |step| and fraction of |step| > 90 deg, per band;"
      "\nand group delay (ps) from a straight-line fit of the unwrapped phase, with the rms phase deviation from that line (deg)")
bands = ((5, 20), (20, 35), (35, 50), (50, 60))
for nm, fn in grp.items():
    v = np.array([fn(C[f]) for f in F]); ph = np.angle(v); st = np.degrees(np.angle(v[1:] / v[:-1]))
    line = f"  {nm:27s}"
    for b0, b1 in bands:
        m = (F[:-1] >= b0) & (F[1:] <= b1); s = abs(st[m])
        u = np.unwrap(ph[(F >= b0) & (F <= b1)]); ff = F[(F >= b0) & (F <= b1)]
        k, c0 = np.polyfit(ff, u, 1); dev = np.degrees(np.sqrt(np.mean((u - (k * ff + c0)) ** 2)))
        tau = -k / (2 * np.pi * 1e9) * 1e12
        line += f" | {b0}-{b1}: med {np.median(s):4.0f}, >90 {np.mean(s > 90)*100:3.0f}%, tau {tau:+6.1f} ps, dev {dev:4.0f}"
    print(line)
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
fig, ax = plt.subplots(3, 1, figsize=(8.5, 9), sharex=True)
ax[0].plot(F, [res[f]["B CPW"] for f in F], "o-", color="#eb6834", ms=3, label="B CPW pattern")
ax[0].plot(F, [res[f]["A CPW"] for f in F], "s-", color="#2a78d6", ms=3, label="A CPW pattern")
ax[0].set_yscale("log"); ax[0].set_ylabel("six-mode fit residual"); ax[0].legend(frameon=False, fontsize=8); ax[0].grid(alpha=0.3, which="both")
for i, (nm, fn) in enumerate(grp.items()):
    v = np.array([fn(C[f]) for f in F]); col = plt.cm.tab10(i)
    ax[1].semilogy(F, abs(v), "o-", color=col, ms=2.5, lw=1, label=nm)
    ax[2].plot(F, np.degrees(np.unwrap(np.angle(v))), "o-", color=col, ms=2.5, lw=1)
ax[1].set_ylabel("|coefficient|"); ax[1].legend(fontsize=6.5, frameon=False, ncol=2); ax[1].grid(alpha=0.3)
ax[2].set_ylabel("phase, unwrapped (deg)"); ax[2].set_xlabel("frequency (GHz)"); ax[2].grid(alpha=0.3)
for a in ax: a.axvspan(0, 7.4, color="0.92", zorder=0)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "dense_modefit.png"), dpi=150)
