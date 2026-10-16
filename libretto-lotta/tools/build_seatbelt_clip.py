# Sprite del lettore del seatbelt toss: solo le ripetizioni fluide (non la parte in cui spiega).
import cv2,numpy as np,json,sys,glob,os
V,OUT=sys.argv[1],sys.argv[2]
cap=cv2.VideoCapture(V);X0,Y0,W,H=60,45,380,285
CL=[('Ripetizione 1 (veloce)',42.25,46.5),('Ripetizione 2 (laterale)',58.25,65.75)]
fps=15;FW,FH=480,360;cols=rows=5;per=25
frames=[];clips=[]
for name,a,b in CL:
    n=int((b-a)*fps);clips.append({'name':name,'t0':a,'a':len(frames),'b':len(frames)+n-1})
    for i in range(n):
        cap.set(cv2.CAP_PROP_POS_MSEC,(a+i/fps)*1000);ok,f=cap.read()
        frames.append(cv2.resize(f[Y0:Y0+H,X0:X0+W],(FW,FH),interpolation=cv2.INTER_CUBIC))
for f in glob.glob(OUT+'/sp*.jpg'):os.remove(f)
ns=(len(frames)+per-1)//per
for s in range(ns):
    sh=np.zeros((rows*FH,cols*FW,3),np.uint8)
    for k in range(per):
        i=s*per+k
        if i<len(frames):sh[(k//cols)*FH:(k//cols+1)*FH,(k%cols)*FW:(k%cols+1)*FW]=frames[i]
    cv2.imwrite(f'{OUT}/sp{s}.jpg',sh,[cv2.IMWRITE_JPEG_QUALITY,72])
json.dump({'t0':CL[0][1],'fps':fps,'n':len(frames),'fw':FW,'fh':FH,'cols':cols,'rows':rows,'sheets':ns,'clips':clips},open(OUT+'/../sprite_meta_seatbelt.json','w'))
print(len(frames),ns,clips)
