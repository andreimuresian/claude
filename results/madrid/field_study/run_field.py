"""usage: run_field.py TAG GAP BUFFER T_ALD MTX MTX_GND  -> TAG.npz (per-element field / absorption data)"""
import json, re, sys, time, numpy as np
tag = sys.argv[1]; G, B, T, M, MG = (float(a) for a in sys.argv[2:7])
nb = json.load(open("/home/user/claude/VPI_Madrid.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"][:5])
for k, v in (("GAP", G), ("BUFFER_H", B), ("T_ALD", T), ("MTX", M), ("MESH_SCALE", 1.4), ("MTX_GND", MG)):
    src, n = re.subn(rf"\n{k} = (?:[0-9.]+|None)", f"\n{k} = {v}", src, count=1); assert n == 1, k
g = {}; exec(compile(src, "nb", "exec"), g)
m = g["fund_mode"]; bas = m.basis
Et, Ez = bas.interpolate(m.E)
E2 = np.abs(Et.value[0])**2 + np.abs(Et.value[1])**2 + np.abs(Ez.value)**2      # (nel, nqp)
dx = bas.dx
E2int = (E2 * dx).sum(1); area = dx.sum(1)
mesh = g["skfem_mesh"]; cen = mesh.p[:, mesh.t].mean(1)
eps = np.array([g["MATERIALS"][mm]["eps_opt"][0] for mm in g["mat_of_el"]], dtype=complex)
np.savez_compressed(f"{tag}.npz", cx=cen[0], cy=cen[1], area=area, E2int=E2int, mat=np.array(g["mat_of_el"], dtype=str),
    imeps=np.abs(eps.imag), p=mesh.p, t=mesh.t, neff=complex(g["n_eff"]), IL=float(g["att_opt_dB_cm"]), VpiL=float(g["Vpi_L_Vcm"]),
    k0=float(g["k0"]), gap=G, buf=B, ald=T, mtx=M, mtxg=MG, slab_h=float(g["SLAB_H"]), cap_w=float(g["CAP_W"]), cap_h=float(g["CAP_H"]))
print("DONE", tag, g["att_opt_dB_cm"], g["Vpi_L_Vcm"])
