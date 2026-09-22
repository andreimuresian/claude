import sys, time, warnings, json
sys.path.insert(0,"/home/user/claude/notebooks/mom")
warnings.filterwarnings("ignore")
import numpy as np
import phase3_run as p3
import mesh_generator as mg
from bloch_solver import line_rlgc
from layered_greens import C0

H = float(sys.argv[1]) if len(sys.argv) > 1 else 6e-6
NROW = int(sys.argv[2]) if len(sys.argv) > 2 else 5
OUT = sys.argv[3] if len(sys.argv) > 3 else "/tmp/claude-0/-home-user-claude/f069cebc-0d61-5069-a4b8-cc5b76a72567/scratchpad/v34.json"

d = p3.load()
# 5 rows spanning the Delta-alpha range (quantiles of alpha_delta_val)
qs = np.linspace(0.02, 0.98, NROW)
idx = [ (d["alpha_delta_val"]-d["alpha_delta_val"].quantile(q)).abs().idxmin() for q in qs ]
idx = list(dict.fromkeys(idx))
print("rows:", idx, "alpha_delta:", [round(float(d.loc[i,'alpha_delta_val']),3) for i in idx])

res = []
for i in idx:
    row = d.loc[i]
    print(f"\nrow {i}  WS={row['WS']:.2f} GAP={row['GAP']:.2f} L1={row['L1']:.1f} L2={row['L2']:.1f} "
          f"W1={row['W1']:.1f} W2={row['W2']:.1f} ETCH={row['ETCH_DEPTH']:.3f}")
    t0 = time.time()
    out = {}
    fk = None
    for etched in (False, True):
        r = p3.solve(row, H, etched=etched, fk=fk)
        fk = r["fk"]
        q = line_rlgc(r["cell"], fk, p3.ZS_AU, r["beta"])
        out[etched] = dict(beta=r["beta"], nm=r["nm"], alpha=r["alpha"],
                           L=complex(q["L"]), C=complex(q["C"]), Z0=complex(q["Z0"]))
        print(f"      L={q['L'].real:.4e} H/m  C={q['C'].real:.4e} F/m  Z0={q['Z0'].real:.2f} ohm")
    dal = out[True]["alpha"] - out[False]["alpha"]
    # The reference columns are LUMPED per tee (H, F); the MoM gives
    # per-unit-length (H/m, F/m).  One tee per period, so x P.
    Pp = mg.PITCH
    dL = (out[True]["L"].real - out[False]["L"].real)*Pp
    dC = (out[True]["C"].real - out[False]["C"].real)*Pp
    ref = dict(dal=float(row["alpha_delta_val"]), dL=float(row["deltaL lumped"]),
               dC=float(row["deltaC lumped"]))
    e = {k: abs(v-ref[k])/abs(ref[k]) for k, v in (("dal",dal),("dL",dL),("dC",dC))}
    print(f"   D_alpha {dal:+.4f} vs {ref['dal']:+.4f}  err {e['dal']*100:6.1f}%")
    print(f"   D_L     {dL:+.4e} vs {ref['dL']:+.4e}  err {e['dL']*100:6.1f}%")
    print(f"   D_C     {dC:+.4e} vs {ref['dC']:+.4e}  err {e['dC']*100:6.1f}%")
    print(f"   [{time.time()-t0:.0f}s]")
    res.append(dict(row=int(i), dal=dal, dL=dL, dC=dC, ref=ref, err=e,
                    nm_u=out[False]["nm"], nm_e=out[True]["nm"],
                    L_u=out[False]["L"].real, C_u=out[False]["C"].real,
                    Z0_u=out[False]["Z0"].real,
                    a_u=out[False]["alpha"], a_e=out[True]["alpha"]))

print("\n===== V3.4 =====")
for k, med, per in (("dal",0.25,0.40), ("dL",0.20,0.35), ("dC",0.20,0.35)):
    v = np.array([r["err"][k] for r in res])
    print(f"  {k}: median {np.median(v)*100:6.1f}% (gate {med*100:.0f}%)  "
          f"worst {v.max()*100:6.1f}% (gate {per*100:.0f}%)  "
          f"{'PASS' if np.median(v)<med and v.max()<per else 'FAIL'}")

print("\n===== V3.5 composite =====")
for r in res:
    row = d.loc[r["row"]]
    nb, zb = float(row["nm_baseline_val"]), float(row["z0_baseline_val"])
    Lb, Cb = nb*zb/C0, nb/(C0*zb)
    Lt, Ct = Lb + r["dL"]/mg.PITCH, Cb + r["dC"]/mg.PITCH
    a_tot = float(row["alpha_baseline_val"]) + r["dal"]
    nm_t = C0*np.sqrt(Lt*Ct); z0_t = np.sqrt(Lt/Ct)
    ea = abs(a_tot-row["alpha_final_val"])/abs(row["alpha_final_val"])
    en = abs(nm_t-row["nm_final_val"])/row["nm_final_val"]
    ez = abs(z0_t-row["z0_final_val"])/row["z0_final_val"]
    print(f"  row {r['row']:3d}  a {a_tot:6.3f}/{row['alpha_final_val']:6.3f} {ea*100:6.1f}% | "
          f"nm {nm_t:6.3f}/{row['nm_final_val']:6.3f} {en*100:6.1f}% | "
          f"z0 {z0_t:6.2f}/{row['z0_final_val']:6.2f} {ez*100:6.1f}%")
    r["v35"] = dict(ea=ea, en=en, ez=ez)
for k, g in (("ea",0.05), ("en",0.03), ("ez",0.05)):
    v = np.array([r["v35"][k] for r in res])
    print(f"  {k}: median {np.median(v)*100:6.1f}%  (gate {g*100:.0f}%)  "
          f"{'PASS' if np.median(v)<g else 'FAIL'}")
json.dump([{k:(str(v) if isinstance(v,complex) else v) for k,v in r.items()} for r in res],
          open(OUT,"w"), indent=1, default=str)
print("saved", OUT)
