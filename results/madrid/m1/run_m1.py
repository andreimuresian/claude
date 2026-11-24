"""usage: run_m1.py GAP BUF CAP_W CAP_H MTX_SMALL [W_S] [fig]   (Madrid 1, 1625 nm, no ALD)"""
import json, os, re, sys, time
a = sys.argv[1:]
G, B, CW, CH, MS_ = (float(x) for x in a[:5]); WS = float(a[5]) if len(a) > 5 else 10.0; FIG = a[6] if len(a) > 6 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("wl", float(os.environ.get("WL", "1.625"))), ("T_ALD", 0.0), ("MESH_SCALE", float(os.environ.get("MS", "1.4")))):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
src, n = re.subn(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1); assert n == 1
src, n = re.subn(r"\nnum_modes_search = \d+", "\nnum_modes_search = %d" % int(os.environ.get("NMODES", "16")), src, count=1); assert n == 1
src, n = re.subn(r"\nn_guess = [0-9.]+", "\nn_guess = %s" % os.environ.get("NGUESS", "1.895"), src, count=1); assert n == 1
par = f"M1_GAP={G}; M1_BUF={B}; M1_CW={CW}; M1_CH={CH}; MTX_SMALL={MS_}; MTX_BIG=10.0; W_S={WS}; W_T=10.0; W_G=10.0\n"
mark = "\npolygons, Y_TOP = build_polygons()"; assert src.count(mark) == 1
src = src.replace(mark, "\n" + par + open("/home/user/claude/results/madrid/m1/m1_geom.py").read() + mark)
_NWIN = float(os.environ.get("NWIN", "0.03"))   # reject spurious rib-corner modes: keep candidates near the expected rib index
src = src.replace('if d["te_ratio"] >= 0.75 and d["core_conf"] >= 0.20 and d["unipolarity"] >= 0.85',
                  'if d["te_ratio"] >= 0.75 and d["core_conf"] >= 0.20 and d["unipolarity"] >= 0.85 and abs(d["neff"].real - n_guess) < %g' % _NWIN)
assert "abs(d[\"neff\"].real - n_guess)" in src
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(wl=float(os.environ.get("WL", "1.625")), gap=G, buf=B, cap_w=CW, cap_h=CH, mtx_small=MS_, w_s=WS, tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))), flush=True)
