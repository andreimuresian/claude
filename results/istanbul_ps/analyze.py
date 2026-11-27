import numpy as np, json
from load import *
from scipy.optimize import least_squares
med=np.median(np.array(list(D.values())),axis=0)
OUT=set()
for k,v in D.items():
    r=v/med; m=np.median(r)
    for i in range(4):
        if abs(r[i]/m-1)>0.05: OUT.add((k[0],k[1],i))
print("outliers",sorted(OUT),[D[(a,b)][i] for a,b,i in sorted(OUT)])
mask={k:np.array([(k[0],k[1],i) not in OUT for i in range(4)]) for k in D}
# field factor
fac={k:float(np.median((v/med)[mask[k]])) for k,v in D.items()}
ff={f:np.mean([fac[(w,f)] for w in ("6IS0001","6IS0002")]) for f in FIELDS}
dw={f:fac[("6IS0001",f)]-fac[("6IS0002",f)] for f in FIELDS}
print("field factor (mean of wafers), wafer diff:")
for f in FIELDS: print(f,POS[f],round(ff[f],4),round(dw[f],4))
print("std field-to-field %.2f %%, rms wafer diff %.2f %%"%(100*np.std(list(ff.values()),ddof=1),100*np.sqrt(np.mean(np.square(list(dw.values()))))/np.sqrt(2)))
w1=np.mean([fac[("6IS0001",f)] for f in FIELDS]); w2=np.mean([fac[("6IS0002",f)] for f in FIELDS]); print("wafer means",w1,w2)
# fit R = A/w + B on all valid
X=[];Y=[];K=[]
for k,v in D.items():
    for i in range(4):
        if mask[k][i]: X.append(W[i]);Y.append(v[i]);K.append(k)
X=np.array(X);Y=np.array(Y)
A=np.c_[1/X,np.ones_like(X)]; p,res,_,_=np.linalg.lstsq(A,Y,rcond=None); r=Y-A@p; s2=r@r/(len(Y)-2); cov=s2*np.linalg.inv(A.T@A)
print("fit R=A/w+B", p, np.sqrt(np.diag(cov)), "rmse",np.sqrt(s2), "R2",1-r@r/np.sum((Y-Y.mean())**2), "n",len(Y))
p0=(X**-1)@Y/((X**-1)@(X**-1)); print("B=0: A",p0)
pl=np.polyfit(X,Y,1); print("linear",pl)
meds=np.array([np.median([D[k][i] for k in D if mask[k][i]]) for i in range(4)]); print("medians",meds, "fit at w",A[:0] if False else p[0]/W+p[1])
# per-field A with common B
pf={}
for k in D:
    m=mask[k]; pf[f"{k[0]}/{k[1]}"]=float(((D[k][m]-p[1])/ (1/W[m])).mean())
json.dump(dict(out=[list(o) for o in sorted(OUT)],fac={f"{a}/{b}":v for (a,b),v in fac.items()},ff=ff,dw=dw,fit=dict(A=p[0],B=p[1],sA=float(np.sqrt(cov[0,0])),sB=float(np.sqrt(cov[1,1])),rmse=float(np.sqrt(s2)),R2=float(1-r@r/np.sum((Y-Y.mean())**2)),n=len(Y)),A0=p0,lin=pl.tolist(),medians=meds.tolist()),open("fit.json","w"),indent=1,default=float)
