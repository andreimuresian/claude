import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=[]
for l in open("results1d.txt"):
    if "RESULT" in l: t=l.split()[0]; r=json.loads(l.split("RESULT ",1)[1]); r["tag"]=t; R.append(r)
NO=(1.9105,0.1618)   # no trench, fill 2.0, buffer 130 (FEM)
f,ax=plt.subplots(1,3,figsize=(16,4.8))
def pl(a,tag,key,xl,title,xf=lambda r:r):
    s=sorted([r for r in R if r["tag"]==tag],key=lambda r:xf(r)); x=[xf(r) for r in s]
    a.plot(x,[r["VpiL_Vcm"] for r in s],"o-",c="#1f4e79",lw=2); a.axhline(NO[0],c="#1f4e79",ls=":",lw=1); a.text(x[0],NO[0]+0.004,"no trench",fontsize=8.5,color="#1f4e79")
    a.set_xlabel(xl); a.set_ylabel("Vπ·L (V·cm)",color="#1f4e79"); a.set_title(title,fontsize=10.5); a.grid(alpha=.3)
    b=a.twinx(); b.plot(x,[r["IL_dBcm"] for r in s],"s--",c="#c0392b"); b.axhline(NO[1],c="#c0392b",ls=":",lw=1); b.set_ylabel("IL (dB/cm)",color="#c0392b")
    return s
pl(ax[0],"WIDTH","trw","trench width (µm)","Trench width (floor 100 nm, pillars touch gold)",lambda r:r["trw"])
pl(ax[1],"FLOOR","trf","oxide left above rib top (nm)","Trench floor (width 1.0 µm)",lambda r:r["trf"]*1e3)
s=pl(ax[2],"PILLAR","trw","pillar width (µm)","Pillars 200 nm away from the gold (air gap)",lambda r:round((r["cap_w"]-r["trw"])/2,3))
ax[2].plot([1.25],[1.7820],"*",c="k",ms=14); ax[2].set_xlim(0.25,1.35); ax[2].annotate("pillars touching gold\n(1.25 µm, trench 1.0 µm)",(1.25,1.782),(0.55,1.81),fontsize=8.5,arrowprops=dict(arrowstyle="->"))
f.suptitle("Madrid 1 U-slot, gap 3.5 µm, buffer 130 nm, fill 2.0 µm, λ = 1625 nm (FEM)",fontsize=11.5); f.tight_layout(); f.savefig("uslot_1d_sweeps.png",dpi=150)
