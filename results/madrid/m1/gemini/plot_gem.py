import json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=[]
for f in ("results.txt","results2.txt"):
    for l in open(f):
        if "RESULT" in l: tag=l.split()[0]; r=json.loads(l.split("RESULT ",1)[1]); r["tag"]=tag; R.append(r)
base=dict(tag="REF",buf=0.1,IL_dBcm=0.23338,VpiL_Vcm=1.85737); R.append(base)
ref=sorted([r for r in R if r["tag"]=="REF"],key=lambda r:r["IL_dBcm"])
f,ax=plt.subplots(figsize=(10,6))
ax.plot([r["IL_dBcm"] for r in ref],[r["VpiL_Vcm"] for r in ref],"o-",c="k",label="reference (fill 1.1 µm, no trench), buffer 85–170 nm")
for r in ref: ax.annotate(f"{r['buf']*1e3:.0f}",(r["IL_dBcm"],r["VpiL_Vcm"]),(4,4),textcoords="offset points",fontsize=8)
for tag,c,lab in (("Bbest_asym","#c0392b","U-slot 1.0 µm, floor 100 nm (Madrid 1)"),("Bbest_sym","#8e44ad","U-slot, symmetric tall ground")):
    s=[r for r in R if (r["tag"] in (tag,) or (r["tag"]==tag.replace("best","")[:6] and r["trw"]==1.0 and r["trf"]==0.1 and abs(r["buf"]-0.1)<1e-9 and ((r["mtx_small"]>5)==("sym" in tag))))]
    s=sorted(s,key=lambda r:r["IL_dBcm"]); ax.plot([r["IL_dBcm"] for r in s],[r["VpiL_Vcm"] for r in s],"s-",c=c,label=lab)
    for r in s: ax.annotate(f"{r['buf']*1e3:.0f}",(r["IL_dBcm"],r["VpiL_Vcm"]),(4,-10),textcoords="offset points",fontsize=8,color=c)
for tag,m,c,lab in (("C","^","#1f77b4","C stepped buffer"),("D","v","#17becf","D inverted-L"),("B+C","P","#e67e22","U-slot + C"),("B+D","X","#2ca02c","U-slot + D")):
    s=[r for r in R if r["tag"]==tag]; ax.plot([r["IL_dBcm"] for r in s],[r["VpiL_Vcm"] for r in s],m,ms=9,c=c,ls="none",label=lab)
ax.set_xscale("log"); ax.set_xlabel("IL (dB/cm)"); ax.set_ylabel("Vπ·L (V·cm)"); ax.grid(alpha=.3,which="both"); ax.legend(fontsize=8.5,loc="upper right")
ax.set_title("Madrid 1, gap 3.5 µm, 1625 nm (FEM): U-slot shifts the whole trade-off by ≈ −5 % (−6.5 % symmetric)",fontsize=10.5)
f.tight_layout(); f.savefig("gemini_variants_tradeoff.png",dpi=150)
