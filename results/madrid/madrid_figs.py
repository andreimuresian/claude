import csv, numpy as np
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as P, Rectangle as R
C=dict(Au="#f2c14e",LN="#8b95a1",SiO2="#a9cdf2",ALD="#e0218a",air="white")
# ---------------- cross-section (true 1:1) ----------------
GAP,B,T,MTX,CW,CH,SL,WH,WT=3.5,0.12,0.04,2.0,3.3,0.5,0.275,0.275,1.4
WB=WT+2*WH/np.tan(np.radians(60)); yb=SL+B; ye=yb+MTX; xg=GAP/2
def draw(a,xl,yl,big=False):
    a.add_patch(R((-60,-4.7),120,4.7,fc=C["SiO2"],ec="k",lw=.4))
    a.add_patch(R((-60,0),120,SL,fc=C["LN"],ec="k",lw=.4))
    a.add_patch(R((-60,SL),120,B,fc=C["SiO2"],ec="k",lw=.4))
    a.add_patch(R((-CW/2,yb),CW,CH,fc=C["SiO2"],ec="k",lw=.4))
    a.add_patch(P([(-WB/2,SL),(-WT/2,SL+WH),(WT/2,SL+WH),(WB/2,SL)],fc=C["LN"],ec="k",lw=.4))
    for s in (-1,1):
        x0=xg if s>0 else -xg-30
        a.add_patch(R((x0,yb),30,MTX,fc=C["Au"],ec="k",lw=.4))
    from shapely.geometry import box as sb, Polygon as sP
    from shapely.ops import unary_union
    sol=unary_union([sb(-60,-4.7,60,yb),sb(-CW/2,yb,CW/2,yb+CH),sb(-xg-30,yb,-xg,ye),sb(xg,yb,xg+30,ye)])
    ald=sol.buffer(T,join_style=2,mitre_limit=10).difference(sol).intersection(sb(-60,-5,60,10))
    for p in [q for q in getattr(ald,"geoms",[ald]) if q.geom_type=="Polygon"]:
        a.add_patch(P(list(p.exterior.coords),fc=C["ALD"],ec="none",zorder=5))
        for h in p.interiors: a.add_patch(P(list(h.coords),fc="white",ec="none",zorder=5))
    a.set_xlim(*xl); a.set_ylim(*yl); a.set_aspect("equal"); a.set_xlabel("x (µm)"); a.set_ylabel("y (µm)")
def dim(a,x0,x1,y,t,vert=False,off=0.05,fs=9,col="k"):
    if vert:
        a.annotate("",(y,x0),(y,x1),arrowprops=dict(arrowstyle="<->",lw=.8,color=col,shrinkA=0,shrinkB=0))
        a.text(y+off,(x0+x1)/2,t,va="center",fontsize=fs,color=col)
    else:
        a.annotate("",(x0,y),(x1,y),arrowprops=dict(arrowstyle="<->",lw=.8,color=col,shrinkA=0,shrinkB=0))
        a.text((x0+x1)/2,y+off,t,ha="center",va="bottom",fontsize=fs,color=col)
fig=plt.figure(figsize=(16,10.5)); gs=fig.add_gridspec(2,2,height_ratios=[0.5,1.3])
a=fig.add_subplot(gs[0,:]); draw(a,(-40,40),(-4.7,4.2))
dim(a,-xg-30,-xg,ye+0.4,"ground 30 µm"); dim(a,xg,xg+30,ye+0.4,"signal 30 µm")
a.text(0,ye+0.45,"gap 3.5",ha="center",fontsize=9); a.text(-38,-2.5,"BOX SiO₂ 4.7 µm",fontsize=9)
a.set_title("MADRID — true 1:1 scale, full cross-section as simulated (λ = 1625 nm)")
b=fig.add_subplot(gs[1,0]); draw(b,(-2.6,2.6),(-0.5,2.9))
dim(b,-xg,xg,2.55,"gap 3.5 µm"); dim(b,-CW/2,CW/2,yb+CH+0.12,"cap 3.3 µm (gap − 0.2)",fs=8.5)
dim(b,yb,yb+CH,-1.55,"cap 0.5 µm",vert=True,fs=8.5); dim(b,yb,ye,2.2,"Au MTX\n2.0 µm\n(≥1.5)",vert=True,fs=8.5)
dim(b,-WT/2,WT/2,SL+WH+0.06,"rib top 1.4 µm",fs=8.5,off=0.01)
dim(b,0,SL,-2.45,"slab 275 nm",vert=True,fs=8.5); dim(b,SL,SL+WH,-1.25,"etch 275 nm (film 550 nm)",vert=True,fs=8.5)
b.annotate("SiO₂ buffer 120 ± 40 nm\n(whole wafer, under gold too)",(2.3,SL+B/2),(1.0,-0.33),fontsize=8,arrowprops=dict(arrowstyle="->"))
b.text(-2.5,-0.35,"rib walls 60°, bottom 1.72 µm",fontsize=8.5)
b.set_title("One gap (1:1)")
c=fig.add_subplot(gs[1,1]); draw(c,(1.45,2.05),(0.15,0.9))
dim(c,SL,yb,1.5,"buffer\n120 nm",vert=True,fs=9); dim(c,CW/2,xg,0.84,"slot 0.1 µm (20 nm air left)",fs=9,off=0.006)
c.annotate("ALD Al₂O₃ 40 nm\n(conformal, after gold)",(1.665,0.55),(1.47,0.66),fontsize=9,arrowprops=dict(arrowstyle="->"))
c.text(1.9,0.6,"Au",fontsize=10); c.text(1.48,0.2,"LN slab",fontsize=9); c.text(1.48,0.42,"cap",fontsize=9)
c.set_title("Zoom: cap / gold slot (1:1)")
import matplotlib.patches as mp
fig.legend(handles=[mp.Patch(color=C[k],label=l) for k,l in [("Au","gold"),("LN","LN (X-cut)"),("SiO2","SiO₂"),("ALD","ALD Al₂O₃ 40 nm")]],loc="lower center",ncol=4)
fig.tight_layout(rect=(0,0.04,1,1)); fig.savefig("madrid_cross_section.png",dpi=170)
# ---------------- FOM plot ----------------
rows=[r for r in csv.DictReader(open("madrid_sweep.csv")) if r["ald_nm"]=="40" and r["mtx_um"] in("2.0","2")]
def get(b):
    rr=sorted([r for r in rows if int(r["buffer_nm"])==b],key=lambda r:float(r["gap_um"]))
    return np.array([float(r["gap_um"]) for r in rr]),np.array([float(r["IL_dB_per_cm"]) for r in rr]),np.array([float(r["VpiL_Vcm"]) for r in rr])
g,i80,v80=get(80); _,i120,v120=get(120); _,i160,v160=get(160)
fig,(a1,a2)=plt.subplots(1,2,figsize=(14,5.2))
a1.fill_between(g,v80,v160,color="#0E2268",alpha=.18,label="buffer 80–160 nm (±40 nm)")
a1.plot(g,v120,"o-",color="#0E2268",ms=4,label="buffer 120 nm (nominal)")
a2.fill_between(g,i160,i80,color="#F20013",alpha=.18,label="buffer 80–160 nm (±40 nm)")
a2.semilogy(g,i120,"o-",color="#F20013",ms=4,label="buffer 120 nm (nominal)")
a2.axhline(0.5,color="k",ls="--",lw=1); a2.text(3.02,0.53,"IL limit 0.5 dB/cm",fontsize=9)
k=list(g).index(3.5)
for a,lo,mid,hi,f in ((a1,v80[k],v120[k],v160[k],"{:.2f} V·cm"),(a2,i160[k],i120[k],i80[k],"{:.2f} dB/cm")):
    a.axvline(3.5,color="0.4",ls=":"); a.errorbar([3.5],[mid],yerr=[[mid-lo],[hi-mid]],fmt="D",color="k",capsize=6,zorder=5)
    a.annotate(f"design (gap 3.5 µm):\n{f.format(mid)}  [{f.format(lo)} … {f.format(hi)}]",(3.5,mid),(3.56,mid*(1.02 if a is a1 else 1.9)),fontsize=9.5,
               bbox=dict(fc="white",ec="0.6"))
a1.set_ylabel("Vπ·L (V·cm)"); a2.set_ylabel("IL (dB/cm)")
for a in (a1,a2): a.set_xlabel("gap (µm)"); a.grid(alpha=.3,which="both"); a.legend(loc="upper left" if a is a1 else "lower left",fontsize=9)
a1.set_title(f"Vπ·L: ±40 nm buffer → {100*(v80[k]/v120[k]-1):+.1f} / {100*(v160[k]/v120[k]-1):+.1f} %")
a2.set_title("IL: stays below 0.5 dB/cm over the full tolerance")
fig.suptitle("MADRID — simulated at λ = 1625 nm · rib 1.4 µm, cap (gap−0.2)×0.5 µm, ALD 40 nm, Au 2 µm",fontsize=12)
fig.tight_layout(); fig.savefig("madrid_fom_tolerance.png",dpi=170)
print(v80[k],v120[k],v160[k],i160[k],i120[k],i80[k])
