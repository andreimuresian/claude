"""FEXT/NEXT from the 30 GHz CST port-mode data (modes 5, 6 = CPW even/odd pair),
compared with the 3-D .s4p files. Assumptions: lossless, n_eff constant vs f,
per-line impedance = 2 x CST Z-line (mode spread over two lines), which of
mode 5/6 is even is unknown (the magnitudes below do not depend on it)."""
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from first_look_lib import load4
c=299792458; k30=2*np.pi*30e9/c
modes={"5":(1186.97/k30,2*17.3801),"6":(1186.02/k30,2*17.1815)}
def line2(f,n,Z,L,z0=50):
    t=np.exp(-2j*np.pi*f*n*L/c); r=(Z-z0)/(Z+z0)
    d=1-r**2*t**2; return r*(1-t**2)/d, (1-r**2)*t/d     # S11, S21
def xt(f,L,nshift=0.0,sameZ=False):
    (na,Za),(nb,Zb)=modes["5"],modes["6"]
    if sameZ: Za=Zb=(Za+Zb)/2
    s11a,s21a=line2(f,na+nshift,Za,L); s11b,s21b=line2(f,nb+nshift,Zb,L)
    return 0.5*(s11a-s11b), 0.5*(s21a-s21b), 0.5*(s21a+s21b)
db=lambda x:20*np.log10(np.abs(x)+1e-30)
cases=[("LINEA0_1MM_200UM_PITCH.s4p",1e-3),("LINEA0_5MM_200UM_PITCH.s4p",5e-3)]
fig,axs=plt.subplots(2,2,figsize=(12,8),sharex=True)
for j,(fn,L) in enumerate(cases):
    f,S=load4(fn); f=f[1:]; S=S[1:]
    nx,fx,th=xt(f,L); nx2,fx2,_=xt(f,L,sameZ=True)
    for i,(cst,mod,mod2,name) in enumerate([(S[:,2,0],nx,nx2,"NEXT |S31|"),(S[:,3,0],fx,fx2,"FEXT |S41|")]):
        a=axs[i,j]; a.plot(f/1e9,db(cst),"k",lw=2,label="CST 3-D .s4p")
        a.plot(f/1e9,db(mod),"C3",label="modal, CST Z-line difference (1.2 %)")
        a.plot(f/1e9,db(mod2),"C0--",label="modal, equal impedances (index difference only)")
        a.set_title(f"{name}, L = {L*1e3:.0f} mm"); a.set_ylim(-120,-20); a.grid(alpha=.3)
        for g in (10,30,60):
            k=np.argmin(abs(f-g*1e9)); print(f"{L*1e3:.0f}mm {name[:4]} {g}GHz CST {db(cst[k]):6.1f}  modal {db(mod[k]):6.1f}  sameZ {db(mod2[k]):6.1f}")
axs[0,0].legend(fontsize=8); [a.set_xlabel("GHz") for a in axs[1]]
fig.tight_layout(); fig.savefig("modal_vs_s4p.png",dpi=110)
