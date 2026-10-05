"""Etched-slab Cordoba notebook: the attached Cordoba notebook with cell 0 replaced by
cells/cell0_cordoba_etched.py and the numerics of cells 1, 2, 4 aligned with the
etched Lisbon-lifted notebook (quadrature order 4, unipolarity filter 0.85)."""
import json, copy, sys
src = json.load(open("/root/.claude/uploads/fd41e088-2b12-5532-ab62-ef0605547492/59b696fd-VPI_interface_optimized.ipynb"))
nb = copy.deepcopy(src)
sub = {
    1: [("basis_dc = Basis(skfem_mesh, ElementTriP1())", "basis_dc = Basis(skfem_mesh, ElementTriP1(), intorder=4)"),
        ("basis_p0 = Basis(skfem_mesh, ElementTriP0())", "basis_p0 = Basis(skfem_mesh, ElementTriP0(), intorder=4)")],
    2: [("basis_epsilon_r = Basis(skfem_mesh, ElementTriP0())", "basis_epsilon_r = Basis(skfem_mesh, ElementTriP0(), intorder=4)")],
    4: [('d["unipolarity"] >= 0.999', 'd["unipolarity"] >= 0.85   # same filter as the etched Lisbon-lifted notebook')],
}
def setsrc(c, text):
    lines = text.rstrip("\n").split("\n")
    c["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
for i, c in enumerate(nb["cells"]):
    text = "".join(c["source"])
    if i == 0:
        text = open("/home/user/claude/cells/cell0_cordoba_etched.py").read()
    for a, b in sub.get(i, []):
        assert a in text, (i, a)
        text = text.replace(a, b)
    setsrc(c, text)
    c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print("wrote", sys.argv[1])
