"""Merge E (planes/) and H (hplanes/) on the common grid z = 0..5 mm; save one npz per frequency."""
import glob, re, sys, numpy as np
S="/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad"
def load(fn):
    a=np.loadtxt(fn,skiprows=2)
    ys=np.unique(np.round(a[:,1],6)); zs=np.unique(np.round(a[:,2],6))
    iy=np.searchsorted(ys,np.round(a[:,1],6)); iz=np.searchsorted(zs,np.round(a[:,2],6))
    F=np.zeros((len(ys),len(zs),3),complex); F[iy,iz]=a[:,3::2]+1j*a[:,4::2]
    return ys,zs,F
fE={float(re.search(r"_f(\d+)[._]",f).group(1)):f for f in glob.glob(S+"/planes/*.txt")}
fH={float(re.search(r"_f(\d+)[._]",f).group(1)):f for f in glob.glob(S+"/hplanes/*.txt")}
for fG in sorted(fH):
    ye,ze,E=load(fE[fG]); yh,zh,H=load(fH[fG])
    assert np.allclose(ye,yh)
    k=np.searchsorted(ze,zh[0]); assert np.allclose(ze[k:k+len(zh)],zh), (ze[k],zh[0])
    np.savez_compressed(f"{S}/eh/eh_{int(fG)}.npz",ys=yh,zs=zh,E=E[:,k:k+len(zh)],H=H)
    print(fG,"GHz: ny",len(yh),"nz",len(zh),zh[0],zh[-1],"|H| max",np.abs(H).max())
