import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as R_, Polygon as P_
au='#f2c14e'; ox='#9ccaf2'; ln='#6b7b8c'
SL=0.275; B=0.13; yb=SL+B; RT=1.4; RH=0.275; bt=RH/np.tan(np.radians(60)); HP=1.0; T1=1.0; TW=1.0; yfl=SL+RH+0.1; xo=1.75
def panel(ax,tl,tr,title):
    R=lambda x,y,w,h,c: ax.add_patch(R_((x,y),w,h,fc=c,ec='k',lw=.6))
    X=3.6; R(-X,-0.25,2*X,0.25,ox); R(-X,0,2*X,SL,ln); R(-X,SL,2*X,B,ox)
    R(-xo,SL,2*xo,yb+HP-SL,ox); R(-TW/2,yfl,TW,yb+HP-yfl+0.001,'#ffffff')
    ax.add_patch(P_([(-RT/2-bt,SL),(RT/2+bt,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
    R(xo,yb,X-xo,T1,au); R(xo-tr,yb+HP,X-xo+tr,3.0,au)                      # signal: layer 1 + layer 2 (tall)
    R(-X,yb,X-xo,T1,au); 
    if tl>0: R(-xo,yb+HP,tl,T1,au)                                           # ground tongue on oxide
    ax.set_xlim(-X,X); ax.set_ylim(-0.25,3.2); ax.set_aspect('equal'); ax.set_title(title,fontsize=10.5); ax.set_xlabel('x (µm)')
    def d(x0,x1,y,t,fs=8.5):
        ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8)); ax.text((x0+x1)/2,y+0.04,t,ha='center',fontsize=fs,bbox=dict(fc='w',ec='none',pad=.4,alpha=.85))
    d(-xo,xo,0.95,'oxide 3.5 µm'); gl=-xo+tl; gr=xo-tr; d(gl,gr,yb+HP+T1+0.12,f'gold gap {gr-gl:.2f} µm')
    ax.text(-X+0.1,yb+0.45,'ground\n1 µm layer',fontsize=8); ax.text(2.1,2.6,'signal\n(1 µm + 9 µm)',fontsize=8)
    ax.text(-0.45,yb+HP-0.2,'trench',fontsize=8)
f,ax=plt.subplots(1,3,figsize=(17,4.6))
panel(ax[0],0.1,0.1,'Aligned: 0.1 µm tongue on both sides')
panel(ax[1],0.0,0.2,'Misaligned → signal: 0.2 µm tongue on signal only')
panel(ax[2],0.2,0.0,'Misaligned → ground: 0.2 µm tongue on ground only')
f.suptitle('Proposed model: oxide fill 3.5 µm × 1.0 µm (= first gold layer), trench 1.0 µm, floor 100 nm, buffer 130 nm · gold tongue 1 µm thick on top of the oxide',fontsize=11)
f.tight_layout(); f.savefig('tongue_xs.png',dpi=150)
