import json, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=[json.loads(l[7:]) for l in open("sweep.txt") if l.startswith("RESULT")]
W=sorted({r["wl"] for r in R}); cm=plt.cm.plasma(np.linspace(0.05,0.85,len(W)))
f,ax=plt.subplots(1,2,figsize=(13,5))
for w,c in zip(W,cm):
    s=sorted([r for r in R if r["wl"]==w],key=lambda r:r["slab_w"]); x=[r["slab_w"] for r in s]
    ax[0].plot(x,[r["IL_dBcm"] for r in s],"o-",ms=3.5,c=c,label=f"{w*1e3:.0f} nm"); ax[1].plot(x,[r["VpiL_Vcm"] for r in s],"o-",ms=3.5,c=c,label=f"{w*1e3:.0f} nm")
    il=np.array([r["IL_dBcm"] for r in s]); i=int(np.argmax(il)); print(f"{w*1e3:.0f} nm: IL {il.min():.3f}-{il.max():.3f} (peak at {x[i]}), VpiL {min(r['VpiL_Vcm'] for r in s):.3f}-{max(r['VpiL_Vcm'] for r in s):.3f}")
for a in (ax[0],ax[1]): a.axvline(4.6,c="k",ls="--",lw=1.2)
ax[0].text(4.62,0.07,"nominal 4.6 µm",fontsize=9,rotation=90,va="bottom")
ax[0].set_yscale("log"); ax[0].set_xlabel("SLAB_W (µm)"); ax[0].set_ylabel("IL (dB/cm)"); ax[0].legend(); ax[0].grid(alpha=.3,which="both"); ax[0].set_title("IL vs SLAB_W (4.0 = slab ends at the gold)",fontsize=10.5)
ax[1].set_xlabel("SLAB_W (µm)"); ax[1].set_ylabel("Vπ·L (V·cm)"); ax[1].grid(alpha=.3); ax[1].legend(loc="lower right",ncol=3,fontsize=8,columnspacing=0.8,handlelength=1.4); ax[1].set_title("Vπ·L vs SLAB_W",fontsize=10.5)
f.suptitle("MTX tall – Chinese: etched slab, no buffer, gap 4.0 µm, WG 1.5 µm, cap 2.5 × 1.4 µm, signal 10 µm / ground 0.5 µm · FEM, mesh 1.4 (IL up to +9 % high)",fontsize=11)
f.tight_layout(); f.savefig("chinese_sweep.png",dpi=150)
