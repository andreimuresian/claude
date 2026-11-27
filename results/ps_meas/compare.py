import numpy as np, openpyxl, json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ws=openpyxl.load_workbook("PS.xlsx").active
# colleague (automatic prober), from plot hover: whislo/whishi = fences, fliers = points beyond
COL={"6LS0004":{"R2":dict(whislo=230.4751,q1=235.8829,med=245.971,q3=251.9684,whishi=254.5146,fliers=[]),
                "R4":dict(whislo=310.1167,q1=320.308,med=335.8438,q3=343.8505,whishi=348.1075,fliers=[])},
     "6LS0005":{"R2":dict(whislo=231.649,q1=232.4279,med=242.6175,q3=249.5488,whishi=255.9244,fliers=[180.9454]),
                "R4":dict(whislo=314.6781,q1=324.0806,med=336.7301,q3=344.5524,whishi=354.0291,fliers=[473.9436])}}
rows={"6LS0004":range(2,17),"6LS0005":range(22,37)}; idx={"R2":1,"R4":3}; nm={"R2":"PS-3","R4":"PS-1"}
YL=(222,362); fig,ax=plt.subplots(figsize=(11,5.4)); K=dict(color="k"); D=dict(color="k",ls="--"); out={}; tp=[];tl=[]
for g,(r,ci) in enumerate(idx.items()):
    for j,w in enumerate(rows):
        p0=g*6.5+j*2.6+1; p1=p0+1
        y=[ws.cell(k,3+ci).value for k in rows[w] if ws.cell(k,3+ci).value is not None]
        ax.boxplot([y],positions=[p0],widths=.6,whis=1.5,showfliers=False,boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
        ax.scatter([p0]*len(y),y,color="0.35",s=20,zorder=3,edgecolor="w",lw=.5,marker="o" if j==0 else "s")
        s=COL[w][r]; ax.bxp([s],positions=[p1],widths=.6,showfliers=False,boxprops=D,medianprops=K,whiskerprops=D,capprops=K)
        for f in s["fliers"]:
            if YL[0]<f<YL[1]: ax.plot(p1,f,"o",mfc="w",mec="k")
            else:
                yy=YL[1]-4 if f>YL[1] else YL[0]+4
                ax.annotate(f"outlier {f:.1f}",(p1,yy),ha="center",va="center",fontsize=8,xytext=(p1+.05,yy),
                            arrowprops=None); ax.text(p1+0.0,yy+(2.6 if f>YL[1] else -2.6),"↑" if f>YL[1] else "↓",ha="center",va="center",fontsize=9)
        m0=np.median(y); ax.text(p0-.36,m0,f"{m0:.1f}",ha="right",va="center",fontsize=8.5); ax.text(p1+.36,s["med"],f"{s['med']:.1f}",ha="left",va="center",fontsize=8.5)
        tp+=[p0,p1]; tl+=[f"{r}\nmanual\n{w[-4:]}",f"{nm[r]}\nauto\n{w[-4:]}"]
        out[f"{r}_{w}"]=dict(ours=m0,col=s["med"],d=s["med"]-m0,iqr_o=float(np.subtract(*np.percentile(y,[75,25]))),iqr_c=s["q3"]-s["q1"])
ax.set_xticks(tp,tl,fontsize=8.5); ax.set_ylim(*YL); ax.set_xlim(-0.2,tp[-1]+1.2)
ax.set_ylabel("R (Ω)"); ax.grid(axis="y",alpha=.3)
ax.set_title("Manual 2-point probe (solid, points: o 6LS0004, s 6LS0005) vs automatic prober (dashed)",fontsize=10.5)
fig.tight_layout(); fig.savefig("compare_both.png",dpi=200); json.dump(out,open("compare.json","w"),indent=1); print(json.dumps(out,indent=1))
