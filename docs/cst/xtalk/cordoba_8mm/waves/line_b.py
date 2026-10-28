"""
Line B (victim) field of the port-1 run: the coupled-mode content lives here
(S+ - S- = 2 x B field). Patterns on B: CPW (Ey+ - Ey-)/2, slot (Ey+ + Ey-)/2.
Bloch pencil on B alone and on B normalised by A's forward-wave envelope.
"""
import numpy as np
from sector_pencil import fd, channels, hankel_sv, pencil, n_alpha, STEP, C0, LAM, DZ, z
np.set_printoptions(linewidth=200)
for f in fd["f_GHz"]:
    F = fd["ports"][f][1]
    Ac = (F["A"][0] - F["A"][1]) / 2; As = (F["A"][0] + F["A"][1]) / 2
    Bc = (F["B"][0] - F["B"][1]) / 2; Bs = (F["B"][0] + F["B"][1]) / 2
    r = lambda x: np.sqrt(np.mean(abs(x[60:-60]) ** 2))
    print(f"\n== {f:.0f} GHz  |A_cpw| {r(Ac):.3e}  A slot/cpw {r(As)/r(Ac):.2e}  B_cpw/A_cpw {r(Bc)/r(Ac):.2e} ({20*np.log10(r(Bc)/r(Ac)):.1f} dB)  B_slot/A_cpw {r(Bs)/r(Ac):.2e} ({20*np.log10(r(Bs)/r(Ac)):.1f} dB)")
    # envelope along z of B patterns (cell-averaged magnitude at 8 positions)
    zz = np.arange(0.5, 7.6, 1.0)
    env = lambda x: [np.sqrt(np.mean(abs(x[int(a/DZ)-18:int(a/DZ)+18])**2))/r(Ac) for a in zz]
    print("   z(mm)      " + " ".join(f"{a:7.1f}" for a in zz))
    print("   |B_cpw|/A  " + " ".join(f"{v:7.1e}" for v in env(Bc)))
    print("   |B_slot|/A " + " ".join(f"{v:7.1e}" for v in env(Bs)))
    X = np.vstack([channels(Bc), channels(Bs)]); X = X / np.sqrt(np.mean(abs(X) ** 2))
    sv, _ = hankel_sv(X)
    print("   B SV: " + " ".join(f"{v:.1e}" for v in sv[:8]))
    for M in (2, 3, 4, 5, 6):
        q, Am, err = pencil(X, M)
        n, a = n_alpha(q, f)
        ac = np.sqrt(np.mean(abs(Am[:, :STEP]) ** 2, axis=1)); as_ = np.sqrt(np.mean(abs(Am[:, STEP:]) ** 2, axis=1))
        o = np.argsort(-(ac + as_))
        print(f"   M={M} resid {err:.1e}: " + "; ".join(f"n {n[i]:+.3f} a {a[i]:6.1f} c {ac[i]:.2f} s {as_[i]:.2f}" for i in o))
