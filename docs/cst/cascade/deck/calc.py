"""All numbers and figures for the CST line-extraction deck."""
import os, numpy as np, matplotlib
matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from scipy.signal import argrelmin
D = '/home/user/claude/docs/cst/cascade'; IMG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'img')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11, 'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.alpha': .3, 'axes.titlesize': 12, 'axes.titleweight': 'bold', 'legend.frameon': False})
NAVY, RED, BLUE, GREEN, ORANGE, GREY, PURPLE = '#0E2268', '#F20013', '#2F6FD0', '#2E8B57', '#E07B39', '#8A8F99', '#6C4BA0'
c = 299792458; R0 = 50; DB = 20/np.log(10)

def load(fn):
    d = np.loadtxt(os.path.join(D, fn), comments=['!', '#']); f = d[:, 0]*1e9; S = np.zeros((len(f), 2, 2), complex)
    for k, (i, j) in enumerate([(0, 0), (1, 0), (0, 1), (1, 1)]): S[:, i, j] = d[:, 1+2*k]*np.exp(1j*np.deg2rad(d[:, 2+2*k]))
    return f, S
def s2t(S, Z=R0):
    a, b, c_, d = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
    A = ((1+a)*(1-d)+b*c_)/(2*c_); B = Z*((1+a)*(1+d)-b*c_)/(2*c_); C = ((1-a)*(1-d)-b*c_)/(2*c_)/Z; Dd = ((1-a)*(1+d)+b*c_)/(2*c_)
    return np.stack([np.stack([A, B], -1), np.stack([C, Dd], -1)], -2)
def t2s(T, Z=R0):
    A, B, C, Dd = T[..., 0, 0], T[..., 0, 1], T[..., 1, 0], T[..., 1, 1]; den = A+B/Z+C*Z+Dd
    S = np.empty_like(T); S[..., 0, 0] = (A+B/Z-C*Z-Dd)/den; S[..., 0, 1] = 2*(A*Dd-B*C)/den; S[..., 1, 0] = 2/den; S[..., 1, 1] = (-A+B/Z-C*Z+Dd)/den
    return S
def gam(T, L):
    A = (T[:, 0, 0]+T[:, 1, 1])/2; r = np.sqrt(A*A-1+0j); y = A-r; y = np.where(abs(y) > 1, A+r, y)
    return (-np.log(abs(y)) - 1j*np.unwrap(np.angle(y)))/L
def zc(T): Z = np.sqrt(T[:, 0, 1]/T[:, 1, 0]); return np.where(Z.real < 0, -Z, Z)
def Lm(g, Z, L):
    gl = g*L; return np.stack([np.stack([np.cosh(gl), Z*np.sinh(gl)], -1), np.stack([np.sinh(gl)/Z, np.cosh(gl)], -1)], -2)
def Pm(Zs, Yp):
    one = np.ones_like(Zs); zero = np.zeros_like(Zs)
    return np.stack([np.stack([one+Zs*Yp, Zs], -1), np.stack([Yp, one], -1)], -2)
def mir(P): return P[:, ::-1, ::-1].transpose(0, 2, 1) if False else np.stack([np.stack([P[:, 1, 1], P[:, 0, 1]], -1), np.stack([P[:, 1, 0], P[:, 0, 0]], -1)], -2)
db = lambda x: 20*np.log10(abs(x))

f, S05 = load('LINEA0_0p5MM.s2p'); _, S1 = load('LINEA0_1MM.s2p'); _, S5 = load('LINEA0_5MM.s2p')
F = f/1e9; w = 2*np.pi*f; nf = len(f); k0 = slice(1, None)
Ls = [0.5e-3, 1e-3, 5e-3]; Sr = dict(zip(Ls, [S05, S1, S5])); T = {L: s2t(Sr[L]) for L in Ls}
pairs = [(1e-3, 5e-3), (0.5e-3, 1e-3), (0.5e-3, 5e-3)]
G = {p: gam(np.linalg.solve(T[p[0]], T[p[1]]), p[1]-p[0]) for p in pairs}
ZB = {p: zc(np.linalg.solve(T[p[0]], T[p[1]])) for p in pairs}
g45 = G[(0.5e-3, 5e-3)]

def fit_port(lengths, g):
    out = np.zeros((nf, 6)); p0 = np.array([39, 0, 0, 0, 0, 0.]); res = np.zeros(nf)
    for k in range(1, nf):
        def r(p):
            Z, Zs, Yp = p[0]+1j*p[1], p[2]+1j*p[3], p[4]+1j*p[5]
            P = Pm(np.array([Zs]), np.array([Yp])); Tm = {L: P @ Lm(np.array([g[k]]), np.array([Z]), L) @ mir(P) for L in lengths}
            e = []
            for L in lengths:
                sm = t2s(Tm[L])[0]; d = np.array([sm[0, 0]-Sr[L][k, 0, 0], sm[1, 0]-Sr[L][k, 1, 0]]); e += [d.real, d.imag]
            return np.concatenate(e)
        sol = least_squares(r, p0, x_scale=[10, 10, 1, 1, 1e-3, 1e-3]); out[k] = p0 = sol.x; res[k] = abs(r(sol.x)).max()
    out[0] = out[1]
    return out[:, 0]+1j*out[:, 1], out[:, 2]+1j*out[:, 3], out[:, 4]+1j*out[:, 5], res
Zf3r, Zs3r, Yp3r, res3 = fit_port(Ls, g45)                     # free per-frequency fit, all three runs
Zf2r, Zs2r, Yp2r, res2 = fit_port([1e-3, 5e-3], G[(1e-3, 5e-3)]) # 1 and 5 mm only (independent of 0.5 mm)
band = (F >= 10) & (F <= 60)
def lc(Zs, Yp): return np.median(Zs.imag[band]/w[band]), np.median(Yp.imag[band]/w[band])
LC3, LC2 = lc(Zs3r, Yp3r), lc(Zs2r, Yp2r)
def fit_zc(lengths, g, Lp, Cp):
    P = Pm(1j*w*Lp, 1j*w*Cp); out = np.zeros(nf, complex); p0 = np.array([39., 0.])
    for k in range(1, nf):
        def r(p):
            e = []
            for L in lengths:
                sm = t2s(P[k:k+1] @ Lm(np.array([g[k]]), np.array([p[0]+1j*p[1]]), L) @ mir(P[k:k+1]))[0]
                d = np.array([sm[0, 0]-Sr[L][k, 0, 0], sm[1, 0]-Sr[L][k, 1, 0]]); e += [d.real, d.imag]
            return np.concatenate(e)
        p0 = least_squares(r, p0).x; out[k] = p0[0]+1j*p0[1]
    out[0] = out[1]; return out, P
Zf3, P3 = fit_zc(Ls, g45, *LC3)
Zf2, P2 = fit_zc([1e-3, 5e-3], G[(1e-3, 5e-3)], *LC2)
Zs3, Yp3 = P3[:, 0, 1], P3[:, 1, 0]

def ref_s(Tx, Z):               # 2-port S referenced to Z(f)
    return t2s(Tx, Z[:, None, None] if np.ndim(Z) else Z)
def s_inZ(Tx, Z):
    A, B, C, Dd = Tx[:, 0, 0], Tx[:, 0, 1], Tx[:, 1, 0], Tx[:, 1, 1]; den = A+B/Z+C*Z+Dd
    return (A+B/Z-C*Z-Dd)/den, 2/den
pS11, pS21 = s_inZ(P3, Zf3)
beta45 = g45.imag
dl_eq = -np.unwrap(np.angle(pS21))/np.where(beta45 > 0, beta45, np.nan)     # equivalent extra length, m
Lser = Zs3.imag/w; Cpar = Yp3.imag/w

# ---- excess (apparent minus true) gamma*L of each single run
exc = {L: gam(T[L], L)*L - g45*L for L in Ls}
exc_model = {L: gam(P3 @ Lm(g45, Zf3, L) @ mir(P3), L)*L - g45*L for L in Ls}
app = {L: gam(T[L], L) for L in Ls}

# ---- 0.5 mm prediction from 1+5 fit
T05p = P2 @ Lm(G[(1e-3, 5e-3)], Zf2, 0.5e-3) @ mir(P2); S05p = t2s(T05p)
S05bare = t2s(Lm(G[(1e-3, 5e-3)], Zf2, 0.5e-3))
# ---- 5 mm: CST vs clean reconstruction (g45, Zf3) with / without ports
T5c = Lm(g45, Zf3, 5e-3); S5c = t2s(T5c); S5cp = t2s(P3 @ T5c @ mir(P3))
# ---- 1x5 cascade raw
S15 = t2s(np.linalg.matrix_power(T[1e-3], 5))
# ---- port-corrected single runs (P from the 1+5 fit)
iP2, iP2m = np.linalg.inv(P2), np.linalg.inv(mir(P2))
corr = {L: gam(iP2 @ T[L] @ iP2m, L) for L in Ls}
corrZ = {L: zc(iP2 @ T[L] @ iP2m) for L in Ls}
# ---- FSR on 5 mm
mins = argrelmin(db(S5[:, 0, 0]), order=20)[0]
n_fsr = [(m+1)*c/(2*5e-3*f[i]) for m, i in enumerate(mins)]
# ---- ideal-line cascade identity
gi = (3/8.686*100)*np.sqrt(f/30e9)+1j*1.95*w/c
ideal_err = np.abs(t2s(np.linalg.matrix_power(Lm(gi, 37-1j+0*f, 1e-3), 5)) - t2s(Lm(gi, 37-1j+0*f, 5e-3))).max()

def at(x, arr): return arr[np.argmin(abs(F-x))]
nm = lambda g: g.imag*c/w; al = lambda g: g.real*DB/100
summary = dict(
    ideal_err=ideal_err,
    dc_loss={L: -db(Sr[L][0, 1, 0]) for L in Ls},
    port={x: dict(L=at(x, Lser)*1e12, C=at(x, Cpar)*1e15, mag=db(at(x, pS21)), ph=np.rad2deg(np.angle(at(x, pS21))),
                  s11=db(at(x, pS11)), dl=at(x, dl_eq)*1e6, Z=at(x, Zf3)) for x in [10, 20, 30, 40, 50, 60]},
    lines={x: {p: (al(G[p])[np.argmin(abs(F-x))], nm(G[p])[np.argmin(abs(F-x))]) for p in pairs} for x in [1, 10, 30, 60]},
    pred05={x: (db(at(x, S05p[:, 1, 0]))-db(at(x, S05[:, 1, 0])), np.rad2deg(np.angle(at(x, S05p[:, 1, 0])/at(x, S05[:, 1, 0]))),
                np.rad2deg(np.angle(at(x, S05bare[:, 1, 0])/at(x, S05[:, 1, 0])))) for x in [1, 10, 30, 50, 60]},
    s5={x: (db(at(x, S5c[:, 1, 0]))-db(at(x, S5[:, 1, 0])), np.rad2deg(np.angle(at(x, S5c[:, 1, 0])/at(x, S5[:, 1, 0]))),
            db(at(x, S5cp[:, 1, 0]))-db(at(x, S5[:, 1, 0])), np.rad2deg(np.angle(at(x, S5cp[:, 1, 0])/at(x, S5[:, 1, 0])))) for x in [10, 30, 50, 60]},
    s5max=dict(clean_db=np.abs(db(S5c[k0, 1, 0])-db(S5[k0, 1, 0])).max(), port_db=np.abs(db(S5cp[k0, 1, 0])-db(S5[k0, 1, 0])).max(),
               clean_deg=np.abs(np.rad2deg(np.angle(S5c[k0, 1, 0]/S5[k0, 1, 0]))).max(), port_deg=np.abs(np.rad2deg(np.angle(S5cp[k0, 1, 0]/S5[k0, 1, 0]))).max()),
    casc_max=np.abs(db(S15[k0, 1, 0])-db(S5[k0, 1, 0])).max(),
    fsr=[(F[i], n) for i, n in zip(mins, n_fsr)],
    exc={x: {L: (at(x, exc[L]).real*DB, np.rad2deg(at(x, exc[L]).imag)) for L in Ls} for x in [10, 30, 60]},
    corr={x: {L: (al(corr[L])[np.argmin(abs(F-x))], nm(corr[L])[np.argmin(abs(F-x))], al(app[L])[np.argmin(abs(F-x))], nm(app[L])[np.argmin(abs(F-x))]) for L in Ls} for x in [10, 30, 60]},
    res3=res3[k0].max(), res2=res2[k0].max(), LC3=LC3, LC2=LC2)
import pickle; pickle.dump(summary, open(os.path.join(os.path.dirname(IMG), 'summary.pkl'), 'wb'))

# ======================= FIGURES =======================
def save(fig, name): fig.savefig(os.path.join(IMG, name), dpi=170, bbox_inches='tight'); plt.close(fig)
CL = {0.5e-3: ORANGE, 1e-3: BLUE, 5e-3: NAVY}; LB = {0.5e-3: '0.5 mm', 1e-3: '1 mm', 5e-3: '5 mm'}

# F1 raw cascade vs 5 mm
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
ax[0].plot(F, db(S5[:, 1, 0]), color=NAVY, lw=2, label='5 mm (CST)'); ax[0].plot(F, db(S15[:, 1, 0]), '--', color=RED, lw=2, label='1 mm × 5 (raw cascade)')
ax[0].set_title('|S21| (dB)'); ax[0].legend(loc='lower left')
ax[1].plot(F, db(S5[:, 0, 0]), color=NAVY, lw=2); ax[1].plot(F, db(S15[:, 0, 0]), '--', color=RED, lw=2); ax[1].set_title('|S11| (dB)')
ax[2].plot(F[k0], np.rad2deg(np.unwrap(np.angle(S15[k0, 1, 0]))-np.unwrap(np.angle(S5[k0, 1, 0]))), color=RED, lw=2); ax[2].set_title('∠S21 cascade − 5 mm (deg)')
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'raw_cascade.png')

# F2 excess gamma*L per run: length independent
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.7))
for L in Ls:
    ax[0].plot(F[k0], np.rad2deg(exc[L][k0].imag), color=CL[L], lw=2, label=LB[L]+' run')
    ax[1].plot(F[k0], exc[L][k0].real*DB, color=CL[L], lw=2)
ax[0].plot(F[k0], np.rad2deg(exc_model[1e-3][k0].imag), 'k:', lw=2, label='port model (2 ports)')
ax[1].plot(F[k0], exc_model[1e-3][k0].real*DB, 'k:', lw=2)
ax[0].set_title('Excess phase of each run (deg)'); ax[1].set_title('Excess loss of each run (dB)'); ax[0].legend(loc='upper left', fontsize=10)
ax[1].set_ylim(-0.1, 0.15)
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'excess.png')

# F3 port region characterisation
fig, ax = plt.subplots(1, 3, figsize=(13, 3.5))
ax[0].plot(F[k0], db(pS21[k0]), color=NAVY, lw=2); ax[0].set_ylim(-0.1, 0.1); ax[0].set_title('|S21| one port region (dB)')
ax[1].plot(F[k0], np.rad2deg(np.angle(pS21[k0])), color=RED, lw=2); ax[1].set_title('∠S21 one port region (deg)')
ax[2].plot(F[85:], dl_eq[85:]*1e6, color=GREEN, lw=2); ax[2].set_ylim(0, 20); ax[2].set_title('Equivalent extra line (µm)')
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'port_char.png')

# F4 three de-embedded lines
fig, ax = plt.subplots(1, 3, figsize=(13, 3.7))
pc = {(1e-3, 5e-3): (BLUE, '4 mm (5 − 1)'), (0.5e-3, 1e-3): (ORANGE, '0.5 mm (1 − 0.5)'), (0.5e-3, 5e-3): (NAVY, '4.5 mm (5 − 0.5)')}
for p, (cl, lb) in pc.items():
    ax[0].plot(F[k0], al(G[p])[k0], color=cl, lw=2, label=lb); ax[1].plot(F[k0], nm(G[p])[k0], color=cl, lw=2)
ax[2].plot(F[k0], ZB[(0.5e-3, 5e-3)][k0].real, color=NAVY, lw=1.2, alpha=.6, label='√(B/C), 4.5 mm')
ax[2].plot(F[k0], Zf3[k0].real, color=RED, lw=2.4, label='port-model fit')
for fr in [c/(2*1.95*4.5e-3)*m/1e9 for m in (1, 2, 3)]: ax[2].axvline(fr, color=GREY, ls=':', lw=1)
ax[0].set_title('α (dB/cm)'); ax[1].set_title('n_m'); ax[2].set_title('Re Zc (Ω)'); ax[1].set_ylim(1.88, 2.1); ax[2].set_ylim(34, 41)
ax[0].legend(fontsize=10); ax[2].legend(fontsize=10)
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'three_lines.png')

# F5 noise amplification
fig, ax = plt.subplots(figsize=(4.6, 3.4)); dls = np.linspace(0.3, 5, 100)
ax.plot(dls, 0.02*np.sqrt(2)/(dls/10), color=NAVY, lw=2)
for d_, lb in [(0.5, '0.5 mm'), (4, '4 mm'), (4.5, '4.5 mm')]:
    v = 0.02*np.sqrt(2)/(d_/10); ax.plot(d_, v, 'o', color=RED); ax.annotate(f'{lb}: ±{v:.2f}', (d_, v), (8, 6), textcoords='offset points', fontsize=10)
ax.set_xlabel('Length difference Δℓ (mm)'); ax.set_ylabel('α uncertainty (dB/cm)'); ax.set_title('0.02 dB run noise ÷ Δℓ'); ax.set_ylim(0, 1)
save(fig, 'noise_amp.png')

# F6 0.5 mm prediction
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
ax[0].plot(F, db(S05[:, 1, 0]), color=NAVY, lw=2.5, label='0.5 mm CST'); ax[0].plot(F, db(S05p[:, 1, 0]), '--', color=RED, lw=2, label='predicted (fit on 1 + 5 mm)')
ax[0].set_title('|S21| (dB)'); ax[0].legend(fontsize=10)
ax[1].plot(F, db(S05[:, 0, 0]), color=NAVY, lw=2.5); ax[1].plot(F, db(S05p[:, 0, 0]), '--', color=RED, lw=2); ax[1].set_title('|S11| (dB)')
ax[2].plot(F[k0], np.rad2deg(np.angle(S05p[k0, 1, 0]/S05[k0, 1, 0])), color=RED, lw=2, label='with port model')
ax[2].plot(F[k0], np.rad2deg(np.angle(S05bare[k0, 1, 0]/S05[k0, 1, 0])), color=GREY, lw=2, label='bare line, no ports')
ax[2].set_title('∠S21 prediction − CST (deg)'); ax[2].legend(fontsize=10)
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'pred05.png')

# F7 5 mm vs clean 4.5-derived
fig, ax = plt.subplots(1, 3, figsize=(13, 3.6))
ax[0].plot(F, db(S5[:, 1, 0]), color=NAVY, lw=2.5, label='5 mm CST'); ax[0].plot(F, db(S5c[:, 1, 0]), '--', color=GREEN, lw=2, label='clean line (γ 4.5 mm, Zc fit)')
ax[0].plot(F, db(S5cp[:, 1, 0]), ':', color=RED, lw=2.2, label='clean line + 2 port regions'); ax[0].set_title('|S21| (dB)'); ax[0].legend(fontsize=9.5, loc='lower left')
ax[1].plot(F, db(S5[:, 0, 0]), color=NAVY, lw=2.5); ax[1].plot(F, db(S5c[:, 0, 0]), '--', color=GREEN, lw=2); ax[1].plot(F, db(S5cp[:, 0, 0]), ':', color=RED, lw=2.2)
ax[1].set_title('|S11| (dB)')
ax[2].plot(F[k0], np.rad2deg(np.angle(S5c[k0, 1, 0]/S5[k0, 1, 0])), color=GREEN, lw=2, label='clean − CST')
ax[2].plot(F[k0], np.rad2deg(np.angle(S5cp[k0, 1, 0]/S5[k0, 1, 0])), color=RED, lw=2, label='clean + ports − CST'); ax[2].set_title('∠S21 difference (deg)'); ax[2].legend(fontsize=10)
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 's5_vs_clean.png')

# F8 corrected single runs
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.7))
for L in Ls:
    ax[0].plot(F[k0], nm(app[L])[k0], color=CL[L], lw=1.3, ls='--', alpha=.8)
    ax[0].plot(F[k0], nm(corr[L])[k0], color=CL[L], lw=2.2, label=LB[L]+' run')
    ax[1].plot(F[k0], al(app[L])[k0], color=CL[L], lw=1.3, ls='--', alpha=.8)
    ax[1].plot(F[k0], al(corr[L])[k0], color=CL[L], lw=2.2)
ax[0].plot(F[k0], nm(g45)[k0], 'k:', lw=2, label='4.5 mm de-embedded'); ax[1].plot(F[k0], al(g45)[k0], 'k:', lw=2)
ax[0].set_ylim(1.88, 2.15); ax[1].set_ylim(0, 7); ax[0].set_xlim(2, 60); ax[1].set_xlim(2, 60); ax[0].set_title('n_m from ONE run: dashed raw, solid port-corrected'); ax[1].set_title('α (dB/cm), same')
ax[0].legend(fontsize=9.5)
for a in ax: a.set_xlabel('Frequency (GHz)')
save(fig, 'corrected_runs.png')

# F9 FSR
fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.5))
ax[0].plot(F, db(S5[:, 0, 0]), color=NAVY, lw=2); ax[0].plot(F[mins], db(S5[mins, 0, 0]), 'o', color=RED)
for m, i in enumerate(mins): ax[0].annotate(f'm={m+1}', (F[i], db(S5[i, 0, 0])), (4, -14), textcoords='offset points', fontsize=10, color=RED)
ax[0].set_title('5 mm |S11| (dB): minima at βL = mπ'); ax[0].set_xlabel('Frequency (GHz)')
ax[1].plot(F[k0], nm(g45)[k0], color=NAVY, lw=2, label='ABCD, every frequency')
ax[1].plot(F[mins], n_fsr, 'o', color=RED, ms=8, label='n = m·c / (2 L f_m)')
ax[1].set_ylim(1.88, 2.1); ax[1].set_title('n_m'); ax[1].set_xlabel('Frequency (GHz)'); ax[1].legend(fontsize=10)
save(fig, 'fsr.png')

# F10 Zc renorm identical
src_Z = Zf3
def renorm(S, Zr):
    I = np.eye(2); out = np.empty_like(S)
    for k in range(len(S)):
        Zm = 50*(I+S[k]) @ np.linalg.inv(I-S[k]); out[k] = (Zm-Zr[k]*I) @ np.linalg.inv(Zm+Zr[k]*I)
    return out
S5z, S15z = renorm(S5, src_Z), renorm(S15, src_Z)
fig, ax = plt.subplots(figsize=(5.4, 3.4))
ax.plot(F[k0], db(S15[k0, 1, 0])-db(S5[k0, 1, 0]), color=NAVY, lw=2.5, label='50 Ω reference')
ax.plot(F[k0], db(S15z[k0, 1, 0])-db(S5z[k0, 1, 0]), '--', color=RED, lw=2, label='Zc reference')
ax.set_title('|S21| cascade − 5 mm (dB)'); ax.set_xlabel('Frequency (GHz)'); ax.legend(fontsize=10)
save(fig, 'renorm.png')
summary['renorm_max'] = (np.abs(db(S15[k0, 1, 0])-db(S5[k0, 1, 0])).max(), np.abs(db(S15z[k0, 1, 0])-db(S5z[k0, 1, 0])).max())
pickle.dump(summary, open(os.path.join(os.path.dirname(IMG), 'summary.pkl'), 'wb'))
import pprint; pprint.pprint(summary, width=150)

# ---- port-free (cleaned) Touchstones of each run, 50 ohm, using the 3-run port model
outd = os.path.join(D, 'cleaned'); os.makedirs(outd, exist_ok=True)
iP, iPm = np.linalg.inv(P3), np.linalg.inv(mir(P3))
for L in Ls:
    Sc = t2s(iP @ T[L] @ iPm)
    with open(os.path.join(outd, f'LINEA0_{L*1e3:g}MM_portfree.s2p'.replace('.', 'p', 1) if False else f"LINEA0_{str(L*1e3).replace('.', 'p')}MM_portfree.s2p"), 'w') as fh:
        fh.write(f"! CST run with both port regions removed (series {LC3[0]*1e12:.3f} pH, shunt {LC3[1]*1e15:.3f} fF each)\n# GHz S MA R 50\n")
        for k in range(nf):
            row = [F[k]] + sum([[abs(Sc[k, i, j]), np.rad2deg(np.angle(Sc[k, i, j]))] for i, j in [(0, 0), (1, 0), (0, 1), (1, 1)]], [])
            fh.write(' '.join(f'{v:.9g}' for v in row) + '\n')
