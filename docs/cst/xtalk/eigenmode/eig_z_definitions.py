"""Absolute line impedance of mode 3 (even/odd) from the eigenmode fields with
three definitions: PV = |V|^2/2P, PI = 2P/|I|^2, VI = |V/I|.
I = Ampere loop integral of H around line A's signal strip
(y 82.5..117.5 um, x 0..2 um), loop 0.5-1 um outside the metal.
usage: python eig_z_definitions.py [fields.zip]"""
import sys, numpy as np
sys.argv = sys.argv[:2]
src = open("eig_impedance.py").read().split("Pe, Ve")[0]
exec(src)
def loop_current(x, y, H, x0, x1, y0, y1):
    ix0, ix1 = np.argmin(abs(x - x0)), np.argmin(abs(x - x1))
    iy0, iy1 = np.argmin(abs(y - y0)), np.argmin(abs(y - y1))
    # counter-clockwise in (y, x): bottom (x0, +y), right (y1, +x), top (x1, -y), left (y0, -x)
    I = np.trapezoid(H[ix0, iy0:iy1+1, 1], y[iy0:iy1+1])
    I += np.trapezoid(H[ix0:ix1+1, iy1, 0], x[ix0:ix1+1])
    I -= np.trapezoid(H[ix1, iy0:iy1+1, 1], y[iy0:iy1+1])
    I -= np.trapezoid(H[ix0:ix1+1, iy0, 0], x[ix0:ix1+1])
    return I
if __name__ == "__main__":
    for tag in ("even", "odd"):
      P, V, Zpv, Sz, x, y = analyse(tag)
      _, _, H = load(f"Mode_3_h_{tag}.txt")
      Is = [loop_current(x, y, H, -m, 2e-6 + m, 82.5e-6 - m, 117.5e-6 + m) for m in (0.5e-6, 1.0e-6)]
      I = np.mean(np.abs(Is)); Vm = np.mean(np.abs(V))
      print(f"{tag}: I loops {np.round(np.abs(Is)/I, 4)} (rel.)  Z_PV {Vm**2/(2*P):6.2f}  "
            f"Z_PI {2*P/I**2:6.2f}  Z_VI {Vm/I:6.2f} ohm")
