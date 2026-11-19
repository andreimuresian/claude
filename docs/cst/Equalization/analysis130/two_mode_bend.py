"""Two-mode bend model (coplanar c + ground-to-ground p) extracted from the L+B+S fields, 0-130 GHz.

Waves on the two lines (cell-averaged v_c, v_p; v_p = (v_inner - v_outer)/2): forward/backward fits with
gamma_c (L+S line model) and gamma_p = k alpha_c + j n_p w/c (two_mode_gamma_p.py), giving at the planes
(line 1 end, z = 2.16 mm; line 2 start) the waves towards the bend a1c, a1p, a2c, a2p and away from it b1c, b1p, b2c, b2p.
Bend (reciprocal, mirror-symmetric, backward conversion and parasitic reflection neglected):
    b1c = r_c a1c + t_c a2c + rho*kap a2p        b1p = t_p a2p + kap a2c
    b2c = t_c a1c + r_c a2c + rho*kap a1p        b2p = t_p a1p + kap a1c
kap: conversion c -> p (voltage waves); rho*kap: conversion p -> c, rho = Zc / Zp (voltage-wave reciprocity between modes of
different impedance). The p equations give kap and t_p alone; the c equations then give r_c and t_c for a given rho.
rho is not fixed by one excitation: it is chosen as the value that makes t_c smoothest in frequency (a correct model removes
the trapped-wave resonance from the coplanar transmission). Also the reflection of the p wave at the PEC-bridged ports.
Outputs: two_mode_bend.npz, printed tables."""
import os, sys, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); C0 = 299792458.0
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "../../../.."))); from mzm_interconnect.physics import fit_alpha_scaled, fit_nm_saturating
d = np.load(os.path.join(HERE, "bend_path_130.npz")); F, S, VC, VP, SEG = d["F"], d["S"] * 1e-3, d["VC"], d["VP"], d["SEG"]
b = np.load(os.path.join(HERE, "lbs_bend_130.npz")); gp = np.load(os.path.join(HERE, "two_mode_gamma_p.npz"))
w = 2 * np.pi * F * 1e9; ac = fit_alpha_scaled(F, *b["pa"]) * 100 / 8.686
gc = ac + 1j * fit_nm_saturating(F, *b["pn"]) * w / C0; gpp = float(gp["k"]) * ac + 1j * float(gp["n_p"]) * w / C0
L1, L2 = 2.16e-3, 1.08e-3; ker = np.ones(36) / 36; cav = lambda x: np.convolve(x, ker, "valid")
def waves(seg, from_port):
    s = S[SEG == seg]; s = s - s.min(); o = np.argsort(s); s = s[o]; ss = cav(s); m = (ss >= ss.min() + 0.18e-3) & (ss <= ss.max() - 0.18e-3)
    out = []
    for i in range(len(F)):
        row = []
        for V, g in ((VC, gc[i]), (VP, gpp[i])):
            v = cav(V[i][SEG == seg][o])[m]; M = np.stack([np.exp(-g * ss[m]), np.exp(g * ss[m])], 1); row.append(np.linalg.lstsq(M, v, rcond=None)[0])
        out.append(row)
    return np.array(out)                                   # [f, mode(c,p), (fwd, bwd)] at s = 0 of the segment
W1, W2 = waves(0, True), waves(4, False)
e = lambda g, L: np.exp(-g * L)
a1c, b1c = W1[:, 0, 0] * e(gc, L1), W1[:, 0, 1] / e(gc, L1); a1p, b1p = W1[:, 1, 0] * e(gpp, L1), W1[:, 1, 1] / e(gpp, L1)
b2c, a2c, b2p, a2p = W2[:, 0, 0], W2[:, 0, 1], W2[:, 1, 0], W2[:, 1, 1]
G1 = W1[:, 1, 0] / W1[:, 1, 1]                                                  # p reflection at port 1 (s = 0)
G2 = (W2[:, 1, 1] / e(gpp, L2)) / (W2[:, 1, 0] * e(gpp, L2))                    # p reflection at port 2 (s = L2)
kap = (b1p * a1p - b2p * a2p) / (a2c * a1p - a1c * a2p); tp = (b2p - kap * a1c) / a1p
def coplanar(rho):
    rc, tc = np.zeros(len(F), complex), np.zeros(len(F), complex)
    for i in range(len(F)):
        A = np.array([[a1c[i], a2c[i]], [a2c[i], a1c[i]]]); y = np.array([b1c[i] - rho * kap[i] * a2p[i], b2c[i] - rho * kap[i] * a1p[i]])
        rc[i], tc[i] = np.linalg.solve(A, y)
    return rc, tc
m = F >= 10
def rough(rho):
    _, tc = coplanar(rho); y = 20 * np.log10(abs(tc[m])); x = F[m]
    return np.sqrt(np.mean((y - np.polyval(np.polyfit(x, y, 3), x)) ** 2))
rhos = np.r_[0.0, np.geomspace(0.05, 5, 80)]; rr = np.array([rough(r) for r in rhos]); rho = rhos[np.argmin(rr)]
print(f"rho = Zc/Zp chosen by smoothness of |t_c|: {rho:.3f} (rough {rr.min():.4f} dB rms; rho = 0: {rr[0]:.4f} dB; rho = 1: {rough(1.0):.4f} dB)")
rc, tc = coplanar(rho); dB = lambda x: 20 * np.log10(abs(x))
print("|Gamma_p| at the ports: port 1 median", np.round(np.median(abs(G1[F >= 25])), 3), "phase", np.round(np.median(np.degrees(np.angle(-G1[F >= 25]))), 1),
      "deg from -1 | port 2 median", np.round(np.median(abs(G2[F >= 25])), 3), "phase", np.round(np.median(np.degrees(np.angle(-G2[F >= 25]))), 1), "deg from -1")
print(" f GHz | |t_c| dB (two-mode) | |S21| dB two-port (fields) | |r_c| | |kap| | |t_p| dB | arg kap deg")
for q in (10, 16, 20, 31, 40, 47, 55, 62, 70, 78, 86, 93, 100, 109, 120, 130):
    i = np.argmin(abs(F - q)); print(f"{F[i]:5.0f} | {dB(tc[i]):+.3f} | {dB(b['SB'][i,1,0]):+.3f} | {abs(rc[i]):.3f} | {abs(kap[i]):.3f} | {dB(tp[i]):+.2f} | {np.degrees(np.angle(kap[i])):+.0f}")
np.savez(os.path.join(HERE, "two_mode_bend.npz"), F=F, rc=rc, tc=tc, kap=kap, tp=tp, rho=rho, G1=G1, G2=G2, rhos=rhos, rough=rr, gc=gc, gp=gpp)
