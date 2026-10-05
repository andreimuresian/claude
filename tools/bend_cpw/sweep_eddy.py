import json, sys, numpy as np
sys.path.insert(0, '.')
import eddy_tensor as E
f = np.array([0.1, 0.5, 1, 2, 5, 10, 20, 30, 45, 60, 80, 100, 130, 160, 200]) * 1e9
r, info = E.solve_Z(f, hfine=0.06)
for x in r:
    print(json.dumps({k: float(v) for k, v in x.items()}), flush=True)
print(json.dumps(dict(info={k: float(v) for k, v in info.items()})))
