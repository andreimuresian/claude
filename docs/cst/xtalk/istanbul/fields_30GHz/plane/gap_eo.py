import sys, glob, re, numpy as np
sys.path.insert(0,'/home/user/claude')
from mzm_interconnect import xtalk_s4p as XS, coupled_line as CL
pr=XS.load_pair('/home/user/claude/docs/cst/xtalk/istanbul/TEST0_XTALK_SW_5mm.s4p',5.0)
out={}
for fn in sorted(glob.glob("*.txt"), key=lambda s: float(re.search(r"f(\d+)",s).group(1))):
    fG=float(re.search(r"f(\d+)",fn).group(1))
    a=np.loadtxt(fn,skiprows=2)
    ys=np.unique(np.round(a[:,1],6)); zs=np.unique(np.round(a[:,2],6))
    iy=np.searchsorted(ys,np.round(a[:,1],6)); iz=np.searchsorted(zs,np.round(a[:,2],6))
    Ey=np.zeros((len(ys),len(zs)),complex); Ey[iy,iz]=a[:,5]+1j*a[:,6]
    col=lambda yv: Ey[np.argmin(abs(ys-yv))]
    VA=0.5*(col(0.32)-col(0.305)); VB=0.5*(col(-0.305)-col(-0.32))
    CB=0.5*(col(-0.305)+col(-0.32))
    m=(zs>=0)&(zs<=5); z=zs[m]; K0=2*np.pi*fG*1e9/2.99792458e8*1e-3
    H=lambda v,ng: np.trapezoid(v[m]*np.exp(1j*K0*ng*z),z)
    rms=lambda v: np.sqrt(np.mean(abs(v[m])**2))
    row={"fields":[20*np.log10(abs(H(VB,ng)/H(VA,ng))) for ng in (2.0,2.27,2.4)],
         "single":20*np.log10(abs(H(col(-0.305),2.27)/H(col(0.305),2.27))),"cm":rms(CB)/rms(VB)}
    for v in XS.VARIANTS:
        e,o=XS.tables_on_grid(pr,np.array([fG*1e9]),v)
        b=CL.coupled_sparams(np.array([fG*1e9]),e,o,pr['L'],ng=2.27,R0=50); r=CL.terminated_response(b,50,50,50)
        row[v]=20*np.log10(abs(r['H_B'][0]/r['H_A'][0]))
    out[fG]=row
    np.savez(f"gapV_{int(fG)}.npz",z=zs,VA=VA,VB=VB,CB=CB)
print(" f GHz | fields n_g 2.0 / 2.27 / 2.4 | single arm | B common/diff | s4p Ze=Zo | s4p exact (n_g 2.27)")
for fG,r in out.items():
    print(f" {fG:5.0f} | {r['fields'][0]:6.1f} {r['fields'][1]:6.1f} {r['fields'][2]:6.1f} | {r['single']:6.1f} | {r['cm']:5.2f} | {r[XS.VARIANTS[0]]:6.1f} | {r[XS.VARIANTS[1]]:6.1f}")
