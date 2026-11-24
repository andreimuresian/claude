import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as R_, Polygon as P_
au='#f2c14e'; ox='#9ccaf2'; ln='#6b7b8c'; air='#ffffff'
G=3.5; xg=G/2; SL=0.275; B=0.10; yb=SL+B; RT=1.4; RH=0.275; bt=RH/np.tan(np.radians(60)); X=4.3; YT=2.7
def base(ax, title, sym=False, buf_fn=None):
    R=lambda x,y,w,h,c,**k: ax.add_patch(R_((x,y),w,h,fc=c,ec='k',lw=.6,**k))
    R(-X,-0.35,2*X,0.35,ox); R(-X,0,2*X,SL,ln); R(-X,SL,2*X,B,ox)
    ax.set_xlim(-X,X); ax.set_ylim(-0.35,YT); ax.set_title(title,fontsize=11); ax.set_aspect(1.0); ax.set_xlabel('x (µm)')
    return R
def rib(ax): ax.add_patch(P_([(-RT/2-bt,SL),(RT/2+bt,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
def d(ax,x0,x1,y,t,c='k',fs=8.5):
    ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8,color=c)); ax.text((x0+x1)/2,y+0.05,t,ha='center',fontsize=fs,color=c,bbox=dict(fc='w',ec='none',pad=.5,alpha=.8))
def dv(ax,x,y0,y1,t,fs=8.5,side=1):
    ax.annotate('',(x,y0),(x,y1),arrowprops=dict(arrowstyle='<->',lw=.8)); ax.text(x+0.08*side,(y0+y1)/2,t,fontsize=fs,va='center',ha='left' if side>0 else 'right',bbox=dict(fc='w',ec='none',pad=.5,alpha=.8))
f,axs=plt.subplots(2,2,figsize=(15,9)); a,b,c,dd=axs.ravel()
# A symmetric flush fill
R=base(a,'A · flush fill, SYMMETRIC (ground tongue as tall as signal)')
H=1.6; R(-xg,yb,G,H,ox); rib(a); R(xg,yb,X-xg,YT,au); R(-X,yb,X-xg,YT,au)
dv(a,0.2,yb,yb+H,'h_fill = 1.1, 1.5, 2.0, 3.0, 5.0 µm'); d(a,-xg,xg,yb+H+0.15,'GAP 3.5 µm = fill width')
a.text(xg+0.15,1.5,'signal\n10 µm tall',fontsize=9); a.text(-X+0.15,1.5,'ground\n10 µm tall\n(symmetric)',fontsize=9)
# B U-slot (actual Madrid 1: thin ground tongue)
R=base(b,'B · U-slot (Gemini 1) on Madrid 1')
H=2.0; R(-xg,yb,G,H,ox); wt=1.0; y0=SL+RH+0.2; R(-wt/2,y0,wt,yb+H-y0,air); rib(b)
R(xg,yb,X-xg,YT,au); R(-X,yb,X-xg,1.0,au)
d(b,-wt/2,wt/2,yb+H-0.35,'w_tr 0.6/1.0/1.5/2.0',fs=8); dv(b,-0.3,SL+RH,y0,'',fs=8); b.text(-0.62,y0-0.12,'floor 100 / 200 nm\nabove rib',fontsize=7.5,ha='right')
dv(b,1.5,yb,yb+H,'h 2.0',side=-1); d(b,-xg,xg,yb+H+0.15,'GAP 3.5 µm')
b.text(-X+0.15,yb+0.45,'ground tongue 1.0 µm',fontsize=8.5); b.text(-X+0.15,yb+1.3,'pillar above the tongue\nfaces air on its left',fontsize=8,color='#b03030')
# C stepped buffer
R=base(c,'C · stepped buffer under the inner electrode edge (Gemini 2a)')
ws=0.4; ts=0.2; H=1.1
for s in (1,-1):
    x0=xg if s>0 else -xg-ws; R(x0,yb,ws,ts-B,ox)
R(-xg,yb,G,H,ox); rib(c)
R(xg+ws,yb,X-xg-ws,YT,au); R(xg,SL+ts,ws,YT-SL-ts,au); R(-X,yb,X-xg-ws,1.0,au); R(-xg-ws,SL+ts,ws,1.0-(ts-B),au)
d(c,xg,xg+ws,2.35,'w_s 0.2 / 0.4 µm',fs=8); c.annotate('t_s 160 / 200 nm under the\ninner w_s of each electrode',(xg+ws/2,SL+ts-0.02),(2.45,1.0),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7),bbox=dict(fc='w',ec='none',pad=1))
c.text(2.7,0.55,'buffer 100 nm elsewhere',fontsize=8,bbox=dict(fc='w',ec='none',pad=1)); d(c,-xg,xg,yb+H+0.15,'GAP 3.5 µm (unchanged)')
# D inverted-L
R=base(dd,'D · inverted-L gold foot (Gemini 2b)')
hb=0.35; dx=0.3; H=1.1
R(-xg,yb,G,H,ox)
for s in (1,-1): R(xg if s>0 else -xg-dx,yb,dx,hb,ox)
rib(dd)
R(xg+dx,yb,X-xg-dx,hb,au); R(xg,yb+hb,X-xg,YT-yb-hb,au); R(-X,yb,X-xg-dx,hb,au); R(-X,yb+hb,X-xg,1.0-hb,au)
d(dd,xg,xg+dx,yb+hb/2,'Δx 0.15/0.30',fs=7.5); dv(dd,xg+dx+0.5,yb,yb+hb,'h_bot 0.35',fs=8)
d(dd,-xg,xg,yb+H+0.15,'GAP 3.5 µm (set by upper gold)'); dd.text(0,0.18,'bottom gap = 3.5 + 2Δx',ha='center',fontsize=8,color='w')
for ax in axs.ravel(): ax.text(-X+0.1,-0.27,'BOX',fontsize=8); ax.text(-X+0.1,0.1,'LN slab 275 nm',fontsize=7.5,color='w')
f.suptitle('Gemini-inspired variants on Madrid 1 (gap 3.5 µm, buffer 100 nm, rib 1.4 µm, 1625 nm) · true scale · cap = gap width',fontsize=12)
f.tight_layout(); f.savefig('gemini_variants_xs.png',dpi=150)
