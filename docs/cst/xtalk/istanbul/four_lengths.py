"""Istanbul slow-wave pair (T period 200 um, line pitch 625 um): 3-D CST runs at
1, 3, 5 and 8.75 mm. Checks (symmetry, reciprocity), per-mode propagation
constants from every pair of lengths, mesh families, and length scaling of
NEXT / FEXT. Ports: 1 = A near, 2 = A far, 3 = B near, 4 = B far."""
import os, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
C0 = 299792458.0
FILES = {1.0: "ISTANBUL_SW_1p00mm.s4p", 3.0: "TEST0_XTALK_SW__3p00mm.s4p",
         5.0: "TEST0_XTALK_SW_5mm.s4p", 8.75: "ISTANBUL_SW_8p75mm.s4p"}
R = 50.0
def rd(fn):
    toks = []
    for l in open(os.path.join(HERE, fn)):
        l = l.split('!')[0].strip()
        if not l or l.startswith('#'): continue
        toks += l.split()
    v = np.array(toks, float).reshape(-1, 33)
    return v[:, 0], (v[:, 1::2] * np.exp(1j * np.radians(v[:, 2::2]))).reshape(-1, 4, 4)
def modes(S):
    out = {}
    for m, sg in (("e", 1), ("o", -1)):
        out[m] = np.array([[S[:, 0, 0] + sg * S[:, 0, 2], S[:, 0, 1] + sg * S[:, 0, 3]],
                           [S[:, 1, 0] + sg * S[:, 1, 2], S[:, 1, 1] + sg * S[:, 1, 3]]]).transpose(2, 0, 1)
    return out
def s2t(s):
    s11, s12, s21, s22 = s[..., 0, 0], s[..., 0, 1], s[..., 1, 0], s[..., 1, 1]
    A = ((1 + s11) * (1 - s22) + s12 * s21) / (2 * s21); B = R * ((1 + s11) * (1 + s22) - s12 * s21) / (2 * s21)
    C = ((1 - s11) * (1 - s22) - s12 * s21) / (2 * s21) / R; D = ((1 - s11) * (1 + s22) + s12 * s21) / (2 * s21)
    return np.stack([np.stack([A, B], -1), np.stack([C, D], -1)], -2)
def gamma_pair(M, La, Lb, m):
    ev = np.linalg.eigvals(s2t(M[La][m]) @ np.linalg.inv(s2t(M[Lb][m])))
    e = np.where(abs(ev[:, 0]) > abs(ev[:, 1]), ev[:, 0], ev[:, 1])
    return (np.log(abs(e)) + 1j * np.unwrap(np.angle(e))) / ((La - Lb) * 1e-3)
f, _ = rd(FILES[1.0]); D = {L: rd(fn)[1] for L, fn in FILES.items()}; M = {L: modes(S) for L, S in D.items()}
k = 2 * np.pi * f * 1e9 / C0
if __name__ == "__main__":
    db = lambda x: 20 * np.log10(np.abs(x) + 1e-30)
    m = (f > 1) & (f < 75)
    print("checks: reciprocity max|S21-S12|/|S21|, A-B symmetry max|S21-S43|/|S21| (dB), |S11|-|S22| rms dB")
    for L, S in D.items():
        print(f"  {L:5.2f} mm  recip {np.max(abs(S[m,1,0]-S[m,0,1])/abs(S[m,1,0])):.1e}  AB {db(np.max(abs(S[m,1,0]-S[m,3,2]))):6.1f} dB"
              f"  S11-S22 {np.sqrt(np.mean((db(S[m,0,0])-db(S[m,1,1]))**2)):.2f} dB")
    pairs = [(5.0, 3.0), (8.75, 1.0), (3.0, 1.0), (5.0, 1.0), (8.75, 3.0), (8.75, 5.0)]
    G = {(p, md): gamma_pair(M, *p, md) for p in pairs for md in "eo"}
    np.savez(os.path.join(HERE, "four_lengths_gamma.npz"), f=f, **{f"{a}_{b}_{md}": G[((a, b), md)] for (a, b) in pairs for md in "eo"})
    print("\nn_even and dn = n_e - n_o (x1e3) from each pair of lengths")
    print("  pair      " + "".join(f"{x:>17.0f} GHz" for x in (10, 20, 30, 40, 50, 60, 70)))
    for p in pairs:
        row = ""
        for x in (10, 20, 30, 40, 50, 60, 70):
            i = np.argmin(abs(f - x)); ne = G[(p, "e")][i].imag / k[i]; dn = (G[(p, "e")][i].imag - G[(p, "o")][i].imag) / k[i]
            row += f"   {ne:.4f} / {dn*1e3:+6.2f}"
        print(f"  {p[0]:4.2f}-{p[1]:4.2f} {row}")
