"""Madrid B (no ALD, gap 3.2, buffer 120 nm, cap 3.0 x 0.5, gold 2.0 um), top cladding air or SiO2.
usage: CLAD=air|SiO2 python3 run_B.py [fig]"""
import json, os, re, sys, time
FIG = sys.argv[1] if len(sys.argv) > 1 else None
CL = os.environ.get("CLAD", "air")
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
src, n = re.subn(r"\nUSE_ALD = \w+", "\nUSE_ALD = False", src, count=1); assert n == 1
BUF = os.environ.get("BUF")
if BUF:
    src, n = re.subn(r"\nBUFFER_H = [0-9.]+", f"\nBUFFER_H = {float(BUF)}", src, count=1); assert n == 1
if CL == "SiO2":
    src, n = re.subn(r"\(\"clad\", \"air\"\)", "(\"clad\", \"SiO2\")", src); assert n == 1
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(clad=CL, gap=g["GAP"], buf=g["BUFFER_H"], cap_w=g["CAP_W"], mtx=g["MTX"], ald=g["T_ALD"], ms=g["MESH_SCALE"],
      tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]),
      VpiL_Vcm=float(g["Vpi_L_Vcm"]), gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
