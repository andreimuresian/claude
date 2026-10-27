import glob, re, numpy as np
S="/tmp/claude-0/-home-user-claude/7930b8bd-7239-59e6-a8de-284bb11bf7ea/scratchpad"
def load(fn):
    a=np.loadtxt(fn,skiprows=2)
    ys=np.unique(np.round(a[:,1],6)); zs=np.unique(np.round(a[:,2],6))
    iy=np.searchsorted(ys,np.round(a[:,1],6)); iz=np.searchsorted(zs,np.round(a[:,2],6))
    F=np.zeros((len(ys),len(zs),3),complex); F[iy,iz]=a[:,3::2]+1j*a[:,4::2]
    return ys,zs,F
for fG in (10,20,30,45,60,80):
    ye,ze,E=load(f"{S}/f3mm/e-field (f={fG}.0000) [1].txt"); yh,zh,H=load(f"{S}/f3mm/h-field (f={fG}.0000) [1].txt")
    assert np.allclose(ye,yh) and np.allclose(ze,zh)
    np.savez_compressed(f"{S}/eh/eh3_{fG}.npz",ys=ye,zs=ze,E=E,H=H); print(fG,"ok",E.shape)
