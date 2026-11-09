"""usage: run_sw.py WL_um GAP BUFFER T_ALD MTX_SIG MTX_GND [fig]  (cap = gap - 1.0 um, 0.5 um tall)"""
import json, re, sys, time
WL, G, B, T, M, MG = (float(a) for a in sys.argv[1:7]); FIG = sys.argv[7] if len(sys.argv) > 7 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("wl", WL), ("GAP", G), ("BUFFER_H", B), ("T_ALD", T), ("MTX", M), ("MESH_SCALE", 1.4), ("MTX_GND", MG)):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
src, n = re.subn(r"\nCAP_W = round\(GAP - 0\.2, 6\)", "\nCAP_W = round(GAP - 1.0, 6)", src, count=1); assert n == 1
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(wl=WL, gap=G, buf=B, ald=T, mtx=M, mtx_gnd=MG, cap_w=g["CAP_W"], tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
