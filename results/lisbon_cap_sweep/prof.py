import json, time, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt; plt.show=lambda *a,**k: plt.close('all')
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Lisbona_lifted_buffer_cap_sweep.ipynb")); g = {}
for i, c in enumerate(nb["cells"][:5]):
    t = time.time(); exec("".join(c["source"]), g); print("cell", i, round(time.time() - t, 1), "s")
