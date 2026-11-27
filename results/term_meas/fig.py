import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
exec(open("analyze.py").read().split("# step 1")[0])
q=[27.17,0.911,0.0]; xs=np.linspace(1.7,4.0,200)
fig,ax=plt.subplots(1,2,figsize=(13,5))
cl={"0":"C0","10":"C2","14":"C1"}
for k,v in D.items():
    c=k[1] in cl; m="o" if k[0]=="6LS0004" else "s"
    ax[0].plot(xg[I],v[I],m,ms=5 if c else 4,color=cl.get(k[1],"0.6"),mfc=cl.get(k[1],"none") if c else "none",alpha=1 if c else .7,
               label=f"{k[0][-4:]} f{k[1]}" if c else None)
ax[0].plot([],[],"o",color="0.6",mfc="none",label="fields 2,5,7,8 (noisy)")
# model curve vs x: parametrise by variant scale s: ws=s*2.6286*wg
sc=np.linspace(12.0,28,200); wsx=sc*Ws[1]/Wg[1]; xx=56*(1/wsx+1/(2*sc)); yy=q[0]*56*(1/(wsx-q[1])+1/(2*(sc-q[1])))
ax[0].plot(xx,yy,"k-",lw=1.6,label=f"R = R□·L·[1/(ws−δ)+1/(2(wg−δ))], R□ = 27.2 Ω/□, δ = 0.9 µm")
ax[0].plot(xx,27.17*xx,"k:",lw=1,label="same R□, δ = 0 (drawn widths)")
ax[0].plot(xg[0],np.median([D[(w,f)][0] for w in ("6LS0004","6LS0005") for f in ("10","14")]),"r*",ms=12,label="variant 1 (cross), median f10/f14")
ax[0].plot(xg[0]*0+28*(1/(Ws[0]-q[1])+1/(2*(Wg[0]-q[1])))*0+xg[0],q[0]*28*(1/(Ws[0]-q[1])+1/(2*(Wg[0]-q[1]))),"r+",ms=12,mew=2,label="variant 1 predicted")
ax[0].set_xlabel("x = L·(1/ws + 1/(2·wg))  (squares, drawn widths)"); ax[0].set_ylabel("R (Ω)"); ax[0].grid(alpha=.3); ax[0].legend(fontsize=7.5)
for k,v in D.items():
    r=v[I]-(q[0]*L[I]*(1/(Ws[I]-q[1])+1/(2*(Wg[I]-q[1]))))
    c=k[1] in cl; ax[1].plot(I+1+(0.15 if k[0]=="6LS0005" else -0.15),r,"o" if k[0]=="6LS0004" else "s",ms=4,color=cl.get(k[1],"0.6"),mfc=cl.get(k[1],"none") if c else "none")
ax[1].axhline(0,c="k",lw=1); ax[1].set_xlabel("variant"); ax[1].set_ylabel("R − model (Ω)"); ax[1].set_xticks(range(2,16)); ax[1].grid(alpha=.3)
ax[1].set_title("Residuals vs common model: clean fields smooth (field-to-field slope ±7 %); noisy fields scattered high (up to +41 Ω)",fontsize=10)
fig.tight_layout(); fig.savefig("term_fit.png",dpi=170)
