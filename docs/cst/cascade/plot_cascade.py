import numpy as np, matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
exec(open('cascade_extract.py').read().split("idx=")[0])
F=f/1e9
fig,ax=plt.subplots(2,2,figsize=(11,7),sharex=True)
k=dict(lw=1.8)
for a,(i,j),nm in [(ax[0,0],(1,0),'|S21| (dB)'),(ax[0,1],(0,0),'|S11| (dB)')]:
    a.plot(F,db(S5[:,i,j]),color='#1f4e9a',label='5 mm (CST)',**k)
    a.plot(F,db(S15[:,i,j]),'--',color='#d9541e',label='1 mm × 5 cascade',**k)
    a.set_ylabel(nm);a.grid(alpha=.3);a.legend()
for a,(i,j),nm in [(ax[1,0],(1,0),'∠S21 (deg)'),(ax[1,1],(0,0),'∠S11 (deg)')]:
    u=lambda x:np.rad2deg(np.unwrap(np.angle(x))) if i==1 else np.rad2deg(np.angle(x))
    a.plot(F,u(S5[:,i,j]),color='#1f4e9a',**k);a.plot(F,u(S15[:,i,j]),'--',color='#d9541e',**k)
    a.set_ylabel(nm);a.set_xlabel('Frequency (GHz)');a.grid(alpha=.3)
fig.suptitle('Five cascaded 1 mm CST segments vs 5 mm CST line (50 Ω reference)')
fig.tight_layout();fig.savefig('cascade_1mmx5_vs_5mm.png',dpi=150)
