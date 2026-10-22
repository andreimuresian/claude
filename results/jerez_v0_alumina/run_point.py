"""Run notebook cells 0-4 for one design point.  usage: run_point.py T_ALD_um MESH_SCALE ALD_CELLS [N_ALD]"""
import json, re, sys, time
T, MS, AC = (float(a) for a in sys.argv[1:4])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_JerezV0_alumina.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
for c in nb["cells"][:5]:
    src += "".join(c["source"]) + "\n"
src = re.sub(r"\nT_ALD = [0-9.]+", f"\nT_ALD = {T}", src)
src = re.sub(r"\nMESH_SCALE = [0-9.]+", f"\nMESH_SCALE = {MS}", src)
src = re.sub(r"\nALD_CELLS = [0-9.]+", f"\nALD_CELLS = {AC}", src)
if len(sys.argv) > 4:
    src = re.sub(r"\nN_ALD = [0-9.]+", f"\nN_ALD = {float(sys.argv[4])}", src)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(T_nm=T * 1e3, mesh_scale=MS, ald_cells=AC, n_ald=g["N_ALD"],
      tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real), im_neff=float(g["n_eff"].imag),
      IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), Gamma=float(abs(g["overlap"])),
      t_s=round(time.time() - t0, 1))), flush=True)
