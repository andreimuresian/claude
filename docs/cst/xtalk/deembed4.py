"""Steps 1-3 on the coupled pair (4-port), ports 1->2 line A, 3->4 line B.
1. Remove the single-line port region (series Zs, shunt Yp, fitted in
   docs/cst/cascade/three_lengths.py) from each line at both ends.
2. Chain five cleaned 1 mm blocks and compare with the cleaned 5 mm.
3. Two-length cancellation T1^-1 T5 (ports cancel without any model) = 4 mm,
   compared with four cleaned 1 mm blocks chained."""
import numpy as np, matplotlib.pyplot as plt
from first_look_lib import load4
R0 = 50.0; I2 = np.eye(2); I4 = np.eye(4)
Lp, Rp = [0, 2], [1, 3]                       # left ports (1,3), right ports (2,4)

def s2abcd(S):
    """4-port S (50 ohm) -> 4x4 ABCD: [V_L; I_L] = T [V_R; -I_R]."""
    Z = R0*(I4 + S) @ np.linalg.inv(I4 - S)
    ZLL, ZLR = Z[:, Lp][:, :, Lp], Z[:, Lp][:, :, Rp]
    ZRL, ZRR = Z[:, Rp][:, :, Lp], Z[:, Rp][:, :, Rp]
    C = np.linalg.inv(ZRL); D = C @ ZRR; A = ZLL @ C; B = ZLL @ D - ZLR
    return np.block([[A, B], [C, D]])

def abcd2s(T):
    A, B, C, D = T[:, :2, :2], T[:, :2, 2:], T[:, 2:, :2], T[:, 2:, 2:]
    Ci = np.linalg.inv(C)                      # Z-matrix from ABCD
    ZLL = A @ Ci; ZRL = Ci; ZRR = Ci @ D; ZLR = A @ Ci @ D - B
    Z = np.zeros_like(T)
    for P, Q, blk in [(Lp, Lp, ZLL), (Lp, Rp, ZLR), (Rp, Lp, ZRL), (Rp, Rp, ZRR)]:
        for a in range(2):
            for b in range(2):
                Z[:, P[a], Q[b]] = blk[:, a, b]
    return (Z - R0*I4) @ np.linalg.inv(Z + R0*I4)

f, S1 = load4("LINEA0_1MM_200UM_PITCH.s4p"); _, S5 = load4("LINEA0_5MM_200UM_PITCH.s4p")
k0 = slice(1, None)                            # skip DC (Z-matrix singular)
f, S1, S5 = f[k0], S1[k0], S5[k0]
pr = np.load("../cascade/three_lengths_results.npz"); Zs, Yp = pr["Zs"][k0], pr["Yp"][k0]
T1, T5 = s2abcd(S1), s2abcd(S5)

# port region, port side -> line side, same on both lines, no coupling
P = np.zeros((len(f), 4, 4), complex)
P[:, :2, :2] = ((1 + Zs*Yp)[:, None, None])*I2; P[:, :2, 2:] = Zs[:, None, None]*I2
P[:, 2:, :2] = Yp[:, None, None]*I2;           P[:, 2:, 2:] = I2
Pm = P.copy(); Pm[:, :2, :2], Pm[:, 2:, 2:] = P[:, 2:, 2:], P[:, :2, :2]   # mirror
clean = lambda T: np.linalg.inv(P) @ T @ np.linalg.inv(Pm)
T1c, T5c = clean(T1), clean(T5)
mp = np.linalg.matrix_power
T4x = np.linalg.solve(T1, T5)                  # step 3: T1^-1 T5

db = lambda x: 20*np.log10(abs(x)); G = f/1e9
cur = {"5 mm CST (raw)": abcd2s(T5), "5 mm, ports removed": abcd2s(T5c),
       "5 x 1 mm, ports removed": abcd2s(mp(T1c, 5)),
       "4 mm = T1^-1 T5": abcd2s(T4x), "4 x 1 mm, ports removed": abcd2s(mp(T1c, 4))}
k = lambda g: np.argmin(abs(G-g))
for g in (1, 10, 20, 30, 45, 60):
    print(f"{g:3d} GHz  " + " | ".join(f"{n[:14]}: N {db(s[k(g),2,0]):6.1f} F {db(s[k(g),3,0]):6.1f}" for n, s in cur.items()))

# modal check: eigenvalues of T1^-1 T5 are e^{+-gamma_e 4mm}, e^{+-gamma_o 4mm}
ev = np.linalg.eigvals(T4x); c = 299792458
lam = np.sort_complex(np.where(abs(ev) < 1, ev, 1/ev))      # forward ones, pairs
n_eff = -np.unwrap(np.angle(lam), axis=0)/(4e-3)*c/(2*np.pi*f[:, None])
for g in (10, 30, 60):
    print(f"{g} GHz n from T1^-1T5 eigenvalues:", np.round(np.sort(n_eff[k(g)]), 4))

st = {"5 mm CST (raw)": ("0.75", ":"), "5 mm, ports removed": ("k", "-"), "5 x 1 mm, ports removed": ("C3", "--"),
      "4 mm = T1^-1 T5": ("C0", "-"), "4 x 1 mm, ports removed": ("C1", "--")}
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
for row, names in enumerate([list(cur)[:3], list(cur)[3:]]):
    for col, (r, t) in enumerate([(2, "NEXT S31"), (3, "FEXT S41")]):
        a = ax[row, col]
        for n in names:
            a.plot(G, db(cur[n][:, r, 0]), color=st[n][0], ls=st[n][1], label=n)
        a.set_title(("Step 2: " if row == 0 else "Step 3: ") + t); a.grid(alpha=.3)
        a.set_xlabel("Frequency (GHz)"); a.set_ylabel("dB"); a.legend(fontsize=8)
plt.tight_layout(); plt.savefig("deembed4.png", dpi=130)
