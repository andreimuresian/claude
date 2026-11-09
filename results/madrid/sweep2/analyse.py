import json,pandas as pd,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt,numpy as np
R=[json.loads(l.split('RESULT',1)[1]) for l in open('sweep.txt') if 'RESULT' in l]
d=pd.DataFrame(R).drop_duplicates(['wl','gap','buf']);d['wl_nm']=(d.wl*1000).round().astype(int);d['buf_nm']=(d.buf*1000).round().astype(int)
d.sort_values(['wl_nm','buf_nm','gap']).to_csv('sweep2.csv',index=False)
W=sorted(d.wl_nm.unique());B=sorted(d.buf_nm.unique());cm=plt.cm.viridis(np.linspace(0,.9,len(B)))
f,ax=plt.subplots(2,3,figsize=(15,8.5),sharex=True)
for j,w in enumerate(W):
  for k,b in enumerate(B):
    s=d[(d.wl_nm==w)&(d.buf_nm==b)].sort_values('gap')
    ax[0,j].plot(s.gap,s.VpiL_Vcm,'o-',ms=3,c=cm[k],label=f'{b} nm');ax[1,j].semilogy(s.gap,s.IL_dBcm,'o-',ms=3,c=cm[k])
  ax[0,j].set_title(f'λ = {w} nm');ax[1,j].set_xlabel('gap (µm)');ax[1,j].axhline(.5,c='r',ls='--',lw=1)
ax[0,0].set_ylabel('Vπ·L (V·cm)');ax[1,0].set_ylabel('IL (dB/cm)');ax[0,0].legend(title='buffer',fontsize=8)
f.suptitle('Madrid sweep2 – ALD 40 nm, cap = gap−1.0 µm × 0.5, signal 10 µm, ground 1.0 µm');f.tight_layout();f.savefig('sweep2_vs_gap.png',dpi=130)
f,ax=plt.subplots(1,3,figsize=(15,5),sharey=True)
for j,w in enumerate(W):
  for k,b in enumerate(B):
    s=d[(d.wl_nm==w)&(d.buf_nm==b)].sort_values('gap');ax[j].semilogx(s.IL_dBcm,s.VpiL_Vcm,'o-',ms=3,c=cm[k],label=f'{b} nm')
  ax[j].set_title(f'λ = {w} nm');ax[j].set_xlabel('IL (dB/cm)');ax[j].grid(alpha=.3,which='both')
ax[0].set_ylabel('Vπ·L (V·cm)');ax[0].legend(title='buffer',fontsize=8);f.suptitle('IL–Vπ·L trade-off (points along each curve: gap 3.5→5.0 µm)');f.tight_layout();f.savefig('sweep2_tradeoff.png',dpi=130)
p=d.pivot_table(index=['wl_nm','buf_nm'],columns='gap',values=['VpiL_Vcm','IL_dBcm'])
print(d.groupby('wl_nm')[['VpiL_Vcm','IL_dBcm']].agg(['min','max']).round(3))
for w in W:
  s=d[(d.wl_nm==w)&(d.IL_dBcm<0.25)].nsmallest(1,'VpiL_Vcm');print(w,'best Vpi with IL<0.25:',s[['gap','buf_nm','VpiL_Vcm','IL_dBcm']].values.round(3))
print(d[d.gap.round(2).isin([3.5,4.0,4.5,5.0])&(d.buf_nm.isin([100,140,200]))].pivot_table(index=['wl_nm','buf_nm'],columns='gap',values=['VpiL_Vcm','IL_dBcm']).round(3).to_string())
