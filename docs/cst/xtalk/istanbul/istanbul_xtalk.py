"""Istanbul slow-wave pair (T period 200 um, line spacing 625 um), CST 3-D
4-ports at 1 mm and 8.75 mm. Ports: 1 A near, 2 A far, 3 B near, 4 B far.
1. NEXT = S31, FEXT = S41 of both runs; data floor |S21 - S43|.
2. Naive cascade: the 1 mm block raised to the power 8.75, per even/odd mode
   (2-port ABCD = [[cosh t, Z sinh t],[sinh t / Z, cosh t]] with t continued in
   frequency), then NEXT = (S11e - S11o)/2, FEXT = (S21e - S21o)/2 at 50 ohm.
   The port regions are repeated 8.75 times, as in any naive cascade.
3. Two-length de-embedding (7.75 mm of line): gamma_e, gamma_o -> n_e, n_o,
   dn, loss of the slow-wave line itself."""
import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
sys.path.insert(0, "..")
from first_look_lib import load4
c, R0 = 299792458, 50.0
f, S1 = load4("ISTANBUL_SW_1p00mm.s4p"); f8, S8 = load4("ISTANBUL_SW_8p75mm.s4p")
assert np.allclose(f, f8)
k = slice(1, None); F = f/1e9; w = 2*np.pi*f
db = lambda x: 20*np.log10(np.abs(x) + 1e-30)
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
    return A, B, C, D
def abcd2s(A, B, C, D):
    d = A + B/R0 + C*R0 + D
    return (A + B/R0 - C*R0 - D)/d, 2/d
def power(S, n):
    """2-port raised to the power n (symmetric, reciprocal): A = cosh t."""
    A, B, C, D = s2abcd(S)
    Am = (A + D)/2
    r = np.sqrt(Am*Am - 1 + 0j); y = Am - r; y = np.where(abs(y) > 1, Am + r, y)   # e^{-t}
    t = -np.log(np.abs(y)) - 1j*np.unwrap(np.angle(y))                              # continued
    Z = np.sqrt(B/C); Z = np.where(Z.real < 0, -Z, Z)
    return abcd2s(np.cosh(n*t), Z*np.sinh(n*t), np.sinh(n*t)/Z, np.cosh(n*t))
casc = {}
for sgn, nm in ((+1, "e"), (-1, "o")):
    casc[nm] = power(mode(S1, sgn), 8.75)
NEXTc = 0.5*(casc["e"][0] - casc["o"][0]); FEXTc = 0.5*(casc["e"][1] - casc["o"][1])
# de-embedded line (7.75 mm)
def gamma(Sa, Sb, L):
    out = {}
    for sgn, nm in ((+1, "e"), (-1, "o")):
        Ta = np.array(s2abcd(mode(Sa, sgn))).T.reshape(-1, 2, 2)
        Tb = np.array(s2abcd(mode(Sb, sgn))).T.reshape(-1, 2, 2)
        T = np.linalg.solve(Ta, Tb); Am = (T[:, 0, 0] + T[:, 1, 1])/2
        r = np.sqrt(Am*Am - 1 + 0j); y = Am - r; y = np.where(abs(y) > 1, Am + r, y)
        out[nm] = -np.log(np.abs(y))/L - 1j*np.unwrap(np.angle(y))/L
    return out
g = gamma(S1, S8, 7.75e-3)
ne, no = g["e"].imag*c/w, g["o"].imag*c/w
ale = g["e"].real*20/np.log(10)/100
rows = []
print(" GHz | NEXT 1mm  8.75mm  casc | FEXT 1mm  8.75mm  casc | n_e     n_o      dn       | alpha_e dB/cm")
for x in (5, 10, 20, 30, 40, 50, 60, 70):
    i = np.argmin(abs(F - x))
    print(f"{F[i]:4.0f} | {db(S1[i,2,0]):6.1f} {db(S8[i,2,0]):7.1f} {db(NEXTc[i]):6.1f} | "
          f"{db(S1[i,3,0]):6.1f} {db(S8[i,3,0]):7.1f} {db(FEXTc[i]):6.1f} | "
          f"{ne[i]:.4f}  {no[i]:.4f}  {ne[i]-no[i]:+.5f} | {ale[i]:.3f}")
np.savez("istanbul_results.npz", f=f, ge=g["e"], go=g["o"], NEXTc=NEXTc, FEXTc=FEXTc)
fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
for a, j, nm in ((ax[0], 2, "NEXT |S31|"), (ax[1], 3, "FEXT |S41|")):
    a.plot(F[k], db(S1[k, j, 0]), color="#8a93a5", lw=1.3, label="CST 1 mm")
    a.plot(F[k], db(S8[k, j, 0]), "k", lw=2, label="CST 8.75 mm")
    a.plot(F[k], db((NEXTc if j == 2 else FEXTc)[k]), "C3--", lw=1.6, label="1 mm cascaded x 8.75")
    a.set_title(f"Istanbul slow-wave pair, {nm}"); a.set_ylim(-110, -20); a.set_ylabel("dB")
a = ax[2]
a.plot(F[k], (ne - no)[k]*1e3, "k"); a.set_ylabel("n_e - n_o  (x 1e-3)")
a.set_title("de-embedded index split (7.75 mm)"); a.set_ylim(-20, 20)
for a in ax: a.grid(alpha=.3); a.set_xlabel("frequency (GHz)")
ax[0].legend(fontsize=8)
fig.tight_layout(); fig.savefig("istanbul_xtalk.png", dpi=120)
