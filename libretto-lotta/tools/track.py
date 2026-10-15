import cv2,json,time
from ultralytics import YOLO
m=YOLO('models/yolo11x-pose.pt')
V='/root/.claude/uploads/794ea706-8ddc-5fbd-854e-68a873be0346/3af847d4-videoplayback.mp4'
cap=cv2.VideoCapture(V);fps=cap.get(cv2.CAP_PROP_FPS);N=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
out=[];t0=time.time();i=0
while True:
    ok,f=cap.read()
    if not ok:break
    if i%2==0:
        r=m.predict(f,imgsz=960,conf=.12,verbose=False)[0]
        P=[]
        for b,k in zip(r.boxes,r.keypoints):
            P.append({'box':[round(float(x),1) for x in b.xyxy[0]],'c':round(float(b.conf),3),'kp':[[round(float(x),1),round(float(y),1),round(float(c),2)] for (x,y),c in zip(k.xy[0],k.conf[0])]})
        out.append({'f':i,'t':round(i/fps,3),'P':P})
    i+=1
    if i%100==0:print(i,N,round(time.time()-t0),flush=True)
json.dump(out,open('vid/kp2d.json','w'))
print('done',len(out))
