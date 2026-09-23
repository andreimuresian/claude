"""Homogeneous-medium validation of the periodic MoM chain.

Fill ALL space (above and below the metal plane) with one permittivity eps_r.
The line then supports an exact TEM mode and every answer is known in closed
form, with no CST, no dataset and no tolerance judgement:

    n_m = sqrt(eps_r)                exactly, independent of WS/GAP
    C(eps_r) / C(1) = eps_r          exactly (electrostatics is linear in eps
                                     when the whole space is filled)
    L(eps_r) / L(1) = 1              exactly (mu = mu0 everywhere; the magnetic
                                     problem does not see the permittivity)

The first tests beta, i.e. the full assembly including the vector-potential
channel.  The second tests the charge/potential extraction through G_q alone,
with no reference to beta.  The third is the statement that isolates G_A.

CAVEAT on L*C, recorded because it is easy to mis-read as a second test:
line_rlgc defines L = Z0*beta/w with Z0 = beta/(w*C), so L*C = beta^2/w^2 =
n_m^2/c^2 IDENTICALLY, for any C whatsoever.  Checking L*C against n_m^2/c^2
therefore re-tests nothing -- it is an algebraic identity of the extraction,
not an independent measurement.  It is reported below for completeness and
flagged.  The genuinely independent second test is the C(eps)/C(1) ratio.

The metal keeps its production surface impedance Zs (lossy gold).  That shifts
Re(n_m) by ~(R/2wL)^2 ~ 2e-5, below the 1e-4 resolution of the test.
"""
import sys, time, json, warnings
sys.path.insert(0, "/home/user/claude/notebooks/mom")
warnings.filterwarnings("ignore")
import numpy as np
import stack_params as sp
import mesh_generator as mg

_LAYERS = sp.device_layers
_AIR = sp.EPS_AIR


def set_homogeneous(eps):
    """Patch the stack so FloquetKernel builds Stack(eps, [], eps)."""
    sp.EPS_AIR = float(eps)
    sp.device_layers = lambda t_LN=None, lossy=True: []


def restore():
    sp.EPS_AIR = _AIR
    sp.device_layers = _LAYERS


C0 = 299792458.0
EPSL = [1.0, 11.7]


def main():
    import phase3_run as p3
    from common_mesh import build_common_cells
    from bloch_solver import bloch_mode, line_rlgc
    from floquet_greens import FloquetKernel

    d = p3.load()
    qs = np.linspace(0.02, 0.98, 5)
    idx = [(d["alpha_delta_val"] - d["alpha_delta_val"].quantile(q)).abs().idxmin()
           for q in qs]
    idx = list(dict.fromkeys(idx))
    H = 9e-6
    res = []
    for i in idx:
        row = d.loc[i]
        cell, _, info = build_common_cells(mg.geom_from_row(row), H)   # unetched
        du = 1.05*(cell["cent"][:, 0].max() - cell["cent"][:, 0].min()) + 1e-5
        for eps in EPSL:
            t0 = time.time()
            set_homogeneous(eps)
            try:
                fk = FloquetKernel(sp.SLAB_REF, P=mg.PITCH, n_rad=200, du_max=du)
                npol = sum(len(v) for v in fk.poles.values())
                cell.pop("_asm_cache", None)
                n_exp = np.sqrt(eps)
                b0 = complex(n_exp, -1e-4)*fk.k0
                b, hist = bloch_mode(cell, fk, p3.ZS_AU, b0)
                q = line_rlgc(cell, fk, p3.ZS_AU, b)
            finally:
                restore()
            nm = b.real*C0/fk.w
            C = complex(q["C"]).real; L = complex(q["L"]).real
            rec = dict(row=int(i), eps=eps, n_exp=float(n_exp), n_meas=float(nm),
                       C=C, L=L, LC=float(L*C), npoles=int(npol),
                       iters=len(hist), Nt=int(info["Nt_unetched"]))
            res.append(rec)
            print(f"row {i:3d} eps={eps:5.2f}  n_exp={n_exp:.4f} "
                  f"n_meas={nm:.4f}  err={(nm/n_exp-1)*100:+7.3f}%   "
                  f"C={C:.4e} L={L:.4e}  LC={L*C:.4e} "
                  f"(n^2/c^2={n_exp**2/C0**2:.4e})  poles={npol} "
                  f"[{time.time()-t0:.0f}s]", flush=True)
            json.dump(res, open("/tmp/claude-0/-home-user-claude/"
                                "f069cebc-0d61-5069-a4b8-cc5b76a72567/"
                                "scratchpad/r/homog.json", "w"), indent=1)

    print("\n===== homogeneous-medium gates =====", flush=True)
    for eps in EPSL:
        v = np.array([r["n_meas"] for r in res if r["eps"] == eps])
        ne = np.sqrt(eps)
        print(f"  eps={eps:5.2f}: n_m expected {ne:.4f}  measured "
              f"{v.min():.4f}..{v.max():.4f}  worst err "
              f"{np.abs(v/ne-1).max()*100:+.3f}%  spread {(v.max()/v.min()-1)*100:.3f}%",
              flush=True)
    print("\n  independent G_q / G_A decomposition (ratio across eps):", flush=True)
    for i in idx:
        a = [r for r in res if r["row"] == i and r["eps"] == 1.0]
        b_ = [r for r in res if r["row"] == i and r["eps"] == 11.7]
        if a and b_:
            print(f"   row {i:3d}  C(11.7)/C(1) = {b_[0]['C']/a[0]['C']:7.4f} "
                  f"(exact 11.7000)   L(11.7)/L(1) = {b_[0]['L']/a[0]['L']:7.4f} "
                  f"(exact 1.0000)", flush=True)


if __name__ == "__main__":
    main()
