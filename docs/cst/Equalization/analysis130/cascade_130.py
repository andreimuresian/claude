"""Step 3: the offline cascade against the full equaliser run, 0-130 GHz.
Cascade: port 1 | line 2.70 mm | bend | line 1.44 mm | bend | line 1.44 mm | port 2, 50 ohm source and load.
  line : gamma = physical fit of the L+S field alpha, n_m; Zc = smooth fit of the L+S touchstone Zc (lbs_bend_130.py)
  ports: the L+S port block (series Ls + shunt Cp) at each end
  bend : L+B+S bend block, touchstone route, referenced to Zc (lbs_bend_130.py), in three versions:
         (a) cubic: |S21| dB, S21 phase, Re and Im S11 = one cubic in f over 1-130 GHz, fitted outside +/-2.5 GHz of the dips;
         (b) bridged: data kept outside the dip windows, each window bridged by a cubic spline (local);
         (c) raw: as extracted, dips kept.
Compared with the full run: S21 and S11 (touchstone), EO response (fields, full_eq_eo_130.csv, re own 1 GHz) and the
voltage profile V(z) on the three lines (pitch-averaged fields vs model, one complex scale per frequency).
EO of the cascade: H = sum_k p_k int V_k(s) exp(j w t_opt) ds, p = (+1, +1, -1), n_g 2.27, light delay in each bend =
slope delay of the bend model (5.03 ps).
Outputs: cascade_130.npz, cascade_130.png, printed table."""
import os, sys, io, contextlib, runpy
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
C0, NG, GAP = 299792458.0, 2.27, 4.45e-6
with contextlib.redirect_stdout(io.StringIO()):
    lb = runpy.run_path(os.path.join(HERE, "lbs_bend_130.py"))
line, ports, pp, f, SA, Zf = lb["line"], lb["ports"], lb["pp"], lb["f"], lb["SA"], lb["Z"]
PM = np.load(os.path.join(HERE, "parasitic_mode_130.npz")); dips = PM["dips"]
far = np.min([abs(f - d) for d in dips], 0) > 2.5
from scipy.interpolate import CubicSpline
def smooth_bend(fill):
    """fill: 'cubic' = one cubic over 1-130 GHz fitted outside the dips; 'bridge' = data kept outside the dip windows,
    each +/-2.5 GHz window bridged by a cubic spline through the data outside the windows (decimated to 1 GHz)."""
    if fill == "cubic":
        sm = lambda y: np.polyval(np.polyfit(f[far], y[far], 3), f)
    else:
        keep = far & (np.r_[0, np.diff(np.floor(f))] > 0)                              # one point per GHz outside the dips
        sm = lambda y: np.where(far, y, CubicSpline(f[keep], y[keep])(f))
    mag = 10 ** (sm(20 * np.log10(abs(SA[:, 1, 0]))) / 20); ph = sm(np.unwrap(np.angle(SA[:, 1, 0])))
    s11 = sm(SA[:, 0, 0].real) + 1j * sm(SA[:, 0, 0].imag)
    out = np.zeros_like(SA); out[:, 0, 0] = out[:, 1, 1] = s11; out[:, 1, 0] = out[:, 0, 1] = mag * np.exp(1j * ph); return out
SS, SSb = smooth_bend("cubic"), smooth_bend("bridge")
tau = -np.polyfit(2 * np.pi * f[f >= 20] * 1e9, np.unwrap(np.angle(SA[f >= 20, 1, 0])), 1)[0]
F = np.r_[np.arange(1, 61), np.arange(62, 131, 2)].astype(float); w = 2 * np.pi * F * 1e9
def on_F(S):
    out = np.zeros((len(F), 2, 2), complex)
    for a in range(2):
        for b in range(2):
            m = np.interp(F, f, abs(S[:, a, b])); p = np.interp(F, f, np.unwrap(np.angle(S[:, a, b]))); out[:, a, b] = m * np.exp(1j * p)
    return out
gF, ZF = line(F)
def s2a_Z(S, Z): return np.array([rf.network.s2a(S[i:i + 1], Z[i])[0] for i in range(len(Z))])
BEND = {"smoothed": s2a_Z(on_F(SS), ZF), "bridged": s2a_Z(on_F(SSb), ZF), "raw": s2a_Z(on_F(SA), ZF)}
def T(g, Z, L): return np.array([[np.cosh(g * L), Z * np.sinh(g * L)], [np.sinh(g * L) / Z, np.cosh(g * L)]]).transpose(2, 0, 1)
SECT = [(2.70e-3, +1), (1.44e-3, +1), (1.44e-3, -1)]
P1, P2 = ports(F, pp[0] * 1e-12, pp[1] * 1e-15)
def cascade(bk, ds=5e-6):
    Bm = BEND[bk]; Tt = P1.copy()
    for j, (L, _) in enumerate(SECT):
        Tt = Tt @ T(gF, ZF, L)
        if j < 2: Tt = Tt @ Bm
    Tt = Tt @ P2; S = rf.network.a2s(Tt, 50.0)
    Zin = (Tt[:, 0, 0] * 50 + Tt[:, 0, 1]) / (Tt[:, 1, 0] * 50 + Tt[:, 1, 1]); VI = np.stack([Zin / (Zin + 50), 1 / (Zin + 50)], 1)[:, :, None]
    VI = np.linalg.solve(P1, VI); H = np.zeros(len(F), complex); t0 = np.zeros(len(F)); prof = []
    for j, (L, p) in enumerate(SECT):
        s = np.arange(0, L + ds / 2, ds); V = VI[:, 0] * np.cosh(gF[:, None] * s) - ZF[:, None] * VI[:, 1] * np.sinh(gF[:, None] * s)
        H += p * np.trapezoid(V * np.exp(1j * w[:, None] * (t0[:, None] + NG * s[None, :] / C0)), s, axis=1); prof.append((s, V))
        VI = np.linalg.solve(T(gF, ZF, L), VI); t0 = t0 + NG * L / C0
        if j < 2: VI = np.linalg.solve(Bm, VI); t0 = t0 + tau
    return S, H, prof
full = rf.Network(os.path.join(HERE, "..", "full equalizer", "130 GHz", "BASELINE - FULL EQUALIZER_130 GHz.s2p")); fS = full.f / 1e9
cplx = lambda x: np.interp(F, fS, abs(x)) * np.exp(1j * np.interp(F, fS, np.unwrap(np.angle(x))))
S21r, S11r = cplx(full.s[:, 1, 0]), cplx(full.s[:, 0, 0])
EQ = np.loadtxt(os.path.join(HERE, "full_eq_eo_130.csv"), delimiter=",", skiprows=1); eo_ref = EQ[:, 4]
# field V(z) of the full run, pitch-averaged, buried metal minus 0.09 mm at each end
D = os.path.join(HERE, "..", "full equalizer", "130 GHz"); LINES = {"L1": (0.0, 2.70e-3, +1), "L2": (1.26e-3, 2.70e-3, -1), "L3": (1.26e-3, 2.70e-3, +1)}
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
VF = {}
for ln, (z0, z1, dr) in LINES.items():
    z, Ep = load(f"{ln}_gap+.txt"); _, Em = load(f"{ln}_gap-.txt"); ker = np.ones(36) / 36
    zs = np.convolve(z, ker, "valid"); Vs = np.array([np.convolve(v, ker, "valid") for v in GAP / 2 * (Ep - Em)]); m = (zs >= z0 + 0.09e-3) & (zs <= z1 - 0.09e-3)
    VF[ln] = ((zs[m] - z0) if dr > 0 else (z1 - zs[m]), Vs[:, m])
dB = lambda x: 20 * np.log10(abs(x)); db0 = lambda h: 20 * np.log10(abs(h) / abs(h[0])); res = {}
for bk in BEND:
    S, H, prof = cascade(bk); eo = db0(H); d_eo = eo - eo_ref; d21 = dB(S[:, 1, 0]) - dB(S21r); d11 = abs(S[:, 0, 0]) - abs(S11r)
    dph = np.degrees(np.angle(S[:, 1, 0] / S21r)); err = []
    for i in range(len(F)):
        mv, fv = [], []
        for k, ln in enumerate(LINES):
            s_, Vm = prof[k]; sf, Vf = VF[ln]; mv.append(np.interp(sf, s_, Vm[i].real) + 1j * np.interp(sf, s_, Vm[i].imag)); fv.append(Vf[i])
        mv, fv = np.concatenate(mv), np.concatenate(fv); c = np.vdot(mv, fv) / np.vdot(mv, mv); err.append(np.linalg.norm(c * mv - fv) / np.linalg.norm(fv))
    res[bk] = dict(S=S, H=H, eo=eo, d_eo=d_eo, d21=d21, d11=d11, dph=dph, err=np.array(err))
    for lo, hi in ((1, 60), (62, 130), (1, 130)):
        m = (F >= lo) & (F <= hi)
        print(f"bend {bk:8s} {lo:3d}-{hi:3d} GHz: EO rms {np.sqrt(np.mean(d_eo[m]**2)):.3f} max {abs(d_eo[m]).max():.3f} dB | |S21| rms {np.sqrt(np.mean(d21[m]**2)):.3f} max {abs(d21[m]).max():.3f} dB"
              f" | S21 phase max {abs(dph[m]).max():.1f} deg | |S11| max diff {abs(d11[m]).max():.3f} | V(z) median {100*np.median(res[bk]['err'][m]):.1f} % max {100*res[bk]['err'][m].max():.1f} %")
print(" f GHz | EO re 1 GHz (dB): fields / cubic / bridged / raw | |S21| dB: CST / cubic / bridged / raw")
for q in (10, 20, 40, 60, 70, 80, 90, 100, 110, 116, 120, 130):
    i = np.argmin(abs(F - q)); print(f"{q:5d}  | {eo_ref[i]:+.2f} / {res['smoothed']['eo'][i]:+.2f} / {res['bridged']['eo'][i]:+.2f} / {res['raw']['eo'][i]:+.2f} | {dB(S21r[i]):+.2f} / {dB(res['smoothed']['S'][i,1,0]):+.2f} / {dB(res['bridged']['S'][i,1,0]):+.2f} / {dB(res['raw']['S'][i,1,0]):+.2f}")
np.savez(os.path.join(HERE, "cascade_130.npz"), F=F, eo_ref=eo_ref, S21r=S21r, S11r=S11r, **{f"{k}_{q}": res[k][q] for k in res for q in ("S", "eo", "d_eo", "d21", "err")})
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
fig, ax = plt.subplots(1, 3, figsize=(14, 4.2)); STY = {"smoothed": ("-", "#0E2268", "cubic smoothing"), "bridged": ("--", "#2A78D6", "local bridging"), "raw": (":", "#9AA0AC", "raw bend (dips kept)")}
ax[0].plot(F, eo_ref, "o", ms=3, color="#EB6834", label="full run (fields)"); ax[1].plot(F, dB(S21r), "o", ms=3, color="#EB6834", label="full run (CST)")
for k, (ls, c, lab) in STY.items():
    ax[0].plot(F, res[k]["eo"], ls, color=c, lw=1.5, label=f"cascade, {lab}"); ax[1].plot(F, dB(res[k]["S"][:, 1, 0]), ls, color=c, lw=1.5, label=f"cascade, {lab}")
    ax[2].plot(F, res[k]["d_eo"], ls, color=c, lw=1.5, label=f"EO error, {lab}")
ax[0].set_ylim(-2.5, 0); ax[0].set_ylabel("EO re 1 GHz (dB)"); ax[1].set_ylim(-6, 0); ax[1].set_ylabel("|S$_{21}$| (dB)")
ax[2].axhline(0, color="0.4", lw=0.8); ax[2].axhspan(-0.05, 0.05, color="#F1F3F8", zorder=0); ax[2].set_ylim(-0.4, 0.4); ax[2].set_ylabel("EO: cascade − fields (dB)")
for a in ax: a.set_xlim(0, 130); a.set_xlabel("Frequency (GHz)"); a.grid(alpha=0.3); a.legend(frameon=False, fontsize=8.5, loc="lower left")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "cascade_130.png"), dpi=200)
