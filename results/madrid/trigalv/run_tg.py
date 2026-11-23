"""usage: run_tg.py G_AL BUFFER TOX P [fig]   (Madrid tri-galvanic, 1625 nm, no ALD, MESH_SCALE 1.4)"""
import json, os, re, sys, time
G, B, TX, P = (float(a) for a in sys.argv[1:5]); FIG = sys.argv[5] if len(sys.argv) > 5 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("wl", 1.625), ("T_ALD", 0.0), ("MESH_SCALE", float(os.environ.get("MS", "1.4")))):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
src, n = re.subn(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1); assert n == 1
par = f"G_AL={G}; TG_B={B}; TOX_H={TX}; TG_P={P}; AL_H=0.4; CAPH_TG=0.6; AU1_H=2.0; AU2_H=10.0; AU2_W=10.0; EL_W=30.0; SKIN_A=0.05\n"
mark = "\npolygons, Y_TOP = build_polygons()"; assert src.count(mark) == 1
src = src.replace(mark, "\n" + par + open("/home/user/claude/results/madrid/trigalv/tg_geom.py").read() + mark)
src, n = re.subn(r"\nresolutions = \{\}", "\n_base_res.update(_TG_RES)\nresolutions = {}", src, count=1); assert n == 1
src, n = re.subn(r'np\.where\(mat_of_el == "Au_sig"\)', 'np.where(np.isin(mat_of_el, ["Au_sig","Al_sig"]))', src); assert n == 1
src, n = re.subn(r'np\.where\(mat_of_el == "Au_gnd"\)', 'np.where(np.isin(mat_of_el, ["Au_gnd","Al_gnd"]))', src); assert n == 1
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
import numpy as np
res = dict(g_al=G, buf=B, tox=TX, p=P, au1_gap=G + 2 * P, tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real),
           IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))
try:
    from skfem import Functional
    m = g["fund_mode"]; E = m.basis.interpolate(m.E); mat = g["mat_of_el"]; bp0 = g["basis_p0"]
    @Functional(dtype=complex)
    def _w(w): return w["msk"] * (abs(w["E"][0][0]) ** 2 + abs(w["E"][0][1]) ** 2 + abs(w["E"][1]) ** 2)
    tot = {}
    for key, mats in (("Al", ["Al_sig", "Al_gnd"]), ("Au", ["Au_sig", "Au_gnd"])):
        im = abs(np.imag(g["MATERIALS"][mats[0]]["eps_opt"][0]))
        tot[key] = im * float(np.real(_w.assemble(m.basis, E=E, msk=bp0.interpolate(np.isin(mat, mats).astype(float)))))
    res["frac_Al"] = round(tot["Al"] / sum(tot.values()), 4)
except Exception as e:
    res["frac_err"] = str(e)[:80]
print("RESULT " + json.dumps(res), flush=True)
