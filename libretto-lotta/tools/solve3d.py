import json,sys,numpy as np,torch
torch.set_num_threads(4)
t0,t1=float(sys.argv[1]),float(sys.argv[2]);OUT=sys.argv[3];F=float(sys.argv[4]) if len(sys.argv)>4 else 500.
CX,CY=320.,180.
TR=json.load(open('vid/tracks.json'));fr=[r for r in TR if t0<=r['t']<=t1];N=len(fr)
# COCO idx for joints: head,shL,shR,elL,elR,wrL,wrR,hipL,hipR,knL,knR,anL,anR
CO=[0,5,6,7,8,9,10,11,12,13,14,15,16]
K2=np.zeros((N,2,13,3),np.float32);box=np.zeros((N,2,4),np.float32)
for i,r in enumerate(fr):
    for k,p in r['a'].items():
        kp=np.array(p['kp'])[CO];K2[i,int(k)]=kp;box[i,int(k)]=p['box']
# lengths (cm)
UA,FA,TH,SH,SHW,HPW,NH=30.,27.,45.,44.,38.,20.,22.
J=dict(head=0,shL=1,shR=2,elL=3,elR=4,wrL=5,wrR=6,hipL=7,hipR=8,knL=9,knR=10,anL=11,anR=12)
BONES=[(1,3,UA),(3,5,FA),(2,4,UA),(4,6,FA),(7,9,TH),(9,11,SH),(8,10,TH),(10,12,SH),(1,2,SHW),(7,8,HPW),(1,7,46.),(2,8,46.),(1,8,53.5),(2,7,53.5)]
# init depth: from first 8 frames' box height (standing ~175cm)
Z0=np.zeros(2)
for p in range(2):
    hs=[box[i,p,3]-box[i,p,1] for i in range(min(8,N)) if box[i,p,3]>0];Z0[p]=F*175./np.median(hs)
Xi=np.zeros((N,2,13,3),np.float32)
for i in range(N):
    for p in range(2):
        for j in range(13):
            u,v,c=K2[i,p,j];
            if c<.05 and i>0:Xi[i,p,j]=Xi[i-1,p,j];continue
            z=Z0[p];Xi[i,p,j]=[(u-CX)*z/F,(v-CY)*z/F,z]
X=torch.tensor(Xi,requires_grad=True)
S=torch.ones(2,requires_grad=True)  # person scale
phi=torch.tensor(0.25,requires_grad=True)          # camera pitch (rad, down)
hc=torch.tensor(np.full(N,140.,np.float32),requires_grad=True)  # camera height per frame
kp=torch.tensor(K2);conf=kp[...,2].clamp(0,1);uv=kp[...,:2]
def proj(X):return torch.stack([F*X[...,0]/X[...,2].clamp(min=30)+CX,F*X[...,1]/X[...,2].clamp(min=30)+CY],-1)
def height(X):  # height above ground (cm), camera y down, z forward
    return hc[:,None,None]-X[...,1]*torch.cos(phi)-X[...,2]*torch.sin(phi)
RAD={1:6,2:6,3:5,4:5,5:4,6:4,7:9,8:9,9:7,10:7,11:5,12:5,0:10}
SEGS=[(1,3,5.5),(3,5,4.5),(2,4,5.5),(4,6,4.5),(7,9,8),(9,11,6),(8,10,8),(10,12,6)]
def mid(X,a,b):return (X[...,a,:]+X[...,b,:])/2
def samples(X):  # points + radii on the body for collision
    pts=[];rs=[]
    neck=mid(X,1,2);hipm=mid(X,7,8)
    for t in np.linspace(0,1,6):pts.append(neck*(1-t)+hipm*t);rs.append(15.)
    for a,b,r in SEGS:
        for t in (0,.5,1):pts.append(X[...,a,:]*(1-t)+X[...,b,:]*t);rs.append(r)
    pts.append(X[...,0,:]);rs.append(10.)
    return torch.stack(pts,-2),torch.tensor(rs)
def seg_dist(P,A,B):  # P [...,n,3] points; A,B [...,m,3] segment endpoints -> [...,n,m]
    AB=B-A;AP=P[...,:,None,:]-A[...,None,:,:];t=((AP*AB[...,None,:,:]).sum(-1)/(AB*AB).sum(-1)[...,None,:].clamp(min=1e-6)).clamp(0,1)
    C=A[...,None,:,:]+t[...,None]*AB[...,None,:,:];return (P[...,:,None,:]-C).norm(dim=-1)
def body_segs(X):
    neck=mid(X,1,2);hipm=mid(X,7,8)
    A=[neck,X[...,1,:],X[...,2,:]]+[X[...,a,:] for a,b,r in SEGS]
    B=[hipm,X[...,2,:],X[...,1,:]]+[X[...,b,:] for a,b,r in SEGS]
    R=[15.,6.,6.]+[r for a,b,r in SEGS]
    return torch.stack(A,-2),torch.stack(B,-2),torch.tensor(R)
def losses(stage):
    L={}
    pr=proj(X);res=(pr-uv).norm(dim=-1)/4.;L['rep']=(conf*torch.nn.functional.huber_loss(res,torch.zeros_like(res),reduction='none',delta=2.)).sum()/N*1.0
    b=0
    for a,c,l in BONES:
        d=(X[:,:,a]-X[:,:,c]).norm(dim=-1);b=b+(((d-l*S[None,:])/1.0)**2).sum()
    nh=(X[:,:,0]-mid(X,1,2)).norm(dim=-1);b=b+(((nh-NH*S[None,:])/3.)**2).sum()
    L['bone']=b/N*0.6
    sm=(X[2:]-2*X[1:-1]+X[:-2])/2.;L['smooth']=(sm**2).sum()/N*(0.15 if stage<2 else 0.25)
    h=height(X);rr=torch.tensor([RAD[j] for j in range(13)])
    L['floor']=(torch.relu(rr-h)**2).sum()/N*0.1
    sup=h[:,:,[9,10,11,12]]-rr[[9,10,11,12]];L['support']=((torch.nn.functional.softplus(-8*sup.min(-1).values)/8*0+ (sup.min(-1).values.clamp(min=0))**2).sum())/N*0.05
    L['sp2']=((sup.min(-1).values)**2).sum()/N*0.02
    L['phi']=(phi-.25)**2*50+((hc[1:]-hc[:-1])**2).sum()*.01
    L['scale']=((S-1)**2).sum()*500
    if stage>=1:
        # collisions between persons
        A0,B0,R0=body_segs(X[:,0]);A1,B1,R1=body_segs(X[:,1]);P0,r0=samples(X[:,0]);P1,r1=samples(X[:,1])
        d01=seg_dist(P0,A1,B1);d10=seg_dist(P1,A0,B0)
        c0=torch.relu(r0[None,:,None]+R1[None,None,:]-d01-3.);c1=torch.relu(r1[None,:,None]+R0[None,None,:]-d10-3.)
        L['coll']=((c0**2).sum()+(c1**2).sum())/N*0.2
        # knee bends forward (relative to horizontal facing)
        up=torch.stack([torch.zeros(1),-torch.cos(phi).reshape(1),-torch.sin(phi).reshape(1)],-1).reshape(3)
        r=X[:,:,2]-X[:,:,1];r=r-(r*up).sum(-1,keepdim=True)*up;r=r/r.norm(dim=-1,keepdim=True).clamp(min=1e-3)
        f=torch.cross(up.expand_as(r),r,dim=-1)
        kn=0
        for hip,k,an in ((7,9,11),(8,10,12)):
            v=X[:,:,k]-(X[:,:,hip]+X[:,:,an])/2;kn=kn+(torch.relu(-(v*f).sum(-1)-1.0)**2).sum()
        L['knee']=kn/N*2.0
    return L
MASK=None
opt=torch.optim.Adam([X,S,phi,hc],lr=.6)
for stage,iters in ((0,500),(1,700),(2,500),(3,500)):
    if stage==3:
        with torch.no_grad():
            hh=height(X)[:,:,[9,10,11,12]]-torch.tensor([7.,7.,5.,5.]);MASK=(hh<9).float();print('pinned contacts',int(MASK.sum()),'of',MASK.numel())
    for g in opt.param_groups:g['lr']=.6 if stage==0 else (.3 if stage==1 else .12)
    for it in range(iters):
        opt.zero_grad();L=losses(min(stage,2));tot=sum(L.values());tot.backward();opt.step()
        if it%250==0 or it==iters-1:print(stage,it,round(float(tot),1),{k:round(float(v),1) for k,v in L.items()},flush=True)
res={'t':[r['t'] for r in fr],'X':X.detach().numpy().tolist(),'phi':float(phi),'hc':hc.detach().numpy().tolist(),'S':S.detach().numpy().tolist(),'F':F}
json.dump(res,open(OUT,'w'));print('saved',OUT,'phi',float(phi),'S',S.detach().numpy())
