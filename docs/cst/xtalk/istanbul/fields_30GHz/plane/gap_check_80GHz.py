"""
Check of the one-point gap estimate (80 GHz, line B, one 200 um cell at z = 2.4-2.6 mm,
y -0.322..-0.303 step 0.25 um, at x = 1 um and at mid-LN depth x = -0.1375 um).
Raw exports (9 MB each) not stored. Usage: python3 gap_check_80GHz.py <x1um.txt> <xLN.txt>
"""
import sys
import numpy as np
def load(p):
    a=np.loadtxt(p,skiprows=2)
    ys=np.unique(np.round(a[:,1],7)); zs=np.unique(np.round(a[:,2],7))
    iy=np.searchsorted(ys,np.round(a[:,1],7)); iz=np.searchsorted(zs,np.round(a[:,2],7))
    F=np.zeros((len(ys),len(zs),3),complex); F[iy,iz]=a[:,3::2]+1j*a[:,4::2]
    return np.unique(a[:,0]),ys,zs,F
import numpy as np
x1,ys,zs,F1=load(sys.argv[1]); xl,ys2,zs2,FL=load(sys.argv[2])
assert np.allclose(ys,ys2) and np.allclose(zs,zs2)
dy=(ys[1]-ys[0])*1e-3                                  # m
gaps={"outer":(-0.32165,-0.31750,-0.320),"inner":(-0.30750,-0.30335,-0.305)}
res={}
for g,(a,b,yc) in gaps.items():
    sel=(ys>a+1e-9)&(ys<b-1e-9)                        # grid points strictly inside the gap
    jc=np.argmin(abs(ys-yc))
    I1=np.sum(F1[sel,:,1],axis=0)*dy                   # V across the gap at x = 1 um (midpoint sum)
    IL=np.sum(FL[sel,:,1],axis=0)*dy                   # same path inside the LN
    c1=F1[jc,:,1]; cL=FL[jc,:,1]
    res[g]=dict(I1=I1,IL=IL,c1=c1,cL=cL,n=sel.sum())
for g,r in res.items():
    k=r["c1"]/r["I1"]; d=r["cL"]/r["c1"]; v=r["IL"]/r["I1"]
    print(f"{g} gap ({r['n']} points): centre/integral at x=1um: |k| mean {np.mean(abs(k)):.4e} 1/m, spread (std/mean) {np.std(abs(k))/np.mean(abs(k)):.4f}, phase spread {np.std(np.angle(k,deg=True)):.3f} deg")
    print(f"     LN centre / x=1um centre: mean {np.mean(abs(d)):.4f}, spread {np.std(abs(d))/np.mean(abs(d)):.4f}, phase spread {np.std(np.angle(d,deg=True)):.3f} deg;  LN integral / x=1um integral {np.mean(abs(v)):.4f}")
# the decisive ratios: same factors in both gaps?
k_o=res["outer"]["c1"]/res["outer"]["I1"]; k_i=res["inner"]["c1"]/res["inner"]["I1"]
print("\nk_inner / k_outer: mean %.4f, min %.4f, max %.4f, phase mean %.3f deg" % (np.mean(abs(k_i/k_o)), np.min(abs(k_i/k_o)), np.max(abs(k_i/k_o)), np.mean(np.angle(k_i/k_o,deg=True))))
# cell-averaged versions (what the EO integral sees)
avg=lambda v: np.trapezoid(v,zs)/(zs[-1]-zs[0])
for nm,num,den in (("centre x=1um / integral x=1um","c1","I1"),("centre LN / integral x=1um","cL","I1"),("integral LN / integral x=1um","IL","I1")):
    ro=avg(res["outer"][num])/avg(res["outer"][den]); ri=avg(res["inner"][num])/avg(res["inner"][den])
    print(f"cell-averaged {nm}: outer {ro:.4e}  inner {ri:.4e}  inner/outer {abs(ri/ro):.4f}, {np.angle(ri/ro,deg=True):+.3f} deg")
# push-pull vs common in this window
Vd=0.5*(res["inner"]["I1"]-res["outer"]["I1"]); Vc=0.5*(res["inner"]["I1"]+res["outer"]["I1"])
cd=0.5*(res["inner"]["c1"]-res["outer"]["c1"]); cc=0.5*(res["inner"]["c1"]+res["outer"]["c1"])
print("\nwindow: |common|/|diff| from integrals %.3f, from centre points %.3f" % (abs(avg(Vc))/abs(avg(Vd)), abs(avg(cc))/abs(avg(cd))))
