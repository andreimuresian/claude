"""usage: run_point.py GAP_um SLAB_W_um -> one RESULT json line (Istanbul + 200 nm buffer)"""
import json, re, sys, time
G, W = (float(a) for a in sys.argv[1:3])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_buffer.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
src = re.sub(r"\nGAP = [0-9.]+", f"\nGAP = {G}", src); src = re.sub(r"\nSLAB_W = [0-9.]+", f"\nSLAB_W = {W}", src)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(gap=G, slab_w=W, tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real),
      im_neff=float(g["n_eff"].imag), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      t_s=round(time.time() - t0, 1))), flush=True)
