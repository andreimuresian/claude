"""Per-mode model (lumped port: series Zs, shunt Yp at each end; line gamma, Zc)
fitted to one mesh family's two lengths, then used to predict every length
(the de-embedded cascade). Families: coarse (3, 5 mm), fine (1, 8.75 mm)."""
import os, sys, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scipy.optimize import least_squares
from four_lengths import f, k, M, D, gamma_pair, R
def line(g, Z, l): return np.array([[np.cosh(g*l), Z*np.sinh(g*l)], [np.sinh(g*l)/Z, np.cosh(g*l)]])
def port(Zs, Yp): return np.array([[1, Zs], [0, 1]]) @ np.array([[1, 0], [Yp, 1]])
def mir(P): return np.array([[P[1, 1], P[0, 1]], [P[1, 0], P[0, 0]]])
def t2s(T):
    A, B, C, Dd = T[0, 0], T[0, 1], T[1, 0], T[1, 1]; den = A + B/R + C*R + Dd
    return np.array([[(A + B/R - C*R - Dd)/den, 2*(A*Dd - B*C)/den], [2/den, (-A + B/R - C*R + Dd)/den]])
def model(p, g, l):
    P = port(p[0] + 1j*p[1], (p[2] + 1j*p[3])*1e-3); return t2s(P @ line(g, p[4] + 1j*p[5], l*1e-3) @ mir(P))
def fit_family(La, Lb):
    out = {}
    for md in "eo":
        g = gamma_pair(M, La, Lb, md); P = np.zeros((len(f), 6)); res = np.zeros(len(f)); prev = [0, 0.3, 0, 0.3, 45, -1]
        for i in range(len(f)):
            if f[i] < 1: continue
            def r(p):
                e = []
                for L in (La, Lb):
                    d = (model(p, g[i], L) - M[L][md][i]).ravel(); e += list(d.real) + list(d.imag)
                return e
            s = least_squares(r, prev); P[i], res[i], prev = s.x, np.linalg.norm(s.fun), s.x
        out[md] = (g, P, res)
    return out
def predict(fam, L, i, dn_mesh=0.0):
    S = {}
    for md in "eo":
        g, P, _ = fam[md]; S[md] = model(P[i], g[i] + 1j*k[i]*dn_mesh, L)
    return 0.5*(S["e"][0, 0] - S["o"][0, 0]), 0.5*(S["e"][1, 0] - S["o"][1, 0]), 0.5*(S["e"][1, 0] + S["o"][1, 0])
if __name__ == "__main__":
    db = lambda x: 20*np.log10(abs(x) + 1e-30)
    fams = {"coarse 3+5": fit_family(5.0, 3.0), "fine 1+8.75": fit_family(8.75, 1.0)}
    for name, fam in fams.items():
        print(f"\n== {name}: fit residual max (1-75 GHz) e {fam['e'][2][(f>1)&(f<75)].max():.1e} o {fam['o'][2][(f>1)&(f<75)].max():.1e}")
        print("  f   n_e     Zc_e         Zc_o        delta=Ze/Zo-1   port Ls(pH) Cp(fF)")
        for x in (10, 20, 30, 40, 50, 60):
            i = np.argmin(abs(f - x)); pe, po = fam["e"][1][i], fam["o"][1][i]
            Ze, Zo = pe[4] + 1j*pe[5], po[4] + 1j*po[5]
            print(f"  {f[i]:3.0f} {fam['e'][0][i].imag/k[i]:.4f}  {Ze.real:6.2f}{Ze.imag:+5.2f}j {Zo.real:6.2f}{Zo.imag:+5.2f}j  {abs(Ze/Zo)-1:+.4f}"
                  f"   {pe[1]/(2*np.pi*f[i]*1e9)*1e12:6.1f} {pe[3]*1e-3/(2*np.pi*f[i]*1e9)*1e15:6.1f}")
    print("\nPredicted vs CST crosstalk (dB): NEXT | FEXT | through-phase error (deg)")
    for name, fam in fams.items():
        print(f"== model from {name}")
        for L in (1.0, 3.0, 5.0, 8.75):
            row = f"  {L:5.2f} mm"
            for x in (10, 30, 50):
                i = np.argmin(abs(f - x)); N, F, T = predict(fam, L, i); Sd = D[L][i]
                row += f" | {x:2d}G N {db(N):6.1f}/{db(Sd[2,0]):6.1f} F {db(F):6.1f}/{db(Sd[3,0]):6.1f} ph {np.degrees(np.angle(T/Sd[1,0])):+5.1f}"
            print(row)
