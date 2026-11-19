"""Full equaliser run, 0-130 GHz: steps 1-2 of the validation.
Step 1: line parameters per fold (forward/backward fit, gamma free, cell average, 0.18 mm cut) against the L+S fields;
        bend 1 and bend 2 two-ports from the waves on both sides (symmetric reciprocal block), against the L+B+S bend.
Step 2: parasitic (ground-to-ground) voltage: rms |v_p|/|v_c| on L1, L2, L3 (cell-averaged) against the L+B+S lines;
        profile along the path; dips of the full |S21| (deviation from a smooth cubic) against the L+B+S comb and the
        comb expected for a parasitic wave trapped over the whole 7.32 mm path.
Inputs: full equaliser 130 GHz exports, full_eq_path_130.npz, ls_extraction_130.npz, lbs_bend_130.npz, parasitic_mode_130.npz.
Outputs: full_eq_analysis_130.npz, printed tables."""
import os, numpy as np, skrf as rf
from scipy.optimize import least_squares
from scipy.signal import find_peaks
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0; D = os.path.join(HERE, "..", "full equalizer", "130 GHz"); GAP = 4.45e-6
LINES = {"L1": (0.0, 2.70e-3, +1), "L2": (1.26e-3, 2.70e-3, -1), "L3": (1.26e-3, 2.70e-3, +1)}
LS = np.load(os.path.join(HERE, "ls_extraction_130.npz")); LB = np.load(os.path.join(HERE, "lbs_bend_130.npz")); PM = np.load(os.path.join(HERE, "parasitic_mode_130.npz"))
def load(fn):
    d = np.loadtxt(os.path.join(D, fn), skiprows=2); fr = np.unique(d[:, 0]); z = d[d[:, 0] == fr[0], 3] * 1e-3
    o = np.argsort(z); return fr, z[o], (d[:, 6] + 1j * d[:, 7]).reshape(len(fr), len(z))[:, o]
def two(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
fitp = {}
for ln, (z0, z1, _) in LINES.items():
    F, z, Ep = load(f"{ln}_gap+.txt"); _, _, Em = load(f"{ln}_gap-.txt"); V = GAP / 2 * (Ep - Em); w = 2 * np.pi * F * 1e9
    ker = np.ones(36) / 36; zs = np.convolve(z, ker, "valid"); m = (zs >= z0 + 0.18e-3) & (zs <= z1 - 0.18e-3); G, Cc, Rr = [], [], []
    for i in range(len(F)):
        vs = np.convolve(V[i], ker, "valid")[m]; g0 = [np.interp(F[i], LS["F"], LS["aF"]) * 100 / 8.686, np.interp(F[i], LS["F"], LS["nF"]) * w[i] / C0]
        r = lambda p: np.r_[(e := two(p[0] + 1j * p[1], zs[m], vs)[1]).real, e.imag]
        p = least_squares(r, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]; c, e = two(g, zs[m], vs)
        G.append(g); Cc.append(c); Rr.append(np.linalg.norm(e) / np.linalg.norm(vs))
    fitp[ln] = (np.array(G), np.array(Cc), np.array(Rr))
a_ = {ln: fitp[ln][0].real * 8.686 / 100 for ln in LINES}; n_ = {ln: fitp[ln][0].imag * C0 / w for ln in LINES}
print("STEP 1a  line parameters per fold vs L+S fields (fold - L+S); fit residual max per fold:", {ln: f"{100*fitp[ln][2].max():.1f} %" for ln in LINES})
for lo, hi in ((4, 60), (62, 130)):
    mm = (F >= lo) & (F <= hi)
    print(f"  {lo}-{hi} GHz: " + " | ".join(f"{ln}: alpha mean {np.mean((a_[ln]-LS['aF'])[mm]):+.3f} dB/cm, n_m mean {np.mean((n_[ln]-LS['nF'])[mm]):+.4f} (max {abs(n_[ln]-LS['nF'])[mm].max():.4f})" for ln in LINES))
def bend(lin, lout, zp):
    g1, c1, _ = fitp[lin]; g2, c2, _ = fitp[lout]
    f1, r1 = c1[:, 0] * np.exp(-g1 * zp), c1[:, 1] * np.exp(g1 * zp); f2, r2 = c2[:, 0] * np.exp(-g2 * zp), c2[:, 1] * np.exp(g2 * zp)
    a1, b1 = (f1, r1) if LINES[lin][2] > 0 else (r1, f1); a2, b2 = (r2, f2) if LINES[lout][2] > 0 else (f2, r2)
    return (b1 * a1 - b2 * a2) / (a1**2 - a2**2), (b2 * a1 - b1 * a2) / (a1**2 - a2**2)
B = {"bend 1": bend("L1", "L2", 2.70e-3), "bend 2": bend("L2", "L3", 1.26e-3)}
dB = lambda x: 20 * np.log10(abs(x)); SBl = LB["SB"]
print("STEP 1b  bend two-ports (fields) vs L+B+S bend (fields)")
for nm, (s11, s21) in B.items():
    mm = F >= 20; c = np.polyfit(w[mm], np.unwrap(np.angle(s21))[mm], 1)
    d21 = dB(s21) - dB(SBl[:, 1, 0]); print(f"  {nm}: delay (slope 20-130 GHz) {-c[0]*1e12:.3f} ps (L+B+S 4.996) | |S21| - L+B+S: mean {d21.mean():+.3f} dB, rms {np.sqrt(np.mean(d21**2)):.3f}, "
                                            f"min {d21.min():+.3f} at {F[np.argmin(d21)]:.0f} GHz, max {d21.max():+.3f} at {F[np.argmax(d21)]:.0f} GHz | |S11| max {abs(s11).max():.3f}")
print("   f GHz | |S21| dB: bend 1 / bend 2 / L+B+S")
for q in (16, 20, 31, 40, 47, 55, 62, 70, 78, 86, 93, 100, 109, 120, 127):
    i = np.argmin(abs(F - q)); print(f"   {F[i]:5.0f} | {dB(B['bend 1'][1][i]):+.3f} / {dB(B['bend 2'][1][i]):+.3f} / {dB(SBl[i,1,0]):+.3f}")
# ---------------- step 2
P = np.load(os.path.join(HERE, "full_eq_path_130.npz")); S, VC, VP, SEG, names = P["S"], P["VC"], P["VP"], P["SEG"], list(P["names"])
cell = lambda X: np.array([np.convolve(x, np.ones(36) / 36, "valid") for x in X]); rms = lambda x: np.sqrt((abs(x) ** 2).mean(1))
r = {ln: rms(cell(VP[:, SEG == names.index(ln)])) / rms(cell(VC[:, SEG == names.index(ln)])) for ln in ("L1", "L2", "L3")}
print("STEP 2a  rms |v_p|/|v_c| (dB): full run L1 / L2 / L3 | L+B+S line 1 / line 2")
for q in (10, 16, 20, 31, 40, 47, 60, 62, 70, 78, 90, 100, 109, 120, 130):
    i = np.argmin(abs(F - q)); print(f"   {F[i]:5.0f} | {20*np.log10(r['L1'][i]):6.1f} / {20*np.log10(r['L2'][i]):6.1f} / {20*np.log10(r['L3'][i]):6.1f} | {20*np.log10(PM['r1'][i]):6.1f} / {20*np.log10(PM['r2'][i]):6.1f}")
for ln in r: print(f"   median over 20-130 GHz, {ln}: {np.median(20*np.log10(r[ln][F>=20])):.1f} dB")
print(f"   median over 20-130 GHz, L+B+S line 1 / 2: {np.median(20*np.log10(PM['r1'][F>=20])):.1f} / {np.median(20*np.log10(PM['r2'][F>=20])):.1f} dB")
net = rf.Network(os.path.join(D, "BASELINE - FULL EQUALIZER_130 GHz.s2p")); fS = net.f / 1e9; s21 = dB(net.s[:, 1, 0]); k = fS >= 1
trend = np.polyval(np.polyfit(fS[k], s21[k], 3), fS); dev = s21 - trend
dips, prop = find_peaks(-dev, prominence=0.04, distance=20)
print("STEP 2b  dips of the full |S21| (prominence > 0.04 dB):", [(round(fS[d], 1), round(prop['prominences'][n], 3)) for n, d in enumerate(dips)])
print("   L+B+S bend dips:", np.round(PM["dips"], 1))
Lp = S[-1] * 1e-3; print(f"   comb for a parasitic wave trapped over the whole path (n_p 2.39, {Lp*1e3:.2f} mm): spacing {C0/(2*2.39*Lp)/1e9:.2f} GHz;"
      f" over L2 + bends between the two arcs ({(S[SEG==names.index('arc 2')][0]-S[SEG==names.index('arc 1')][-1]):.2f} mm): spacing {C0/(2*2.39*(S[SEG==names.index('arc 2')][0]-S[SEG==names.index('arc 1')][-1])*1e-3)/1e9:.1f} GHz")
np.savez(os.path.join(HERE, "full_eq_analysis_130.npz"), F=F, a=np.array([a_[l] for l in LINES]), n=np.array([n_[l] for l in LINES]), res=np.array([fitp[l][2] for l in LINES]),
         B1=np.array(B["bend 1"]), B2=np.array(B["bend 2"]), r=np.array([r[l] for l in ("L1", "L2", "L3")]), fS=fS, s21=s21, trend=trend, dips=fS[dips])
