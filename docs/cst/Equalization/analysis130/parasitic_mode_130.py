"""Parasitic (ground-to-ground) mode in the L+B+S run: strength along the path, propagation constant, resonance comb.
Input: bend_path_130.npz (bend_path_130.py), lbs_bend_130.npz (bend two-port, touchstone route).
1. ratio |v_p| / |v_c| (rms over each segment) vs frequency on line 1, line 2 and at the arc stations;
   (lines: voltages averaged over one 0.18 mm cell of the periodic loading)
2. gamma_p from a free two-wave fit of the pitch-averaged v_p on line 1 (0.18 mm cut at each end), where v_p is
   above -30 dB of v_c; n_p = c Im(gamma_p) / w;
3. resonance comb f_m = m c / (2 n_p L_path), L_path = 4.11 mm (port 1 to port 2 along the path; the parasitic mode is
   reflected at both ports, where only the coplanar mode is matched); compared with the dips of the bend |S21|
   (local minima of |S21| dB after removing a smooth trend) and with the peaks of the v_p ratio on the lines.
Outputs: parasitic_mode_130.npz, printed table."""
import os, numpy as np
from scipy.optimize import least_squares
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0
d = np.load(os.path.join(HERE, "bend_path_130.npz")); F, S, VC, VP, SEG = d["F"], d["S"], d["VC"], d["VP"], d["SEG"]
b = np.load(os.path.join(HERE, "lbs_bend_130.npz")); f, SA = b["f"], b["SA"]
rms = lambda x: np.sqrt((abs(x) ** 2).mean(1))
cell = lambda X: np.array([np.convolve(x, np.ones(36) / 36, "valid") for x in X])          # average over one 0.18 mm cell
r1 = rms(cell(VP[:, SEG == 0])) / rms(cell(VC[:, SEG == 0])); r2 = rms(cell(VP[:, SEG == 4])) / rms(cell(VC[:, SEG == 4]))
arc = np.where(SEG == 2)[0]; ra = abs(VP[:, arc]) / abs(VC[:, arc])              # along the arc (2 deg steps)
# gamma_p on line 1
z = S[SEG == 0] * 1e-3; k = 36; ker = np.ones(k) / k; zs = np.convolve(z, ker, "valid"); m = (zs >= 0.18e-3) & (zs <= 2.16e-3 - 0.18e-3)
def two_wave(g, vv):
    Mx = np.stack([np.exp(-g * zs[m]), np.exp(g * zs[m])], 1); c = np.linalg.lstsq(Mx, vv, rcond=None)[0]; return c, Mx @ c - vv
n_p, a_p, res_p = np.full(len(F), np.nan), np.full(len(F), np.nan), np.full(len(F), np.nan)
for i, fr in enumerate(F):
    if 20 * np.log10(r1[i]) < -30: continue
    vv = np.convolve(VP[i, SEG == 0], ker, "valid")[m]; w = 2 * np.pi * fr * 1e9; best = None
    for n0 in np.arange(1.6, 3.4, 0.1):                       # multistart over the index
        r = lambda p: np.r_[(e := two_wave(p[0] + 1j * p[1], vv)[1]).real, e.imag]
        sol = least_squares(r, [20.0, n0 * w / C0])
        if best is None or sol.cost < best.cost: best = sol
    g = best.x[0] + 1j * best.x[1]; _, e = two_wave(g, vv)
    n_p[i], a_p[i], res_p[i] = best.x[1] * C0 / w, best.x[0] * 8.686 / 100, np.linalg.norm(e) / np.linalg.norm(vv)
ok = np.isfinite(n_p) & (res_p < 0.1)
print("parasitic mode on line 1 (fit residual < 10 %): n_p median", round(np.median(n_p[ok]), 3), "range", np.round(np.percentile(n_p[ok], [10, 90]), 3),
      "| alpha_p median", round(np.median(a_p[ok]), 2), "dB/cm |", ok.sum(), "frequencies")
for q in (20, 40, 60, 80, 100, 120):
    i = np.argmin(abs(F - q)); print(f"   {F[i]:.0f} GHz: n_p {n_p[i]:.3f}, alpha_p {a_p[i]:.2f} dB/cm, residual {100*res_p[i]:.1f} %, v_p/v_c line1 {20*np.log10(r1[i]):.1f} dB")
# dips of the bend |S21| (touchstone route) and peaks of the v_p ratio
s21 = 20 * np.log10(abs(SA[:, 1, 0])); trend = np.polyval(np.polyfit(f, s21, 3), f)
dips, _ = find_peaks(-(s21 - trend), prominence=0.04, distance=40)
pk, _ = find_peaks(20 * np.log10(r2), prominence=3, height=-30)       # above the -30 dB noise floor
L = 4.1107e-3; npm = np.median(n_p[ok]); comb = np.arange(1, 9) * C0 / (2 * npm * L) / 1e9
print("dips of bend |S21| (GHz):        ", np.round(f[dips], 1))
print("peaks of v_p/v_c on line 2 (GHz):", F[pk])
print(f"comb m c/(2 n_p L), n_p {npm:.3f}, L {L*1e3:.2f} mm:", np.round(comb, 1))
sp = np.diff(f[dips]); print("dip spacing (GHz):", np.round(sp, 1), "-> n from spacing:", round(C0 / (2 * L * np.median(sp) * 1e9), 3))
print("|v_p/v_c| in the arc (0 / 90 / 180 deg) and on the lines (rms, cell-averaged):")
for q in (1, 10, 20, 40, 60, 79, 100, 109, 130):
    i = np.argmin(abs(F - q)); print(f"   {F[i]:.0f} GHz: {ra[i,0]:.3f} / {ra[i,45]:.3f} / {ra[i,-1]:.3f}   line 1 {r1[i]:.3f}, line 2 {r2[i]:.3f}")
np.savez(os.path.join(HERE, "parasitic_mode_130.npz"), F=F, r1=r1, r2=r2, ra=ra, n_p=n_p, a_p=a_p, res_p=res_p, ok=ok, f=f, s21=s21,
         dips=f[dips], peaks=F[pk], comb=comb, npm=npm)
