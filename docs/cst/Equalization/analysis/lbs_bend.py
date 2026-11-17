"""L+B+S run (line 2.16 mm, bend block, line 1.08 mm): the bend block, three ways, compared with the full run.

(a) Fields: two-wave fit on each line (pitch-averaged V(z), 0.18 mm cut at the ends of the buried metal), waves at
    the planes z = 2.16 (end of buried metal), symmetric reciprocal 2-port solved as in full_eq_fields.py.
(b) Touchstones, port-free: T_LBS T_LS^-1 = P1 T(L) B T(L)^-1 P1^-1 (same ports, same straight length 3.24 mm),
    so its trace equals tr(B) exactly, ports included or not. tr(B)/2 = cosh(theta_b) -> exp(-theta_b) is the
    bend transmission for a matched symmetric block: loss and delay, no impedance.
(c) Touchstones, full 2-port: B = T(L)^-1 T_LBS T(S)^-1 with T from the L+S line (alpha, n_m, Zc of the touchstone
    extraction), ports assumed absorbed in the line model. S-matrix of B referenced to Zc.
Compared with bend 1 and bend 2 of the full run (full_eq_fields.csv).
Outputs: lbs_bend.png, lbs_bend.csv, printed table."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "../../../.."))
sys.path.insert(0, ROOT)
import numpy as np, skrf as rf, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from mzm_interconnect.extractor import extract_line_fit
from mzm_interconnect.physics import C0

D = os.path.join(HERE, "..", "L+B+S"); GAP = 4.45e-6; PITCH = 0.18e-3; CUT = 0.18e-3
LL, SS, ZP = 2.16e-3, 1.08e-3, 2.16e-3
LS = np.genfromtxt(os.path.join(HERE, "ls_extraction.csv"), delimiter=",", names=True)
FE = np.genfromtxt(os.path.join(HERE, "full_eq_fields.csv"), delimiter=",", names=True)

def load_gap(fn):
    a = np.loadtxt(os.path.join(D, fn), comments="#", skiprows=2); out = {}
    for f in np.unique(a[:, 0]):
        b = a[a[:, 0] == f]; o = np.argsort(b[:, 3]); out[f] = (b[o, 3] * 1e-3, b[o, 6] + 1j * b[o, 7])
    return out
def V_of(ln):
    gp, gm = load_gap(f"{ln}_gap+.txt"), load_gap(f"{ln}_gap-.txt"); F = np.array(sorted(gp))
    return F, gp[F[0]][0], np.array([0.5 * GAP * (gp[f][1] - gm[f][1]) for f in F])
F, z1, V1 = V_of("L1"); _, z2, V2 = V_of("L2"); w = 2 * np.pi * F * 1e9

def two_wave(g, zz, vv):
    M = np.stack([np.exp(-g * zz), np.exp(g * zz)], 1); c = np.linalg.lstsq(M, vv, rcond=None)[0]; return c, M @ c - vv
def fit_line(z, V, z0, z1_):
    dz = z[1] - z[0]; k = int(round(PITCH / dz)); ker = np.ones(k) / k
    zs = np.convolve(z, ker, "valid"); m = (zs >= z0 + CUT) & (zs <= z1_ - CUT); G, C = [], []
    for i in range(len(F)):
        vs = np.convolve(V[i], ker, "valid")[m]
        g0 = [np.interp(F[i], LS["f_GHz"], LS["alpha_fields_dB_cm"]) * 100 / 8.686, np.interp(F[i], LS["f_GHz"], LS["nm_fields"]) * w[i] / C0]
        res = lambda p: np.concatenate([(e := two_wave(p[0] + 1j * p[1], zs[m], vs)[1]).real, e.imag])
        p = least_squares(res, g0, x_scale=[max(g0[0], 1), g0[1]]).x; g = p[0] + 1j * p[1]
        G.append(g); C.append(two_wave(g, zs[m], vs)[0])
    return np.array(G), np.array(C)
G1, C1 = fit_line(z1, V1, 0.0, LL); G2, C2 = fit_line(z2, V2, LL - SS, LL)

# (a) fields: line 1 along +z (bend at its +z end), line 2 along -z (starts at the bend)
a1 = C1[:, 0] * np.exp(-G1 * ZP); b1 = C1[:, 1] * np.exp(G1 * ZP)
b2 = C2[:, 1] * np.exp(G2 * ZP); a2 = C2[:, 0] * np.exp(-G2 * ZP)
S11a = (b1 * a1 - b2 * a2) / (a1**2 - a2**2); S21a = (b2 * a1 - b1 * a2) / (a1**2 - a2**2)

# touchstones
def abcd(path):
    n = rf.Network(path); return n.f / 1e9, rf.network.s2a(n.s, 50.0)
fT, TL = abcd(os.path.join(HERE, "..", "L+B+S", "BASELINE_LBS.s2p")); _, TS = abcd(os.path.join(HERE, "..", "L+S", "BASELINE_LS.s2p"))
k = (fT >= F[0] - 1e-9) & (fT <= F[-1] + 1e-9)
# (b) port-free trace
M = TL[k] @ np.linalg.inv(TS[k]); th = np.arccosh(0.5 * np.trace(M, axis1=1, axis2=2))
th = np.where(th.real < 0, -th, th); fk = fT[k]
S21b = np.exp(-(th.real + 1j * np.unwrap(th.imag)))
# (c) full 2-port with the L+S line model
fit = extract_line_fit(os.path.join(HERE, "..", "L+S", "BASELINE_LS.s2p"), 3.24)
def Tline(f, Lm):
    g = np.interp(f, fit.raw_f_GHz, fit.raw_alpha_dB_cm) * 100 / 8.686 + 1j * np.interp(f, fit.raw_f_GHz, fit.raw_nm) * 2 * np.pi * f * 1e9 / C0
    Z = np.interp(f, fit.raw_f_GHz, fit.raw_Zc.real) + 1j * np.interp(f, fit.raw_f_GHz, fit.raw_Zc.imag)
    gl = g * Lm; T = np.empty((len(f), 2, 2), complex)
    T[:, 0, 0] = np.cosh(gl); T[:, 0, 1] = Z * np.sinh(gl); T[:, 1, 0] = np.sinh(gl) / Z; T[:, 1, 1] = np.cosh(gl); return T, Z
TLm, Zc = Tline(fk, LL); TSm, _ = Tline(fk, SS)
Bc = np.linalg.inv(TLm) @ TL[k] @ np.linalg.inv(TSm)
Sc = np.array([rf.network.a2s(Bc[i:i+1], Zc[i])[0] for i in range(len(fk))]); S11c, S21c = Sc[:, 0, 0], Sc[:, 1, 0]

dly = lambda S, f: -np.unwrap(np.angle(S)) / (2 * np.pi * f * 1e9) * 1e12
dB = lambda S: 20 * np.log10(abs(S))
ta, tb, tc = dly(S21a, F), dly(S21b, fk), dly(S21c, fk)
print("bend block: |S21| dB / delay ps / |S11|")
print(" f GHz | (a) fields L+B+S      | (b) touchstones, trace | (c) touchstones, 2-port | full run bend 1 | full run bend 2")
for q in (5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F - q)); j = np.argmin(abs(fk - F[i])); e = np.argmin(abs(FE["f_GHz"] - F[i]))
    print(f"{F[i]:5.0f}  | {dB(S21a[i]):+.3f} {ta[i]:5.2f} {abs(S11a[i]):.3f} | {dB(S21b[j]):+.3f} {tb[j]:5.2f}        |"
          f" {dB(S21c[j]):+.3f} {tc[j]:5.2f} {abs(S11c[j]):.3f}  | {FE['bend1_S21_dB'][e]:+.3f} {FE['bend1_delay_ps'][e]:5.2f} {FE['bend1_S11'][e]:.3f}"
          f" | {FE['bend2_S21_dB'][e]:+.3f} {FE['bend2_delay_ps'][e]:5.2f} {FE['bend2_S11'][e]:.3f}")
print("line parameters in L+B+S (fields), 30 GHz: n_m L1 %.3f, L2 %.3f | L+S %.3f" % (
    (G1[np.argmin(abs(F-30))].imag * C0 / w[np.argmin(abs(F-30))]), (G2[np.argmin(abs(F-30))].imag * C0 / w[np.argmin(abs(F-30))]),
    LS["nm_fields"][np.argmin(abs(LS["f_GHz"] - 30))]))

np.savetxt(os.path.join(HERE, "lbs_bend.csv"),
           np.column_stack([F, dB(S21a), ta, abs(S11a), np.interp(F, fk, dB(S21b)), np.interp(F, fk, tb),
                            np.interp(F, fk, dB(S21c)), np.interp(F, fk, tc), np.interp(F, fk, abs(S11c))]),
           delimiter=",", fmt="%.5g", comments="",
           header="f_GHz,fields_S21_dB,fields_delay_ps,fields_S11,trace_S21_dB,trace_delay_ps,twoport_S21_dB,twoport_delay_ps,twoport_S11")

fig, ax = plt.subplots(1, 3, figsize=(14, 4.2))
sty = [("(a) L+B+S fields", F, S21a, S11a, ta, "o", "#eb6834"), ("(b) touchstones, trace (port-free)", fk, S21b, None, tb, "-", "k"),
       ("(c) touchstones, 2-port", fk, S21c, S11c, tc, "--", "#7a4bd1")]
for lab, f, S21, S11, t, ls, c in sty:
    kw = dict(ms=3) if ls == "o" else {}
    ax[0].plot(f, dB(S21), ls, color=c, label=lab, **kw); ax[1].plot(f, t, ls, color=c, label=lab, **kw)
    if S11 is not None: ax[2].plot(f, dB(S11), ls, color=c, label=lab, **kw)
for nm, c in (("bend1", "#2a78d6"), ("bend2", "#1baa7d")):
    ax[0].plot(FE["f_GHz"], FE[f"{nm}_S21_dB"], ":", color=c, label=f"full run {nm}")
    ax[1].plot(FE["f_GHz"], FE[f"{nm}_delay_ps"], ":", color=c, label=f"full run {nm}")
    ax[2].plot(FE["f_GHz"], 20 * np.log10(FE[f"{nm}_S11"]), ":", color=c, label=f"full run {nm}")
ax[0].set_ylabel("bend |S21| (dB)"); ax[0].set_ylim(-0.8, 0.2); ax[1].set_ylabel("bend delay (ps)"); ax[1].set_ylim(4.5, 5.6)
ax[2].set_ylabel("bend |S11| (dB)"); ax[2].set_ylim(-60, -15)
for a_ in ax: a_.set_xlabel("frequency (GHz)"); a_.set_xlim(3, 60); a_.grid(alpha=0.3); a_.legend(frameon=False, fontsize=7)
fig.suptitle("Bend block (raised taper + arc + raised taper): L+B+S vs full equalizer run", fontsize=10)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "lbs_bend.png"), dpi=200)
