import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.patches import Polygon,Rectangle
import numpy as np
GTI=3.5;P=0.5;TI=0.10;PADW=2.0;PADH=0.5;TIX=0.5;SP=1.0;BUF=0.12;BR=0.3;OW=4.0;OH=10.0;CAPH=0.5
SL=0.275;RH=0.275;RW=1.4;A=60
f,ax=plt.subplots(figsize=(16,7.5))
au='#f2c14e';ti='#d62728';ox='#cfe5f7';ln='#6b7b8c'
xL=-(GTI/2+TI*0+P+PADW+TIX+SP+OW+1.5)
ax.add_patch(Rectangle((xL,-0.6),-2*xL,0.6,fc='#e8eef3',ec='k',lw=.5));ax.text(xL+0.3,-0.35,'BOX SiO$_2$ 4.7 µm',fontsize=9)
ax.add_patch(Rectangle((xL,0),-2*xL,SL,fc=ln,ec='k',lw=.6))
b=RH/np.tan(np.radians(A))
ax.add_patch(Polygon([(-RW/2-b,SL),(RW/2+b,SL),(RW/2,SL+RH),(-RW/2,SL+RH)],fc=ln,ec='k',lw=.6))
y0=SL
for s in (-1,1):
  xi=GTI/2; xg=xi+P; xpo=xg+PADW; xto=xpo+TIX; xo=xto+SP
  R=lambda x0,x1,y,h,c,**k: ax.add_patch(Rectangle((s*x0 if s>0 else -x1,y),x1-x0,h,fc=c,ec='k',lw=.6,**k))
  R(xi,xto,y0,TI,ti)                      # Ti
  R(xto,xo+OW+1.5,y0,BUF,ox)              # buffer outside
  R(xg,xpo,y0+TI,PADH,au)                 # inner pad
  R(xpo,xo,y0+TI,PADH,ox)                 # fill between pad and tall el
  R(xg,xo,y0+TI+PADH,BR,au)               # bridge
  h=OH if s<0 else OH
  R(xo,xo+OW,y0+BUF,min(h,3.2),au)        # tall electrode (cut)
cap=Rectangle((-(GTI/2+P),y0),2*(GTI/2+P),TI+CAPH,fc=ox,ec='k',lw=.6,alpha=.9);ax.add_patch(cap)
ax.add_patch(Polygon([(-RW/2-b,SL),(RW/2+b,SL),(RW/2,SL+RH),(-RW/2,SL+RH)],fc=ln,ec='k',lw=.6))
for s in (-1,1): ax.add_patch(Rectangle((s*GTI/2 if s>0 else -GTI/2-P,y0),P,TI,fc=ti,ec='k',lw=.6))
def dim(x0,x1,y,t,c='k',fs=9):
  ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8,color=c));ax.text((x0+x1)/2,y+0.05,t,ha='center',fontsize=fs,color=c)
xi=GTI/2;xg=xi+P;xpo=xg+PADW;xto=xpo+TIX;xo=xto+SP
dim(-xi,xi,y0+TI+CAPH+0.06,f'Ti gap G$_{{Ti}}$ = {GTI} µm (sweep)',c='#b00000',fs=10)
dim(-xg,xg,1.4,f'Au gap = G$_{{Ti}}$+2·{P} = {GTI+2*P} µm',fs=10)
dim(xi,xg,y0+TI+0.08,f'{P}',c='#b00000');dim(xg,xpo,1.25,f'pad {PADW}');dim(xpo,xto,y0+TI+0.08,f'{TIX}',c='#b00000');dim(xpo,xo,0.75,f'{SP} oxide')
dim(xo,xo+OW,3.6,f'{OW} µm');
ax.text(-xi+0.2,0.55-0.2, '',fontsize=8)
ann=[(xg+0.1,y0-0.12,f'Ti {int(TI*1000)} nm on bare LN (no buffer)'),(xg+0.4,y0+TI+PADH/2,f'Au pad {PADH} µm'),(xg+0.4,y0+TI+PADH+BR/2,f'Au bridge {BR} µm'),
     (xo+OW+0.1,y0+BUF/2+0.02,f'SiO$_2$ buffer {int(BUF*1000)} nm (outside Ti only)'),(xo+0.3,2.6,f'tall Au\n{OH} µm\n(cut)'),
     (-1.6,y0+TI+CAPH-0.15,f'SiO$_2$ cap {CAPH} µm, fills Au gap'),(xL+0.3,0.12,'LN slab 0.275 µm, continuous (not etched)')]
for x,y,t in ann: ax.text(x,y,t,fontsize=8.5,va='center',color='w' if 'LN slab' in t else 'k')
for s in (-1,1): ax.add_patch(plt.Circle((s*xi,y0+TI/2),0.18,fill=False,ec='g',lw=1.5)); ax.add_patch(plt.Circle((s*xto,y0+TI/2),0.18,fill=False,ec='g',lw=1.5))
ax.text(-xo-OW/2,3.4,'SIGNAL',ha='center',fontsize=10,weight='bold');ax.text(xo+OW/2,3.4,'GROUND',ha='center',fontsize=10,weight='bold')
ax.set_xlim(xL,-xL);ax.set_ylim(-0.6,4.0);ax.set_aspect(2.2);ax.set_xlabel('x (µm)');ax.set_ylabel('y (µm)  [vertical ×2.2]')
ax.set_title('Madrid-Ti proposal, λ = 1625 nm — LN 0.55 / etch 0.275, rib top 1.4 µm, 60°  (green: Ti edges checked for reflections)')
f.tight_layout();f.savefig('madrid_ti_xs.png',dpi=140)
