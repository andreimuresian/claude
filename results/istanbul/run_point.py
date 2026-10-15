"""usage: run_point.py SLAB_W_um [WL_um]  -> one RESULT json line"""
import json, re, sys, time
W = float(sys.argv[1]); WL = float(sys.argv[2]) if len(sys.argv) > 2 else 1.575
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
src = re.sub(r"\nwl = [0-9.]+", f"\nwl = {WL}", src)
src = re.sub(r"\nSLAB_W = [0-9.]+", f"\nSLAB_W = {W}", src)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(slab_w=W, wl=WL, tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real),
      im_neff=float(g["n_eff"].imag), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      Gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
