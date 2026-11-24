import json,numpy as np,sys
sys.path.insert(0,'/home/user/claude/results/field_theory');import slab1d as s1
R=[json.loads(l.split('RESULT',1)[1]) for l in open('/home/user/claude/results/madrid/sweep2/sweep.txt') if 'RESULT' in l]
nr_tab={round(w,3):np.mean([r['neff'] for r in R if abs(r['wl']-w)<1e-6]) for w in (1.525,1.575,1.625)}
W=np.array(sorted(nr_tab));N=np.array([nr_tab[w] for w in W]);pf=np.polyfit(W,N,2)
def nLN(l):
  l2=l*l;ne=np.sqrt(1+2.9804*l2/(l2-0.02047)+0.5981*l2/(l2-0.0666)+8.9543*l2/(l2-416.08));no=np.sqrt(1+2.6734*l2/(l2-0.01764)+1.2290*l2/(l2-0.05914)+12.614*l2/(l2-474.6));return ne,no
def nS(l):
  l2=l*l;return np.sqrt(1+0.6961663*l2/(l2-0.0684043**2)+0.4079426*l2/(l2-0.1162414**2)+0.8974794*l2/(l2-9.896161**2))
AU=np.array([(1.393,0.43,9.519),(1.610,0.56,11.210),(1.937,0.92,13.780)])
def eAu(l):
  E=1.239842/AU[:,0];e=(AU[:,1]-1j*AU[:,2])**2;x=1.239842/l
  return complex(np.interp(x,E[::-1],e.real[::-1]),np.interp(x,E[::-1],e.imag[::-1]))
out=[]
for wl in np.round(np.arange(1.525,1.6251,0.005),3):
  nr=np.polyval(pf,wl);ne,no=nLN(wl);ns=nS(wl);eau=eAu(wl);k0=2*np.pi/wl
  lay=lambda es,buf: [(ns**2,ns**2,0),(es,no**2,0.275)]+([(ns**2,ns**2,buf)] if buf>0 else [])+[(eau,eau,0)]
  nl=s1.solve(lay(no**2,0),k0,'TM',2.08)
  for _ in range(6):
    th=np.arccos(nr/nl.real);es=no**2*np.cos(th)**2+ne**2*np.sin(th)**2;nl=s1.solve(lay(es,0),k0,'TM',nl)
  half0=np.pi/(k0*np.sqrt(nl.real**2-nr**2))
  tb=np.arange(0,0.1201,0.001);prev=nl;nb=[]
  for t in tb:
    prev=s1.solve(lay(es,t),k0,'TM',prev);nb.append(prev.real)
  nb=np.array(nb);tc=float(np.interp(-nr,-nb,tb))
  kap={b:float(k0*np.sqrt(max(nr**2-np.interp(b,tb,nb)**2,0))) for b in (0.04,0.05,0.06,0.08,0.1)}
  out.append(dict(wl=wl,n_rib=nr,n_lat0=nl.real,period0_um=half0,tc_nm=tc*1e3,kappa=kap))
json.dump(out,open('cutoff_1d_fine.json','w'),indent=1)
for o in out[::4]: print(o['wl'],round(o['tc_nm'],1),round(o['period0_um'],3),{k:round(v,2) for k,v in o['kappa'].items()})
print('tc range',min(o['tc_nm'] for o in out),max(o['tc_nm'] for o in out))
