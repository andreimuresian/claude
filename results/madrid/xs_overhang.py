import json, re, sys, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as P
from shapely.ops import unary_union
def geom(ald):
    s="".join(json.load(open("/home/user/claude/VPI_Madrid.ipynb"))["cells"][0]["source"])
    s=s[:s.index("polygons, Y_TOP = build_polygons()")]
    for k,v in (("GAP",3.5),("BUFFER_H",0.12),("T_ALD",ald),("MTX",10.0)):
        s=re.sub(rf"\n{k} = [0-9.]+",f"\n{k} = {v}",s,1)
    s=s.replace('GND_STYLE = "flat"','GND_STYLE = "overhang"')
    g={}; exec(s,g); polys,_=g["build_polygons"](); M={}
    for n,p in polys.items(): M.setdefault(g["material_of"](n),[]).append(p)
    return {k:unary_union(v) for k,v in M.items()}, g
COL={"LN":"#8b95a1","SiO2":"#a9cdf2","Al2O3":"#e0218a","air":"#ffffff","Au_sig":"#f2c14e","Au_gnd":"#e5a92e"}
def draw(a,M,xl,yl):
    for m,shp in M.items():
        for p in getattr(shp,"geoms",[shp]):
            if p.geom_type!="Polygon": continue
            a.add_patch(P(np.asarray(p.exterior.coords),fc=COL[m],ec="k" if m!="air" else "none",lw=.4))
            for h in p.interiors: a.add_patch(P(np.asarray(h.coords),fc="white",ec="k",lw=.4))
    a.set_xlim(*xl); a.set_ylim(*yl); a.set_aspect("equal"); a.set_xlabel("x (µm)"); a.set_ylabel("y (µm)")
def dim(a,x0,x1,y,t,vert=False,fs=8.5):
    if vert:
        a.annotate("",(y,x0),(y,x1),arrowprops=dict(arrowstyle="<->",lw=.8,shrinkA=0,shrinkB=0)); a.text(y+0.04,(x0+x1)/2,t,va="center",fontsize=fs,zorder=10,bbox=dict(fc="white",ec="none",alpha=.8,pad=.5))
    else:
        a.annotate("",(x0,y),(x1,y),arrowprops=dict(arrowstyle="<->",lw=.8,shrinkA=0,shrinkB=0)); a.text((x0+x1)/2,y+0.04,t,ha="center",va="bottom",fontsize=fs,zorder=10,bbox=dict(fc="white",ec="none",alpha=.8,pad=.5))
fig,ax=plt.subplots(2,2,figsize=(16,10.5),gridspec_kw=dict(width_ratios=[1.5,1]))
for row,ald in enumerate((0.0,0.04)):
    M,g=geom(ald); yb=g["SLAB_H"]+g["BUFFER_H"]; ct=yb+g["CAP_H"]; xg=g["GAP"]/2; xoh=g["OH_GAP"]-xg
    a=ax[row,0]; draw(a,M,(-6.5,3.0),(-0.4,2.4))
    dim(a,-xoh,xg,1.95,"3.0 µm (overhang → signal)"); dim(a,-xg,xg,ct+0.62+0.25,"gap 3.5 µm (cap 3.3 µm + 0.1 µm slot on the signal side)",fs=8)
    dim(a,-xoh-2.5,-xoh,ct+0.55,"overhang 2.5 µm")
    dim(a,ct,ct+0.5,-xoh-2.5-0.35,"0.5 µm",vert=True); dim(a,yb,ct,-5.9,"ground\n0.5 µm\n(= cap)",vert=True)
    dim(a,-1.65,-1.25,ct-0.18,"0.4 µm",fs=7.5)
    a.text(2.0,1.5,"signal\n10 µm tall\n(continues ↑)",fontsize=9,ha="center")
    a.text(-4.5,yb+0.2,"ground (Au)",fontsize=9); a.text(-0.45,yb+0.28,"cap 0.5",fontsize=8)
    a.text(-6.4,yb-0.08,"buffer SiO₂ 120 nm",fontsize=8,va="top"); a.text(-6.4,0.05,"LN slab 275 nm",fontsize=8)
    a.set_title(f"Madrid overhang ground — {'ALD 40 nm' if ald else 'no ALD'} (true 1:1)")
    b=ax[row,1]; draw(b,M,(-2.0,-0.9),(0.2,1.2)); b.set_title("Zoom: ground / cap / overhang"+(" (ALD pink)" if ald else ""))
    b.text(-1.95,0.33,"buffer",fontsize=8); b.text(-1.95,0.22,"LN slab",fontsize=8); b.text(-1.2,0.6,"cap",fontsize=8); b.text(-1.9,0.6,"Au",fontsize=9); b.text(-1.6,0.95,"Au overhang",fontsize=8)
import matplotlib.patches as mp
fig.legend(handles=[mp.Patch(color=COL[k],label=l) for k,l in [("Au_sig","Au signal"),("Au_gnd","Au ground"),("LN","LN"),("SiO2","SiO₂"),("Al2O3","ALD Al₂O₃ 40 nm")]],loc="lower center",ncol=5)
fig.suptitle("Madrid gap 3.5 µm, ground on the cap + 2.5×0.5 µm overhang (3.0 µm to the signal) — geometry as it will be simulated at 1625 nm",fontsize=12)
fig.tight_layout(rect=(0,0.04,1,0.97)); fig.savefig("madrid_overhang_xs.png",dpi=160)
