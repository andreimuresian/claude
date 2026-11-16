"""Line A gap voltage V(z): uniform-line model from the touchstone vs CST gap fields, Istanbul 8.75 mm runs with both.
Model: alpha, n_m, Zc fitted from the line A two-port (ports 1 near, 2 far of the s4p; line B ports in 50 ohm) by
extract_line_fit (the GUI extraction); V(z) = V+ (exp(-g z) + G_L exp(-2 g L) exp(g z)), G_L = (50 - Zc)/(50 + Zc),
source and load = the 50 ohm CST ports. The field V(z) is the push-pull gap field (xtalk_fields), median-filtered over
9 points (45 um) to remove the single-point dips every 0.2 mm. One complex scale factor (field units) is fitted per
frequency; the error is ||V_field - k V_model|| / ||V_field||.
EO: |H_A| normalised to its mean over 3-10.7 GHz, formula (same fits, n_g 2.27, 50/50 ohm) vs fields.
Outputs: vz_touchstone_vs_fields.png, printed table."""
import os, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); X = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(X, "istanbul_run_a")); sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.signal import medfilt
from mzm_interconnect import parameters as P, xtalk_fields as XF
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import eo_transfer, C0
from load_fields import load
p = P.defaults(); p["Rt_R"] = 50.0; p["Zs_R"] = 50.0
LA, BAD = "e-field (f=1) [1]_lineA.zip", (2.0, 15.0)
RUNS = {"(a) bare line": (load(skip_f=BAD), os.path.join(X, "istanbul_run_a", "v0_istanbul_rf_line.s4p")),
        "(a) wide substrate": (load(base=os.path.join(X, "istanbul_run_a_wide"), a_zip=LA, skip_f=BAD), os.path.join(X, "istanbul_run_a_wide", "v0_istanbul_rf_line_625.s4p")),
        "(c) launch pads": (load(base=os.path.join(X, "istanbul_run_c"), a_zip=LA, drop="first", skip_f=BAD + (1.0,)), os.path.join(X, "istanbul_run_c", "v0_istanbul_rf_lineLaunch.s4p"))}
L, tmp, QF = 8.75e-3, tempfile.mkdtemp(), (10.0, 30.0, 58.0)
fig, ax = plt.subplots(len(RUNS), 4, figsize=(17, 3.3 * len(RUNS)))
print("run | V(z) error 10/30/58 GHz (%), median 3-60 | EO formula - fields: rms, max (dB), ripple corr | Zc fit 30 GHz | far-end |G| model vs fields 30/58")
for r, (name, (fd, s4p)) in enumerate(RUNS.items()):
    o = XF.eo_crosstalk_fields(p, fd); f = o["f_GHz"]; z = o["z"] - o["z"][0]
    tp = os.path.join(tmp, f"r{r}"); rf.Network(s4p).subnetwork([0, 1]).write_touchstone(tp); fit = extract_line_fit(tp + ".s2p", L * 1e3)
    al, nm, zc = fit.alpha_dB_cm(f) * 100 / 8.686, fit.nm(f), fit.Zc(f)
    errs, Gm, Gf, pan = [], [], [], {}
    for i, q in enumerate(f):
        Vp, Vm = o["V"][q]["A"]; V = 0.5 * (Vp + Vm); V = medfilt(V.real, 9) + 1j * medfilt(V.imag, 9)
        g = al[i] + 1j * 2 * np.pi * q * 1e9 * nm[i] / C0; GL = (50 - zc[i]) / (50 + zc[i])
        Vmod = np.exp(-g * z) + GL * np.exp(-2 * g * z[-1]) * np.exp(g * z)
        k = np.vdot(Vmod, V) / np.vdot(Vmod, Vmod); errs.append(np.linalg.norm(V - k * Vmod) / np.linalg.norm(V))
        M = np.c_[np.exp(-g * z), np.exp(g * z)]; c, *_ = np.linalg.lstsq(M, V, rcond=None)   # field standing wave, model gamma
        Gf.append(abs(c[1] * np.exp(g * z[-1]) / (c[0] * np.exp(-g * z[-1])))); Gm.append(abs(GL))
        if q in QF: pan[q] = (abs(V) / np.mean(abs(V)), abs(k * Vmod) / np.mean(abs(V)))
    errs = 100 * np.array(errs)
    H, _ = eo_transfer(f, fit.alpha_dB_cm(f), nm, zc, L, 2.27, 50.0, 50.0); ref = (f >= 3) & (f <= 10.7)
    nd = lambda h: 20 * np.log10(abs(h) / np.mean(abs(h)[ref])); yF, yM = nd(o["I_A"]), nd(H); d = yF - yM
    at = lambda y, q: y[np.argmin(abs(f - q))]
    print(f"{name:18s} | {at(errs, 10):.1f} {at(errs, 30):.1f} {at(errs, 58):.1f}, {np.median(errs[f >= 3]):.1f} | {np.sqrt(np.mean(d**2)):.2f}, {abs(d).max():.2f}, "
          f"{np.corrcoef(np.diff(yF), np.diff(yM))[0, 1]:+.2f} | {fit.Zc(np.array([30.0]))[0].real:.1f} | {at(np.array(Gm), 30):.3f} vs {at(np.array(Gf), 30):.3f}, {at(np.array(Gm), 58):.3f} vs {at(np.array(Gf), 58):.3f}")
    for c_, q in enumerate(QF):
        a = ax[r, c_]; vf, vm = pan[q]
        a.plot(z * 1e3, vf, color="#eb6834", lw=1.0, label="CST gap fields"); a.plot(z * 1e3, vm, "k--", lw=1.5, label="uniform line from touchstone")
        a.set_title(f"{name}: |V(z)| at {q:g} GHz (error {at(errs, q):.1f} %)", fontsize=9); a.set_ylim(0.7, 1.35); a.grid(alpha=0.3)
        if r == len(RUNS) - 1: a.set_xlabel("z (mm)")
    a = ax[r, 3]; a.plot(f, yF, "o-", color="#eb6834", ms=2.5, lw=1.2, label="fields"); a.plot(f, yM, "k--", lw=1.5, label="touchstone formula")
    a.set_title(f"{name}: EO response (dB)", fontsize=9); a.set_ylim(-3, 1); a.set_xlim(0, 60); a.grid(alpha=0.3)
    if r == len(RUNS) - 1: a.set_xlabel("frequency (GHz)")
ax[0, 0].legend(frameon=False, fontsize=8); ax[0, 3].legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "vz_touchstone_vs_fields.png"), dpi=150)
