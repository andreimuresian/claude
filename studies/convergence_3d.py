"""Mesh convergence of the differential penalties dL, dC.

The composite method's bet is that the etched-minus-unetched difference is
far better conditioned than either absolute capacitance.  This checks it.
"""
import sys, time
sys.path.insert(0, ".")

from tfln3d import build, penalties

if __name__ == "__main__":
    print(f"{'lc':>5} {'nodes':>9} {'C_un pF/m':>11} {'dC fF':>9} {'dL pH':>9} {'s':>6}")
    for lc in (4.0, 2.5, 1.5):
        f_u, nn, _ = build(etched=False, lc_gap=lc, air_h=40., si_h=60.,
                           n_air=4, n_si=4, out=f"cv_{lc}_u.msh")
        f_e, _, _ = build(etched=True, lc_gap=lc, air_h=40., si_h=60.,
                          n_air=4, n_si=4, out=f"cv_{lc}_e.msh")
        p = penalties(f_e, f_u)
        print(f"{lc:>5.1f} {nn:>9d} {p.C_unetched*1e12:>11.3f} "
              f"{p.dC*1e15:>+9.4f} {p.dL*1e12:>+9.4f} {p.seconds:>6.0f}")
