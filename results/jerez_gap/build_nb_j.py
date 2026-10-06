"""Buffered Jerez lifted notebook: the attached Lisbon-lifted-buffer notebook with cell 0
replaced by cells/cell0_jerez_lifted_buffer.py (1360 nm, Sellmeier/J&C materials,
400 nm film, 170 nm etch, GAP_TOP 8)."""
import json, copy, sys
src = json.load(open("/root/.claude/uploads/fd41e088-2b12-5532-ab62-ef0605547492/ef5b4fb9-VPI_interface_optimized_Lisbona_lifted_buffer.ipynb"))
nb = copy.deepcopy(src)
for i, c in enumerate(nb["cells"]):
    text = "".join(c["source"])
    if i == 0:
        text = open("/home/user/claude/cells/cell0_jerez_lifted_buffer.py").read()
    lines = text.rstrip("\n").split("\n")
    c["source"] = [l + "\n" for l in lines[:-1]] + [lines[-1]]
    c["outputs"] = []; c["execution_count"] = None
json.dump(nb, open(sys.argv[1], "w"), indent=1, ensure_ascii=False)
print("wrote", sys.argv[1])
