import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from predictor import Predictor
from gp_build import load
P=Predictor("models/model_card.json"); R,X,IL,V=load()
# 1 WG effect
wg=np.linspace(1.0,1.5,51); fig,ax=plt.subplots(1,2,figsize=(12,4.6))
cases=[("GAP 3.0, buf 100 nm",3.0,0.10),("GAP 3.5, buf 100 nm",3.5,0.10),("GAP 3.5, buf 150 nm",3.5,0.15),("GAP 4.0, buf 100 nm",4.0,0.10)]
for (lab,g,b),c in zip(cases,["C0","C1","C2","C3"]):
    Xs=np.array([[g,b,0.0,1.1,1.0,w] for w in wg]); r=P.predict_array(Xs)
    for a,k in zip(ax,("VpiL","IL")):
        a.plot(wg,r[k]["mean"],c=c,label=lab); a.fill_between(wg,r[k]["lo95"],r[k]["hi95"],color=c,alpha=.15)
ax[0].set_ylabel("Vπ·L (V·cm)"); ax[1].set_ylabel("IL (dB/cm)"); ax[1].set_yscale("log")
for a in ax: a.set_xlabel("rib top width WG (µm)"); a.grid(alpha=.3,which="both"); a.axvline(1.4,c="k",ls=":",lw=1)
ax[0].legend(fontsize=9); ax[0].set_title("Cap fills the gap (CAP_W = GAP), CAP_H 1.1 µm, MTX_small 1.0 µm",fontsize=10)
ax[1].set_title("Bands: GP 95 %; dotted: original dataset (WG 1.4)",fontsize=10)
fig.tight_layout(); fig.savefig("wg_effect.png",dpi=160)
# 2 dataset + validation
val=json.load(open("validation_wg.json")); fig,ax=plt.subplots(1,3,figsize=(15,4.4))
w=np.array([r["wg"] for r in R]); ax[0].hist([w[w==1.4],w[w!=1.4]],bins=np.linspace(1.0,1.5,21),stacked=True,label=["original 112 (WG 1.4)","new 76 (16 corners + 60 LHS)"],color=["0.6","C0"])
ax[0].set_xlabel("WG (µm)"); ax[0].set_ylabel("FEM points"); ax[0].legend(fontsize=9); ax[0].set_title("Training set: 188 FEM points",fontsize=10)
for a,k,kp,lo,hi,lab in ((ax[1],"IL","IL_p","IL_lo","IL_hi","IL (dB/cm)"),(ax[2],"V","V_p","V_lo","V_hi","Vπ·L (V·cm)")):
    y=np.array([v[k] for v in val]); p=np.array([v[kp] for v in val]); e=np.array([[v[kp]-v[lo] for v in val],[v[hi]-v[kp] for v in val]])
    a.errorbar(y,p,yerr=e,fmt="o",capsize=3); m=[min(y.min(),p.min())*0.9,max(y.max(),p.max())*1.1]; a.plot(m,m,"r--")
    if k=="IL": a.set_xscale("log"); a.set_yscale("log")
    err=100*np.abs(p/y-1); a.set_title(f"8 held-out FEM points: max error {err.max():.2f} %, all in 95 %",fontsize=10); a.set_xlabel("FEM "+lab); a.set_ylabel("GP "+lab); a.grid(alpha=.3,which="both")
fig.tight_layout(); fig.savefig("dataset_validation.png",dpi=160)
