"""45-60 GHz (and 5-20 GHz): does an extra wave fix B' CPW? Six modes + one extra forward/backward wave,
pattern = odd substrate cell mode 4 (5 deg run) or strips-vs-bottom pattern; n scanned 0.4-3.4, alpha 0-3 dB/mm.
Also: the substrate cell modes from the runs, with their own n (interpolated from the cell points)."""
import numpy as np, sweepfit as S
up = {"cell(odd m4)": S.pattern_raw("p5_odd/eig_odd_mode4_e.txt"),
      "cell(even m4)": S.pattern_raw("p5_even/eig_even_mode4_e.txt"),
      "sb pattern": S.pattern_raw("p20_even/eig_even_mode1_e.txt"),
      "CPW pattern": S.pattern_raw("p20_even/eig_even_mode3_e.txt")}
odd4 = [(44.8722501493, 5), (46.6417138449, 10), (49.4865, 15), (53.2591087204, 20), (57.7858407632, 25)]
print("odd cell family n at its points:", " ".join(f"{f:.1f}:{S.C0*np.deg2rad(p)/S.LAM/(2*np.pi*f*1e9):.3f}" for f, p in odd4))
for f in (5, 10, 15, 40, 45, 50, 55, 60):
    td = S.TDData(f); base = S.fit(f, td)["res"]["B CPW"]
    line = f"{f:2d} GHz six {base:.3f} |"
    for nm, u in up.items():
        best = (9, 0, 0)
        for n in np.arange(0.4, 3.41, 0.05):
            for a_db in (0.0, 0.3, 1.0, 3.0):
                ex = {"x": (u, n, a_db / 8.686e-3)}
                for side in ("e", "o"):
                    kw = {"extra_e": ex} if side == "e" else {"extra_o": ex}
                    r = S.fit(f, td, **kw)["res"]["B CPW"]
                    if r < best[0]: best = (r, n, a_db, side)
        line += f" {nm}: {best[0]:.3f} (n {best[1]:.2f}, {best[2]} dB/mm, {best[3]}) |"
    print(line, flush=True)
