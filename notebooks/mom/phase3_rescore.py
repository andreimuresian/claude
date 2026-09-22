"""Re-score a finished V3.4 JSON with the lumped conversion (dL,dC x PITCH)."""
import sys, json
import numpy as np
sys.path.insert(0,"/home/user/claude/notebooks/mom")
import pandas as pd
P = 200e-6; C0 = 299792458.0
res = json.load(open(sys.argv[1]))
d = pd.read_excel("/root/.claude/uploads/f069cebc-0d61-5069-a4b8-cc5b76a72567/51442c2b-FULL_DATASET.xlsx")
scaled = "prescaled" in sys.argv
for r in res:
    for k in ("dal","dL","dC"):
        r[k] = float(r[k])
    if not scaled:
        r["dL"] *= P; r["dC"] *= P
    r["err"] = {k: abs(r[k]-r["ref"][k])/abs(r["ref"][k]) for k in ("dal","dL","dC")}
print(f"{'row':>5} {'Dalpha MoM/CST':>26} {'err':>8} | {'DL MoM/CST':>26} {'err':>8} | {'DC MoM/CST':>26} {'err':>8}")
for r in res:
    print(f"{r['row']:>5} {r['dal']:+11.4f}/{r['ref']['dal']:+11.4f} {r['err']['dal']*100:7.1f}% |"
          f" {r['dL']:+11.4e}/{r['ref']['dL']:+11.4e} {r['err']['dL']*100:7.1f}% |"
          f" {r['dC']:+11.4e}/{r['ref']['dC']:+11.4e} {r['err']['dC']*100:7.1f}%")
print("\n===== V3.4 =====")
ok = True
for k, med, per, nm in (("dal",0.25,0.40,"Dalpha"), ("dL",0.20,0.35,"DL"), ("dC",0.20,0.35,"DC")):
    v = np.array([r["err"][k] for r in res])
    p = np.median(v) < med and v.max() < per
    ok &= p
    print(f"  {nm:7s} median {np.median(v)*100:7.1f}% (gate {med*100:.0f}%)   "
          f"worst {v.max()*100:7.1f}% (gate {per*100:.0f}%)   {'PASS' if p else 'FAIL'}")
print("\n===== V3.5 composite =====")
for r in res:
    row = d.loc[r["row"]]
    nb, zb = float(row["nm_baseline_val"]), float(row["z0_baseline_val"])
    Lb, Cb = nb*zb/C0, nb/(C0*zb)
    Lt, Ct = Lb + r["dL"]/P, Cb + r["dC"]/P
    a = float(row["alpha_baseline_val"]) + r["dal"]
    nmt = C0*np.sqrt(Lt*Ct) if Lt*Ct > 0 else float("nan")
    z0t = np.sqrt(Lt/Ct) if Lt*Ct > 0 else float("nan")
    r["v35"] = dict(ea=abs(a-row["alpha_final_val"])/abs(row["alpha_final_val"]),
                    en=abs(nmt-row["nm_final_val"])/row["nm_final_val"],
                    ez=abs(z0t-row["z0_final_val"])/row["z0_final_val"])
    print(f"  row {r['row']:3d}  a {a:7.3f}/{row['alpha_final_val']:7.3f} {r['v35']['ea']*100:6.1f}% | "
          f"nm {nmt:6.3f}/{row['nm_final_val']:6.3f} {r['v35']['en']*100:6.1f}% | "
          f"z0 {z0t:6.2f}/{row['z0_final_val']:6.2f} {r['v35']['ez']*100:6.1f}%")
for k, g, nm in (("ea",0.05,"alpha"), ("en",0.03,"nm"), ("ez",0.05,"z0")):
    v = np.array([r["v35"][k] for r in res])
    print(f"  {nm:6s} median {np.median(v)*100:7.1f}%  (gate {g*100:.0f}%)  "
          f"{'PASS' if np.median(v)<g else 'FAIL'}")
json.dump(res, open(sys.argv[1].replace(".json","_scored.json"),"w"), indent=1, default=str)
