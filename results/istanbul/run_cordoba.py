"""usage: run_cordoba.py GAP SLAB_W -> etched Cordoba notebook (flat 2 um gold) at that point"""
import json, re, sys, time
G, W = (float(a) for a in sys.argv[1:3])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Cordoba_etched_slab.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
src = re.sub(r"\nGAP = [0-9.]+", f"\nGAP = {G}", src); src = re.sub(r"\nSLAB_W = [0-9.]+", f"\nSLAB_W = {W}", src)
g = {}; exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(model="cordoba_flat", gap=G, slab_w=W, IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]))), flush=True)
