"""Step 1: chain five 1 mm blocks and compare with the 5 mm CST result.
Ports: 1->2 line A, 3->4 line B; ports 1 and 3 at the same (left) end."""
import numpy as np, matplotlib.pyplot as plt
from first_look_lib import load4

L, R = [0, 2], [1, 3]          # left-end ports (1,3), right-end ports (2,4)

def blocks(S):
    """Split S into left/right blocks: b_L = S_LL a_L + S_LR a_R, etc."""
    return (S[:, L][:, :, L], S[:, L][:, :, R], S[:, R][:, :, L], S[:, R][:, :, R])

def star(SA, SB):
    """Redheffer star product: A's right end connected to B's left end."""
    A11, A12, A21, A22 = blocks(SA); B11, B12, B21, B22 = blocks(SB)
    I = np.eye(2)
    M1 = np.linalg.inv(I - B11 @ A22)       # bounces between the two blocks
    M2 = np.linalg.inv(I - A22 @ B11)
    S11 = A11 + A12 @ M1 @ B11 @ A21
    S12 = A12 @ M1 @ B12
    S21 = B21 @ M2 @ A21
    S22 = B22 + B21 @ M2 @ A22 @ B12
    S = np.zeros_like(SA)
    for (i, j), blk in {(0, 0): S11, (0, 1): S12, (1, 0): S21, (1, 1): S22}.items():
        P, Q = (L, R)[i], (L, R)[j]
        for a in range(2):
            for b in range(2):
                S[:, P[a], Q[b]] = blk[:, a, b]
    return S

if __name__ == "__main__":
    f1, S1 = load4("LINEA0_1MM_200UM_PITCH.s4p")
    f5, S5 = load4("LINEA0_5MM_200UM_PITCH.s4p")
    assert np.allclose(f1, f5)
    Sc = S1
    for _ in range(4):
        Sc = star(Sc, S1)
    db = lambda x: 20*np.log10(abs(x)); G = f1/1e9
    k = lambda g: np.argmin(abs(G-g))
    print("   GHz | thru S21 dB: 5mm  1mmx5 | NEXT S31: 5mm  1mmx5 | FEXT S41: 5mm  1mmx5")
    for g in (1, 10, 30, 50, 60):
        i = k(g)
        print(f"{g:6.0f} | {db(S5[i,1,0]):7.2f} {db(Sc[i,1,0]):7.2f} | "
              f"{db(S5[i,2,0]):6.1f} {db(Sc[i,2,0]):6.1f} | {db(S5[i,3,0]):6.1f} {db(Sc[i,3,0]):6.1f}")
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.2))
    for a, (r, c, name) in zip(ax, [(1, 0, "Through S21 (line A)"), (2, 0, "NEXT S31"), (3, 0, "FEXT S41")]):
        a.plot(G, db(S1[:, r, c]), color="0.7", label="1 mm (CST)")
        a.plot(G, db(S5[:, r, c]), "k", label="5 mm (CST)")
        a.plot(G, db(Sc[:, r, c]), "C3--", label="5 x 1 mm chained")
        a.set_title(name); a.set_xlabel("Frequency (GHz)"); a.set_ylabel("dB"); a.grid(alpha=.3)
    ax[0].legend()
    plt.tight_layout(); plt.savefig("cascade_naive.png", dpi=130)
