"""Two-length de-embedding on the 0.5, 1 and 5 mm CST runs, and a fitted
model of the port region.

1. For each pair (short, long), both orderings:
     Ta = T_short^-1 . T_long   = P2^-1 . L(dl) . P2   (keeps the residue of port 2)
     Tb = T_long . T_short^-1   = P1 . L(dl) . P1^-1   (keeps the residue of port 1)
   gamma from half the trace (exact for both), Zc = sqrt(B/C) (each carries a residue).
2. Port model: every run is P . L(l) . mirror(P), P = series Zs then shunt Yp
   (port side to line side). gamma is fixed to the de-embedded value; Zc, Zs, Yp
   are fitted to all three runs at each frequency.
"""
import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
src = open('cascade_extract.py').read()
exec(src.split("f,S1=load")[0])                       # load, s2abcd, abcd2s, c, R0
f, S05 = load('LINEA0_0p5MM.s2p'); _, S1 = load('LINEA0_1MM.s2p'); _, S5 = load('LINEA0_5MM.s2p')
runs = {0.5e-3: s2abcd(S05), 1e-3: s2abcd(S1), 5e-3: s2abcd(S5)}
w = 2*np.pi*f; F = f/1e9; nf = len(f)
DB = 20/np.log(10)

def gamma_from_trace(T, L):
    A = (T[:, 0, 0] + T[:, 1, 1]) / 2
    r = np.sqrt(A*A - 1 + 0j); y = A - r; y = np.where(abs(y) > 1, A + r, y)   # y = e^{-gamma L}
    al = -np.log(abs(y)) / L; be = -np.unwrap(np.angle(y)) / L
    return al + 1j*be

def zc(T):
    Z = np.sqrt(T[:, 0, 1] / T[:, 1, 0]); return np.where(Z.real < 0, -Z, Z)

pairs = [(1e-3, 5e-3), (0.5e-3, 1e-3), (0.5e-3, 5e-3)]
res = {}
for a, b in pairs:
    Ta = np.linalg.solve(runs[a], runs[b])                    # T_a^-1 T_b
    Tb = runs[b] @ np.linalg.inv(runs[a])                     # T_b T_a^-1
    dl = b - a
    res[(a, b)] = dict(g=gamma_from_trace(Ta, dl), gb=gamma_from_trace(Tb, dl), Za=zc(Ta), Zb=zc(Tb))

idx = [np.argmin(abs(F - x)) for x in [1, 5, 10, 20, 30, 40, 50, 60]]
lab = {k: f"{(k[1]-k[0])*1e3:g} mm ({k[1]*1e3:g}-{k[0]*1e3:g})" for k in pairs}
print("== gamma: alpha (dB/cm) and n_m for the three de-embedded lines")
print(" f   | " + " | ".join(f"{lab[k]:^20}" for k in pairs))
for i in idx:
    print(f"{F[i]:4.0f} | " + " | ".join(f"{res[k]['g'][i].real*DB/100:6.3f}  {res[k]['g'][i].imag*c/w[i]:7.4f}  " for k in pairs))
print("check: both orderings give the same gamma, max diff =",
      max(np.abs(res[k]['g'] - res[k]['gb'])[1:].max() for k in pairs))
g45, g4, g05 = res[(0.5e-3, 5e-3)]['g'], res[(1e-3, 5e-3)]['g'], res[(0.5e-3, 1e-3)]['g']
print("consistency |g4.5*4.5 - (g4*4 + g0.5*0.5)| (Np, rad), max over f:",
      np.abs(g45*4.5e-3 - (g4*4e-3 + g05*0.5e-3))[1:].max())

print("\n== Zc = sqrt(B/C): residue of port 2 (T_s^-1 T_l) vs port 1 (T_l T_s^-1)")
for i in idx:
    print(f"{F[i]:4.0f} | " + " | ".join(f"{res[k]['Za'][i].real:5.2f}{res[k]['Za'][i].imag:+5.2f}j / {res[k]['Zb'][i].real:5.2f}{res[k]['Zb'][i].imag:+5.2f}j" for k in pairs))

# ---------------- port model fit -----------------
g = g45                                                       # best gamma (longest difference)
def Lmat(gl, Z):
    ch, sh = np.cosh(gl), np.sinh(gl)
    return np.array([[ch, Z*sh], [sh/Z, ch]])
def mirror(P):
    return np.array([[P[1, 1], P[0, 1]], [P[1, 0], P[0, 0]]])
def model(p, k):
    Z, Zs, Yp = p[0]+1j*p[1], p[2]+1j*p[3], p[4]+1j*p[5]
    P = np.array([[1, Zs], [0, 1]]) @ np.array([[1, 0], [Yp, 1]])
    return {L: P @ Lmat(g[k]*L, Z) @ mirror(P) for L in runs}
def s_of(T):
    A, B, C, D = T[0, 0], T[0, 1], T[1, 0], T[1, 1]; d = A + B/R0 + C*R0 + D
    return np.array([(A + B/R0 - C*R0 - D)/d, 2/d, (-A + B/R0 - C*R0 + D)/d])
meas = {L: abcd2s(T) for L, T in runs.items()}
fit = np.zeros((nf, 6)); resid = np.zeros(nf)
p0 = np.array([zc(np.linalg.solve(runs[1e-3], runs[5e-3]))[1].real, 0, 0, 0, 0, 0])
for k in range(1, nf):
    def r(p):
        M = model(p, k); out = []
        for L in runs:
            Sm = meas[L][k]; e = s_of(M[L]) - np.array([Sm[0, 0], Sm[1, 0], Sm[1, 1]])
            out += [e.real, e.imag]
        return np.concatenate(out)
    sol = least_squares(r, p0, x_scale=[10, 10, 1, 1, 1e-3, 1e-3])
    fit[k] = sol.x; p0 = sol.x; resid[k] = np.abs(r(sol.x)).max()
Zfit = fit[:, 0] + 1j*fit[:, 1]; Zs = fit[:, 2] + 1j*fit[:, 3]; Yp = fit[:, 4] + 1j*fit[:, 5]
# one port region as a 2-port referenced to Zfit
Pk = [np.array([[1, Zs[k]], [0, 1]]) @ np.array([[1, 0], [Yp[k], 1]]) for k in range(nf)]
def s_ref(T, Z):
    A, B, C, D = T[0, 0], T[0, 1], T[1, 0], T[1, 1]; d = A + B/Z + C*Z + D
    return (A + B/Z - C*Z - D)/d, 2/d
pS11 = np.array([s_ref(Pk[k], Zfit[k])[0] if k else 0 for k in range(nf)])
pS21 = np.array([s_ref(Pk[k], Zfit[k])[1] if k else 1 for k in range(nf)])
print("\n== port model: Zc fitted, series Zs, shunt Yp; one port region in the Zc reference")
print(" f   Zc fit        Zs (ohm)        R_s   L_s(pH)  C_p(fF) G_p(mS) | |S21p| dB  ang S21p  |S11p| dB  max resid")
for i in idx:
    print(f"{F[i]:4.0f} {Zfit[i].real:5.2f}{Zfit[i].imag:+5.2f}j  {Zs[i].real:6.3f}{Zs[i].imag:+6.3f}j  "
          f"{Zs[i].real:5.3f} {Zs[i].imag/w[i]*1e12:7.2f}  {Yp[i].imag/w[i]*1e15:7.2f} {Yp[i].real*1e3:7.3f} | "
          f"{20*np.log10(abs(pS21[i])):8.4f}  {np.rad2deg(np.angle(pS21[i])):7.3f}  {20*np.log10(abs(pS11[i])):7.1f}  {resid[i]:.1e}")
np.savez('three_lengths_results.npz', f=f, g=g, Zfit=Zfit, Zs=Zs, Yp=Yp, **{f"g_{k[0]*1e4:g}_{k[1]*1e4:g}": res[k]['g'] for k in pairs})

# ---------------- figure -----------------
fig, ax = plt.subplots(2, 3, figsize=(15, 8))
cols = ['#1f4e9a', '#d9541e', '#2e8b57']
for k, cl in zip(pairs, cols):
    ax[0, 0].plot(F[1:], res[k]['g'][1:].real*DB/100, color=cl, label=lab[k])
    ax[0, 1].plot(F[1:], res[k]['g'][1:].imag*c/w[1:], color=cl)
    ax[0, 2].plot(F[1:], res[k]['Za'][1:].real, color=cl); ax[0, 2].plot(F[1:], res[k]['Zb'][1:].real, ':', color=cl)
ax[0, 2].plot(F[1:], Zfit[1:].real, 'k', lw=2, label='fit with port model')
ax[0, 0].set_ylabel('α (dB/cm)'); ax[0, 1].set_ylabel('n_m'); ax[0, 2].set_ylabel('Re Zc (Ω)  solid: P2 residue, dotted: P1')
ax[0, 0].legend(); ax[0, 2].legend(); ax[0, 1].set_ylim(1.85, 2.1); ax[0, 2].set_ylim(33, 41)
ax[1, 0].plot(F[1:], 20*np.log10(abs(pS21[1:])), color='k'); ax[1, 0].set_ylabel('one port region: |S21| (dB)')
ax[1, 1].plot(F[1:], np.rad2deg(np.angle(pS21[1:])), color='k'); ax[1, 1].set_ylabel('one port region: ∠S21 (deg)')
ax[1, 2].plot(F[1:], 20*np.log10(abs(pS11[1:])), color='k'); ax[1, 2].set_ylabel('one port region: |S11| (dB), Zc ref')
for a in ax.flat: a.grid(alpha=.3); a.set_xlabel('Frequency (GHz)')
fig.suptitle('De-embedded line parameters from three lengths, and the fitted port region')
fig.tight_layout(); fig.savefig('three_lengths.png', dpi=140)
