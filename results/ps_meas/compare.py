import numpy as np, openpyxl, json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ws=openpyxl.load_workbook("PS.xlsx").active
# colleague (automatic prober), 6LS0004, read from plot hover: min,q1,med,q3,max (fences = min/max)
COL={"6LS0004":{"R2":dict(label="PS-3",whislo=230.4751,q1=235.8829,med=245.971,q3=251.9684,whishi=254.5146),
                "R4":dict(label="PS-1",whislo=310.1167,q1=320.308,med=335.8438,q3=343.8505,whishi=348.1075)}}
rows={"6LS0004":range(2,17),"6LS0005":range(22,37)}; idx={"R2":1,"R4":3}
w="6LS0004"; fig,ax=plt.subplots(figsize=(8,5)); K=dict(color="k"); out={}
for g,(r,ci) in enumerate(idx.items()):
    y=[ws.cell(k,3+ci).value for k in rows[w] if ws.cell(k,3+ci).value is not None]; p0,p1=g*3+1,g*3+2
    ax.boxplot([y],positions=[p0],widths=.6,whis=1.5,showfliers=False,boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
    ax.scatter([p0]*len(y),y,color="0.35",s=22,zorder=3,edgecolor="w",lw=.5)
    s=COL[w][r]; ax.bxp([s],positions=[p1],widths=.6,showfliers=False,boxprops=dict(color="k",ls="--"),medianprops=K,whiskerprops=dict(color="k",ls="--"),capprops=K)
    m0=np.median(y); ax.text(p0-.36,m0,f"{m0:.1f}",ha="right",va="center",fontsize=9); ax.text(p1+.36,s["med"],f"{s['med']:.1f}",ha="left",va="center",fontsize=9)
    out[r]=dict(ours=m0,col=s["med"],d=s["med"]-m0,iqr_o=np.subtract(*np.percentile(y,[75,25])),iqr_c=s["q3"]-s["q1"],n=len(y))
ax.set_xticks([1,2,4,5],["R2\nmanual 2-pt","PS-3\nautomatic","R4\nmanual 2-pt","PS-1\nautomatic"]); ax.set_xlim(-.3,6.3)
ax.set_ylabel("R (Ω)"); ax.grid(axis="y",alpha=.3); ax.set_title("6LS0004: manual 2-point probe (solid, points) vs automatic prober (dashed)",fontsize=10.5)
fig.tight_layout(); fig.savefig("compare_6LS0004.png",dpi=200); print(json.dumps(out,indent=1,default=float))
