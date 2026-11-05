import json, numpy as np, csv
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
R=[json.loads(l.split("RESULT ")[1]) for l in open("sweep.txt") if l.startswith("RESULT")]
fails=[l for l in open("sweep.txt") if l.startswith("FAIL")]
with open("madrid_sweep.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["gap_um","buffer_nm","ald_nm","mtx_um","IL_dB_per_cm","VpiL_Vcm","neff","gamma","triangles"])
    for r in sorted(R,key=lambda r:(r["ald"],r["mtx"],r["buf"],r["gap"])):
        w.writerow([r["gap"],round(r["buf"]*1e3),round(r["ald"]*1e3),r["mtx"],f'{r["IL_dBcm"]:.4f}',f'{r["VpiL_Vcm"]:.4f}',f'{r["neff"]:.6f}',f'{r["gamma"]:.4f}',r["tri"]])
def sel(**k): return sorted([r for r in R if all(abs(r[a]-v)<1e-9 for a,v in k.items())],key=lambda r:r["gap"])
COMF=0.25; LIM=0.5
bufs=sorted({r["buf"] for r in R if r["ald"]==0.04 and r["mtx"]==2.0})
S={}
def cross(rows,thr):
    g=np.array([r["gap"] for r in rows]); il=np.array([r["IL_dBcm"] for r in rows]); v=np.array([r["VpiL_Vcm"] for r in rows])
    if il[0]<=thr: return g[0],v[0]
    if il[-1]>thr: return None
    i=np.where(il<=thr)[0][0]; t=(np.log(thr)-np.log(il[i-1]))/(np.log(il[i])-np.log(il[i-1]))
    return g[i-1]+t*(g[i]-g[i-1]), v[i-1]+t*(v[i]-v[i-1])
fig,(a1,a2)=plt.subplots(1,2,figsize=(13,4.8)); cm=plt.cm.viridis
for k,b in enumerate(bufs):
    rows=sel(buf=b,ald=0.04,mtx=2.0); 
    if len(rows)<3: continue
    c=cm(k/max(1,len(bufs)-1)); g=[r["gap"] for r in rows]
    a1.semilogy(g,[r["IL_dBcm"] for r in rows],"o-",ms=3,color=c,label=f"{b*1e3:.0f} nm")
    a2.plot(g,[r["VpiL_Vcm"] for r in rows],"o-",ms=3,color=c,label=f"{b*1e3:.0f} nm")
    S[f"buf{b*1e3:.0f}"]={"gap_at_IL0.25":cross(rows,COMF),"gap_at_IL0.5":cross(rows,LIM)}
for a in (a1,a2): a.set_xlabel("gap (µm)"); a.grid(alpha=.3); a.axvspan(2.95,3.0,color="0.85")
a1.axhline(LIM,color="r",ls="--"); a1.axhline(COMF,color="r",ls=":"); a1.text(3.92,LIM*1.06,"0.5",color="r",ha="right"); a1.text(3.92,COMF*1.06,"0.25",color="r",ha="right")
a1.set_ylabel("IL (dB/cm)"); a2.set_ylabel("Vπ·L (V·cm)"); a1.legend(title="SiO₂ buffer",fontsize=8,ncol=2)
a1.set_title("Madrid, 1625 nm, ALD 40 nm, MTX 2 µm: IL"); a2.set_title("Vπ·L")
fig.tight_layout(); fig.savefig("madrid_gap_buffer.png",dpi=160)
# Vpi vs IL trade-off (all buffers)
fig,a=plt.subplots(figsize=(7,4.8))
for k,b in enumerate(bufs):
    rows=sel(buf=b,ald=0.04,mtx=2.0)
    a.semilogx([r["IL_dBcm"] for r in rows],[r["VpiL_Vcm"] for r in rows],"o-",ms=3,color=cm(k/max(1,len(bufs)-1)),label=f"{b*1e3:.0f} nm")
a.axvline(LIM,color="r",ls="--"); a.axvline(COMF,color="r",ls=":"); a.set_xlabel("IL (dB/cm)"); a.set_ylabel("Vπ·L (V·cm)"); a.grid(alpha=.3,which="both")
a.legend(title="buffer (gap 3.0→4.0 along each line)",fontsize=8,ncol=2); a.set_title("Case b: Vπ·L–IL trade-off (each point = one gap)")
fig.tight_layout(); fig.savefig("madrid_tradeoff.png",dpi=160)
# ALD and MTX
fig,(a1,a2,a3)=plt.subplots(1,3,figsize=(15,4.3))
for T,c in ((0.0,"#888"),(0.04,"#e0218a")):
    rows=sel(buf=0.08,ald=T,mtx=2.0)
    a1.plot([r["gap"] for r in rows],[r["VpiL_Vcm"] for r in rows],"o-",ms=3,color=c,label=f"ALD {T*1e3:.0f} nm")
    a1b=a1
ax2=a1.twinx()
for T,c in ((0.0,"#888"),(0.04,"#e0218a")):
    rows=sel(buf=0.08,ald=T,mtx=2.0); ax2.semilogy([r["gap"] for r in rows],[r["IL_dBcm"] for r in rows],"s--",ms=3,color=c,alpha=.6)
a1.set_xlabel("gap (µm)"); a1.set_ylabel("Vπ·L (V·cm), solid"); ax2.set_ylabel("IL (dB/cm), dashed"); a1.legend(fontsize=8); a1.set_title("ALD on/off, buffer 80 nm")
rows=sorted([r for r in R if r["gap"]==3.5 and r["buf"]==0.08 and r["mtx"]==2.0],key=lambda r:r["ald"])
a2.plot([r["ald"]*1e3 for r in rows],[r["VpiL_Vcm"] for r in rows],"o-",color="#0E2268"); a2b=a2.twinx(); a2b.plot([r["ald"]*1e3 for r in rows],[r["IL_dBcm"] for r in rows],"s--",color="#F20013")
a2.set_xlabel("ALD thickness (nm)"); a2.set_ylabel("Vπ·L (V·cm)",color="#0E2268"); a2b.set_ylabel("IL (dB/cm)",color="#F20013"); a2.set_title("ALD sweep, gap 3.5, buffer 80 nm")
rows=sorted([r for r in R if r["gap"]==3.5 and r["buf"]==0.08 and r["ald"]==0.04],key=lambda r:r["mtx"])
a3.plot([r["mtx"] for r in rows],[r["VpiL_Vcm"] for r in rows],"o-",color="#0E2268"); a3b=a3.twinx(); a3b.plot([r["mtx"] for r in rows],[r["IL_dBcm"] for r in rows],"s--",color="#F20013")
a3.set_xlabel("gold thickness MTX (µm)"); a3.set_ylabel("Vπ·L (V·cm)",color="#0E2268"); a3b.set_ylabel("IL (dB/cm)",color="#F20013"); a3.set_title("MTX sweep, gap 3.5, buffer 80, ALD 40")
for a in (a1,a2,a3): a.grid(alpha=.3)
fig.tight_layout(); fig.savefig("madrid_ald_mtx.png",dpi=160)
S["ald_sweep"]=[(r["ald"],r["IL_dBcm"],r["VpiL_Vcm"]) for r in sorted([r for r in R if r["gap"]==3.5 and r["buf"]==0.08 and r["mtx"]==2.0],key=lambda r:r["ald"])]
S["mtx_sweep"]=[(r["mtx"],r["IL_dBcm"],r["VpiL_Vcm"]) for r in rows]
S["ald0_buf80"]=[(r["gap"],r["IL_dBcm"],r["VpiL_Vcm"]) for r in sel(buf=0.08,ald=0.0,mtx=2.0)]
S["n"]=len(R); S["fails"]=fails
json.dump(S,open("summary.json","w"),indent=1,default=float)
for b in bufs:
    print(f"buf {b*1e3:4.0f}:", "  ".join(f'{r["gap"]:.1f}:{r["IL_dBcm"]:.3f}/{r["VpiL_Vcm"]:.3f}' for r in sel(buf=b,ald=0.04,mtx=2.0)))
print({k:v for k,v in S.items() if k.startswith("buf")}); print("ALD",S["ald_sweep"]); print("MTX",S["mtx_sweep"]); print("ALD0",S["ald0_buf80"]); print(len(R),"runs", len(fails),"fails")
