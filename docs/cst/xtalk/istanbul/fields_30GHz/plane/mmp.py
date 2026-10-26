import numpy as np
d=np.load("plane.npz"); ys,zs,F=d["ys"],d["zs"],d["F"]
K0=2*np.pi*30e9/2.99792458e8*1e-3
W=40                                  # 200 um cell = 40 samples
def cavg(v): return np.convolve(v,np.ones(W)/W,mode="valid")
zc=cavg(zs)
def channels(ysel, comps=(0,1), norm=True, zr=(0.3,4.7), dec=5):
    m=(zc>zr[0])&(zc<zr[1]); idx=np.where(m)[0][::dec]
    ch=[];info=[]
    for j in np.where(ysel(ys))[0]:
        for c in comps:
            v=cavg(F[j,:,c])[idx]
            if np.max(abs(v))==0: continue
            ch.append(v/(np.sqrt(np.mean(abs(v)**2)) if norm else 1)); info.append((ys[j],c))
    return zc[idx], np.array(ch), info
def mmp(ch, dz, M, Lp=None):
    N=ch.shape[1]; Lp=Lp or N//2
    H=np.vstack([np.array([v[i:i+Lp+1] for i in range(N-Lp)]) for v in ch])
    _,S,Vh=np.linalg.svd(H,full_matrices=False)
    V=Vh[:M].T
    lam=np.linalg.eigvals(np.linalg.pinv(V[:-1])@V[1:])
    s=np.log(lam)/dz
    Z=np.exp(np.outer(np.arange(N)*dz,s))
    R,*_=np.linalg.lstsq(Z,ch.T,rcond=None)          # amplitudes per channel
    err=np.linalg.norm(Z@R-ch.T)/np.linalg.norm(ch)
    return s,R,err,S
