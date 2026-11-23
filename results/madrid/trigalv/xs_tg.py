import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
from matplotlib.patches import Rectangle as R_,Polygon as P_
GAL=3.5;P=2.0;B=0.12;AL=0.4;CAPH=0.6;TOX=0.1;AU1=2.0;SB=5.0;AU2=10.0;SL=0.275;RH=0.275;RT=1.4;b=RH/np.tan(np.radians(60))
ox='#9ccaf2';au='#f2c14e';al='#a99bbf';ln='#6b7b8c'
xa=GAL/2;xg=xa+P;x2=xg+SB
def draw(ax,X,Y,full):
  R=lambda x,y,w,h,c,**k: ax.add_patch(R_((x,y),w,h,fc=c,ec='k',lw=.5,**k))
  R(-X,-0.6,2*X,0.6,ox);R(-X,0,2*X,SL,ln);ax.add_patch(P_([(-RT/2-b,SL),(RT/2+b,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.5))
  # conformal buffer: slab top + rib
  buf=[(-X,SL),(-RT/2-b,SL),(-RT/2,SL+RH),(RT/2,SL+RH),(RT/2+b,SL),(X,SL),(X,SL+B),(RT/2+b+B*0.58,SL+B),(RT/2+B*0.27,SL+RH+B),(-RT/2-B*0.27,SL+RH+B),(-RT/2-b-B*0.58,SL+B),(-X,SL+B)]
  ax.add_patch(P_(buf,fc=ox,ec='k',lw=.5))
  yb=SL+B;R(-xa,yb,2*xa,CAPH,ox)
  ax.add_patch(P_([(-RT/2-b,SL),(RT/2+b,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.5))
  for s in (-1,1):
    f=lambda x0,x1:(x0,x1-x0) if s>0 else (-x1,x1-x0)
    x,w=f(xa,X);R(x,yb,w,AL,al)
    x,w=f(xa,xg);R(x,yb+AL,w,TOX,ox)
    x,w=f(xg,X);R(x,yb+AL,w,AU1,au)
    x,w=f(x2,X);R(x,yb+AL+AU1,w,min(AU2,Y-(yb+AL+AU1)-0.05),au)
  def d(x0,x1,y,t,c='k',fs=8.5):
    ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8,color=c));ax.text((x0+x1)/2,y+0.05*(Y/4),t,ha='center',fontsize=fs,color=c)
  if full:
    d(-xg,xg,yb+AL+AU1-0.5,f'Au1 gap = G$_{{Al}}$+2P = {GAL+2*P} µm');d(-x2,x2,yb+AL+AU1+1.2,f'Au2 gap = Au1 gap + 2·{SB} = {GAL+2*P+2*SB} µm')
    ax.text(x2+0.5,yb+AL+AU1+1.5,f'Au2 (3rd metal) {AU2} µm\n(cut)',fontsize=9);ax.text(xg+0.5,yb+AL+AU1/2,f'Au1 (2nd metal) {AU1} µm',fontsize=9,va='center')
    ax.text(-X+0.5,-0.35,'BOX SiO$_2$ 4.7 µm',fontsize=8.5);ax.text(-X+0.5,yb+AL+AU1/2,'Au1/Au2 extend 30 µm (sim)',fontsize=8.5)
  else:
    d(-xa,xa,yb+CAPH+0.12,f'Al gap G$_{{Al}}$ = cap width = {GAL} µm',c='#5b3f8c',fs=9.5)
    d(xa,xg,yb+AL+TOX+0.12,f'buried Al protrusion P = {P} µm',fs=9)
    d(-RT/2,RT/2,SL+RH+B+0.04,'rib 1.4',fs=8)
    for t,x,y in [(f'Al (1st metal) {int(AL*1e3)} nm, on buffer, continues under Au1',-X+0.15,yb+AL/2),(f'top SiO$_2$ {int(TOX*1e3)} nm',xa+0.15,yb+AL+TOX/2+0.0),
                  (f'SiO$_2$ cap {CAPH} µm tall (top {CAPH-AL:.1f} µm above Al)',-xa+0.1,yb+CAPH-0.08),(f'conformal SiO$_2$ buffer {int(B*1e3)} nm (0 = no-buffer case)',-X+0.15,yb-0.05),
                  ('LN film 0.55, etch 0.275, 60°, slab continuous',-X+0.15,SL/2)]:
      ax.text(x,y,t,fontsize=8,va='center',color='w' if 'LN' in t else 'k')
    ax.text(xg+0.15,yb+AL+0.35,'Au1',fontsize=9)
  ax.set_xlim(-X,X);ax.set_ylim(-0.6,Y)
f,(a1,a2)=plt.subplots(2,1,figsize=(15,10),gridspec_kw=dict(height_ratios=[1,1.1]))
draw(a1,16,5.5,True);a1.set_title('Madrid tri-galvanic, buffered (λ = 1625 nm) — full view',fontsize=11);a1.set_ylabel('y (µm)')
draw(a2,5.2,1.9,False);a2.set_title('Zoom on the gap (vertical exaggerated)',fontsize=11);a2.set_xlabel('x (µm)');a2.set_ylabel('y (µm)')
f.tight_layout();f.savefig('madrid_trigalv_xs.png',dpi=140)
