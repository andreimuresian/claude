# Fireman's carry (setup): fotogrammi dei passaggi + sprite del lettore (solo le parti dimostrate, senza il parlato in primo piano)
import cv2,numpy as np,json,sys,os,glob
V,OUT=sys.argv[1],sys.argv[2];os.makedirs(OUT,exist_ok=True)
cap=cv2.VideoCapture(V)
STEPS=[76.0,90.0,102.0,107.0,118.0,126.0,138.0,152.0,186.0,196.0,207.6,223.6]
for n,t in enumerate(STEPS,1):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
    c=cv2.resize(f,(960,540),interpolation=cv2.INTER_LANCZOS4);bl=cv2.GaussianBlur(c,(0,0),2);c=cv2.addWeighted(c,1.4,bl,-.4,0)
    cv2.imwrite(f'{OUT}/s{n:02d}.jpg',c,[cv2.IMWRITE_JPEG_QUALITY,84])
CL=[('Presa e testa',74.0,119.5),('Reazione e finta',125.5,147.8),('Varianti e livello',174.8,216.8),('Il tiro',218.6,229.4)]
fps=10;FW,FH=320,180;cols=rows=8;per=64
frames=[];clips=[]
for name,a,b in CL:
    n=int((b-a)*fps);clips.append({'name':name,'t0':a,'a':len(frames),'b':len(frames)+n-1})
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_MSEC,(a+i/fps)*1000);ok,f=cap.read();frames.append(cv2.resize(f,(FW,FH),interpolation=cv2.INTER_AREA))
for f in glob.glob(OUT+'/sp*.jpg'):os.remove(f)
ns=(len(frames)+per-1)//per
for s in range(ns):
    sh=np.zeros((rows*FH,cols*FW,3),np.uint8)
    for k in range(per):
        i=s*per+k
        if i<len(frames):sh[(k//cols)*FH:(k//cols+1)*FH,(k%cols)*FW:(k%cols+1)*FW]=frames[i]
    cv2.imwrite(f'{OUT}/sp{s}.jpg',sh,[cv2.IMWRITE_JPEG_QUALITY,58])
json.dump({'t0':CL[0][1],'fps':fps,'n':len(frames),'fw':FW,'fh':FH,'cols':cols,'rows':rows,'sheets':ns,'clips':clips},open(OUT+'/sprite_meta.json','w'))
print(len(frames),ns)
