"""Run notebook cells 0-4 for one point.  usage: run_point.py T_ALD_um GAP_BOT_um"""
import json, re, sys, time
T, G = (float(a) for a in sys.argv[1:3])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Lisbona_lifted_buffer_alumina.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
for c in nb["cells"][:5]:
    src += "".join(c["source"]) + "\n"
src = re.sub(r"\nT_ALD = [0-9.]+", f"\nT_ALD = {T}", src)
src = re.sub(r"\nGAP_BOT = [0-9.]+", f"\nGAP_BOT = {G}", src)
import os
MS = float(os.environ.get("MESH_SCALE", "1"))
if os.environ.get("ALD_CELLS"):
    src = re.sub(r"\nALD_CELLS = [0-9.]+", "\nALD_CELLS = " + os.environ["ALD_CELLS"], src)
if MS != 1.0:
    src = src.replace("raw_mesh = mesh_from_OrderedDict(", "resolutions = {k: {'resolution': v['resolution'] * %r, 'distance': v['distance']} for k, v in resolutions.items()}\nraw_mesh = mesh_from_OrderedDict(" % MS, 1)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(T_nm=round(T * 1e3, 3), gap=G, mesh_scale=MS, ald_cells=g["ALD_CELLS"], tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), im_neff=float(g["n_eff"].imag), IL_dBcm=float(g["att_opt_dB_cm"]),
      VpiL_Vcm=float(g["Vpi_L_Vcm"]), Gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
