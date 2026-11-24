import json,numpy as np,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle as R_,Polygon as P_
plt.rcParams.update({'font.size':11,'font.family':'DejaVu Sans'})
au='#f2c14e';ox='#9ccaf2';ln='#6b7b8c'
# ---- F1 cross-section (one arm, as simulated) ----
G=3.2;B=0.10;CW=3.0;CH=0.5;MS=1.0;SL=0.275;RH=0.275;RT=1.4;b=RH/np.tan(np.radians(60));xg=G/2
f,ax=plt.subplots(figsize=(11,4.2));X0,X1=-22.5,13;YT=4.2
R=lambda x,y,w,h,c: ax.add_patch(R_((x,y),w,h,fc=c,ec='k',lw=.6))
R(X0,-0.9,X1-X0,0.9,ox);R(X0,0,X1-X0,SL,ln);R(X0,SL,X1-X0,B,ox)
R(-CW/2,SL+B,CW,CH,ox);ax.add_patch(P_([(-RT/2-b,SL),(RT/2+b,SL),(RT/2,SL+RH),(-RT/2,SL+RH)],fc=ln,ec='k',lw=.6))
R(xg,SL+B,10,YT-SL-B,au);R(-xg-10,SL+B,10,MS,au);R(-xg-20,SL+B,20-10,YT-SL-B,au)
def d(x0,x1,y,t,c='k',fs=10):
  ax.annotate('',(x0,y),(x1,y),arrowprops=dict(arrowstyle='<->',lw=.9,color=c));ax.text((x0+x1)/2,y+0.08,t,ha='center',fontsize=fs,color=c)
def dv(x,y0,y1,t,fs=10,ha='left'):
  ax.annotate('',(x,y0),(x,y1),arrowprops=dict(arrowstyle='<->',lw=.9));ax.text(x+(0.15 if ha=='left' else -0.15),(y0+y1)/2,t,fontsize=fs,va='center',ha=ha)
d(-xg,xg,2.7,'GAP 3.0–4.5 µm');d(-CW/2,CW/2,SL+B+CH+0.1,'',fs=9);ax.text(0,SL+B+CH+0.45,'CAP_W 2.8 µm → GAP',ha='center',fontsize=9,bbox=dict(fc='w',ec='none',pad=1))
dv(-xg-5,SL+B,SL+B+MS,'MTX_small\n0.5–1.0 µm',fs=9);dv(CW/2-0.15,SL+B,SL+B+CH,'',fs=9);ax.annotate('CAP_H 0.5–1.4 µm',(CW/2-0.15,SL+B+CH/2),(3.0,2.15),fontsize=9,arrowprops=dict(arrowstyle='->',lw=.7))
ax.annotate('BUFFER_H 50–200 nm (SiO$_2$)',(8.5,SL+B/2),(5.5,-0.55),fontsize=9,arrowprops=dict(arrowstyle='->',lw=.7))
d(xg,xg+10,3.6,'signal: 10 µm wide × 10 µm tall');d(-xg-10,-xg,1.75,'ground tongue 10 µm');ax.text(-xg-19.6,3.75,'ground\n10 × 10 µm',fontsize=9)
ax.text(X0+0.3,-0.6,'BOX SiO$_2$ 4.7 µm',fontsize=9);ax.text(X0+0.3,SL/2,'LN slab 275 nm (film 550, etch 275, 60°), continuous',fontsize=8.5,color='w',va='center')
ax.text(0,SL+RH+0.07,'rib 1.4',ha='center',fontsize=8,color='w')
ax.set_xlim(X0,X1);ax.set_ylim(-0.9,YT);ax.set_xlabel('x (µm)');ax.set_ylabel('y (µm)  [vertical ×2.5, gold cut at 4 µm]');ax.set_aspect(2.5)
f.tight_layout();f.savefig('F1_xs.png',dpi=200);plt.close()
# ---- F2 standing wave ----
R0=[json.loads(l[7:]) for l in open('../sweep_sw.txt') if l.startswith('RESULT')]
R5=[json.loads(l[7:]) for l in open('../sweep_sw50.txt') if l.startswith('RESULT')]
f,ax=plt.subplots(1,2,figsize=(11,4.8))
for rs,b,c,lab,mk,off in ((R0,0.0,'#c0392b','no buffer','o-',0),(R5,0.05,'#e67e22','50 nm','s--',0),(R0,0.1,'#1f4e79','100 nm','^:',0)):
  s=sorted([r for r in rs if r['buf']==b],key=lambda r:r['w_s']);w=[r['w_s'] for r in s];il=np.array([r['IL_dBcm'] for r in s])
  ax[0].plot(w,100*(il/il.mean()-1),mk,ms=4 if b else 3.5,mfc='none' if b==0.05 else c,c=c,label=f'{lab}: mean IL {il.mean():.3g} dB/cm, ripple {100*(il.max()-il.min())/il.mean():.2g} %')
  ax[1].plot([b*1e3],[il.mean()],'o',c=c,ms=9)
ax[0].set_xlabel('signal electrode width W$_S$ (µm)');ax[0].set_ylabel('IL deviation from mean (%)');ax[0].legend(fontsize=8.5,loc='upper center',bbox_to_anchor=(0.5,-0.18),ncol=1,frameon=False);ax[0].grid(alpha=.3)
ax[0].set_title('IL vs signal width: ±15 % ripple without buffer, flat with',fontsize=10.5)
ax[1].set_yscale('log');ax[1].set_xlabel('buffer (nm)');ax[1].set_ylabel('mean IL (dB/cm)');ax[1].grid(alpha=.3,which='both');ax[1].set_xlim(-10,110)
ax[1].set_title('Mean IL (gap 3.2, cap 3.0×0.5, 1625 nm)',fontsize=10.5)
f.tight_layout();f.savefig('F2_standing_wave.png',dpi=200);plt.close()
# ---- F3 wavelength ----
D=json.load(open('cutoff_1d_fine.json'));wl=np.array([o['wl'] for o in D])*1e3
f,ax=plt.subplots(1,3,figsize=(12,3.8))
ax[0].plot(wl,[o['period0_um'] for o in D],'-',c='#c0392b',lw=2);ax[0].set_ylabel('ripple period, no buffer (µm)');ax[0].set_title('Peaks move to larger W$_S$ as λ grows',fontsize=10)
ax[0].plot([1625],[0.95],'s',c='k',ms=7,label='2D (FEM) at 1625 nm');ax[0].legend(fontsize=8,loc='upper left')
ax[1].plot(wl,[o['tc_nm'] for o in D],'-',c='#1f4e79',lw=2);ax[1].set_ylim(25,45);ax[1].set_ylabel('buffer cut-off (nm)');ax[1].set_title('Cut-off flat across the band: 32.8–33.1 nm',fontsize=10)
for b,c in ((0.04,'#e67e22'),(0.05,'#2ca02c'),(0.06,'#17becf'),(0.1,'#1f4e79')):
  k=np.array([o['kappa'][str(b)] if str(b) in o['kappa'] else o['kappa'][b] for o in D]);ax[2].semilogy(wl,np.exp(-2*k*10),'-',c=c,lw=2,label=f'{int(b*1e3)} nm')
ax[2].set_ylabel('round-trip amplitude over 10 µm');ax[2].set_title('Above cut-off the wave dies before returning',fontsize=10);ax[2].legend(fontsize=7.5,loc='center',bbox_to_anchor=(0.5,0.33),ncol=4,frameon=False,handlelength=1.2,columnspacing=0.8)
for a in ax: a.set_xlabel('λ (nm)');a.grid(alpha=.3,which='both')
f.tight_layout();f.savefig('F3_wavelength.png',dpi=200);plt.close()
