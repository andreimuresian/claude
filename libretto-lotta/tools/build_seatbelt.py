import cv2,numpy as np,json,os
from crops import crop,cap,X0,Y0,W,H
OUT='/home/user/claude/libretto-lotta/seatbelt/';os.makedirs(OUT,exist_ok=True)
ST=[18.25,19.5,21.0,24.0,28.0,30.5,34.5,40.0,40.75,41.25,41.55,42.0]
MK={1:[(.55,.22,'testa'),(.48,.54,'mano'),(.575,.53,'mano'),(.67,.92,'piede avanti'),(.725,.915,'piede dietro')],
2:[(.49,.36,'testa')],
3:[(.575,.50,'testa'),(.63,.745,'mani'),(.73,.80,'ginocchio a terra')],
4:[(.556,.39,'testa'),(.625,.61,'mani'),(.73,.91,'piede avanti'),(.78,.93,'piede dietro')],
5:[(.5625,.36,'testa'),(.594,.64,'mano'),(.73,.91,'piede avanti'),(.79,.93,'piede dietro')],
6:[(.55,.38,'testa'),(.58,.74,'mano'),(.56,.61,'braccio dietro il ginocchio'),(.64,.92,'piede avanti'),(.78,.92,'piede dietro')],
7:[(.53,.38,'testa'),(.68,.65,'mano'),(.575,.61,'mano'),(.74,.92,'piede')],
8:[(.54,.36,'testa'),(.59,.58,'avambraccio'),(.64,.91,'piede avanti'),(.80,.91,'piede dietro')],
9:[(.50,.35,'testa'),(.68,.88,'piede che attraversa')],
10:[(.41,.51,'testa'),(.375,.90,'piede'),(.58,.92,'piede')],
11:[],12:[]}
meta=[]
for n,t in enumerate(ST,1):
    c=crop(t);cv2.imwrite(OUT+f's{n:02d}.jpg',c,[cv2.IMWRITE_JPEG_QUALITY,86])
    v=c.copy()
    for j,(x,y,k) in enumerate(MK[n],1):
        cv2.circle(v,(int(x*960),int(y*720)),14,(0,0,255),-1);cv2.putText(v,str(j),(int(x*960)-7,int(y*720)+7),0,.7,(255,255,255),2)
    cv2.putText(v,f'{n} t={t}',(8,28),0,.9,(0,255,255),2);cv2.imwrite(f'v{n:02d}.jpg',v)
    meta.append({'n':n,'t':t,'pts':[{'x':x,'y':y,'k':k} for x,y,k in MK[n]]})
json.dump(meta,open('steps_meta.json','w'))
ims=[cv2.resize(cv2.imread(f'v{n:02d}.jpg'),(640,480)) for n in range(1,13)]
cv2.imwrite('vsheet.jpg',np.vstack([np.hstack(ims[i:i+3]) for i in range(0,12,3)]))
fps=10;t0=17.0;N=int((43.0-t0)*fps)+1;FW,FH=480,360;cols,rows=5,5;per=25;ns=(N+per-1)//per
for s in range(ns):
    sh=np.zeros((rows*FH,cols*FW,3),np.uint8)
    for k in range(per):
        i=s*per+k
        if i>=N:break
        cap.set(cv2.CAP_PROP_POS_MSEC,(t0+i/fps)*1000);ok,f=cap.read()
        f=f[int(Y0):int(Y0+H),int(X0):int(X0+W)];sh[(k//cols)*FH:(k//cols+1)*FH,(k%cols)*FW:(k%cols+1)*FW]=cv2.resize(f,(FW,FH),interpolation=cv2.INTER_CUBIC)
    cv2.imwrite(OUT+f'sp{s}.jpg',sh,[cv2.IMWRITE_JPEG_QUALITY,70])
json.dump({'t0':t0,'fps':fps,'n':N,'fw':FW,'fh':FH,'cols':cols,'rows':rows,'sheets':ns},open('sprite_meta.json','w'))
print(N,ns)
