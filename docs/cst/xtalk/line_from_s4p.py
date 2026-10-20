"""The 200 um pitch line's own parameters (alpha, n_m, Zc) from the CROSSTALK
runs only (LINEA0_1MM/5MM_200UM_PITCH.s4p), compared with the single-line
cascade (../cascade/three_lengths_results.npz, from LINEA0_0p5/1/5MM.s2p).

Ports: 1 = A near, 2 = A far, 3 = B near, 4 = B far.
Even / odd 2-ports: S_e,o(i,j) = S(i,j) +- S(i,j') with j' the same end of the
other line. Per mode, exactly the cascade's method:
  gamma: eigenvalue of T_1mm^-1 T_5mm (4 mm of line; exact, the port residue
         is a similarity transform);
  Zc:    port model P . L(l) . mirror(P), P = series Zs, shunt Yp, with gamma
         fixed, fitted to both lengths per frequency (8 real data, 6 unknowns).
The line is the average of the two modes: gamma = (ge + go)/2, Zc = sqrt(Ze Zo).
The split itself stays with the 2-D port modes (3-D is at its error floor)."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from first_look_lib import load4
c, R0 = 299792458, 50.0
f, S1 = load4("LINEA0_1MM_200UM_PITCH.s4p"); f5, S5 = load4("LINEA0_5MM_200UM_PITCH.s4p")
assert np.allclose(f, f5)
w = 2*np.pi*f; F = f/1e9; nf = len(f); DB = 20/np.log(10)

def mode(S, sgn):
    M = np.empty((len(S), 2, 2), complex)
    for i, (a, a2) in enumerate(((0, 2), (1, 3))):
        for j, (b, b2) in enumerate(((0, 2), (1, 3))):
            M[:, i, j] = S[:, a, b] + sgn*S[:, a, b2]
    return M
def s2abcd(S):
    s11, s12, s21, s22 = S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1]
    A = ((1+s11)*(1-s22)+s12*s21)/(2*s21); B = R0*((1+s11)*(1+s22)-s12*s21)/(2*s21)
    C = ((1-s11)*(1-s22)-s12*s21)/(2*s21)/R0; D = ((1-s11)*(1+s22)+s12*s21)/(2*s21)
    return np.stack([np.stack([A, B], -1), np.stack([C, D], -1)], -2)
def gamma_from_trace(T, L):
    A = (T[:, 0, 0]+T[:, 1, 1])/2
    r = np.sqrt(A*A-1+0j); y = A-r; y = np.where(abs(y) > 1, A+r, y)
    return -np.log(abs(y))/L - 1j*np.unwrap(np.angle(y))/L
def Lmat(gl, Z):
    return np.array([[np.cosh(gl), Z*np.sinh(gl)], [np.sinh(gl)/Z, np.cosh(gl)]])
def mirror(P):
    return np.array([[P[1, 1], P[0, 1]], [P[1, 0], P[0, 0]]])
def s_of(T):
    A, B, C, D = T[0, 0], T[0, 1], T[1, 0], T[1, 1]; d = A+B/R0+C*R0+D
    return np.array([(A+B/R0-C*R0-D)/d, 2/d, (-A+B/R0-C*R0+D)/d])

def extract(sgn, Zguess):
    M1, M5 = mode(S1, sgn), mode(S5, sgn)
    T1, T5 = s2abcd(M1), s2abcd(M5)
    g = gamma_from_trace(np.linalg.solve(T1, T5), 4e-3)
    meas = {1e-3: M1, 5e-3: M5}
    Z = np.full(nf, np.nan+0j); res = np.zeros(nf); p0 = np.array([Zguess, 0, 0, 0, 0, 0.0])
    for k in range(1, nf):
        def r(p):
            Zc, Zs, Yp = p[0]+1j*p[1], p[2]+1j*p[3], p[4]+1j*p[5]
            P = np.array([[1, Zs], [0, 1]]) @ np.array([[1, 0], [Yp, 1]])
            out = []
            for L, Mm in meas.items():
                e = s_of(P @ Lmat(g[k]*L, Zc) @ mirror(P)) - np.array([Mm[k, 0, 0], Mm[k, 1, 0], Mm[k, 1, 1]])
                out += [e.real, e.imag]
            return np.concatenate(out)
        sol = least_squares(r, p0, x_scale=[10, 10, 1, 1, 1e-3, 1e-3])
        Z[k] = sol.x[0]+1j*sol.x[1]; p0 = sol.x; res[k] = np.abs(r(sol.x)).max()
    return g, Z, res

ge, Ze, re_ = extract(+1, 37.0)
go, Zo, ro_ = extract(-1, 37.0)
g = (ge+go)/2; Z = np.sqrt(Ze*Zo)
R = np.load("../cascade/three_lengths_results.npz"); gc_, Zc_ = R["g"], R["Zfit"]
assert np.allclose(R["f"], f)
k = slice(1, None)
al, alc = g.real*DB/100, gc_.real*DB/100
n, nc = g.imag*c/w, gc_.imag*c/w
print("f GHz | alpha dB/cm  xtalk  single | n_m  xtalk  single | Re Zc xtalk single | Im Zc xtalk single | fit resid e/o")
for x in (1, 5, 10, 20, 30, 40, 50, 60):
    i = np.argmin(abs(F-x))
    print(f"{F[i]:5.0f} | {al[i]:7.3f} {alc[i]:7.3f} | {n[i]:7.4f} {nc[i]:7.4f} | {Z[i].real:6.2f} {Zc_[i].real:6.2f} | "
          f"{Z[i].imag:6.2f} {Zc_[i].imag:6.2f} | {re_[i]:.1e} {ro_[i]:.1e}")
b = (F >= 2) & (F <= 60)
print("\n2-60 GHz: max |d alpha| %.3f dB/cm (%.1f %%), max |d n_m| %.4f (%.2f %%), max |d Zc| %.2f ohm (%.1f %%)" % (
    np.max(abs(al-alc)[b]), 100*np.max(abs(al-alc)[b]/alc[b]), np.max(abs(n-nc)[b]), 100*np.max(abs(n-nc)[b]/nc[b]),
    np.max(abs(Z-Zc_)[b]), 100*np.max(abs(Z-Zc_)[b]/abs(Zc_[b]))))
print("even-odd from 3-D (floor-limited, for info): dn at 30 GHz = %.5f, 2-D gives ~0.0015" % ((ge-go).imag*c/w)[np.argmin(abs(F-30))])
np.savez("line_from_s4p_results.npz", f=f, g=g, Z=Z, ge=ge, go=go, Ze=Ze, Zo=Zo)

fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))
ax[0].plot(F[k], alc[k], "k", lw=2, label="single-line runs (cascade, 3 lengths)")
ax[0].plot(F[k], al[k], "C3--", lw=1.6, label="crosstalk runs (even/odd average, 2 lengths)")
ax[1].plot(F[k], nc[k], "k", lw=2); ax[1].plot(F[k], n[k], "C3--", lw=1.6)
ax[2].plot(F[k], Zc_[k].real, "k", lw=2); ax[2].plot(F[k], Z[k].real, "C3--", lw=1.6)
ax[2].plot(F[k], Zc_[k].imag, "k:", lw=1.5, label="Im, single"); ax[2].plot(F[k], Z[k].imag, "C3:", lw=1.5, label="Im, crosstalk")
ax[0].set_ylabel("α (dB/cm)"); ax[1].set_ylabel("n_m"); ax[2].set_ylabel("Zc (Ω): solid Re, dotted Im")
ax[1].set_ylim(1.85, 2.15); ax[2].set_ylim(-10, 45); ax[0].legend(fontsize=8); ax[2].legend(fontsize=8)
for a in ax: a.grid(alpha=.3); a.set_xlabel("frequency (GHz)")
fig.suptitle("200 µm pitch line: single-line 3-D runs vs crosstalk 3-D runs")
fig.tight_layout(); fig.savefig("line_from_s4p.png", dpi=120)
