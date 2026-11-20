import json,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt;import numpy as np
from matplotlib.patches import Rectangle,Polygon
G=3.2;B=0.12;CW=3.0;CH=0.5;M=2.0;SL=0.275;RH=0.275;RT=1.4;b=RH/np.tan(np.radians(60))
au='#f2c14e';ox='#9ccaf2';ln='#6b7b8c';air='#ffffff'
def draw(ax,clad,title):
  X=7.5;ax.add_patch(Rectangle((-X,-0.8),2*X,0.8,fc=ox,ec='none'));ax.add_patch(Rectangle((-X,0),2*X,5,fc=ox if clad else air,ec='none'))
  ax.add_patch(Rectangle((-X,0),2*X,SL,fc=ln,ec='k',lw=.6));ax.add_patch(Polygon([(-RT/2-b,SL),(RT/2+b,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
  ax.add_patch(Rectangle((-X,SL),2*X,B,fc=ox,ec='k',lw=.6))
  ax.add_patch(Polygon([(-CW/2,SL+B),(-RT/2-b+0.07,SL+B),(-RT/2,SL+RH),(RT/2,SL+RH),(RT/2+b-0.07,SL+B),(CW/2,SL+B),(CW/2,SL+B+CH),(-CW/2,SL+B+CH)],fc=ox,ec='k',lw=.6))
  ax.add_patch(Polygon([(-RT/2-b,SL),(RT/2+b,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
  for s in (-1,1): ax.add_patch(Rectangle((G/2 if s>0 else -X,SL+B),X-G/2,M,fc=au,ec='k',lw=.6))
  d=lambda x0,x1,y,t,c='k': (ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.8,color=c)),ax.text((x0+x1)/2,y+0.06,t,ha='center',fontsize=8.5,color=c))
  d(-G/2,G/2,SL+B+M+0.25,f'gap {G} µm');d(-CW/2,CW/2,SL+B+CH+0.12,f'cap {CW} µm');d(-RT/2,RT/2,SL+RH+0.03,'rib 1.4',c='w')
  ax.text(G/2+0.2,SL+B+M/2,f'Au {M} µm\n(30 µm wide)',fontsize=8.5,va='center');ax.text(-X+0.2,SL/2,'LN slab 0.275 (film 0.55, etch 0.275, 60°)',fontsize=8,color='w',va='center')
  ax.text(-X+0.2,-0.4,'BOX SiO$_2$ 4.7 µm',fontsize=8);ax.text(G/2+0.2,SL+B/2,f'SiO$_2$ buffer {int(B*1e3)} nm',fontsize=7.5,va='center')
  ax.text(-CW/2+0.05,SL+B+CH-0.12,f'cap h {CH}',fontsize=7.5);ax.text(-X+0.2,4.3,'SiO$_2$ top cladding (≥15 µm in sim)' if clad else 'air',fontsize=10,weight='bold')
  if not clad: ax.annotate('air pockets\n0.1 µm',(CW/2+0.05,SL+B+0.25),(CW/2+1.2,SL+B+M+0.9),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7),color='#b03030')
  ax.set_xlim(-X,X);ax.set_ylim(-0.8,4.8);ax.set_aspect(1.4);ax.set_title(title,fontsize=10.5);ax.set_xlabel('x (µm)');ax.set_ylabel('y (µm) [vert ×1.4]')
R=[json.loads(l[7:]) for l in open('resB.txt') if l.startswith('RESULT')]
a=[r for r in R if r['clad']=='air'][0];c=sorted([r for r in R if r['clad']=='SiO2'],key=lambda r:r['buf'])
f=plt.figure(figsize=(16,9.5));g=f.add_gridspec(2,2,height_ratios=[1,0.9])
draw(f.add_subplot(g[0,0]),False,f"Madrid B (air top)  —  Vπ·L {a['VpiL_Vcm']:.3f} V·cm, IL {a['IL_dBcm']:.3f} dB/cm")
c12=[r for r in c if abs(r['buf']-0.12)<1e-6][0]
draw(f.add_subplot(g[0,1]),True,f"Madrid B buried (SiO$_2$ top)  —  Vπ·L {c12['VpiL_Vcm']:.3f} V·cm, IL {c12['IL_dBcm']:.3f} dB/cm")
ax=f.add_subplot(g[1,:]);bb=[r['buf']*1e3 for r in c]
ax.plot([r['IL_dBcm'] for r in c],[r['VpiL_Vcm'] for r in c],'o-',c='#1f6fb4',label='buried, gap 3.2 µm, buffer sweep')
for r,t in zip(c,bb): ax.annotate(f'{t:.0f} nm',(r['IL_dBcm'],r['VpiL_Vcm']),(6,4),textcoords='offset points',fontsize=8.5)
ax.plot(a['IL_dBcm'],a['VpiL_Vcm'],'s',c='k',ms=9,label='Madrid B, air top, buffer 120 nm');ax.plot(0.1895,1.8894,'*',c='#888',ms=13,label='Madrid A (ALD, gap 3.5)')
ax.axvline(.5,c='r',ls='--',lw=1);ax.set_xlabel('IL (dB/cm)');ax.set_ylabel('Vπ·L (V·cm)');ax.grid(alpha=.3);ax.legend(loc='upper right')
ax.set_title('Same gap 3.2 µm, λ = 1625 nm, no ALD: buried oxide moves the whole buffer trade-off down',fontsize=10.5)
f.tight_layout();f.savefig('madrid_B_buried.png',dpi=130)
for r in c: print(r['buf'],round(r['VpiL_Vcm'],4),round(r['IL_dBcm'],4))
