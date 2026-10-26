"""
Even/odd sector test on the Istanbul lengths.

Each sector (even: V_A = V_B, odd: V_A = -V_B) of the mirror-symmetric pair is
a 2-port. Model per sector: one uniform mode (gamma, line normalised to 60 ohm)
between two identical, mirrored, reciprocal end junctions J (ABCD a, b, c;
d = (1 + b c)/a). Unknowns per frequency: a, b, c, gamma (4 complex).
Data per length: S11, S21 of the end-symmetrised sector 2-port (2 complex).
With 3 lengths: 6 complex equations for 4 unknowns, so the residual is a
genuine test of 'one mode + fixed ends'.
"""
import os, numpy as np, skrf
from scipy.optimize import least_squares
UP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = {3.0: "TEST0_XTALK_SW__3p00mm.s4p", 5.0: "TEST0_XTALK_SW_5mm.s4p",
         8.75: "ISTANBUL_SW_8p75mm.s4p", 1.0: "ISTANBUL_SW_1p00mm.s4p"}
R0, ZL, C0 = 50.0, 60.0, 2.99792458e8

def sectors(fn):
    n = skrf.Network(os.path.join(UP, fn)); s = n.s
    out = {}
    for name, sg in (("even", 1), ("odd", -1)):
        S11 = 0.5*((s[:, 0, 0] + sg*s[:, 0, 2]) + (s[:, 1, 1] + sg*s[:, 1, 3]))
        S21 = 0.5*((s[:, 1, 0] + sg*s[:, 1, 2]) + (s[:, 0, 1] + sg*s[:, 0, 3]))
        out[name] = (S11, S21)
    return n.f, out

def model(x, L_list, w):
    a, b, c = x[0]+1j*x[1], x[2]+1j*x[3], x[4]+1j*x[5]
    g = x[6] + 1j*x[7]                         # 1/m
    d = (1 + b*c)/a
    J = np.array([[a, b], [c, d]]); Jr = np.array([[d, b], [c, a]])
    res = []
    for L in L_list:
        gl = g*L*1e-3
        Ln = np.array([[np.cosh(gl), ZL*np.sinh(gl)], [np.sinh(gl)/ZL, np.cosh(gl)]])
        A, B, C, D = (J @ Ln @ Jr).ravel()
        den = A + B/R0 + C*R0 + D
        res.append(((A + B/R0 - C*R0 - D)/den, 2/den))
    return res

def fit(f, data, Ls, pick):
    out = []
    x = np.array([1, 0, 0, 0, 0, 0, 0.0, 0.0])
    for i in pick:
        w = 2*np.pi*f[i]
        if i == pick[0] or True:
            x[6] = max(x[6], 0.5); x[7] = w*2.10/C0 if x[7] == 0 else x[7]*f[i]/f[prev] if 'prev' in dir() else w*2.10/C0
        def r(xx):
            m = model(xx, Ls, w); e = []
            for (S11, S21), L in zip(m, Ls):
                e += [S11 - data[L][0][i], S21 - data[L][1][i]]
            e = np.array(e); return np.concatenate([e.real, e.imag])
        best = None
        for x0 in (x, np.array([1, 0, 0, 0, 0, 0, x[6], x[7]])):
            s = least_squares(r, x0, method="lm", max_nfev=4000)
            if best is None or s.cost < best.cost: best = s
        x = best.x; prev = i
        e = r(x); e = e[:len(e)//2] + 1j*e[len(e)//2:]
        out.append((f[i], np.max(np.abs(e)), x[7]*C0/w, x[6]*8.686/100))
    return np.array(out)

if __name__ == "__main__":
    data = {}
    for L, fn in FILES.items():
        f, sec = sectors(fn); data[L] = sec
    Ls = [3.0, 5.0, 8.75]
    pick = [i for i in range(len(f)) if 2e9 <= f[i] <= 60e9][::5]
    res = {}
    for name in ("even", "odd"):
        dd = {L: data[L][name] for L in Ls}
        res[name] = fit(f, dd, Ls, pick)
    print(" GHz | even: max|err|  n    a dB/cm | odd: max|err|  n    a dB/cm")
    for k in range(0, len(pick), 4):
        e, o = res["even"][k], res["odd"][k]
        print(f"{e[0]/1e9:5.1f} | {e[1]:.4f} {e[2]:.4f} {e[3]:5.2f} | {o[1]:.4f} {o[2]:.4f} {o[3]:5.2f}")
    for name in ("even", "odd"):
        r = res[name]; m = (r[:, 0] >= 10e9) & (r[:, 0] <= 40e9)
        print(name, "median max|err| 2-60 GHz", np.median(r[:, 1]), " 10-40 GHz", np.median(r[m, 1]))
    np.savez("sector_fit.npz", even=res["even"], odd=res["odd"])
