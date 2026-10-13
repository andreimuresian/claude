"""Fit the port model on the 1 mm and 5 mm runs only (gamma from 5-1), then
predict the 0.5 mm run and compare it with CST."""
import numpy as np
src = open('three_lengths.py').read()
exec(src.split("# ---------------- port model fit")[0].replace('print(', '(lambda *a, **k: None)('))
from scipy.optimize import least_squares
g = res[(1e-3, 5e-3)]['g']
def Lmat(gl, Z):
    return np.array([[np.cosh(gl), Z*np.sinh(gl)], [np.sinh(gl)/Z, np.cosh(gl)]])
def mirror(P): return np.array([[P[1, 1], P[0, 1]], [P[1, 0], P[0, 0]]])
def Tm(p, k, L):
    Z, Zs, Yp = p[0]+1j*p[1], p[2]+1j*p[3], p[4]+1j*p[5]
    P = np.array([[1, Zs], [0, 1]]) @ np.array([[1, 0], [Yp, 1]])
    return P @ Lmat(g[k]*L, Z) @ mirror(P)
def s_of(T):
    A, B, C, D = T[0, 0], T[0, 1], T[1, 0], T[1, 1]; d = A + B/R0 + C*R0 + D
    return np.array([(A + B/R0 - C*R0 - D)/d, 2/d])
meas = {L: abcd2s(T) for L, T in runs.items()}
p0 = np.array([39, 0, 0, 0, 0, 0.]); out = []
for k in range(1, nf):
    def r(p):
        e = []
        for L in (1e-3, 5e-3):
            d = s_of(Tm(p, k, L)) - np.array([meas[L][k][0, 0], meas[L][k][1, 0]]); e += [d.real, d.imag]
        return np.concatenate(e)
    p0 = least_squares(r, p0, x_scale=[10, 10, 1, 1, 1e-3, 1e-3]).x
    sp = s_of(Tm(p0, k, 0.5e-3)); sm = meas[0.5e-3][k]
    out.append((F[k], 20*np.log10(abs(sp[1])) - 20*np.log10(abs(sm[1, 0])), np.rad2deg(np.angle(sp[1]/sm[1, 0])),
                20*np.log10(abs(sp[0])), 20*np.log10(abs(sm[0, 0]))))
out = np.array(out)
for x in [1, 10, 20, 30, 40, 50, 60]:
    i = np.argmin(abs(out[:, 0] - x)); o = out[i]
    print(f"{o[0]:4.0f} GHz  0.5 mm predicted - CST: |S21| {o[1]:+.4f} dB, phase {o[2]:+.3f} deg | |S11| pred {o[3]:6.1f} CST {o[4]:6.1f} dB")
