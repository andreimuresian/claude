"""Run one Madrid-1 point and save DC potential/Ex and the optical mode intensity on the mesh.  usage: TRW=.. python3 dump_field.py OUT GAP BUF CAP_W CAP_H MTXs"""
import json, os, re, sys, numpy as np
OUT = sys.argv[1]; G, B, CW, CH, MS_ = map(float, sys.argv[2:7])
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
pre = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src = "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("wl", 1.625), ("T_ALD", 0.0), ("MESH_SCALE", 1.4)):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1
src = re.sub(r"\nUSE_ALD = \w+", "\nUSE_ALD = True", src, count=1)
src = re.sub(r"\nnum_modes_search = \d+", "\nnum_modes_search = 16", src, count=1); src = re.sub(r"\nn_guess = [0-9.]+", "\nn_guess = 1.895", src, count=1)
src = src.replace('if d["te_ratio"] >= 0.75 and d["core_conf"] >= 0.20 and d["unipolarity"] >= 0.85', 'if d["te_ratio"] >= 0.75 and d["core_conf"] >= 0.20 and d["unipolarity"] >= 0.85 and abs(d["neff"].real - n_guess) < 0.03')
par = f"M1_GAP={G}; M1_BUF={B}; M1_CW={CW}; M1_CH={CH}; MTX_SMALL={MS_}; MTX_BIG=10.0; W_S=10.0; W_T=10.0; W_G=10.0\n"
mark = "\npolygons, Y_TOP = build_polygons()"
src = src.replace("\nresolutions = {}", "\n_base_res.setdefault(\"trn\", (0.035, 0.30))\nresolutions = {}", 1)
src = src.replace(mark, "\n" + par + open("/home/user/claude/results/madrid/m1/m1_geom.py").read() + mark)
g = {}; exec(compile(pre + src, "nb", "exec"), g)
m = g["skfem_mesh"]; p = m.p; t = m.t
cent = p[:, t].mean(axis=1)
mode = g["fund_mode"]; Ex_opt = mode.basis.interpolate(mode.E)[0][0]   # (2, nel, nq): x,y components at quad points
I_opt = np.mean(np.abs(Ex_opt) ** 2, axis=-1)
np.savez_compressed(OUT, p=p, t=t, cent=cent, pot=g["potential_nodes"], Ex=g["Ex_dc"], Iopt=I_opt, mat=np.array(g["mat_of_el"], dtype=str),
                    VpiL=g["Vpi_L_Vcm"], IL=g["att_opt_dB_cm"], gamma=abs(g["overlap"]), gap=G)
print("saved", OUT, g["Vpi_L_Vcm"], g["att_opt_dB_cm"])
