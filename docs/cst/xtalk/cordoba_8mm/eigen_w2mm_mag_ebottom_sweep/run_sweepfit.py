"""Driver: dispersion tables, then the six-mode fit at the 12 TD monitor frequencies (nearest and
interpolated patterns), residuals per pattern and EO crosstalk (model vs data). Output: run_sweepfit.log."""
import numpy as np, sweepfit as S
print("Dispersion fits n(f) = n_inf + b/sqrt(f) + c f (f in GHz); residual at the eigen points:")
for fam, D in S.DISP.items():
    print(f"  {fam:7s} n_inf {D.cn[0]:.4f} b {D.cn[1]:+.4f} c {D.cn[2]:+.2e}  max|resid| {abs(D.resid_n()).max():.1e}"
          f"  f {D.f.min():.1f}-{D.f.max():.1f} GHz  alpha fit max rel err "
          f"{abs(D.alpha(D.f)/D.alpha_pts-1).max():.2%}")
print("CPW split (n_e - n_o) at 5..60 GHz:", " ".join(f"{S.split_cpw(f):.2e}" for f in S.FTD))
for mode in ("nearest", "interp"):
    print(f"\n=== patterns: {mode} ===")
    print(" f  | A CPW | A slot | B' CPW | B' slot | EO data kept | EO model kept | diff dB, deg | EO full (dB)")
    for f in S.FTD:
        td = S.TDData(f); o = S.fit(f, td, mode=mode); e = o["eo"]
        Xd = e["Hd_B"] / e["Hd_A"]; Xm = e["Hm_B"] / e["Hm_A"]
        r = o["res"]
        print(f"{f:3d} | {r['A CPW']:.3f} | {r['A slot']:6.2f} | {r['B CPW']:.3f}  | {r['B slot']:.3f}   |"
              f" {20*np.log10(abs(Xd)):7.2f}      | {20*np.log10(abs(Xm)):7.2f}       |"
              f" {20*np.log10(abs(Xm/Xd)):+5.2f} {np.degrees(np.angle(Xm/Xd)):+6.1f} | {20*np.log10(abs(S.eo_full(td, f))):7.2f}")
