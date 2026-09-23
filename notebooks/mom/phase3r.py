"""Phase 3 remediation driver: common-mesh differencing + root audit.

Two targeted changes against the Phase 3 V3.4 run, nothing else:
  1. the etched and unetched cells share ONE triangulation (common_mesh), so
     the discretisation error is common-mode and cancels in dC / dL / d_alpha;
  2. the Bloch root is bracketed on a fine |g| grid that stops below the TM0
     surface-wave index instead of a 7-point grid that ran past it.

Everything else -- kernel, assembly, eigenvalue, RLGC extraction, scoring -- is
reused verbatim from Phase 3.
"""
import sys, time, json, warnings
sys.path.insert(0, "/home/user/claude/notebooks/mom")
warnings.filterwarnings("ignore")
import numpy as np
import mesh_generator as mg
import phase3_run as p3
from common_mesh import build_common_cells
from root_audit import gscan, minima, fmt
from bloch_solver import (assemble_periodic, bloch_mode, tl_test_vector,
                          line_rlgc)
from layered_greens import C0

H = float(sys.argv[1]) if len(sys.argv) > 1 else 9e-6
NPTS = int(sys.argv[2]) if len(sys.argv) > 2 else 14
TAG = sys.argv[3] if len(sys.argv) > 3 else "r"
SCR = "/tmp/claude-0/-home-user-claude/f069cebc-0d61-5069-a4b8-cc5b76a72567/scratchpad/r"
ZS = p3.ZS_AU


def rlgc2(cell, fk, Zs, beta, **kw):
    """RLGC with BOTH eigenvector choices, to test whether Vh[-1] (the smallest
    singular vector, which Phase 3 used) is the transmission-line mode or a
    loop current from the EFIE near-null subspace.

    'inv' is one step of inverse iteration from the TL test vector, x = Z^-1 y,
    which targets the mode that carries longitudinal current by construction."""
    Z, C_b, Gpot = assemble_periodic(cell, fk, Zs, beta, want_pot=True, **kw)
    reg = cell["region"]; A = cell["area"]
    sig = reg == "sig"; gnd = ~sig
    y = tl_test_vector(cell)
    _, _, Vh = np.linalg.svd(Z)
    out = {}
    for name, x in (("svd", Vh[-1].conj()),
                    ("inv", np.linalg.solve(Z, y))):
        x = x/np.linalg.norm(x)
        q = C_b @ x
        phi = Gpot @ q
        V = (phi[sig] @ A[sig])/A[sig].sum() - (phi[gnd] @ A[gnd])/A[gnd].sum()
        Qp = q[sig].sum()/cell["Lz"]
        C = Qp/V
        Z0 = beta/(fk.w*C)
        out[name] = dict(C=C, L=Z0*beta/fk.w, Z0=Z0,
                         overlap=float(abs(np.vdot(y/np.linalg.norm(y), x))),
                         qnorm=float(np.linalg.norm(q)))
    return out


def run_cell(cell, fk, label, log):
    ns, g = gscan(cell, fk, ZS, npts=NPTS)
    log.append(fmt(ns, g, label))
    m = minima(ns, g)
    n0 = m[0][0] if m else float(ns[int(np.argmin(g))])
    b, hist = bloch_mode(cell, fk, ZS, complex(n0, -0.02)*fk.k0)
    nm = b.real*C0/fk.w
    al = abs(b.imag)*8.686/100.0
    q = rlgc2(cell, fk, ZS, b)
    log.append(f"   -> seed n={n0:.3f}  root n_m={nm:.4f} alpha={al:.4f} dB/cm"
               f"  ({len(hist)} iters)  overlap svd={q['svd']['overlap']:.3f}"
               f" inv={q['inv']['overlap']:.3f}")
    return dict(beta=b, nm=nm, alpha=al, rlgc=q, scan=(ns.tolist(), g.tolist()),
                minima=m, n_seed=n0, Nt=len(cell["tris"]), Ne=len(cell["L"]))


def main():
    d = p3.load()
    qs = np.linspace(0.02, 0.98, 5)
    idx = [(d["alpha_delta_val"] - d["alpha_delta_val"].quantile(q)).abs().idxmin()
           for q in qs]
    idx = list(dict.fromkeys(idx))
    print("rows:", idx, flush=True)
    log, res = [], []
    for i in idx:
        row = d.loc[i]; t0 = time.time()
        g = mg.geom_from_row(row)
        cu, ce, info = build_common_cells(g, H)
        print(f"\nrow {i}: Nt {info['Nt_unetched']}/{info['Nt_etched']} "
              f"(slot {info['Nt_slot']})  Ne {info['Ne_unetched']}/"
              f"{info['Ne_etched']}  shared_identical={info['shared_identical']}",
              flush=True)
        log.append(f"\n===== row {i} =====  common mesh: Nt {info['Nt_unetched']}"
                   f" unetched / {info['Nt_etched']} etched (slot "
                   f"{info['Nt_slot']}), Ne {info['Ne_unetched']}/"
                   f"{info['Ne_etched']}")
        du = 1.05*(cu["cent"][:, 0].max() - cu["cent"][:, 0].min()) + 1e-5
        fk = p3.kernel_for(row, du)
        out = {}
        for etched, cell in ((False, cu), (True, ce)):
            out[etched] = run_cell(cell, fk, f"{'etched' if etched else 'unetched'}", log)
            print(log[-1], flush=True)
        P = mg.PITCH
        rec = dict(row=int(i), info=info,
                   nm_u=out[False]["nm"], nm_e=out[True]["nm"],
                   a_u=out[False]["alpha"], a_e=out[True]["alpha"],
                   dal=out[True]["alpha"] - out[False]["alpha"],
                   scan_u=out[False]["scan"], scan_e=out[True]["scan"],
                   min_u=out[False]["minima"], min_e=out[True]["minima"],
                   seed_u=out[False]["n_seed"], seed_e=out[True]["n_seed"])
        for k in ("svd", "inv"):
            Cu = out[False]["rlgc"][k]["C"].real; Ce = out[True]["rlgc"][k]["C"].real
            Lu = out[False]["rlgc"][k]["L"].real; Le = out[True]["rlgc"][k]["L"].real
            rec[f"dC_{k}"] = (Ce - Cu)*P
            rec[f"dL_{k}"] = (Le - Lu)*P
            rec[f"C_u_{k}"] = Cu; rec[f"L_u_{k}"] = Lu
            rec[f"ov_u_{k}"] = out[False]["rlgc"][k]["overlap"]
            rec[f"ov_e_{k}"] = out[True]["rlgc"][k]["overlap"]
        rec["ref"] = dict(dal=float(row["alpha_delta_val"]),
                          dL=float(row["deltaL lumped"]),
                          dC=float(row["deltaC lumped"]),
                          nm_base=float(row["nm_baseline_val"]),
                          a_base=float(row["alpha_baseline_val"]),
                          z0_base=float(row["z0_baseline_val"]))
        for k in ("svd", "inv"):
            rec[f"e_dC_{k}"] = abs(rec[f"dC_{k}"] - rec["ref"]["dC"])/abs(rec["ref"]["dC"])
            rec[f"e_dL_{k}"] = abs(rec[f"dL_{k}"] - rec["ref"]["dL"])/abs(rec["ref"]["dL"])
        rec["e_dal"] = abs(rec["dal"] - rec["ref"]["dal"])/abs(rec["ref"]["dal"])
        rec["e_nm"] = abs(rec["nm_u"] - rec["ref"]["nm_base"])/rec["ref"]["nm_base"]
        print(f"   n_m unetched {rec['nm_u']:.4f} vs {rec['ref']['nm_base']:.4f}"
              f"  ({rec['e_nm']*100:.1f}%)", flush=True)
        print(f"   D_alpha {rec['dal']:+.4f} vs {rec['ref']['dal']:+.4f}"
              f"  err {rec['e_dal']*100:6.1f}%", flush=True)
        for k in ("svd", "inv"):
            print(f"   [{k}] D_C {rec['dC_'+k]:+.4e} vs {rec['ref']['dC']:+.4e}"
                  f" err {rec['e_dC_'+k]*100:6.1f}%   |   D_L {rec['dL_'+k]:+.4e}"
                  f" vs {rec['ref']['dL']:+.4e} err {rec['e_dL_'+k]*100:6.1f}%",
                  flush=True)
        print(f"   [{time.time()-t0:.0f}s]", flush=True)
        res.append(rec)
        json.dump(res, open(f"{SCR}/{TAG}.json", "w"), default=str, indent=1)
        open(f"{SCR}/{TAG}_audit.txt", "w").write("\n".join(log))

    print("\n===== gates =====", flush=True)
    for nm, key, med, per in (("V3.4a  d_alpha", "e_dal", 0.25, 0.40),
                              ("V3.4c  d_C [svd]", "e_dC_svd", 0.20, 0.35),
                              ("V3.4c  d_C [inv]", "e_dC_inv", 0.20, 0.35),
                              ("3R.3   d_L [svd]", "e_dL_svd", 0.20, 0.35),
                              ("3R.3   d_L [inv]", "e_dL_inv", 0.20, 0.35)):
        v = np.array([r[key] for r in res])
        print(f"  {nm}: median {np.median(v)*100:6.1f}% (gate {med*100:.0f}%)"
              f"  worst {v.max()*100:6.1f}% (gate {per*100:.0f}%)  "
              f"{'PASS' if np.median(v) < med and v.max() < per else 'FAIL'}",
              flush=True)
    v = np.array([r["e_nm"] for r in res])
    print(f"  n_m unetched: median {np.median(v)*100:6.1f}%  worst {v.max()*100:6.1f}%",
          flush=True)
    print("saved", f"{SCR}/{TAG}.json", flush=True)


if __name__ == "__main__":
    main()
