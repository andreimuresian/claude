import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as R_, Polygon as P_
au='#f2c14e'; ox='#9ccaf2'; ln='#6b7b8c'
G=3.5; xg=G/2; SL=0.275; B=0.13; yb=SL+B; RT=1.4; RH=0.275; bt=RH/np.tan(np.radians(60)); H=2.0; TW=1.0; TF=0.10; MS=1.0
ytop=yb+H; yfl=SL+RH+TF
def draw(ax,X0,X1,Y1,full):
    R=lambda x,y,w,h,c: ax.add_patch(R_((x,y),w,h,fc=c,ec='k',lw=.6))
    R(X0,-0.6,X1-X0,0.6,ox); R(X0,0,X1-X0,SL,ln); R(X0,SL,X1-X0,B,ox)
    R(-xg,SL,G,yb+H-SL,ox); R(-TW/2,yfl,TW,ytop-yfl+0.001,'#ffffff')
    ax.add_patch(P_([(-RT/2-bt,SL),(RT/2+bt,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
    R(xg,yb,10,Y1,au); R(-xg-10,yb,10,MS,au); R(-xg-20,yb,10,Y1,au)
    ax.set_xlim(X0,X1); ax.set_ylim(-0.6 if full else -0.15,Y1); ax.set_xlabel('x (µm)'); ax.set_ylabel('y (µm)')
def d(ax,x0,x1,y,t,fs=9,c='k'):
    ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8,color=c)); ax.text((x0+x1)/2,y+0.04,t,ha='center',va='bottom',fontsize=fs,color=c,bbox=dict(fc='w',ec='none',pad=.6,alpha=.85))
def dv(ax,x,y0,y1,t,fs=9,ha='left'):
    ax.annotate('',(x,y0),(x,y1),arrowprops=dict(arrowstyle='<->',lw=.8)); ax.text(x+(0.06 if ha=='left' else -0.06),(y0+y1)/2,t,fontsize=fs,va='center',ha=ha,bbox=dict(fc='w',ec='none',pad=.6,alpha=.85))
f,(a,b)=plt.subplots(2,1,figsize=(14,10.5),gridspec_kw=dict(height_ratios=[1,1.35]))
draw(a,-22.5,13,4.6,True)
a.set_aspect(1.6); a.set_title('Madrid 1 · U-slot · gap 3.5 µm  (full view, vertical ×1.6, gold cut at 4.6 µm)',fontsize=11)
d(a,xg,xg+10,4.1,'signal 10 µm wide × 10 µm tall'); d(a,-xg-10,-xg,1.75,'ground tongue 10 µm wide, MTX_small 1.0 µm'); d(a,-xg-20,-xg-10,4.1,'ground 10 µm × 10 µm')
a.text(-22.2,-0.35,'BOX SiO$_2$ 4.7 µm',fontsize=9); a.text(-22.2,0.1,'LN slab 275 nm (continuous)',fontsize=8.5,color='w')
draw(b,-3.2,3.2,2.75,False); b.set_aspect(1.0); b.set_title('Zoom on the gap (true scale)',fontsize=11)
d(b,-xg,xg,ytop+0.1,'GAP 3.5 µm = oxide fill width')
dv(b,-2.05,yb,ytop,'fill 2.0 µm\nabove buffer',ha='right'); d(b,-TW/2,TW/2,1.6,'air trench 1.0 µm')
dv(b,0.0,SL+RH,yfl,'',fs=8); b.annotate('trench floor 100 nm above rib top\n(etch stop on 100 nm oxide over rib)',(0.05,yfl-0.05),(0.8,0.95),fontsize=8.5,arrowprops=dict(arrowstyle='->',lw=.7),bbox=dict(fc='w',ec='none',pad=1))
dv(b,2.6,SL,yb,'',fs=8); b.text(2.65,yb+0.12,'buffer 130 nm',fontsize=9,bbox=dict(fc='w',ec='none',pad=1))
d(b,-RT/2,RT/2,SL+RH-0.17,'rib 1.4',fs=8,c='w'); b.text(-2.95,0.11,'LN 550 / etch 275 nm, 60°',fontsize=8,color='w')
b.text(-1.72,1.65,'SiO$_2$\npillar',fontsize=9,ha='left'); b.text(1.0,1.65,'SiO$_2$\npillar',fontsize=9)
b.text(-3.15,0.95,'ground\ntongue',fontsize=9); b.text(1.95,2.3,'signal (tall)',fontsize=9)
txt=("FEM, λ = 1625 nm, no ALD\n"
     "Vπ·L = 1.782 V·cm   IL = 0.189 dB/cm\n"
     "buffer −40 nm (90 nm): 1.729 V·cm / 0.323 dB/cm\n"
     "vs. no-slot robust (buffer 115 nm): 1.880 / 0.192  →  −5.2 %")
f.text(0.5,0.015,txt,ha='center',fontsize=10.5,family='monospace',bbox=dict(fc='#eaf0f7',ec='#1f4e79',pad=6))
f.tight_layout(rect=(0,0.08,1,1)); f.savefig('madrid1_uslot_xs.png',dpi=160)
