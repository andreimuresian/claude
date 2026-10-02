import sys, json, io, contextlib, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.show = lambda *a, **k: plt.close("all")
import matplotlib.tri as mtri
reps = json.loads(sys.argv[1]); tag = sys.argv[2]
src0 = open("/home/user/claude/cells/cell0_etched.py").read()
for a, b in reps.items():
    assert a in src0, a; src0 = src0.replace(a, b)
g = {"__name__": "__main__"}
for name, src in [("c0", src0)] + [(f"c{i}", open(f"ox_c{i}.py").read()) for i in (1, 2, 3, 4)]:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(src, name, "exec"), g)
m = g["fund_mode"]; mesh = g["skfem_mesh"]
Ei = m.basis.interpolate(m.E)
val = lambda f: np.asarray(f.value if hasattr(f, "value") else f)
Et, Ez = val(Ei[0]), val(Ei[1])
I_el = np.mean(np.abs(Et[0])**2, -1) + np.mean(np.abs(Et[1])**2, -1) + np.mean(np.abs(Ez)**2, -1)
In = np.zeros(mesh.p.shape[1]); c = np.zeros_like(In)
for i in range(3):
    np.add.at(In, mesh.t[i], I_el); np.add.at(c, mesh.t[i], 1)
In /= np.maximum(c, 1)
tri = mtri.Triangulation(mesh.p[0], mesh.p[1], mesh.t.T)
f = mtri.LinearTriInterpolator(tri, In / In.max())
x = np.linspace(0, 14, 2801)
out = {"x": x, "IL": g["att_opt_dB_cm"], "VpiL": g["Vpi_L_Vcm"], "slab_w": g["SLAB_W"], "x_lift": g["X_LIFT"]}
for yy, k in [(g["SLAB_H"] * 0.5, "mid"), (-0.05, "box")]:
    out[k] = np.asarray(f(x, np.full_like(x, yy)).filled(np.nan))
np.savez(f"fcut_{tag}.npz", **out)
print(tag, out["IL"], out["VpiL"])
