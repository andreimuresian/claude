import json,cv2,numpy as np
V='/root/.claude/uploads/794ea706-8ddc-5fbd-854e-68a873be0346/3af847d4-videoplayback.mp4'
OUT='/home/user/claude/libretto-lotta/doppia/'
T=json.load(open('vid/tracks.json'));cap=cv2.VideoCapture(V)
# step: (t, markers [(kpindex,label)], )
STEPS=[
 (28.75,[(0,'testa'),(9,'mano'),(10,'mano'),(16,'piede avanti'),(15,'piede dietro')]),
 (29.5,[(0,'testa'),(9,'mano'),(10,'mano'),(15,'piede dietro')]),
 (30.0,[(0,'testa'),(14,'ginocchio avanti'),(15,'piede dietro')]),
 (30.5,[(0,'testa'),(9,'mano'),(10,'mano'),(15,'piede dietro')]),
 (33.0,[(0,'testa'),(9,'mano'),(10,'mano')]),
 (36.0,[(0,'testa'),(9,'mano'),(10,'mano')]),
 (46.0,[(0,'testa'),(14,'ginocchio a terra'),(15,'piede esterno'),(9,'mano'),(10,'mano')]),
 (49.5,[(0,'testa'),(14,'ginocchio'),(15,'piede esterno')]),
 (50.25,[]),
 (51.0,[]),
]
def crop_for(r,t):
    bx=[p['box'] for p in r['a'].values()]
    x0=min(b[0] for b in bx);y0=min(b[1] for b in bx);x1=max(b[2] for b in bx);y1=max(b[3] for b in bx)
    w,h=x1-x0,y1-y0;cx,cy=(x0+x1)/2,(y0+y1)/2
    H=min(360,max(h*1.18,w*1.18*3/4));W=H*4/3
    if W>640:W=640;H=480*0+W*3/4
    X0=min(max(0,cx-W/2),640-W);Y0=min(max(0,cy-H/2),360-H);return X0,Y0,W,H
meta=[]
for n,(t,mk) in enumerate(STEPS,1):
    r=min(T,key=lambda r:abs(r['t']-t));cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
    X0,Y0,W,H=crop_for(r,t);c=f[int(Y0):int(Y0+H),int(X0):int(X0+W)]
    c=cv2.resize(c,(960,720),interpolation=cv2.INTER_LANCZOS4)
    bl=cv2.GaussianBlur(c,(0,0),2);c=cv2.addWeighted(c,1.5,bl,-.5,0)
    cv2.imwrite(OUT+f's{n:02d}.jpg',c,[cv2.IMWRITE_JPEG_QUALITY,84])
    pts=[]
    if '0' in r['a']:
        kp=r['a']['0']['kp']
        for i,lab in mk:
            x,y,cf=kp[i]
            if cf>.25:pts.append({'x':round((x-X0)/W,4),'y':round((y-Y0)/H,4),'k':lab,'kp':i})
    meta.append({'n':n,'t':t,'pts':pts})
    v=c.copy()
    for j,p in enumerate(pts,1):
        cv2.circle(v,(int(p['x']*960),int(p['y']*720)),14,(0,0,255),-1);cv2.putText(v,str(j),(int(p['x']*960)-7,int(p['y']*720)+7),0,.7,(255,255,255),2)
    cv2.putText(v,f'{n}  t={t}',(8,28),0,.9,(0,255,255),2);cv2.imwrite(f'vid/v{n:02d}.jpg',v)
json.dump(meta,open('vid/steps_meta.json','w'))
ims=[cv2.resize(cv2.imread(f'vid/v{n:02d}.jpg'),(640,480)) for n in range(1,11)]
cv2.imwrite('vid/vsheet.jpg',np.vstack([np.hstack(ims[i:i+3]+([np.zeros_like(ims[0])]*(3-len(ims[i:i+3])))) for i in range(0,10,3)]))
# sprites
fps=10;t0=28.0;N=int((53.0-t0)*fps)+1;FW,FH=480,270;cols,rows=5,5;per=cols*rows
sheets=[]
for s in range((N+per-1)//per):
    sh=np.zeros((rows*FH,cols*FW,3),np.uint8)
    for k in range(per):
        i=s*per+k
        if i>=N:break
        cap.set(cv2.CAP_PROP_POS_MSEC,(t0+i/fps)*1000);ok,f=cap.read()
        if ok:sh[(k//cols)*FH:(k//cols+1)*FH,(k%cols)*FW:(k%cols+1)*FW]=cv2.resize(f,(FW,FH),interpolation=cv2.INTER_AREA)
    cv2.imwrite(OUT+f'sp{s}.jpg',sh,[cv2.IMWRITE_JPEG_QUALITY,70]);sheets.append(s)
json.dump({'t0':t0,'fps':fps,'n':N,'fw':FW,'fh':FH,'cols':cols,'rows':rows,'sheets':len(sheets)},open('vid/sprite_meta.json','w'))
print(N,len(sheets))
