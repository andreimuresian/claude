"""usage: run_point.py cordoba|jerez T_ALD_um sellmeier|scaled -> RESULT json line with ng"""
import json, re, sys, time
D, T, M = sys.argv[1], float(sys.argv[2]), sys.argv[3]
nb = json.load(open({"cordoba_buf": "/home/user/claude/VPI_group_index_Cordoba_buffer_ALD.ipynb", "cordoba": "/home/user/claude/VPI_group_index_Cordoba_ALD.ipynb", "jerez": "/home/user/claude/VPI_group_index_JerezV0_ALD.ipynb"}[D]))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"
src += "\n".join("".join(c["source"]) for c in nb["cells"])
src, n1 = re.subn(r"\nT_ALD = [0-9.]+", f"\nT_ALD = {T}", src, count=1)
src, n2 = re.subn(r'\nALD_MODEL = "\w+"', f'\nALD_MODEL = "{M}"', src, count=1); assert n1 == n2 == 1
import os
LIGHT = os.environ.get("LIGHT") == "1"
if LIGHT:   # light mesh for ng: coarser gold skin, 2 elements across the alumina, 3 um fine-skin band
    src, k1 = re.subn(r"\nh_skin = ([0-9.]+)", lambda m: "\nh_skin = %r" % (2.5 * float(m.group(1))), src, count=1)
    src, k2 = re.subn(r"\nALD_CELLS = [0-9.]+", "\nALD_CELLS = 2.0", src, count=1)
    src, k3 = re.subn(r"\nSKIN_NEAR = [0-9.]+", "\nSKIN_NEAR = 3.0", src, count=1)
    # unetched slab: the 25 nm "fine" slab mesh spanned the whole 66 um slab; keep it to |x| < 8 um, 50 nm beyond
    src, k4 = re.subn(r"x_fine = max\(X_FINE_MIN, min\(xs, x_out\) \+ 1\.0\)", "x_fine = X_FINE_MIN", src, count=1)
    src, k5 = re.subn(r'"slab_mid":    \(0\.110, 0\.40\)', '"slab_mid":    (0.050, 0.40)', src, count=1)
    assert k1 == k2 == k3 == k4 == k5 == 1
if os.environ.get("WG_TOP"):   # rib top width override (+ matching n_guess)
    src, k6 = re.subn(r"\nWG_TOP = [0-9.]+", "\nWG_TOP = " + os.environ["WG_TOP"], src, count=1)
    src, k7 = re.subn(r"\nn_guess = [0-9.]+", "\nn_guess = " + os.environ.get("N_GUESS", "1.88"), src, count=1)
    assert k6 == k7 == 1
t0 = time.time(); g = {}
src = re.sub(r"\nnum_modes_search = \d+", "\nnum_modes_search = 6", src, count=1)
try:
    exec(compile(src, "nb", "exec"), g)
except RuntimeError:                     # TE mode not among the 6 nearest: fall back to the 20-mode search
    src = src.replace("\nnum_modes_search = 6", "\nnum_modes_search = 20", 1); g = {}
    exec(compile(src, "nb", "exec"), g)
print("RESULT " + json.dumps(dict(design=D, wg_top=float(g["WG_TOP"]), light=LIGHT, modes=int(g["num_modes_search"]), T_nm=round(T * 1e3), model=M, n_ald=float(g["n_ALD"](g["wl"])), tri=int(g["skfem_mesh"].nelements),
      neff=float(g["n_eff"].real), IL_dBcm=float(g["att_opt_dB_cm"]), VpiL_Vcm=float(g["Vpi_L_Vcm"]),
      neffs={f"{(g['wl'] + k) * 1e3:.1f}": [float(v[0].real), float(v[1])] for k, v in g["ng_rows"].items()},
      ng_1nm=float(g["ng_results"][0.001]), ng_2nm=float(g["ng_results"][0.002]), t_s=round(time.time() - t0, 1))), flush=True)
