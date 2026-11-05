"""usage: run_point.py GAP BUFFER_um T_ALD_um MTX [MESH_SCALE] [savefig_prefix]"""
import json, re, sys, time, os
G, B, T, M = (float(a) for a in sys.argv[1:5])
MS = float(sys.argv[5]) if len(sys.argv) > 5 else 1.0
FIG = sys.argv[6] if len(sys.argv) > 6 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("GAP", G), ("BUFFER_H", B), ("T_ALD", T), ("MTX", M), ("MESH_SCALE", MS)):
    src, n = re.subn(rf"\n{k} = [0-9.]+", f"\n{k} = {v}", src, count=1); assert n == 1, k
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(gap=G, buf=B, ald=T, mtx=M, ms=MS, tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
