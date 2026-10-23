import sys,numpy as np
sys.path.insert(0,'/home/user/claude')
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from mzm_interconnect import coupled_line as CL
from mzm_interconnect.physics import C0
out=sys.argv[1]
db=lambda x:20*np.log10(np.abs(x)+1e-30)
p=dict(f_max_GHz=60,xt_L_mm=14.0,ng=2.27,Zs_R=50,Zs_L_pH=0,Zs_C_fF=0,Rt_R=40,Rt_L_pH=0,Rt_C_fF=0)
ds=CL.load_dataset()
plt.rcParams.update({"font.size":9,"axes.grid":True,"grid.alpha":.3})
B="#2a6fdb";O="#d98a1e";R="#d0453f";G="#6b7280"
def run(L,dz,f=None):
    q=dict(p);q["xt_L_mm"]=L;return CL.device_crosstalk(q,dz,f)
lo,hi=run(14,ds["dz_lo"]),run(14,ds["dz_hi"]);f=lo["f_GHz"]
def band(ax,a,b,c,lab):
    ya,yb=db(a),db(b);ax.fill_between(f,np.minimum(ya,yb),np.maximum(ya,yb),color=c,alpha=.4,lw=0,label=lab);ax.plot(f,yb,c=c,lw=.9)
S=lambda d,i:d["block"]["S"][i][0]
fig,axs=plt.subplots(2,2,figsize=(11,7),sharex=True)
band(axs[0,0],S(lo,2),S(hi,2),B,"NEXT |S31|");band(axs[0,0],S(lo,3),S(hi,3),O,"FEXT |S41|")
axs[0,0].set_title("(1) Electrical crosstalk, all ports 50 Ω");axs[0,0].set_ylabel("dB")
ra,rl=hi["resp"],lo["resp"];h0=abs(ra["H_A"][0])
axs[0,1].plot(f,db(ra["H_A"]/h0),c=G,lw=1.5,label="aggressor A: |H_A|");band(axs[0,1],rl["H_B"]/h0,ra["H_B"]/h0,R,"victim B: |H_B|")
axs[0,1].set_title("(2) Voltage seen by the light (device source/load)");axs[0,1].set_ylabel("dB re |H_A(f→0)|")
band(axs[1,0],rl["H_B"]/rl["H_A"],ra["H_B"]/ra["H_A"],R,"|H_B / H_A|");axs[1,0].set_title("(3) EO crosstalk = victim / aggressor modulation");axs[1,0].set_ylabel("dB")
band(axs[1,1],rl["NE_B"]/rl["V"][0],ra["NE_B"]/ra["V"][0],B,"near end V_B(0)/V_A1");band(axs[1,1],rl["FE_B"]/rl["V"][0],ra["FE_B"]/ra["V"][0],O,"far end V_B(L)/V_A1")
axs[1,1].set_title("(4) Victim terminal voltages (device source/load)");axs[1,1].set_ylabel("dB re aggressor input voltage")
for ax in axs.flat: ax.legend(fontsize=8,loc="lower right")
for ax in axs[1]: ax.set_xlabel("frequency (GHz)")
fig.suptitle("Twin, 14 mm, n_g = 2.27, source 50 Ω, load 40 Ω; band = Ze/Zo−1 from 0.30 % to 0.45 %");fig.tight_layout();fig.savefig(out+"/gui4.png",dpi=110)
# --- NEXT nulls and band
fig,ax=plt.subplots(figsize=(9,3.6))
for dz,c,ls in ((ds["dz_lo"],B,"-"),(ds["dz_hi"],"#0b2e6b","--")):
    r=run(14,dz);ax.plot(r["f_GHz"],db(r["block"]["S"][2][0]),c=c,ls=ls,lw=1.1,label=f"NEXT, δ = {dz*100:.2f} %")
r=run(14,ds["dz_hi"]);ax.plot(r["f_GHz"],db(r["block"]["S"][3][0]),c=O,lw=1.3,label="FEXT (both δ: curves overlap)")
n=1.95
for m in range(1,12): ax.axvline(m*C0/(2*n*0.014)/1e9,c="k",lw=.5,alpha=.35)
ax.set_xlabel("frequency (GHz)");ax.set_ylabel("dB");ax.set_ylim(-100,-35);ax.legend(fontsize=8,loc="lower right")
ax.set_title("14 mm: NEXT nulls at f_m = m·c/(2nL) ≈ m·5.5 GHz (n ≈ 1.95) (grey lines); the band is only the δ uncertainty")
fig.tight_layout();fig.savefig(out+"/nulls.png",dpi=110)
# --- length dependence
Ls=np.linspace(0.5,25,120);fg=np.array([10.,30.,60.])
fig,axs=plt.subplots(1,3,figsize=(12,3.8))
for fq,c in zip(fg,(B,O,R)):
    NE=[];FE=[];EO=[]
    for L in Ls:
        r=run(L,ds["dz_hi"],np.array([fq]));NE.append(db(r["block"]["S"][2][0][0]));FE.append(db(r["block"]["S"][3][0][0]));EO.append(db(r["resp"]["H_B"][0]/r["resp"]["H_A"][0]))
    gamma,Z=CL.dataset_line(np.array([fq]));dn=float(r["dn"][0]);a=gamma.real[0]
    approx=db(np.pi*fq*1e9*Ls*1e-3*dn/C0*np.exp(-a*Ls*1e-3))
    axs[0].plot(Ls,FE,c=c,lw=1.4,label=f"{fq:.0f} GHz");axs[0].plot(Ls,approx,c=c,ls=":",lw=1)
    axs[1].plot(Ls,NE,c=c,lw=1.4,label=f"{fq:.0f} GHz");axs[2].plot(Ls,EO,c=c,lw=1.4,label=f"{fq:.0f} GHz")
axs[0].set_title("FEXT vs L (dotted: π f L Δn e^{−αL}/c)");axs[1].set_title("NEXT vs L (δ = 0.45 %)");axs[2].set_title("EO crosstalk |H_B/H_A| vs L")
for ax in axs: ax.set_xlabel("electrode length L (mm)");ax.set_ylabel("dB");ax.legend(fontsize=8)
fig.tight_layout();fig.savefig(out+"/length.png",dpi=110)
# table numbers
for L in (1,5,14):
    for fq in (10,30,60):
        a=run(L,ds["dz_lo"],np.array([fq*1.]));b=run(L,ds["dz_hi"],np.array([fq*1.]))
        print(L,fq,"NEXT %.1f..%.1f FEXT %.1f..%.1f EO %.1f..%.1f dn %.5f"%(db(a["block"]["S"][2][0][0]),db(b["block"]["S"][2][0][0]),db(a["block"]["S"][3][0][0]),db(b["block"]["S"][3][0][0]),db(a["resp"]["H_B"][0]/a["resp"]["H_A"][0]),db(b["resp"]["H_B"][0]/b["resp"]["H_A"][0]),a["dn"][0]))
g,Z=CL.dataset_line(np.array([10.,30,60]));print("line n",g.imag*C0/(2*np.pi*np.array([10e9,30e9,60e9])),"alpha dB/cm",g.real*8.686/100,"Z",Z)
