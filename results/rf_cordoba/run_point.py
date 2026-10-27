"""usage: run_point.py BUFFER_H_um T_ALD_um [TAN_ALD]   env: LAT_PAD, AIR_H, MESH_FACTOR, CELLS (default 0,1,2,3,4,6)"""
import json, os, re, sys, time
B, T = float(sys.argv[1]), float(sys.argv[2]); TAN = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0
nb = json.load(open(os.environ.get("NB", "/home/user/claude/VPI_RF_Cordoba_buffer_ALD.ipynb")))
cells = [int(c) for c in os.environ.get("CELLS", "0,1,2,3,4,5").split(",")]
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(nb["cells"][i]["source"]) for i in cells)
over = {"BUFFER_H": B, "T_ALD": T, "TAN_ALD": TAN}
for k, e in (("lat_pad", "LAT_PAD"), ("air_h", "AIR_H"), ("MESH_FACTOR", "MESH_FACTOR")):
    if os.environ.get(e): over[k] = float(os.environ[e])
for k, v in over.items():
    src, n = re.subn(rf"\n{k}( *)= [^\s#]+", rf"\n{k}\g<1>= {v}", src, count=1); assert n == 1, k
t0 = time.time(); g = {}
exec(compile(src, "nb", "exec"), g)
r = dict(buffer_nm=B * 1e3, ald_nm=T * 1e3, tan_ald=TAN, lat_pad=g["lat_pad"], air_h=g["air_h"], mesh_factor=g["MESH_FACTOR"],
         tri=int(g["mesh"].nelements), t_s=round(time.time() - t0, 1))
if 5 in cells:
    r.update(n_m=float(g["n_m_c"]), Z0=float(g["Z0_c"]), Z0_volt=float(g["Z_VP_c"]), alpha_dBcm=float(g["alpha_db_cm_c"]),
             alpha_d_dBcm=float(g["DB_PER_NEPER"] * g["alpha_d"] / 100), n_m_pec=float(g["n_m_pec"]), Z0_pec=float(g["Z0_pec"]),
             score=float(g["fundamental"]["score"]), div=float(g["fundamental"]["div"]), R_mqs=float(g["R_mqs"]),
             n_m_qs=float(g["n_m_qs"]), Z0_qs=float(g["Z0_qs"]))
print("RESULT " + json.dumps(r), flush=True)
