import json,numpy as np,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
R=[json.loads(l[7:]) for l in open('sweep.txt') if l.startswith('RESULT')]
S2=[json.loads(l.split('RESULT',1)[1]) for l in open('../sweep2/sweep.txt') if 'RESULT' in l]
S2=[r for r in S2 if abs(r['wl']-1.625)<1e-6]
f,ax=plt.subplots(1,3,figsize=(17,5))
col={0.05:'#1f77b4',0.1:'#d62728',0.2:'#2ca02c'}
for t,c in col.items():
  s=sorted([r for r in R if r['ti_h']==t and r['ti_p']==0.5],key=lambda r:r['gti'])
  g=np.array([r['gti'] for r in s]);il=np.array([r['IL_dBcm'] for r in s]);v=np.array([r['VpiL_Vcm'] for r in s])
  p=np.polyfit(g,np.log(il),2);res=np.log(il)-np.polyval(p,g);print(f'Ti {t*1e3:.0f} nm: max |dev| from smooth fit {100*np.abs(res).max():.2f} %')
  ax[0].semilogy(g,il,'o-',ms=3,c=c,label=f'Ti {t*1e3:.0f} nm');ax[1].plot(g,v,'o-',ms=3,c=c,label=f'Ti {t*1e3:.0f} nm')
  ax[2].semilogx(il,v,'o-',ms=3,c=c,label=f'Madrid-Ti, Ti {t*1e3:.0f} nm')
for b,ls in ((100,'-'),(200,'--')):
  s=sorted([r for r in S2 if round(r['buf']*1000)==b],key=lambda r:r['gap'])
  ax[2].semilogx([r['IL_dBcm'] for r in s],[r['VpiL_Vcm'] for r in s],ls,c='k',lw=1.5,label=f'Madrid sweep2, buffer {b} nm, ALD (gap 3.5–5.0)')
ax[2].plot(0.1895,1.8894,'k*',ms=12,label='Madrid A (ALD, gap 3.5, cap gap−0.2)')
ax[2].plot(0.2134,1.8539,'kP',ms=10,label='Madrid B (no ALD, gap 3.2)')
for a in ax[:2]: a.set_xlabel('Ti gap (µm)'); a.grid(alpha=.3,which='both')
ax[0].axhline(.5,c='r',ls='--',lw=1);ax[2].axvline(.5,c='r',ls='--',lw=1)
ax[0].set_ylabel('IL (dB/cm)');ax[1].set_ylabel('Vπ·L (V·cm)');ax[2].set_xlabel('IL (dB/cm)');ax[2].set_ylabel('Vπ·L (V·cm)')
ax[0].set_title('IL vs Ti gap (smooth: no standing wave)');ax[1].set_title('Vπ·L vs Ti gap');ax[2].set_title('Trade-off vs Madrid');ax[2].grid(alpha=.3,which='both')
ax[0].legend();ax[2].legend(fontsize=7.5,loc='upper right')
f.suptitle('Madrid-Ti, λ = 1625 nm, no ALD, protrusion 0.5 µm, Ti n = 3.7+4.4i (ASSUMED)');f.tight_layout();f.savefig('madrid_ti_sweep.png',dpi=130)
f,ax=plt.subplots(1,2,figsize=(11,4.2))
s=sorted([r for r in R if r['gti']==4.0 and r['ti_p']==0.5],key=lambda r:r['ti_h'])
t=[r['ti_h']*1e3 for r in s];ax[0].plot(t,[r['IL_dBcm'] for r in s],'o-',c='#d62728');ax[0].set_ylabel('IL (dB/cm)',color='#d62728')
a2=ax[0].twinx();a2.plot(t,[r['VpiL_Vcm'] for r in s],'s--',c='k');a2.set_ylabel('Vπ·L (V·cm)');ax[0].set_xlabel('Ti thickness (nm)');ax[0].set_title('Ti thickness, Ti gap 4.0 µm')
s=sorted([r for r in R if r['gti']==4.0 and r['ti_h']==0.1],key=lambda r:r['ti_p'])
p=[r['ti_p'] for r in s];ax[1].plot(p,[r['IL_dBcm'] for r in s],'o-',c='#d62728');ax[1].set_ylabel('IL (dB/cm)',color='#d62728');ax[1].set_ylim(2.5,3.3)
a3=ax[1].twinx();a3.plot(p,[r['VpiL_Vcm'] for r in s],'s--',c='k');a3.set_ylabel('Vπ·L (V·cm)');ax[1].set_xlabel('Ti protrusion beyond Au (µm)');ax[1].set_title('Protrusion, Ti gap 4.0 µm, Ti 100 nm')
f.tight_layout();f.savefig('madrid_ti_thick_protr.png',dpi=130)
