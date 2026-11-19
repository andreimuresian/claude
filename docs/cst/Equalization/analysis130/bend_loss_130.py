"""Where is the bend loss? Forward-wave amplitude along the L+B+S path (calibrated coplanar voltage v_c, bend_path_130.py).

Sections: line 1 (buried, z 0..2.16), rise 1 (50 um), raised path = raised straight + arc + raised straight
(s = 2.215 .. 2.975 mm, constant cross-section: metal on the cladding), rise 2 (50 um), line 2 (buried).
Fits of V = A e^{-gamma s} + B e^{+gamma s} (A: wave travelling from port 1 towards port 2):
  lines: gamma fixed to the L+S line value, pitch average, 0.18 mm cut at the ports;
  raised path: gamma free (no periodic loading there), multistart over the index.
Forward amplitudes at the section boundaries give, in dB: rise 1, raised path, rise 2. A small impedance step at a rise
shifts the forward amplitude by 20 log|1 + Gamma| at rise 1 and 20 log|1 - Gamma| at rise 2: their sum is free of it.
Also: parasitic reflection at the ports from the v_p fits on lines 1 and 2 (|backward / forward| at the port plane),
and the bend delay from the slope of the S21 phase (both routes, lbs_bend_130.npz).
Outputs: bend_loss_130.npz, printed table."""
import os, numpy as np
from scipy.optimize import least_squares
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0
d = np.load(os.path.join(HERE, "bend_path_130.npz")); F, S, VC, VP, SEG = d["F"], d["S"] * 1e-3, d["VC"], d["VP"], d["SEG"]
b = np.load(os.path.join(HERE, "lbs_bend_130.npz")); gF = (lambda g: g)(None)
import sys; sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../..")))
from mzm_interconnect.physics import fit_alpha_scaled, fit_nm_saturating
w = 2 * np.pi * F * 1e9
gL = fit_alpha_scaled(F, *b["pa"]) * 100 / 8.686 + 1j * fit_nm_saturating(F, *b["pn"]) * w / C0
def lsq(g, s, v):
    M = np.stack([np.exp(-g * s), np.exp(g * s)], 1); c = np.linalg.lstsq(M, v, rcond=None)[0]; return c, np.linalg.norm(M @ c - v) / np.linalg.norm(v)
ker = np.ones(36) / 36; sm = lambda x: np.convolve(x, ker, "valid")
def line_fit(seg, s0, s1, V, g):
    s = S[SEG == seg]; o = np.argsort(s); s, v = s[o], V[SEG == seg][o]; ss, vv = sm(s), sm(v); m = (ss >= s0) & (ss <= s1)
    return lsq(g, ss[m], vv[m])
R0, R1 = 2.215e-3, 2.975e-3; mr = (S >= R0) & (S <= R1)
out = {k: np.full(len(F), np.nan, complex) for k in ("A1p", "Ars", "Are", "A2p", "gr")}; resr = np.full(len(F), np.nan)
for i in range(len(F)):
    c1, _ = line_fit(0, 0.18e-3, 2.16e-3, VC[i], gL[i]); out["A1p"][i] = c1[0] * np.exp(-gL[i] * 2.16e-3)
    s2 = S[SEG == 4] - S[SEG == 4].min(); o = np.argsort(s2); ss, vv = sm(s2[o]), sm(VC[i][SEG == 4][o]); m = (ss <= 1.08e-3 - 0.18e-3)
    c2, _ = lsq(gL[i], ss[m], vv[m]); out["A2p"][i] = c2[0]
    sr = S[mr] - R0; vr = VC[i][mr]; best = None
    for n0 in np.arange(1.3, 2.6, 0.1):
        r = lambda p: np.r_[(e := (np.stack([np.exp(-(p[0] + 1j * p[1]) * sr), np.exp((p[0] + 1j * p[1]) * sr)], 1) @ lsq(p[0] + 1j * p[1], sr, vr)[0] - vr)).real, e.imag]
        sol = least_squares(r, [30.0, n0 * w[i] / C0], bounds=([-500, 0], [500, 10 * w[i] / C0]))
        if best is None or sol.cost < best.cost: best = sol
    g = best.x[0] + 1j * best.x[1]; c, resr[i] = lsq(g, sr, vr); out["Ars"][i], out["Are"][i], out["gr"][i] = c[0], c[0] * np.exp(-g * (R1 - R0)), g
dB = lambda x: 20 * np.log10(abs(x))
rise1, raised, rise2 = dB(out["Ars"] / out["A1p"]), dB(out["Are"] / out["Ars"]), dB(out["A2p"] / out["Are"]); total = dB(out["A2p"] / out["A1p"])
ar, nr = out["gr"].real * 8.686 / 100, out["gr"].imag * C0 / w
S21B = dB(b["SB"][:, 1, 0])
print(" f GHz | raised path: alpha dB/cm, n, fit res | forward-wave change dB: rise1 / raised path (0.76 mm) / rise2 / rises together / total | field-route |S21|")
for q in (10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130):
    i = np.argmin(abs(F - q))
    print(f"{F[i]:5.0f} | {ar[i]:6.2f} {nr[i]:.3f} {100*resr[i]:4.1f}% | {rise1[i]:+.3f} / {raised[i]:+.3f} / {rise2[i]:+.3f} / {rise1[i]+rise2[i]:+.3f} / {total[i]:+.3f} | {S21B[i]:+.3f}")
# parasitic reflection at the ports
def gp(seg, at_port_s):
    res = []
    for i in range(len(F)):
        s = S[SEG == seg]; o = np.argsort(s); ss, vv = sm(s[o]), sm(VP[i][SEG == seg][o]); m = (ss >= ss.min() + 0.18e-3) & (ss <= ss.max() - 0.18e-3)
        best = None
        for n0 in np.arange(1.8, 3.0, 0.1):
            r = lambda p: np.r_[(e := (np.stack([np.exp(-(p[0] + 1j * p[1]) * ss[m]), np.exp((p[0] + 1j * p[1]) * ss[m])], 1) @ lsq(p[0] + 1j * p[1], ss[m], vv[m])[0] - vv[m])).real, e.imag]
            sol = least_squares(r, [20.0, n0 * w[i] / C0])
            if best is None or sol.cost < best.cost: best = sol
        g = best.x[0] + 1j * best.x[1]; c, rr = lsq(g, ss[m], vv[m]); sp = at_port_s(ss)
        res.append((abs(c[1] * np.exp(g * sp) / (c[0] * np.exp(-g * sp))), rr, g.imag * C0 / w[i]))
    return np.array(res)
P1 = gp(0, lambda ss: 0.0)                                       # port 1 at s = 0: backward/forward = B/A
P2 = gp(4, lambda ss: S[SEG == 4].max())                        # port 2 at the end of line 2: A/B there -> invert below
P2[:, 0] = 1 / P2[:, 0]
strong = (np.array([np.sqrt((abs(VP[i][SEG == 0]) ** 2).mean() / (abs(VC[i][SEG == 0]) ** 2).mean()) for i in range(len(F))]) > 0.05)
print("parasitic reflection |Gamma_p| at port 1 (where v_p/v_c > 0.05 on line 1): median", np.round(np.median(P1[strong, 0]), 3), "range", np.round(np.percentile(P1[strong, 0], [10, 90]), 3))
print("parasitic reflection |Gamma_p| at port 2: median", np.round(np.median(P2[strong, 0]), 3), "range", np.round(np.percentile(P2[strong, 0], [10, 90]), 3))
# delay from the phase slope (both routes): phase = phi0 - w tau, fitted over 20-130 GHz
f, SA, SB = b["f"], b["SA"], b["SB"]
for lab, ff, s21 in (("touchstone", f, SA[:, 1, 0]), ("fields", F, SB[:, 1, 0])):
    k = (ff >= 1); ph = np.unwrap(np.angle(s21[k])); ww = 2 * np.pi * ff[k] * 1e9; m = ff[k] >= 20
    c = np.polyfit(ww[m], ph[m], 1); print(f"{lab}: delay from phase slope (20-130 GHz) {-c[0]*1e12:.3f} ps, phase offset at 0 Hz {np.degrees(c[1]):+.2f} deg")
np.savez(os.path.join(HERE, "bend_loss_130.npz"), F=F, rise1=rise1, raised=raised, rise2=rise2, total=total, ar=ar, nr=nr, resr=resr, S21B=S21B, P1=P1, P2=P2, strong=strong)
