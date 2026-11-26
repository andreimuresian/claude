import numpy as np, openpyxl, json, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
ws=openpyxl.load_workbook("PS.xlsx").active
L=np.array([197.1,226.5,255.9,307.5]); W={"6LS0004":range(2,17),"6LS0005":range(22,37)}
D={}
for w,rows in W.items():
    for r in rows:
        f=ws.cell(r,2).value; v=[ws.cell(r,c).value for c in range(3,7)]
        if any(v): D[(w,f)]=v
fields=sorted({f for _,f in D}); cmap=plt.cm.viridis(np.linspace(0,0.95,len(fields))); col=dict(zip(fields,cmap))
# boxplots
fig,ax=plt.subplots(figsize=(11,5.2)); pos=[];lab=[]
for i in range(4):
    for j,w in enumerate(W):
        p=i*3+j+1; pos.append(p); lab.append(f"R{i+1}\n{w[-4:]}")
        y=[v[i] for (ww,f),v in D.items() if ww==w and v[i] is not None]
        ax.boxplot([y],positions=[p],widths=0.6,whis=1.5,showfliers=False,
           boxprops=dict(color="k"),medianprops=dict(color="k"),whiskerprops=dict(color="k"),capprops=dict(color="k"))
        for (ww,f),v in D.items():
            if ww==w and v[i] is not None: ax.scatter(p,v[i],color=col[f],edgecolor="w",lw=.5,s=30,zorder=3,marker="o" if j==0 else "s")
ax.set_xticks(pos,lab); ax.set_ylabel("R (Ω)"); ax.grid(axis="y",alpha=.3)
for i in range(4): ax.text(i*3+1.5,ax.get_ylim()[1] if False else 352,f"ΔL = {L[i]} µm",ha="center",fontsize=9)
ax.set_ylim(195,358)
for f in fields: ax.scatter([],[],color=col[f],label=f"{f:02d}")
ax.legend(title="field",fontsize=8,title_fontsize=8,loc="center left",bbox_to_anchor=(1.0,.5),frameon=False)
ax.set_title("Phase-shifter resistance, 2-point DC @ 10 mA · wafers 6LS0004 (o) and 6LS0005 (s), 9 fields each",fontsize=10.5)
fig.tight_layout(); fig.savefig("boxplots.png",dpi=200)
# fit
X=[];Y=[]
for v in D.values():
    for l,y in zip(L,v):
        if y is not None: X.append(l);Y.append(y)
X=np.array(X);Y=np.array(Y); n=len(X)
A=np.vstack([X,np.ones(n)]).T; (m,b),res,_,_=np.linalg.lstsq(A,Y,rcond=None)
r=Y-(m*X+b); s2=r@r/(n-2); cov=s2*np.linalg.inv(A.T@A); sm,sb=np.sqrt(np.diag(cov)); R2=1-r@r/((Y-Y.mean())@(Y-Y.mean()))
m0=(X@Y)/(X@X)
means=[np.mean([v[i] for v in D.values() if v[i] is not None]) for i in range(4)]
T=[175,190,205]; out={"m":m,"b":b,"sm":sm,"sb":sb,"R2":R2,"n":n,"m0":m0,"means":means,"rmse":np.sqrt(s2)}
pf={}
for k,v in D.items():
    ok=[i for i in range(4) if v[i] is not None]; q=np.polyfit(L[ok],[v[i] for i in ok],1); pf[k]=q
rows=[]
for t in T:
    l=(t-b)/m; g=np.array([-1/m,-(t-b)/m**2]); sl=np.sqrt(g@np.array([[cov[1,1],cov[1,0]],[cov[0,1],cov[0,0]]])@g)
    per=[(t-q[1])/q[0] for q in pf.values()]
    pw={w:np.mean([(t-q[1])/q[0] for k,q in pf.items() if k[0]==w]) for w in W}
    rows.append(dict(R=t,dL=l,ci=1.96*sl,lo=min(per),hi=max(per),sd=np.std(per,ddof=1),w4=pw["6LS0004"],w5=pw["6LS0005"],dL0=t/m0))
out["rows"]=rows; json.dump(out,open("fit.json","w"),indent=1,default=float)
fig,ax=plt.subplots(figsize=(8.5,5.2)); xx=np.linspace(150,320,200)
for (w,f),v in D.items():
    ax.scatter([l for l,y in zip(L,v) if y],[y for y in v if y],color=col[f],s=18,zorder=3,marker="o" if w.endswith("4") else "s",alpha=.8)
qs=np.array(list(pf.values()))
ax.fill_between(xx,np.min(np.outer(qs[:,0],xx)+qs[:,1:2],0),np.max(np.outer(qs[:,0],xx)+qs[:,1:2],0),color="0.85",label="per-field fits (envelope)")
ax.plot(xx,m*xx+b,"k-",lw=1.6,label=f"fit, all {n} points: R = {m:.4f}·ΔL {b:+.2f} Ω")
ax.plot(L,means,"kD",ms=6,mfc="w",label="mean per ΔL")
for rw in rows:
    ax.plot([140,rw["dL"]],[rw["R"]]*2,"k:",lw=1); ax.plot([rw["dL"]]*2,[150,rw["R"]],"k:",lw=1)
    ax.errorbar(rw["dL"],rw["R"],xerr=[[rw["dL"]-rw["lo"]],[rw["hi"]-rw["dL"]]],fmt="o",color="C3",capsize=4,ms=5)
    ax.text(rw["dL"]+3,rw["R"]-9,f"{rw['dL']:.1f} µm",color="C3",fontsize=9)
ax.axvspan(140,197.1,color="C3",alpha=.05); ax.text(143,345,"extrapolation (ΔL < 197.1 µm)",color="C3",fontsize=9)
ax.set_xlim(140,320); ax.set_ylim(150,360); ax.set_xlabel("ΔL (µm)"); ax.set_ylabel("R (Ω)"); ax.grid(alpha=.3); ax.legend(fontsize=8.5,loc="lower right")
fig.tight_layout(); fig.savefig("fit.png",dpi=200)
print(json.dumps(out,indent=1,default=float))
