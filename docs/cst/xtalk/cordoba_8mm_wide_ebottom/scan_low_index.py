"""30 GHz, electric bottom: does a slow-index-free wave with n between 1.0 and 2.3 (substrate-wave range)
improve the six-mode fit of the TD gap fields? Extra wave: forward + backward, pattern of the 2 mm even
mode 4 (substrate wave) and, for comparison, of the open-bottom A-vs-B mode; n and loss scanned."""
import os, sys, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
with contextlib.redirect_stdout(io.StringIO()):
    exec(open(os.path.join(HERE, "fit30_ebottom_modes.py")).read().split("# free extra wave")[0])
import numpy as np
base = F.fit(E, O)["rBc"]
print(f"six modes (1.2 mm cell): B' CPW residual {base:.3f}")
orig = F.gamma
for lab, fn in (("2 mm even mode 4 (substrate wave)", "../eigen_w2mm_mag_ebottom/eig_even_mode4_e.txt"),
                ("open-bottom A vs B", "../eigen_w1.2mm_mag/eig_odd_mode1_AvsB.txt")):
    F.MODES["x_free"] = (fn, 22.4143168874, 4.604, None)
    res = []
    for n in np.arange(1.0, 2.31, 0.05):
        for a in (1, 3, 8, 15, 30):
            def g(f_GHz, Q, ng, n_override=None, n=n, a=a):
                if abs(f_GHz - 22.4143168874) < 1e-6:
                    return a * 100 / 8.686 + 1j * n * 2 * np.pi * F.F / F.C0, n, a
                return orig(f_GHz, Q, ng)
            F.gamma = g; o = F.fit(E, O + ["x_free"]); F.gamma = orig
            res.append((o["rBc"], n, a))
    res.sort(); prof = {}
    for r, n, a in res: prof[round(n, 2)] = min(prof.get(round(n, 2), 9), r)
    print(f"{lab}: best n {res[0][1]:.2f}, a {res[0][2]} dB/cm -> {res[0][0]:.3f}")
    print("   best residual vs n:", " ".join(f"{n:.2f}:{v:.3f}" for n, v in sorted(prof.items())))
