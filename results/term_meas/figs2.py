import numpy as np, matplotlib, json; matplotlib.use("Agg"); import matplotlib.pyplot as plt
exec(open("analyze.py").read().split("# step 1")[0])
RS,DW=27.17,0.911; xe=L*(1/(Ws-DW)+1/(2*(Wg-DW)))
NOISY={"2","5","7","8"}; K=dict(color="k")
# 1) boxplots per variant
fig,ax=plt.subplots(figsize=(14,5.2)); tp=[];tl=[]
for v in range(15):
    base=1 if v==0 else 2.2+v*2.4-2.4+1.5
    for j,w in enumerate(["6LS0004","6LS0005"]):
        p=base+j*1.0; y=[D[(w,f)][v] for f in F]
        ax.boxplot([y],positions=[p],widths=.7,whis=1.5,showfliers=False,boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
        for f in F:
            n=f in NOISY; ax.plot(p,D[(w,f)][v],"o" if j==0 else "s",ms=3.5,color="0.25",mfc="none" if n else "0.25",mew=.8,zorder=3)
        ax.text(p,np.median(y),"",)
    tp.append(base+.5); tl.append(f"{v+1}" + ("\ncross" if v==0 else ""))
ax.axvline(3.0,color="0.5",ls=":",lw=1)
ax.set_xticks(tp,tl); ax.set_xlabel("termination variant (left box 6LS0004 ○, right box 6LS0005 □)"); ax.set_ylabel("R (Ω)"); ax.grid(axis="y",alpha=.3)
ax.plot([],[],"o",color="0.25",ms=4,label="fields 0, 10, 14"); ax.plot([],[],"o",color="0.25",mfc="none",ms=4,label="fields 2, 5, 7, 8 (contact problems)")
ax.legend(loc="upper left",fontsize=9); ax.set_xlim(-0.2,tp[-1]+1.3)
ax.set_title("TiN terminations: 3-point DC probe, 7 fields per wafer",fontsize=10.5)
ax.set_yticks(range(40,141,10)); ax.set_ylim(40,142)
fig.tight_layout(); fig.savefig("box_variants.png",dpi=200)
for j,w in enumerate(["6LS0004","6LS0005"]):
    fig,ax=plt.subplots(figsize=(14,5.2)); tp=[];tl=[]
    for v in range(15):
        p=v+1+(0.6 if v>0 else 0); y=[D[(w,f)][v] for f in F]
        ax.boxplot([y],positions=[p],widths=.6,whis=1.5,showfliers=False,boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
        for f in F: ax.plot(p,D[(w,f)][v],"o" if j==0 else "s",ms=4,color="0.25",mfc="none" if f in NOISY else "0.25",mew=.8,zorder=3)
        m=np.median(y); ax.text(p+.33,m,f"{m:.1f}",va="center",fontsize=8.5)
        tp.append(p); tl.append(f"{v+1}"+("\ncross" if v==0 else ""))
    ax.axvline(1.8,color="0.5",ls=":",lw=1); ax.set_xticks(tp,tl); ax.set_xlim(0.4,tp[-1]+0.9)
    ax.set_yticks(range(40,141,10)); ax.set_ylim(40,142); ax.grid(axis="y",alpha=.3)
    ax.set_xlabel("termination variant"); ax.set_ylabel("R (Ω)")
    ax.plot([],[],"o" if j==0 else "s",color="0.25",ms=4,label="fields 0, 10, 14"); ax.plot([],[],"o" if j==0 else "s",color="0.25",mfc="none",ms=4,label="fields 2, 5, 7, 8 (contact problems)")
    ax.legend(loc="upper left",fontsize=9); ax.set_title(f"{w}: TiN terminations, 7 fields, median values labelled",fontsize=10.5)
    fig.tight_layout(); fig.savefig(f"box_{w}.png",dpi=200)
# 2) per-measurement sheet resistance
fig,ax=plt.subplots(figsize=(6.5,5)); S={}; pos=1; tl=[];tp=[]
for w in ["6LS0004","6LS0005"]:
    for grp,fs in (("clean",["0","10","14"]),("all",F)):
        y=np.array([D[(w,f)][v]/xe[v] for f in fs for v in range(1,15)])
        ax.boxplot([y],positions=[pos],widths=.6,whis=1.5,showfliers=True,flierprops=dict(marker="o",mfc="none",mec="k",ms=4),boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
        m=np.median(y); ax.text(pos+.36,m,f"{m:.1f}",va="center",fontsize=9)
        S[f"{w}/{grp}"]=dict(med=float(m),q1=float(np.percentile(y,25)),q3=float(np.percentile(y,75)),n=int(len(y)))
        tp.append(pos); tl.append(f"{w[-4:]}\n{'fields 0,10,14' if grp=='clean' else 'all fields'}"); pos+=1 if grp=="clean" else 1.6
ax.set_xticks(tp,tl,fontsize=9); ax.set_ylabel("R_sh per measurement (Ω/sq)"); ax.grid(axis="y",alpha=.3)
ax.set_title(f"R_sh = R / x_eff, widths corrected by δ = {DW:.1f} µm (variants 2–15)",fontsize=10)
fig.tight_layout(); fig.savefig("box_rsq.png",dpi=200); json.dump(S,open("rsq_box.json","w"),indent=1); print(json.dumps(S,indent=1))
