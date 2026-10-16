import cv2,numpy as np,sys
cap=cv2.VideoCapture('v.mp4')
X0,Y0,W,H=75,40,330,247.5
def crop(t):
    cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,f=cap.read()
    c=f[int(Y0):int(Y0+H),int(X0):int(X0+W)];c=cv2.resize(c,(960,720),interpolation=cv2.INTER_LANCZOS4)
    bl=cv2.GaussianBlur(c,(0,0),2);return cv2.addWeighted(c,1.5,bl,-.5,0)
def grid(ts,name,cols=3):
    ims=[]
    for t in ts:
        c=crop(t).copy()
        for i in range(1,10):
            cv2.line(c,(i*96,0),(i*96,720),(255,255,255),1);cv2.line(c,(0,i*72),(960,i*72),(255,255,255),1)
            cv2.putText(c,str(i/10),(i*96+2,12),0,.4,(0,255,255),1);cv2.putText(c,str(i/10),(2,i*72-2),0,.4,(0,255,255),1)
        cv2.putText(c,str(t),(10,50),0,1.3,(0,0,255),3);ims.append(cv2.resize(c,(800,600)))
    cv2.imwrite(name,np.vstack([np.hstack(ims[i:i+cols]) for i in range(0,len(ims),cols)]))
if __name__=='__main__':
    ts=[float(x) for x in sys.argv[2:]];grid(ts,sys.argv[1],2)
