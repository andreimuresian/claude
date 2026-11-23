import json,numpy as np,matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
R=[json.loads(l[7:]) for l in open('sweep.txt') if l.startswith('RESULT')]
q=lambda **k:sorted([r for r in R if all(abs(r[a]-v)<1e-9 for a,v in k.items())],key=lambda r:r[[a for a in ('g_al','buf','tox','p') if a not in k][0]])
f,ax=plt.subplots(2,2,figsize=(15,10))
a=ax[0,0]
for t,c in ((0.1,'#5b3f8c'),(0.3,'#c77dff')):
  s=q(buf=0.12,tox=t,p=2.0);a.semilogy([r['g_al'] for r in s],[r['IL_dBcm'] for r in s],'o-',ms=3,c=c,label=f'IL, top SiO2 {int(t*1e3)} nm')
s=q(buf=0.0,tox=0.2,p=2.0);a.semilogy([r['g_al'] for r in s],[r['IL_dBcm'] for r in s],'s-',ms=3,c='#d62728',label='IL, NO buffer')
a.axhline(.5,c='r',ls='--',lw=1);a.set_xlabel('Al gap (µm)');a.set_ylabel('IL (dB/cm)');a.grid(alpha=.3,which='both')
b=a.twinx()
for t,c in ((0.1,'#5b3f8c'),(0.3,'#c77dff')):
  s=q(buf=0.12,tox=t,p=2.0);b.plot([r['g_al'] for r in s],[r['VpiL_Vcm'] for r in s],'--',c=c)
b.set_ylabel('Vπ·L (V·cm), dashed');a.legend(fontsize=8,loc='lower left');a.set_title('Al gap sweep (buffer 120 nm, P 2.0 µm)')
a=ax[0,1];s=q(g_al=3.5,buf=0.12,p=2.0);t=[r['tox']*1e3 for r in s]
a.plot(t,[r['VpiL_Vcm'] for r in s],'o-',c='k');a.set_ylabel('Vπ·L (V·cm)');a.set_xlabel('top SiO2 thickness (nm), 0 = air');a.set_ylim(1.90,1.98)
b=a.twinx();b.plot(t,[r['IL_dBcm'] for r in s],'s--',c='#5b3f8c');b.set_ylabel('IL (dB/cm)',color='#5b3f8c');b.set_ylim(0.19,0.25)
a.set_title('Top oxide: < 0.7 % effect (Al gap 3.5, buffer 120 nm)');a.grid(alpha=.3)
a=ax[1,0]
s=q(g_al=3.5,buf=0.12,tox=0.2);a.plot([r['p'] for r in s],[r['IL_dBcm'] for r in s],'o-',ms=3,c='#5b3f8c',label='buffer 120 nm, Al gap 3.5')
s=q(g_al=4.5,buf=0.0,tox=0.2);a.plot([r['p'] for r in s],[r['IL_dBcm'] for r in s],'s-',ms=4,c='#d62728',label='NO buffer, Al gap 4.5')
a.set_xlabel('buried Al protrusion P (µm)');a.set_ylabel('IL (dB/cm)');a.set_title('Protrusion: flat with buffer, resonant without');a.grid(alpha=.3);a.legend()
a=ax[1,1]
s=q(buf=0.12,tox=0.1,p=2.0);a.semilogx([r['IL_dBcm'] for r in s],[r['VpiL_Vcm'] for r in s],'o-',ms=3,c='#5b3f8c',label='tri-galvanic, Al gap 3.0–4.5 (buf 120)')
s=q(g_al=3.5,tox=0.2,p=2.0);s=[r for r in s if r['buf']>0];a.semilogx([r['IL_dBcm'] for r in s],[r['VpiL_Vcm'] for r in s],'^-',ms=4,c='#9d7cd8',label='tri-galvanic, buffer 100–200 (gap 3.5)')
s=q(buf=0.0,tox=0.2,p=2.0);a.semilogx([r['IL_dBcm'] for r in s],[r['VpiL_Vcm'] for r in s],'s-',ms=3,c='#d62728',label='tri-galvanic NO buffer, gap 4.0–5.0')
B=[json.loads(l[7:]) for l in open('../buried/resB.txt') if l.startswith('RESULT') and '"SiO2"' in l];B=sorted(B,key=lambda r:r['buf'])
a.semilogx([r['IL_dBcm'] for r in B],[r['VpiL_Vcm'] for r in B],'D-',ms=4,c='#1f6fb4',label='Madrid B buried, gap 3.2, buffer 120–200')
S2=[json.loads(l.split('RESULT',1)[1]) for l in open('../sweep2/sweep.txt') if 'RESULT' in l];S2=sorted([r for r in S2 if abs(r['wl']-1.625)<1e-6 and abs(r['buf']-0.1)<1e-6],key=lambda r:r['gap'])
a.semilogx([r['IL_dBcm'] for r in S2],[r['VpiL_Vcm'] for r in S2],'-',c='#888',label='Madrid sweep2 (ALD, cap gap−1, buf 100)')
a.plot(0.1895,1.8894,'*',c='k',ms=12,label='Madrid A');a.plot(0.2095,1.8545,'P',c='k',ms=10,label='Madrid B (air)')
a.axvline(.5,c='r',ls='--',lw=1);a.set_xlim(0.01,7);a.set_ylim(1.65,2.55);a.set_xlabel('IL (dB/cm)');a.set_ylabel('Vπ·L (V·cm)');a.grid(alpha=.3,which='both');a.legend(fontsize=7.5,loc='upper right')
a.set_title('Trade-off vs Madrid designs')
f.suptitle('Madrid tri-galvanic (Al 400 nm + Au 2 µm + Au 10 µm), λ = 1625 nm, no ALD, cap 0.6 µm, Al n = 1.55+16i (assumed)');f.tight_layout();f.savefig('madrid_trigalv_results.png',dpi=125)
