"""Does the line A / line B asymmetry spoil the 5 x 1 mm cascade?
Force exact A/B symmetry (average S with its A<->B mirror image) in both
files, then cascade again and compare with the raw cascade."""
import numpy as np
from first_look_lib import load4
from cascade_naive import star
P = [2, 3, 0, 1]                          # swap ports 1<->3, 2<->4 (line A <-> line B)
sym = lambda S: 0.5*(S + S[:, P][:, :, P])
f, S1 = load4("LINEA0_1MM_200UM_PITCH.s4p"); _, S5 = load4("LINEA0_5MM_200UM_PITCH.s4p")
def chain(S, n=5):
    C = S
    for _ in range(n-1): C = star(C, S)
    return C
db = lambda x: 20*np.log10(abs(x)); G = f/1e9
cases = {"raw": (S5, chain(S1)), "A/B symmetrised": (sym(S5), chain(sym(S1)))}
print(" GHz |      NEXT S31: 5mm  5x1mm (raw) | 5mm  5x1mm (sym) ||  FEXT S41: 5mm 5x1mm (raw) | 5mm 5x1mm (sym)")
for g in (1, 10, 20, 30, 45, 60):
    i = np.argmin(abs(G-g)); r5, rc = cases["raw"]; s5, sc = cases["A/B symmetrised"]
    print(f"{g:4d} | {db(r5[i,2,0]):7.1f} {db(rc[i,2,0]):7.1f} | {db(s5[i,2,0]):7.1f} {db(sc[i,2,0]):7.1f} || "
          f"{db(r5[i,3,0]):7.1f} {db(rc[i,3,0]):7.1f} | {db(s5[i,3,0]):7.1f} {db(sc[i,3,0]):7.1f}")
