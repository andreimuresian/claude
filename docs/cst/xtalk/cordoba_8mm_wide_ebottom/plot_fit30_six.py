"""30 GHz, electric bottom: TD gap fields vs the six-mode eigenmode fit (fit30_ebottom_modes.py), along the
whole line. The fit uses the interior 0.31-7.69 mm without the T-stem cell positions; the model is then
evaluated at every sample (0-8 mm, stems included) with the fitted amplitudes.
Fig. 1: |data|, |model|, |data - model| for A and B' (B mirrored onto A), CPW and slot patterns (dB re
max |A CPW|). Fig. 2: B' CPW pattern near the two ends, real part and magnitude."""
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "fit30_ebottom_modes.py")).read().split("# free extra wave")[0])
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
o = F.fit(E, O)
# full-length data and model
z = F.fd["z"]; Fp = F.fd["ports"][30.0][1]
Afull = np.stack([Fp["A"][0], Fp["A"][1]]); Bfull = np.stack([-Fp["B"][1], -Fp["B"][0]])
F.zz = z; F.idx = np.round(((z * 1e3 - 0.04) % 0.18) / 0.005).astype(int) % 36
ce, le = F.basis(E); co, lo = F.basis(O)
mA = sum(0.5 * c * o["x"][l] for c, l in zip(ce, le)) + sum(0.5 * c * o["x"][l] for c, l in zip(co, lo))
mB = sum(0.5 * c * o["x"][l] for c, l in zip(ce, le)) - sum(0.5 * c * o["x"][l] for c, l in zip(co, lo))
cpw = lambda v: (v[0] - v[1]) / 2; slot = lambda v: (v[0] + v[1]) / 2
ref = np.abs(cpw(Afull)).max(); dB = lambda v: 20 * np.log10(np.abs(v) / ref + 1e-15)
zm = z * 1e3; stem = (F.idx >= 13) & (F.idx <= 23); fitted = (~stem) & (zm >= 0.31) & (zm <= 7.69)
C = {"data": "#1f1f1e", "model": "#eb6834", "res": "#2a78d6"}
fig, ax = plt.subplots(4, 1, figsize=(10, 11), sharex=True)
for a, (lab, d, m) in zip(ax, (("line A, CPW pattern (push-pull)", cpw(Afull), cpw(mA)), ("line A, slot pattern", slot(Afull), slot(mA)),
                               ("line B, CPW pattern (push-pull)", cpw(Bfull), cpw(mB)), ("line B, slot pattern", slot(Bfull), slot(mB)))):
    a.plot(zm, dB(d), color=C["data"], lw=1.0, label="TD field")
    a.plot(zm, dB(m), "--", color=C["model"], lw=1.0, label="six-mode fit")
    a.plot(zm, dB(d - m), color=C["res"], lw=0.8, alpha=0.8, label="|TD - fit|")
    nr = lambda v: np.linalg.norm(v[fitted])
    extra = "  (the fit puts a spurious slot field on A, ~25 dB above the data)" if "A, slot" in lab else ""
    a.set_title(f"{lab}: residual {nr(d - m)/nr(d):.3f} of its own rms (fitted samples){extra}", fontsize=10, loc="left")
    a.axvspan(0, 0.31, color="0.9"); a.axvspan(7.69, 8, color="0.9")
    a.set_ylabel("dB re max |A CPW|"); a.grid(alpha=0.3)
ax[0].legend(frameon=False, ncol=3, loc="lower center", fontsize=9)
ax[0].set_ylim(-60, 5); ax[1].set_ylim(-90, -20); ax[2].set_ylim(-110, -40); ax[3].set_ylim(-110, -40)
ax[-1].set_xlabel("z along the line (mm); grey: outside the fitted window")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "fit30_six_full.png"), dpi=140)
# fig 2: ends of B CPW
d, m = cpw(Bfull), cpw(mB); s = np.abs(d[fitted]).max()
fig, ax = plt.subplots(2, 2, figsize=(10, 6), sharey="row")
for j, (lo_, hi_) in enumerate(((0, 1.5), (6.5, 8))):
    w = (zm >= lo_) & (zm <= hi_)
    ax[0, j].plot(zm[w], d[w].real / s, color=C["data"], lw=1.2, label="TD field (real part)")
    ax[0, j].plot(zm[w], m[w].real / s, "--", color=C["model"], lw=1.2, label="six-mode fit")
    ax[1, j].plot(zm[w], np.abs(d[w]) / s, color=C["data"], lw=1.2, label="|TD|")
    ax[1, j].plot(zm[w], np.abs(m[w]) / s, "--", color=C["model"], lw=1.2, label="|fit|")
    ax[1, j].plot(zm[w], np.abs(d - m)[w] / s, color=C["res"], lw=1.0, label="|TD - fit|")
    for a in ax[:, j]:
        a.axvspan(*( (0, 0.31) if j == 0 else (7.69, 8)), color="0.9"); a.grid(alpha=0.3)
    ax[0, j].set_title(("near end (port 1 side)" if j == 0 else "far end (port 2 side)") + ": line B, CPW pattern", fontsize=10)
    ax[1, j].set_xlabel("z (mm)")
ax[0, 0].set_ylabel("Re, normalised"); ax[1, 0].set_ylabel("magnitude, normalised")
ax[0, 0].legend(frameon=False, fontsize=8); ax[1, 0].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "fit30_six_ends.png"), dpi=140)
for lab, d_, m_ in (("A CPW", cpw(Afull), cpw(mA)), ("B CPW", cpw(Bfull), cpw(mB))):
    r = np.abs(d_ - m_); n0 = np.sqrt(np.mean(np.abs(d_[fitted]) ** 2))
    print(lab, "|TD - fit| / rms(TD), non-stem samples, by window:",
          " ".join(f"{a:.2f}-{b:.2f}:{np.sqrt(np.mean(r[(zm>=a)&(zm<b)&~stem]**2))/n0:.2f}" for a, b in ((0, .31), (.31, 1), (1, 2), (2, 6), (6, 7), (7, 7.69), (7.69, 8.001))))
