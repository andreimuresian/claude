"""Even/odd decomposition of the 1 mm coupled pair. Ports: 1,2 = line A near/far; 3,4 = line B near/far."""
import numpy as np
c0 = 299792458.0; R0 = 50.0; L = 1e-3
d = np.load("s4p.npz"); f, S = d["f"], d["S"]
AA = S[:, :2, :2]; AB = S[:, :2, 2:]          # [[S11,S12],[S21,S22]] and [[S13,S14],[S23,S24]]
def gz(M, Rm):
    s11, s21, s12, s22 = M[:, 0, 0], M[:, 1, 0], M[:, 0, 1], M[:, 1, 1]
    A = ((1+s11)*(1-s22) + s12*s21)/(2*s21)
    B = Rm*((1+s11)*(1+s22) - s12*s21)/(2*s21)
    C = ((1-s11)*(1-s22) - s12*s21)/(2*s21)/Rm
    e = A - np.sqrt(A*A-1); e = np.where(abs(e) > 1, A + np.sqrt(A*A-1), e)   # e^{-gL}
    al = -np.log(abs(e))/L
    be = np.unwrap(-np.angle(e))/L
    return al, be, np.sqrt(B/C)
# even mode: line voltages (1,1)/sqrt2 -> S_AA + S_AB, reference R0 per line
# odd mode : (1,-1)/sqrt2 -> S_AA - S_AB
out = {}
for name, M in (("even", AA+AB), ("odd", AA-AB), ("single-line view", AA)):
    al, be, Z = gz(M, R0); out[name] = (al, be, Z)
for G in (5, 10, 30, 60):
    i = np.argmin(abs(f-G*1e9)); w = 2*np.pi*f[i]
    s = f"{G:3d} GHz"
    for n in ("even", "odd"):
        al, be, Z = out[n]
        s += f" | {n}: n={be[i]*c0/w:.4f} a={al[i]*0.0868589:.2f} dB/cm Z={Z[i].real:.2f}{Z[i].imag:+.2f}j"
    print(s)
ne = out["even"][1]*c0/(2*np.pi*f+1e-30); no = out["odd"][1]*c0/(2*np.pi*f+1e-30)
np.savez("modes.npz", f=f, ne=ne, no=no, Ze=out["even"][2], Zo=out["odd"][2], ae=out["even"][0], ao=out["odd"][0])
