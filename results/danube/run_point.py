"""usage: run_point.py TEE(0/1) OE_um SLAB_W_um [WL_um]   env: SKIN, CORNER, CORE, ALL (mesh scale factors)"""
import json, os, re, sys, time
TEE, OE, W = bool(int(sys.argv[1])), float(sys.argv[2]), float(sys.argv[3])
WL = float(sys.argv[4]) if len(sys.argv) > 4 else 1.310
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Danube.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("TEE", TEE), ("OE", OE), ("SLAB_W", W), ("wl", WL)):
    src, n = re.subn(rf"\n{k} = [^\s#]+", f"\n{k} = {v}", src, count=1); assert n == 1, k
f = {k: float(os.environ.get(k, "1")) for k in ("SKIN", "CORNER", "CORE", "ALL")}
src = src.replace("\nh_skin = 0.006", f"\nh_skin = 0.006 * {f['SKIN']}").replace("\nh_corner = 0.006", f"\nh_corner = 0.006 * {f['CORNER']}")
if f["CORE"] != 1 or f["ALL"] != 1:
    src = src.replace("raw_mesh = mesh_from_OrderedDict(",
        "resolutions = {k: {'resolution': v['resolution'] * (%r if (k.endswith('_corner') or 'skin' in k) else %r * (%r if k.split('_')[0] in ('core', 'slab', 'cap', 'clad', 'box') and not k.endswith('far') else 1.0)), 'distance': v['distance']} for k, v in resolutions.items()}\nraw_mesh = mesh_from_OrderedDict(" % (f["ALL"], f["ALL"], f["CORE"]), 1)
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(tee=int(TEE), oe=OE, slab_w=W, wl=WL, **{k.lower(): v for k, v in f.items()},
      tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real), im_neff=float(g["n_eff"].imag),
      IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), mode=int(g["chosen_idx"]),
      t_s=round(time.time() - t0, 1))), flush=True)
