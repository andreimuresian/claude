import json, sys, re
src="import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\nplt.show=lambda *a,**k: plt.close('all')\n"+"\n".join("".join(c["source"]) for c in json.load(open("/home/user/claude/VPI_Madrid.ipynb"))["cells"])
src=src.replace("USE_ALD = True","USE_ALD = "+sys.argv[1],1); src=re.sub(r"\nMESH_SCALE = [0-9.]+","\nMESH_SCALE = 1.4",src,1)
g={}; exec(compile(src,"nb","exec"),g); print("CHECK",sys.argv[1],g["GAP"],g["T_ALD"],g["BUFFER_H"],round(g["att_opt_dB_cm"],4),round(g["Vpi_L_Vcm"],4))
