"""MTX tall - Chinese: etched slab (SLAB_W), no buffer, no ALD, gap 4.0, WG_W 1.5, cap 2.5 x 1.4, signal 10 um, ground 0.5 um.
usage: run_cn.py WL SLAB_W [MS] [fig]"""
import json, re, sys, time, os
WL = float(sys.argv[1]); SW = float(sys.argv[2]); MS = float(sys.argv[3]) if len(sys.argv) > 3 else 1.4; FIG = sys.argv[4] if len(sys.argv) > 4 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
ng = 1.897 + 0.22 * (1.625 - WL)
for k, v in (("wl", WL), ("GAP", 4.0), ("BUFFER_H", 0.0), ("T_ALD", 0.0), ("MTX", 10.0), ("MESH_SCALE", MS), ("MTX_GND", 0.5), ("WG_TOP", 1.5), ("CAP_H", 1.4), ("SLAB_W", SW)):
    src, n = re.subn(rf"\n{k} = (?:[0-9.e]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
src, n = re.subn(r"\nCAP_W = round\(GAP - 0\.2, 6\)", "\nCAP_W = 2.5", src, count=1); assert n == 1
src, n = re.subn(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1); assert n == 1
src, n = re.subn(r"\nn_guess = [0-9.]+", f"\nn_guess = {ng:.4f}", src, count=1); assert n == 1
# conformal gold over the etched slab: on the slab top where it overlaps the slab, on the BOX beyond; gold fills against the slab facet
o1 = "    el_r = box(xg, y_buf_top, x_out, y_el_top)\n"
assert src.count(o1) == 1
src = src.replace(o1, o1 + "    if xs < x_out:\n        el_r = Polygon(unary_union([el_r, box(max(xs, xg), 0.0, x_out, y_buf_top)]).exterior)\n")
o2 = "        el_l = mirror(box(xg, y_buf_top, x_out, y_gnd_top))   # ground (left)\n"
assert src.count(o2) == 1
src = src.replace(o2, "        _tg = (MTX if MTX_GND is None else MTX_GND)\n"
  "        _parts = ([box(xg, y_buf_top, xs, y_buf_top + _tg)] if xs > xg + 1e-9 else []) + [box(max(xs, xg), 0.0, x_out, _tg)]\n"
  "        el_l = mirror(Polygon(unary_union(_parts).exterior))   # ground (left), 0.5 um conformal: steps down off the slab\n")
o3 = "    pts = [(xg, y_buf_top), (x_out, y_buf_top)]     # gold / (buffer|LN) / air corners\n"
assert src.count(o3) == 1
src = src.replace(o3, "    pts = [(xg, y_buf_top), (x_out, 0.0)] + ([(xs, 0.0), (xs, y_slab_top)] if xs > xg + 0.05 else [(xg, 0.0)])\n")
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(wl=WL, slab_w=SW, ms=MS, gap=g["GAP"], buf=g["BUFFER_H"], cap_w=g["CAP_W"], cap_h=g["CAP_H"], wg=g["WG_TOP"],
      tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
