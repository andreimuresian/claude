"""VALIDATION RECORD for cpw_2d_static.py (kept: it is the evidence).
Driver for mtx_2d_probe: does finite electrode thickness reproduce CST's
MTX sensitivity in n_m AND Z0?  Pass criterion: within 30 % of CST's partials."""
import sys, json, time
sys.path.insert(0, "/home/user/claude/notebooks/mom")
# cpw_2d_static now lives in the parent (production)
import numpy as np, pandas as pd
import stack_params as sp
from cpw_2d_static import solve_cs, observables

C0 = 299792458.0
DATA = "/root/.claude/uploads/f069cebc-0d61-5069-a4b8-cc5b76a72567/51442c2b-FULL_DATASET.xlsx"
KW = dict(hmax=6e-6, pad_x=1200e-6, pad_up=800e-6)
V4 = ["WS", "GAP", "MTX", "ETCH_DEPTH"]


def run(row, mtx_um):
    return observables(*solve_cs(
        row.WS*1e-6, row.GAP*1e-6, 70e-6, mtx_um*1e-6,
        sp.TFLN - row.ETCH_DEPTH*1e-6, sp.BOX_H, sp.SI_H,
        sp.EPS_LN, sp.EPS_SIO2, sp.EPS_SI, **KW)[:2])


def partials(d, y, V=V4):
    X = np.column_stack([np.ones(len(d))] + [d[v].values for v in V])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    pred = X @ b
    R2 = 1 - ((y-pred)**2).sum()/((y-y.mean())**2).sum()
    return dict(zip(V, b[1:])), R2


def main():
    d = pd.read_excel(DATA)
    print("=== CST partials, 4-var baseline model (WS,GAP,MTX,ETCH_DEPTH) ===")
    pn, R2n = partials(d, d.nm_baseline_val.values)
    pz, R2z = partials(d, d.z0_baseline_val.values)
    print("  nm_baseline: R2=%.4f  dnm/dMTX = %+.5f /um" % (R2n, pn["MTX"]))
    print("  z0_baseline: R2=%.4f  dZ0/dMTX = %+.5f ohm/um" % (R2z, pz["MTX"]))

    rows = [118, 416, 121, 38, 49]
    print("\n=== per-row central difference, MTX +-20 %% ===", flush=True)
    print("| row | MTX um | n_m 2D | dn/dMTX 2D | dn/dMTX CST | ratio | "
          "Z0 2D | dZ0/dMTX 2D | dZ0/dMTX CST | ratio |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    per = []
    for i in rows:
        r = d.loc[i]; m = float(r.MTX); t0 = time.time()
        (n0, z0) = run(r, m)
        (nm_, zm_) = run(r, 0.8*m)
        (np_, zp_) = run(r, 1.2*m)
        dn = (np_-nm_)/(0.4*m); dz = (zp_-zm_)/(0.4*m)
        per.append(dict(row=int(i), MTX=m, n2d=n0, z2d=z0, dn=dn, dz=dz))
        print("| %d | %.3f | %.4f | %+.5f | %+.5f | %.2f | %.2f | %+.4f | %+.4f | %.2f |"
              % (i, m, n0, dn, pn["MTX"], dn/pn["MTX"], z0, dz, pz["MTX"], dz/pz["MTX"]),
              flush=True)

    print("\n=== 50-row scatter: regress the 2D predictions the same way ===", flush=True)
    idx = list(d.index[::10][:50])
    n2, z2 = [], []
    t0 = time.time()
    for k, i in enumerate(idx):
        a, b = run(d.loc[i], float(d.loc[i].MTX))
        n2.append(a); z2.append(b)
        if (k+1) % 10 == 0:
            print("   %d/50  [%.0fs]" % (k+1, time.time()-t0), flush=True)
    sub = d.loc[idx]
    qn, R2qn = partials(sub, np.array(n2))
    qz, R2qz = partials(sub, np.array(z2))
    cn, _ = partials(sub, sub.nm_baseline_val.values)
    cz, _ = partials(sub, sub.z0_baseline_val.values)
    print("\n| quantity | 2D partial dMTX | CST partial dMTX (same 50 rows) | ratio | 2D R2 |")
    print("|---|---|---|---|---|")
    print("| n_m | %+.5f | %+.5f | %.2f | %.3f |" % (qn["MTX"], cn["MTX"], qn["MTX"]/cn["MTX"], R2qn))
    print("| Z0  | %+.5f | %+.5f | %.2f | %.3f |" % (qz["MTX"], cz["MTX"], qz["MTX"]/cz["MTX"], R2qz))

    print("\n=== anchor: MTX -> 0 against C_base = nm/(c z0) from CST ===", flush=True)
    print("| row | C 2D @MTX=0 | C 2D @MTX | C_base CST | 2D(0)/CST | 2D(MTX)/CST |")
    print("|---|---|---|---|---|---|")
    anc = []
    for i in rows:
        r = d.loc[i]
        C0_, Ca0, _ = solve_cs(r.WS*1e-6, r.GAP*1e-6, 70e-6, 0.0,
                               sp.TFLN - r.ETCH_DEPTH*1e-6, sp.BOX_H, sp.SI_H,
                               sp.EPS_LN, sp.EPS_SIO2, sp.EPS_SI, **KW)
        Cm, Cam, _ = solve_cs(r.WS*1e-6, r.GAP*1e-6, 70e-6, r.MTX*1e-6,
                              sp.TFLN - r.ETCH_DEPTH*1e-6, sp.BOX_H, sp.SI_H,
                              sp.EPS_LN, sp.EPS_SIO2, sp.EPS_SI, **KW)
        Cb = r.nm_baseline_val/(C0*r.z0_baseline_val)
        anc.append(dict(row=int(i), C0=C0_, Cm=Cm, Cb=float(Cb)))
        print("| %d | %.4e | %.4e | %.4e | %+.1f%% | %+.1f%% |"
              % (i, C0_, Cm, Cb, (C0_/Cb-1)*100, (Cm/Cb-1)*100), flush=True)

    print("\n=== absolute n_m: does thickness close the 10-30 %% bias? ===", flush=True)
    print("| row | n_m CST | n_m 2D @MTX | err | n_m 2D @MTX=0 | err | n_m MoM 3D (zero-thk) | err |")
    print("|---|---|---|---|---|---|---|---|")
    mom = {118: 2.2808, 416: 2.2601, 121: 2.2722, 38: 2.2670, 49: 2.2650}
    for p, a in zip(per, anc):
        r = d.loc[p["row"]]; nb = float(r.nm_baseline_val)
        n0 = np.sqrt(a["C0"]/(a["C0"]/1))  # placeholder, recomputed below
        print("| %d | %.4f | %.4f | %+.1f%% | - | - | %.4f | %+.1f%% |"
              % (p["row"], nb, p["n2d"], (p["n2d"]/nb-1)*100,
                 mom[p["row"]], (mom[p["row"]]/nb-1)*100), flush=True)
    json.dump(dict(per=per, anc=anc, cst=dict(n=pn["MTX"], z=pz["MTX"])),
              open("/tmp/claude-0/-home-user-claude/f069cebc-0d61-5069-a4b8-cc5b76a72567/scratchpad/r/mtx2d.json", "w"), indent=1)


if __name__ == "__main__":
    main()
