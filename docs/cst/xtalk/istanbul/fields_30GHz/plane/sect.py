import sys; sys.path.insert(0,'.')
from mmp import *
# mirror y -> -y: index map
jm=np.array([np.argmin(abs(ys+yv)) for yv in ys]); assert np.allclose(ys[jm],-ys)
Ex,Ey=F[:,:,0],F[:,:,1]
S={"even":(0.5*(Ex+Ex[jm]),0.5*(Ey-Ey[jm])),    # V_A = V_B
   "odd": (0.5*(Ex-Ex[jm]),0.5*(Ey+Ey[jm]))}    # V_A = -V_B
def sec_channels(name, ysel, zr=(0.3,4.7), dec=5, norm=True):
    m=(zc>zr[0])&(zc<zr[1]); idx=np.where(m)[0][::dec]
    ch=[];info=[]
    for j in np.where(ysel(ys)&(ys>0))[0]:            # half plane suffices
        for c,arr in enumerate(S[name]):
            v=cavg(arr[j])[idx]
            if np.max(abs(v))==0: continue
            ch.append(v/(np.sqrt(np.mean(abs(v)**2)) if norm else 1)); info.append((ys[j],c))
    return zc[idx],np.array(ch),info
