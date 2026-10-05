import json, sys
sys.path.insert(0, '.')
import eddy_tensor as E
rows = [json.loads(l) for l in open("results/doe_qs.jsonl")]
for r in rows:
    res, info = E.solve_Z([20e9, 60e9, 150e9], hfine=0.06, sig_w=r["S"], gap=r["W"], t=r["t"])
    print(json.dumps(dict(S=r["S"], W=r["W"], t=r["t"], h=r["h"], C_eps=r["C_eps"], C_air=r["C_air"],
                          R=[x["R"] for x in res], L=[x["L"] for x in res], f=[20, 60, 150])), flush=True)
