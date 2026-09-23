"""Test 1/1b: the Floquet kernel against its exact free-space closed form.

Fill all space with air.  The 1D-periodic free-space Green's function then has
a closed form with no Ewald, no tables and no truncation.  Writing
g(R) = exp(-jkR)/(4 pi R) for the scalar 3D kernel, the Floquet sum

    g_p(du, dv) = sum_m g(sqrt(du^2 + (dv - mP)^2)) exp(j beta m P)

is, by Poisson,

    g_p = sum_n c_n(du) exp(j beta_n dv),   beta_n = beta + 2 pi n / P
    c_n = (-j/4P) H0^(2)(kappa_n |du|),     kappa_n = sqrt(k^2 - beta_n^2)

with the branch Im(kappa_n) <= 0.  For an evanescent harmonic kappa_n = -j a_n
(a_n = sqrt(beta_n^2 - k^2) > 0) and H0^(2)(-j a rho) = (2j/pi) K0(a rho), so
c_n = K0(a_n |du|)/(2 pi P), which is real and decays exponentially in n.

In air the two potential kernels are scalar multiples of the same function:
    G_q = g / eps0        (K_q = 1/(4 pi eps0))
    G_A = mu0 * g         (K_A = mu0/(4 pi))

so one reference serves both.  This tests the whole periodic machinery -- the
soft harmonic sum, the sharp radial table, the image truncation n_sharp, the
Bloch phase -- with no MoM assembly involved.

Test 1b runs the same comparison at beta = 0, where every Bloch phase is 1 and
the n = 0 harmonic is propagating.  A kernel that is right at beta = 0 and
wrong at beta != 0 indicts the Bloch phase; one wrong at both indicts the
Ewald split.
"""
import sys, warnings
sys.path.insert(0, "/home/user/claude/notebooks/mom")
warnings.filterwarnings("ignore")
import numpy as np
from scipy import special
import stack_params as sp
import mesh_generator as mg
import homog_test as ht

EPS0 = 8.8541878128e-12
MU0 = 4.0e-7*np.pi
C0 = 299792458.0


def g_exact(du, dv, beta, k, P, N=6000):
    """Exact 1D-periodic free-space scalar Green's function."""
    du = np.abs(np.atleast_1d(du).astype(float))
    dv = np.atleast_1d(dv).astype(float)
    n = np.arange(-N, N+1)
    bn = beta + 2*np.pi*n/P
    kap = np.sqrt(complex(k)**2 - bn.astype(complex)**2)
    kap = np.where(kap.imag > 0, -kap, kap)             # Im <= 0, outgoing
    out = np.zeros(du.shape, complex)
    for i in range(du.size):
        ev = kap.imag < -1e-12                          # evanescent harmonics
        c = np.empty(bn.shape, complex)
        a = (1j*kap[ev]).real                           # a_n > 0
        c[ev] = special.kv(0, a*du.flat[i])/(2*np.pi*P)
        if (~ev).any():
            c[~ev] = (-0.25j/P)*special.hankel2(0, kap[~ev]*du.flat[i])
        out.flat[i] = np.sum(c*np.exp(1j*bn*dv.flat[i]))
    return out


def main():
    P = mg.PITCH
    k = 2*np.pi*sp.F0/C0
    DU = np.array([5., 20., 50., 100., 200., 400.])*1e-6
    rows = []
    ht.set_homogeneous(1.0)
    try:
        from floquet_greens import FloquetKernel
        fk = FloquetKernel(sp.SLAB_REF, P=P, n_rad=200, du_max=1.2e-3)
        print(f"poles={sum(len(v) for v in fk.poles.values())}  "
              f"n_sharp={fk.n_sharp}  E*P={fk.E*P:.2f}  k0={fk.k0:.2f}", flush=True)
        for beta, blab in ((1285.0, "1285"), (0.0, "0")):
            fk.set_beta(beta)
            for dv in (0.0, 0.5*P):
                for ns in (fk.n_sharp, 16):
                    gq, ga = fk.G_periodic(DU, np.full(DU.shape, dv), n_sharp=ns)
                    ge = g_exact(DU, np.full(DU.shape, dv), beta, k, P)
                    gqe, gae = ge/EPS0, MU0*ge
                    for j, du in enumerate(DU):
                        rows.append(dict(du=du*1e6, dv=dv*1e6, beta=beta, ns=ns,
                                         gq=gq[j], gqe=gqe[j], ga=ga[j], gae=gae[j],
                                         eq=abs(gq[j]-gqe[j])/abs(gqe[j]),
                                         ea=abs(ga[j]-gae[j])/abs(gae[j])))
    finally:
        ht.restore()

    for ns in sorted({r["ns"] for r in rows}):
        print(f"\n### n_sharp = {ns}", flush=True)
        print("| du (um) | dv (um) | beta | G_q solver | G_q exact | rel err | "
              "G_A solver | G_A exact | rel err |")
        print("|---|---|---|---|---|---|---|---|---|")
        for r in rows:
            if r["ns"] != ns:
                continue
            print(f"| {r['du']:.0f} | {r['dv']:.0f} | {r['beta']:.0f} | "
                  f"{r['gq'].real:.4e} | {r['gqe'].real:.4e} | {r['eq']:.2e} | "
                  f"{r['ga'].real:.4e} | {r['gae'].real:.4e} | {r['ea']:.2e} |")
    print("\n===== worst relative error =====", flush=True)
    for beta in (1285.0, 0.0):
        for ns in sorted({r["ns"] for r in rows}):
            s = [r for r in rows if r["beta"] == beta and r["ns"] == ns]
            wq = max(r["eq"] for r in s); wa = max(r["ea"] for r in s)
            print(f"  beta={beta:6.0f} n_sharp={ns:2d}:  G_q {wq:.3e}   G_A {wa:.3e}",
                  flush=True)


if __name__ == "__main__":
    main()
