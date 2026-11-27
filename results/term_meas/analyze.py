import numpy as np, openpyxl, json
from scipy.optimize import least_squares
ws=openpyxl.load_workbook("RES_MTX.xlsx",data_only=True).active
geo=np.array([[ws.cell(r,c).value for c in (2,3,4)] for r in range(62,77)]); L,Ws,Wg=geo.T
F=["0","2","5","7","8","10","14"]; W={"6LS0004":21,"6LS0005":3}; D={}
for w,r0 in W.items():
    for j,f in enumerate(F): D[(w,f)]=np.array([ws.cell(r0+i,3+j).value for i in range(15)],float)
I=np.arange(1,15); xg=L*(1/Ws+1/(2*Wg))
def mdl(q,i): Rs,d,R0=q; return Rs*L[i]*(1/(Ws[i]-d)+1/(2*(Wg[i]-d)))+R0
# step 1: field quality = rms about its own straight line
qual0={k:float(np.std(v[I]-np.polyval(np.polyfit(xg[I],v[I],1),xg[I]))) for k,v in D.items()}
clean=[k for k in D if qual0[k]<2.5]; qual={f"{k[0]}/{k[1]}":v for k,v in qual0.items()}
def fit(keys,loss="linear"):
    ii=np.concatenate([I]*len(keys)); Y=np.concatenate([D[k][I] for k in keys])
    t=least_squares(lambda q: mdl(q,ii)-Y,[26,1,2],loss=loss,f_scale=1.0)
    J=t.jac; cov=np.linalg.inv(J.T@J)*np.mean(t.fun**2)*len(Y)/(len(Y)-3); return t.x,np.sqrt(np.diag(cov)),float(np.std(Y-mdl(t.x,ii)))
q,e,rms=fit(clean,"soft_l1")
lin=np.polyfit(np.concatenate([xg[I]]*len(clean)),np.concatenate([D[k][I] for k in clean]),1)
perf={f"{k[0]}/{k[1]}":fit([k])[0].tolist() for k in clean}
perw={w:dict(zip(["Rsq","dw","R0"],fit([k for k in clean if k[0]==w])[0].tolist())) for w in W}
exc={f"{k[0]}/{k[1]}":dict(med=float(np.median(D[k][I]-mdl(q,I))),max=float(np.max(D[k][I]-mdl(q,I)))) for k in D}
v1=dict(pred=float(mdl(q,np.array([0]))[0]),meas={f"{k[0]}/{k[1]}":float(D[k][0]) for k in clean})
res=dict(Rsq=q[0],dw=q[1],R0=q[2],e=e.tolist(),rms=rms,lin=lin.tolist(),qual=qual,clean=[f"{a}/{b}" for a,b in clean],perf=perf,perw=perw,excess=exc,v1=v1)
json.dump(res,open("fit.json","w"),indent=1,default=float); print(json.dumps(res,indent=1,default=float))
def fit2(keys,R0=0.0):
    ii=np.concatenate([I]*len(keys)); Y=np.concatenate([D[k][I] for k in keys])
    t=least_squares(lambda p: mdl([p[0],p[1],R0],ii)-Y,[26,1]); J=t.jac; cov=np.linalg.inv(J.T@J)*np.sum(t.fun**2)/(len(Y)-2)
    return t.x.tolist(),np.sqrt(np.diag(cov)).tolist(),float(np.std(t.fun))
best=[k for k in clean if k[1] in ("10","14")]
print("R0=0 clean6",fit2(clean)); print("R0=0 best4",fit2(best)); print("3par best4",fit(best)); print("R0=2 best4",fit2(best,2.0))
for k in clean: print(k,fit2([k]))
