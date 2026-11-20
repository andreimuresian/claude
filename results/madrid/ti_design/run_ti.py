"""usage: run_ti.py G_TI TI_H TI_P [fig]   (Madrid-Ti, 1625 nm, no ALD)"""
import json, re, sys, time
G, TH, P = (float(a) for a in sys.argv[1:4]); FIG = sys.argv[4] if len(sys.argv) > 4 else None
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n"
pre += ("_figc=[0]\ndef _show(*a,**k):\n    _figc[0]+=1; plt.savefig(%r+f'_{_figc[0]}.png',dpi=110); plt.close('all')\nplt.show=_show\n" % FIG) if FIG else "plt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("wl", 1.625), ("BUFFER_H", 0.12), ("T_ALD", 0.0), ("MESH_SCALE", 1.4)):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
src, n = re.subn(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1); assert n == 1
par = f"G_TI={G}; TI_H={TH}; TI_P={P}; PAD_W=2.0; PAD_H=0.5; TI_X=0.5; SP_W=1.0; BR_H=0.3; OUT_W=30.0; TALL_H=10.0\n"
geo = open("/home/user/claude/results/madrid/ti_design/ti_geom.py").read()
mark = "\npolygons, Y_TOP = build_polygons()"
assert src.count(mark) == 1
src = src.replace(mark, "\n" + par + geo + mark)
src, n = re.subn(r"\nresolutions = \{\}", "\n_base_res.update(_TI_RES)\nresolutions = {}", src, count=1); assert n == 1
src, n = re.subn(r'np\.where\(mat_of_el == "Au_sig"\)', 'np.where(np.isin(mat_of_el, ["Au_sig","Ti_sig"]))', src); assert n == 1
src, n = re.subn(r'np\.where\(mat_of_el == "Au_gnd"\)', 'np.where(np.isin(mat_of_el, ["Au_gnd","Ti_gnd"]))', src); assert n == 1
t0 = time.time(); g = {}
exec(compile(pre + src, "nb", "exec"), g)
import numpy as np
# loss split: integral |Im eps| |E|^2 per material (relative)
res = dict(gti=G, ti_h=TH, ti_p=P, au_gap=G + 2 * P, tri=int(g["skfem_mesh"].nelements), neff=float(g["n_eff"].real),
           IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]), gamma=float(abs(g["overlap"])), t_s=round(time.time() - t0, 1))
try:
    from skfem import Functional
    m = g["fund_mode"]; E = m.basis.interpolate(m.E); mat = g["mat_of_el"]; bp0 = g["basis_p0"]
    @Functional(dtype=complex)
    def _w(w): return w["msk"] * (abs(w["E"][0][0]) ** 2 + abs(w["E"][0][1]) ** 2)
    tot = {}
    for key, mats in (("Ti", ["Ti_sig", "Ti_gnd"]), ("Au", ["Au_sig", "Au_gnd"])):
        im = abs(np.imag(g["MATERIALS"][mats[0]]["eps_opt"][0]))
        tot[key] = im * float(np.real(_w.assemble(m.basis, E=E, msk=bp0.interpolate(np.isin(mat, mats).astype(float)))))
    s = sum(tot.values()); res["frac_Ti"] = round(tot["Ti"] / s, 4)
except Exception as e:
    res["frac_err"] = str(e)[:80]
print("RESULT " + json.dumps(res), flush=True)
