import numpy as np, json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from scipy.optimize import least_squares
from load import *
J=json.load(open("fit.json")); OUT={tuple(o) for o in J["out"]}
WF=["6IS0001","6IS0002"]; cm=plt.cm.viridis(np.linspace(0,.95,len(FIELDS))); col=dict(zip(FIELDS,cm)); K=dict(color="k")
ok=lambda k,i:(k[0],k[1],i) not in OUT
# 1 boxplots
fig,ax=plt.subplots(figsize=(11,5.4)); pos=[];lab=[]
for i in range(4):
    for j,w in enumerate(WF):
        p=i*3+j+1; pos.append(p); lab.append(f"R{i+1}\n{w[-4:]}")
        y=[D[(w,f)][i] for f in FIELDS if ok((w,f),i)]
        ax.boxplot([y],positions=[p],widths=.6,whis=1.5,showfliers=False,boxprops=K,medianprops=K,whiskerprops=K,capprops=K)
        for f in FIELDS:
            v=D[(w,f)][i]
            if ok((w,f),i): ax.scatter(p,v,color=col[f],edgecolor="w",lw=.5,s=30,zorder=3,marker="o" if j==0 else "s")
            else: ax.scatter(p,v,color="r",marker="x",s=45,zorder=4)
        m=np.median(y); ax.text(p+(0.36 if j else -0.36),m,f"{m:.1f}",va="center",ha="left" if j else "right",fontsize=8.5)
for i in range(4): ax.text(i*3+1.5,327,f"w = {W[i]} µm",ha="center",fontsize=9)
ax.scatter([],[],color="r",marker="x",label="excluded (>5 % off its field)")
for f in FIELDS: ax.scatter([],[],color=col[f],label=f"{f:02d}")
ax.legend(title="field",fontsize=8,title_fontsize=8,loc="center left",bbox_to_anchor=(1.0,.5),frameon=False)
ax.set_xticks(pos,lab); ax.set_xlim(-0.4,11.8); ax.set_ylim(200,332); ax.set_yticks(range(200,331,10)); ax.set_ylabel("R (Ω)"); ax.grid(axis="y",alpha=.3)
ax.set_title("Istanbul phase-shifter resistance · wafers 6IS0001 (o), 6IS0002 (s) · 13 fields each",fontsize=10.5)
fig.tight_layout(); fig.savefig("boxplots.png",dpi=200)
# 2 field map
fig,ax=plt.subplots(1,3,figsize=(13,5.2),gridspec_kw=dict(width_ratios=[1,1,1.5]))
for a,w in zip(ax[:2],WF):
    M=np.full((5,3),np.nan)
    for f in FIELDS: c,r=POS[f]; M[r,c]=100*(J["fac"][f"{w}/{f}"]-1)
    im=a.imshow(M,cmap="RdBu_r",vmin=-8,vmax=8)
    for f in range(15):
        c,r=POS[f]; t=f"{f}\n" + ("n.m." if np.isnan(M[r,c]) else f"{M[r,c]:+.1f}%"); a.text(c,r,t,ha="center",va="center",fontsize=9)
    a.set_xticks([]); a.set_yticks([]); a.set_title(f"{w}: R / median − 1",fontsize=10)
fig.colorbar(im,ax=ax[:2],orientation="horizontal",fraction=.05,pad=.04,label="R / wafer median − 1 (%)")
ff=J["ff"]; dw=J["dw"]; fs=sorted(FIELDS,key=lambda f:ff[str(f)])
a=ax[2]; a.bar(range(len(fs)),[100*(ff[str(f)]-1) for f in fs],color=[col[f] for f in fs])
a.errorbar(range(len(fs)),[100*(ff[str(f)]-1) for f in fs],yerr=[50*abs(dw[str(f)]) for f in fs],fmt="none",ecolor="k",capsize=3)
a.set_xticks(range(len(fs)),[str(f) for f in fs]); a.set_xlabel("field (sorted)"); a.set_ylabel("field offset, mean of wafers (%)"); a.grid(axis="y",alpha=.3)
a.set_title("Bars: field offset · error bars: ± half wafer-to-wafer difference",fontsize=9.5)
fig.savefig("field_map.png",dpi=180,bbox_inches="tight")
# 3 fit: R = A/(w-d), plus field-normalised version
X=[];Y=[];F=[]
for k,v in D.items():
    for i in range(4):
        if ok(k,i): X.append(W[i]);Y.append(v[i]);F.append(k)
X=np.array(X);Y=np.array(Y)
s=least_squares(lambda q:q[0]/(X-q[1])-Y,[2000,5]); Jm=s.jac; cov=np.linalg.inv(Jm.T@Jm)*np.sum(s.fun**2)/(len(Y)-2); A,d=s.x; sA,sd=np.sqrt(np.diag(cov))
pl=np.polyfit(X,Y,1)
fig,ax=plt.subplots(figsize=(8.5,5.2)); xx=np.linspace(11.6,13.5,200)
for (w,f),xv,yv in zip(F,X,Y): ax.scatter(xv+(-0.03 if w=="6IS0001" else 0.03),yv,color=col[f],s=16,marker="o" if w=="6IS0001" else "s",alpha=.85)
ax.plot(xx,A/(xx-d),"k-",lw=1.8,label=f"R = {A:.0f} / (w − {d:.2f}) Ω   (w in µm)")
ax.plot(xx,np.polyval(pl,xx),"k:",lw=1.2,label=f"linear: R = {pl[0]:.2f}·w + {pl[1]:.1f} Ω")
for c,lab_,fac_ in (("C3","field 7 (+3.8 %)",1.0376),("C0","field 1 (−7.0 %)",0.9296)): ax.plot(xx,fac_*A/(xx-d),"--",color=c,lw=1,label=lab_)
meds=J["medians"]; ax.plot(W,meds,"kD",mfc="w",ms=7,label="median per width")
ax.set_xlabel("resistive-line width w (µm)"); ax.set_ylabel("R (Ω)"); ax.grid(alpha=.3); ax.legend(fontsize=8.5)
ax.set_title(f"Least squares on {len(Y)} points · RMSE {np.std(s.fun):.1f} Ω (mostly field-to-field)",fontsize=10)
fig.tight_layout(); fig.savefig("fit.png",dpi=200)
J.update(fitd=dict(A=A,d=d,sA=sA,sd=sd,rmse=float(np.std(s.fun)),n=len(Y)),lin=pl.tolist()); json.dump(J,open("fit.json","w"),indent=1,default=float)
print(A,sA,d,sd,pl)
