"""usage: run_point.py OE_um BUFFER_L_um   env: SKIN, CORNER, ALL (mesh scale factors)"""
import json, os, re, sys, time
OE, L = float(sys.argv[1]), float(sys.argv[2])
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_buffer_overetch.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("OE", OE), ("BUFFER_L", L)):
    src, n = re.subn(rf"\n{k} = [^\s#]+", f"\n{k} = {v}", src, count=1); assert n == 1, k
f = {k: float(os.environ.get(k, "1")) for k in ("SKIN", "CORNER", "ALL")}
src, n1 = re.subn(r"\nh_skin = ([0-9.]+)", lambda m: f"\nh_skin = {m.group(1)} * {f['SKIN']}", src)
src, n2 = re.subn(r"\nh_corner = ([0-9.]+)", lambda m: f"\nh_corner = {m.group(1)} * {f['CORNER']}", src)
assert n1 == 1 and n2 == 1, (n1, n2)
if f["ALL"] != 1:
    src = src.replace("raw_mesh = mesh_from_OrderedDict(",
        "resolutions = {k: {'resolution': v['resolution'] * (1.0 if (k.endswith('_corner') or 'skin' in k) else %r), 'distance': v['distance']} for k, v in resolutions.items()}\nraw_mesh = mesh_from_OrderedDict(" % f["ALL"], 1)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(oe=OE, L=L, **{k.lower(): v for k, v in f.items()}, tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), im_neff=float(g["n_eff"].imag), IL_dBcm=float(g["att_opt_dB_cm"]),
      VpiL_Vcm=float(g["Vpi_L_Vcm"]), t_s=round(time.time() - t0, 1))), flush=True)
