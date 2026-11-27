import numpy as np, json
rng=np.random.default_rng(7)
LO=np.array([3.0,0.05,0.0,0.5,0.5,1.0]); HI=np.array([4.5,0.20,1.0,1.4,1.0,1.5])
old=[]
for l in open("../sweep_gp.txt"):
    if l.startswith("RESULT"):
        r=json.loads(l[7:]); old.append([r["gap"],r["buf"],(r["gap"]-r["cap_w"])/(r["gap"]-2.8),r["cap_h"],r["mtx_small"],1.4])
old=(np.clip(np.array(old),LO,HI)-LO)/(HI-LO)
# 16 half-fraction corners at WG=1.0 (x5 = x1*x2*x3*x4)
import itertools
cor=[]
for b in itertools.product([0,1],repeat=4):
    s=[2*v-1 for v in b]; cor.append(list(b)+[int((np.prod(s)+1)/2),0])
cor=np.array(cor,float)
base=np.vstack([old,cor]); best=None
def lhs(n): return (np.argsort(rng.random((6,n)),axis=1).T+rng.random((n,6)))/n
for _ in range(3000):
    c=lhs(60); P=np.vstack([base,c]); D=np.linalg.norm(c[:,None,:]-P[None,:,:],axis=2); D[D==0]=9
    s=D.min()
    if best is None or s>best[0]: best=(s,c)
new=best[1]; print("min dist",best[0])

# validation: 8 points LHS
val=(np.argsort(rng.random((6,8)),axis=1).T+rng.random((8,6)))/8
def jobs(U,tag):
    X=LO+U*(HI-LO); out=[]
    for g,b,f,ch,ms,wg in X:
        cw=g-f*(g-2*wg); out.append(f"{wg:.4f} {g:.4f} {b:.4f} {cw:.4f} {ch:.4f} {ms:.4f} 10.0 {tag}")
    return out
L=jobs(cor,"corner")+jobs(new,"lhs")+jobs(val,"val")
open("jobs_wg.txt","w").write("\n".join(L)+"\n"); print(len(L)); print("WG of new:",np.round(np.sort(LO[5]+new[:,5]*0.5),2))
