import json,numpy as np,cv2
from scipy.optimize import linear_sum_assignment as lsa
D=json.load(open('vid/kp2d.json'))
def cen(p):
    k=np.array(p['kp']);pts=[k[i][:2] for i in (5,6,11,12) if k[i][2]>.3]
    b=p['box'];return np.mean(pts,0) if len(pts)>=2 else np.array([(b[0]+b[2])/2,(b[1]+b[3])/2])
def feat(p):return np.array(cen(p))
# per frame keep up to 3 detections, drop low conf
seq=[]
for d in D:
    P=[p for p in d['P'] if p['c']>.25]
    P=sorted(P,key=lambda p:-p['c'])[:3]
    seq.append((d['t'],P))
# init at first frame with >=2 people: left is id0 (coach)
prev=None;tracks=[]
for t,P in seq:
    if prev is None:
        if len(P)>=2:
            P=sorted(P,key=lambda p:cen(p)[0]);prev=[cen(P[0]),cen(P[1])];tracks.append((t,{0:P[0],1:P[1]}))
        else:tracks.append((t,{}))
        continue
    asg={}
    if P:
        C=np.array([[np.linalg.norm(cen(p)-q) for q in prev] for p in P])
        r,c=lsa(C)
        for i,j in zip(r,c):
            if C[i,j]<260:asg[j]=P[i]
    for j,p in asg.items():prev[j]=0.5*prev[j]+0.5*cen(p)
    tracks.append((t,asg))
json.dump([{'t':t,'a':{str(k):v for k,v in a.items()}} for t,a in tracks],open('vid/tracks.json','w'))
miss=[sum(1 for t,a in tracks if k not in a and 54<=t<=70) for k in (0,1)];print('missing in 54-70',miss, 'frames',sum(1 for t,a in tracks if 54<=t<=70))
