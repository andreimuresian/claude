import json,sys,numpy as np
from scipy.ndimage import gaussian_filter1d as gf
R=json.load(open(sys.argv[1]));OUT=sys.argv[2]
X=np.array(R['X']);ts=np.array(R['t']);phi=R['phi'];hc=np.array(R['hc']);N=len(ts)
up=np.array([0,-np.cos(phi),-np.sin(phi)]);fwd=np.array([0,-np.sin(phi),np.cos(phi)])
W=np.stack([X[...,0],X@up+hc[:,None,None],-(X@fwd)],-1)   # x right, y up, z toward camera (cm)
hipm=lambda p:(W[:,p,7]+W[:,p,8])/2
d=hipm(1)-hipm(0);ang=np.zeros(N);last=0.
for i in range(N):
    h=np.hypot(d[i,0],d[i,2])
    if h>25:last=np.arctan2(d[i,2],d[i,0])
    ang[i]=last
ang=np.unwrap(ang);ang=gf(ang,6,mode='nearest')
cen=(hipm(0)+hipm(1))/2;cen=gf(cen,3,axis=0,mode='nearest')
Wc=W-np.array([cen[:,0],np.zeros(N),cen[:,2]]).T[:,None,None,:]
e1=np.stack([np.cos(ang),np.zeros(N),np.sin(ang)],-1);e3=np.stack([-np.sin(ang),np.zeros(N),np.cos(ang)],-1)
out=np.zeros_like(W)
out[...,0]=(Wc*e1[:,None,None,:]).sum(-1);out[...,2]=(Wc*e3[:,None,None,:]).sum(-1);out[...,1]=Wc[...,1]
out=gf(out,1.0,axis=0,mode='nearest')
# ground: shift so the lowest ankle/knee of the whole clip ~ rests on floor (median of per-frame minima)
low=np.minimum(out[:,:,11:13,1].min(-1),1e9);print('ankle min per-frame median',np.median(out[:,:,[11,12],1].min(-1)).round(1))
print('shooter-coach hip dist (cm) first/mid/last',[round(float(np.hypot(*(hipm(1)-hipm(0))[i][[0,2]])),0) for i in (0,N//2,N-1)])
campos=np.stack([0*ts,hc,0*ts],-1)-np.array([cen[:,0],np.zeros(N),cen[:,2]]).T
cp=np.stack([(campos*e1).sum(-1),campos[:,1],(campos*e3).sum(-1)],-1)
ld=np.array([0,-np.sin(phi),-np.cos(phi)]);cd=np.stack([ld[2]*e3[:,0]+0*e1[:,0],0*ts+ld[1],ld[2]*e3[:,2]],-1)
cd=np.stack([(ld[2]*e3[:,0]),np.full(N,ld[1]),(ld[2]*e3[:,2])],-1)
cd=np.stack([cd[:,0]*0,cd[:,1],cd[:,2]*0],-1)
# direction in attack frame: components along e1,e3 of world direction (0,ld1,ld2) in W coords (x right, y up, z toward cam)
dW=np.array([0,ld[1],ld[2]]);dx=np.array([ (np.array([dW[0],0,dW[2]])*e1[i]).sum() for i in range(N)]);dz=np.array([ (np.array([dW[0],0,dW[2]])*e3[i]).sum() for i in range(N)])
cd=np.stack([dx,np.full(N,dW[1]),dz],-1)
json.dump({'cam':np.round(cp,1).tolist(),'camdir':np.round(cd,3).tolist(),'fps':12,'t0':float(ts[0]),'names':['head','shL','shR','elL','elR','wrL','wrR','hipL','hipR','knL','knR','anL','anR'],
 'A':np.round(out[:,0].reshape(N,-1),1).tolist(),'B':np.round(out[:,1].reshape(N,-1),1).tolist()},open(OUT,'w'))
print('saved',OUT,N)
