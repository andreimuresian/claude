"""
Istanbul 5 mm pair, CST field monitors at 30 GHz, port 1 (line A near end) driven.
Lines of samples along z at x = 1 um (mid gold height), y = +-0.305425 mm
(centre of the signal-ground gap of A / B on the side facing the other line).

1. Cell-average (200 um period) E_y and H_x.
2. Line A: fit forward + backward line waves (common gamma, wave impedance Zw).
3. Line B: forward and backward envelopes (polynomial in z) on the line gamma,
   from E and from H separately.
4. Group delay of NEXT / FEXT / through from the four .s4p files.
"""
import os, numpy as np
from scipy.optimize import least_squares
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__)); UP = os.path.dirname(HERE)
F0, C0, W, L = 30e9, 2.99792458e8, 100, 5.0
K0 = 2*np.pi*F0/C0*1e-3                          # rad/mm

def load(n):
    a = np.loadtxt(os.path.join(HERE, n), skiprows=2)
    return a[:, 2], a[:, 3::2] + 1j*a[:, 4::2]
z, EA = load("e-field_f30_Ypos_A.txt"); _, EB = load("e-field_f30_Yneg_B.txt")
_, HA = load("h-field_f30_Ypos_A.txt"); _, HB = load("h-field_f30_Yneg_B.txt")
cav = lambda v: np.convolve(v, np.ones(W)/W, mode="valid")
zc = cav(z); E = {"A": cav(EA[:, 1]), "B": cav(EB[:, 1])}; H = {"A": cav(HA[:, 0]), "B": cav(HB[:, 0])}
m = (zc > 0.25) & (zc < 4.75); zz = zc[m]

# ---- line A: two line waves, E and H jointly
def fitA(q, ret=False):
    beta, alpha, zr, zi = q; Zw = zr + 1j*zi; g = alpha + 1j*beta
    ef, eb = np.exp(-g*zz), np.exp(g*zz)
    M = np.vstack([np.column_stack([ef, eb]), np.column_stack([ef/Zw, -eb/Zw])])
    y = np.concatenate([E["A"][m], H["A"][m]])
    sc = np.concatenate([np.full(m.sum(), 1/abs(E["A"][m]).mean()), np.full(m.sum(), 1/abs(H["A"][m]).mean())])
    ab, *_ = np.linalg.lstsq(M*sc[:, None], y*sc, rcond=None)
    r = (M @ ab - y)*sc
    return (ab, np.linalg.norm(r)/np.linalg.norm(y*sc)) if ret else np.concatenate([r.real, r.imag])
q = min((least_squares(fitA, [2.1*K0, 0.01, s, 0]) for s in (-300, 300)), key=lambda s: s.cost).x
(aA, bA), errA = fitA(q, True); g = q[1] + 1j*q[0]; Zw = q[2] + 1j*q[3]

# ---- line B: polynomial envelopes on the line gamma, E and H separately
KP = 3
def envB(y):
    cols = [np.exp(-g*zz)*(zz/L)**k for k in range(KP)] + [np.exp(g*zz)*((L-zz)/L)**k for k in range(KP)]
    M = np.column_stack(cols); c, *_ = np.linalg.lstsq(M, y, rcond=None)
    return c, np.linalg.norm(M @ c - y)/np.linalg.norm(y)
cE, errE = envB(E["B"][m]); cH, errH = envB(H["B"][m])
fwd = lambda c, x: sum(c[k]*(x/L)**k for k in range(KP))
bwd = lambda c, x: sum(c[KP+k]*((L-x)/L)**k for k in range(KP))
db = lambda x: 20*np.log10(np.abs(x))

# ---- group delays from the s-parameters
import skrf
files = [("1", "ISTANBUL_SW_1p00mm.s4p"), ("3", "TEST0_XTALK_SW__3p00mm.s4p"),
         ("5", "TEST0_XTALK_SW_5mm.s4p"), ("8.75", "ISTANBUL_SW_8p75mm.s4p")]
gd_rows = []
for lab, fn in files:
    n = skrf.Network(os.path.join(UP, fn)); w = 2*np.pi*n.f
    gd = lambda x: -np.gradient(np.unwrap(np.angle(x)), w)*1e12
    sel = (n.f >= 10e9) & (n.f <= 40e9)
    t21, tN, tF = (np.median(gd(n.s[:, i, 0])[sel]) for i in (1, 2, 3))
    i30 = np.argmin(abs(n.f - F0))
    gd_rows.append((float(lab), t21, tN, tF, db(n.s[i30, 2, 0]), db(n.s[i30, 3, 0])))

if __name__ == "__main__":
    print(f"A: n = {q[0]/K0:.4f}, alpha = {q[1]*86.86:.2f} dB/cm, Zw = {Zw:.0f}, |b/a| = {abs(bA/aA):.3f}, fit residual {errA:.4f}")
    print(f"B envelope fits: residual E {errE:.4f}, H {errH:.4f}")
    print(" z(mm)  B fwd/E  B fwd/H   B bwd/E  B bwd/H  (dB re A forward)")
    for x in (0.25, 1, 2, 3, 4, 4.75):
        print(f" {x:5.2f}  {db(fwd(cE,x)/aA):6.1f}  {db(fwd(cH,x)*Zw/aA):6.1f}   {db(bwd(cE,x)/aA):6.1f}  {db(-bwd(cH,x)*Zw/aA):6.1f}")
    print(" L(mm)  t21   tNEXT  tNEXT/t21  (ps, median 10-40 GHz)   NEXT, FEXT at 30 GHz (dB)")
    for r in gd_rows:
        print(f" {r[0]:5.2f} {r[1]:6.1f} {r[2]:6.1f}  {r[2]/r[1]:5.2f}    {r[4]:6.1f} {r[5]:6.1f}")

    fig, ax = plt.subplots(3, 1, figsize=(9, 10), gridspec_kw=dict(height_ratios=[1, 1, 0.9]))
    a0 = ax[0]
    a0.plot(z, db(EA[:, 1]/aA), color="#3f7fd0", lw=0.8, label="line A, raw")
    a0.plot(z, db(EB[:, 1]/aA), color="#e2504a", lw=0.8, label="line B, raw")
    a0.plot(zc, db(E["B"]/aA), color="#8b1a1a", lw=1.8, label="line B, cell-averaged")
    a0.set_ylabel("$|E_y|$ re A forward wave (dB)"); a0.set_xlim(-0.05, 5.05); a0.set_ylim(-75, 10)
    a0.set_title("Istanbul 5 mm, 30 GHz, port 1 (A near end) driven: $E_y$ at the centre of the inner gaps")
    a1 = ax[1]; xs = np.linspace(0.25, 4.75, 200)
    a1.plot(xs, db(bwd(cE, xs)/aA), color="#8b1a1a", lw=2, label="B backward wave, from $E_y$")
    a1.plot(xs, db(-bwd(cH, xs)*Zw/aA), "--", color="#8b1a1a", lw=1.5, label="B backward wave, from $H_x$")
    a1.plot(xs, db(fwd(cE, xs)/aA), color="#2e8b57", lw=2, label="B forward wave, from $E_y$")
    a1.plot(xs, db(fwd(cH, xs)*Zw/aA), "--", color="#2e8b57", lw=1.5, label="B forward wave, from $H_x$")
    a1.axhline(gd_rows[2][4], color="#8b1a1a", ls=":", lw=1, label=f"|S31| NEXT = {gd_rows[2][4]:.1f} dB")
    a1.axhline(gd_rows[2][5], color="#2e8b57", ls=":", lw=1, label=f"|S41| FEXT = {gd_rows[2][5]:.1f} dB")
    a1.set_ylabel("wave amplitude on B\nre A forward wave (dB)"); a1.set_xlabel("z (mm)"); a1.set_xlim(-0.05, 5.05)
    a2 = ax[2]; Ls = [r[0] for r in gd_rows]
    a2.plot(Ls, [r[1] for r in gd_rows], "o-", color="#3f7fd0", label="through S21")
    a2.plot(Ls, [r[2] for r in gd_rows], "s-", color="#8b1a1a", label="NEXT S31")
    a2.plot(Ls, [2*r[1] for r in gd_rows], ":", color="#3f7fd0", label="2 x through (round trip)")
    a2.set_xlabel("line length (mm)"); a2.set_ylabel("group delay, median 10-40 GHz (ps)")
    for a in ax:
        a.grid(alpha=0.3); a.legend(fontsize=8, loc="best")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "field_decomposition.png"), dpi=130)
