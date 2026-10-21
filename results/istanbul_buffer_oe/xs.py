import json
nb = json.load(open("/home/user/claude/VPI_interface_optimized_Istanbul_buffer_overetch.ipynb"))
src = "import matplotlib; matplotlib.use('Agg')\nimport matplotlib.pyplot as plt\n_PC=[0]\ndef _s(*a,**k):\n    _PC[0]+=1; plt.savefig(f'cross_section_{_PC[0]}.png',dpi=110); plt.close('all')\nplt.show=_s\n"
src += "".join(nb["cells"][0]["source"])
exec(compile(src, "nb", "exec"), {})
