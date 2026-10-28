"""usage: run_point.py WG_TOP CAP_H CAP_W"""
import json, re, sys, time
W, Hc, Wc = (float(a) for a in sys.argv[1:4])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Lisbona_lifted_buffer_cap_sweep.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("WG_TOP", W), ("CAP_H", Hc), ("CAP_W", Wc)):
    src, n = re.subn(rf"\n{k} = [0-9.]+", f"\n{k} = {v}", src, count=1); assert n == 1, k
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(wg_top=W, cap_h=Hc, cap_w=Wc, tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real),
      IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), t_s=round(time.time() - t0, 1))), flush=True)
