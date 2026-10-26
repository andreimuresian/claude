"""RF notebook for Cordoba (+ optional buffer and ALD), from the user's unetched RF notebook."""
import json, copy, sys
src = sys.argv[1]; out = sys.argv[2]
nb = json.load(open(src)); nb = copy.deepcopy(nb)
def setsrc(c, t):
    L = t.rstrip("\n").split("\n"); c["source"] = [l + "\n" for l in L[:-1]] + [L[-1]]
setsrc(nb["cells"][0], open("/home/user/claude/results/rf_cordoba/cell0.py").read())
c3 = "".join(nb["cells"][3]["source"])
a = "np.vstack([_xpath, np.full_like(_xpath, slab_h + au_h / 2.0)]))"
assert a in c3; c3 = c3.replace(a, "np.vstack([_xpath, np.full_like(_xpath, y_b + au_h / 2.0)]))")
setsrc(nb["cells"][3], c3)
for c in nb["cells"]: c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(out, "w"), indent=1, ensure_ascii=False); print("wrote", out)
