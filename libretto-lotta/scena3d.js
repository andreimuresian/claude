/* Scena 3D: due lottatori modellati, posati dai dati delle tecniche (cm, vista dall'alto x/y + altezze). */
(function(){
const V=(x,y,z)=>new THREE.Vector3(x,y,z);
const D2R=Math.PI/180;
const lerp=(a,b,e)=>a+(b-a)*e, clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const ease=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
const angLerp=(a,b,e)=>{const d=((b-a+540)%360)-180;return a+d*e};
const to3=(x,y,h)=>V(x-150,h||0,y-100);
const LEN={th:45,sh:44,ua:30,fa:27};

/* ---------- normalizzazione dei fotogrammi chiave ---------- */
function norm(b){
  if(b._n)return b._n;
  const n={x:b.x,y:b.y,a:b.a,head:b.head||[0,0],feet:b.feet,knee:b.knee||{},hL:b.hL,hR:b.hR};
  const lean=b.lean||0, kn=Object.keys(n.knee).length;
  if(lean>=40){n.lying=true;n.a=b.a+180;n.pitch=-84;n.h=13}
  else if(kn){n.pitch=b.pitch!=null?b.pitch:clamp(18+lean*1.6,-20,75);n.h=b.h||(kn===2?50-Math.max(0,lean-15)*.6:56)}
  else{n.pitch=b.pitch!=null?b.pitch:clamp(14+lean*1.7,-30,75);n.h=b.h||clamp(86-Math.max(0,lean)*1.0,40,92)}
  if(b.pitch!=null)n.pitch=b.pitch; if(b.h)n.h=b.h;
  b._n=n;return n;
}
const ELEMS=['body','fL','fR','hL','hR'];
function sig(k,W,el){const w=k[W];
  if(el==='body')return JSON.stringify([w.x,w.y,w.a,w.lean,w.head,w.h,w.pitch]);
  if(el==='fL')return JSON.stringify([w.feet.L,(w.knee||{}).L]);if(el==='fR')return JSON.stringify([w.feet.R,(w.knee||{}).R]);
  return JSON.stringify(w[el]);}
const changed=(k0,k1,W,el)=>sig(k0,W,el)!==sig(k1,W,el);
const windowOf=(k1,W,el)=>((k1.tm&&k1.tm[W])||{})[el]||[0,1];

/* ---------- scheletro: posizioni delle articolazioni ---------- */
function frame(a,pitch){const f=V(Math.cos(a*D2R),0,Math.sin(a*D2R)),r=V(-Math.sin(a*D2R),0,Math.cos(a*D2R)),up=V(0,1,0);
  const p=pitch*D2R,u=up.clone().multiplyScalar(Math.cos(p)).add(f.clone().multiplyScalar(Math.sin(p)));
  const fw=f.clone().multiplyScalar(Math.cos(p)).add(up.clone().multiplyScalar(-Math.sin(p)));return {f,r,u,fw}}
const add=(p,...t)=>{const q=p.clone();for(let i=0;i<t.length;i+=2)q.addScaledVector(t[i],t[i+1]);return q};
function torsoParts(B){
  const F=frame(B.a,B.pitch),P=to3(B.x,B.y,B.h),{r,u,fw}=F,J={F,P};
  J.c=add(P,u,10);J.hipL=add(P,r,-10);J.hipR=add(P,r,10);
  J.N=add(P,u,50);J.shL=add(J.N,u,-5,r,-19);J.shR=add(J.N,u,-5,r,19);
  J.chest=add(P,u,36,fw,12);J.back=add(P,u,36,fw,-12);J.belly=add(P,u,14,fw,12);J.waistBack=add(P,u,14,fw,-11);
  J.sideL=add(P,u,26,r,-17);J.sideR=add(P,u,26,r,17);J.armpitL=add(J.N,u,-13,r,-14);J.armpitR=add(J.N,u,-13,r,14);
  J.head=add(J.N,u,15,r,(B.head[1]||0)*.6,fw,(B.head[0]||0)*.4);J.neck=add(J.N,u,5,fw,-4);
  return J;
}
function ik(root,target,l1,l2,pole){
  const d=target.clone().sub(root);let dist=d.length();const dir=d.clone().normalize();
  const dc=clamp(dist,Math.abs(l1-l2)+1,l1+l2-.3);
  const a=Math.acos(clamp((l1*l1+dc*dc-l2*l2)/(2*l1*dc),-1,1));
  let pp=pole.clone().sub(dir.clone().multiplyScalar(pole.dot(dir)));if(pp.lengthSq()<1e-6)pp=V(0,-1,0);pp.normalize();
  const mid=root.clone().addScaledVector(dir,Math.cos(a)*l1).addScaledVector(pp,Math.sin(a)*l1);
  const end=mid.clone().addScaledVector(target.clone().sub(mid).normalize(),l2);
  return {mid,end};
}

/* ---------- stato a un istante ---------- */
function resolve(spec,J,owner,bodyN){
  if(!spec)return null;if(typeof spec==='string')spec=[spec];
  if(typeof spec[0]==='number'){const low=bodyN&&(bodyN.pitch>40||bodyN.lying);return to3(spec[0],spec[1],low?3:95)}
  const [w,part]=spec[0].split('.');const P=(J[w][part]||J[w].c).clone();
  P.x+=(spec[1]||0);P.z+=(spec[2]||0);return P;
}
const PART_R={wrL:3.5,wrR:3.5,handL:3,handR:3,triL:5.5,triR:5.5,elbL:4.5,elbR:4.5,kneeL:6,kneeR:6,neck:6,head:10,shL:7,shR:7,hipL:9,hipR:9,armpitL:4,armpitR:4,ankleL:4,ankleR:4,heelL:4,heelR:4};
function stateAt(keys,i,T){
  const k1=keys[i],k0=keys[Math.max(0,i-1)],J={},S={};
  for(const W of ['A','B']){const b0=norm(k0[W]),b1=norm(k1[W]);const e={};
    for(const el of ELEMS){const w=windowOf(k1,W,el);e[el]=i===0?1:ease(clamp((T-w[0])/((w[1]-w[0])||1),0,1))}
    const eb=e.body;
    const B={x:lerp(b0.x,b1.x,eb),y:lerp(b0.y,b1.y,eb),a:angLerp(b0.a,b1.a,eb),pitch:lerp(b0.pitch,b1.pitch,eb),h:lerp(b0.h,b1.h,eb),
      head:[lerp(b0.head[0],b1.head[0],eb),lerp(b0.head[1],b1.head[1],eb)],lying:eb>.5?b1.lying:b0.lying};
    J[W]=torsoParts(B);S[W]={B,b0,b1,e};}
  // gambe
  for(const W of ['A','B']){const {B,b0,b1,e}=S[W],j=J[W];
    for(const s of ['L','R']){const ef=e['f'+s],f0=b0.feet[s],f1=b1.feet[s];
      const fx=lerp(f0.p[0],f1.p[0],ef),fy=lerp(f0.p[1],f1.p[1],ef),fa=angLerp(f0.a,f1.a,ef);
      const toe=lerp(f0.toe?1:0,f1.toe?1:0,ef),lift=(i>0&&changed(k0,k1,W,'f'+s))?Math.sin(Math.PI*ef)*9:0;
      const fd=V(Math.cos(fa*D2R),0,Math.sin(fa*D2R));const hip=j['hip'+s];
      const ground=to3(fx,fy,0);
      const ankle=add(ground,fd,lerp(-7,-9,toe),V(0,1,0),lerp(8,15,toe)+lift);
      const toeP=add(ground,fd,lerp(13,9,toe),V(0,1,0),lerp(3,1,toe)+lift);
      const pole=add(V(0,0,0),j.F.f,1,j.F.r,s==='L'?-.25:.25);
      const kIK=b=>{return ik(hip,ankle,LEN.th,LEN.sh,pole).mid};
      const k0p=b0.knee[s]?to3(b0.knee[s][0],b0.knee[s][1],6):null,k1p=b1.knee[s]?to3(b1.knee[s][0],b1.knee[s][1],6):null;
      let knee;const solved=kIK();
      if(k0p||k1p){knee=(k0p||solved).clone().lerp(k1p||solved,ef);}else knee=solved;
      j['knee'+s]=knee;j['ankle'+s]=ankle;j['toe'+s]=toeP;j['heel'+s]=add(ankle,fd,-4,V(0,1,0),-4);j['foot'+s]=ground;}}
  // braccia (3 passaggi per i riferimenti incrociati)
  const H={A:{},B:{}};
  for(let pass=0;pass<3;pass++)for(const W of ['A','B']){const {b0,b1,e}=S[W],j=J[W];
    for(const s of ['L','R']){const eh=e['h'+s];
      const sp0=b0['h'+s],sp1=b1['h'+s],t0=sp0&&(sp0.to!==undefined?sp0.to:sp0),t1=sp1&&(sp1.to!==undefined?sp1.to:sp1);
      const sh=j['sh'+s];const rest=add(j.chest,j.F.fw,18,j.F.r,s==='L'?-14:14,j.F.u,-14);
      const p0=t0?resolve(t0,J,W,S[W].b0):rest,p1=t1?resolve(t1,J,W,S[W].b1):rest;
      const tgt=p0.clone().lerp(p1,eh);
      // la mano si appoggia sulla superficie del bersaglio, palmo verso il bersaglio
      const partName=(x=>x&&typeof x!=='string'&&typeof x[0]==='string'?x[0]:x)(eh<.5?t0:t1);
      const pr=typeof partName==='string'?(PART_R[partName.split('.')[1]]||3):0;
      const appr=tgt.clone().sub(sh).normalize();
      const palm=tgt.clone().addScaledVector(appr,-pr-1.5);
      const wrist=palm.clone().addScaledVector(appr,-5.5);
      const wrap=typeof partName==='string'&&/belly|waistBack|back|side/.test(partName);
      const pole=wrap?add(V(0,0,0),V(0,1,0),-.25,j.F.r,s==='L'?-1.6:1.6):add(V(0,0,0),V(0,1,0),-1,j.F.r,s==='L'?-.8:.8,j.F.fw,-.5);
      const res=ik(sh,wrist,LEN.ua,LEN.fa,pole);
      const grip=lerp(t0?1:0,t1?1:0,eh);
      H[W][s]={sh,el:res.mid,wr:res.end,tgt,grip,appr};
      j['elb'+s]=res.mid;j['tri'+s]=sh.clone().lerp(res.mid,.55);j['wr'+s]=res.end;j['hand'+s]=add(res.end,res.end.clone().sub(res.mid).normalize(),5);}}
  return {J,S,H};
}

/* ---------- modello del lottatore ---------- */
function mats(team){
  const singlet=team==='A'?0xc9302c:0x2457b0;
  return {skin:new THREE.MeshStandardMaterial({color:team==='A'?0xe3b48f:0xd09a72,roughness:.62}),
    suit:new THREE.MeshStandardMaterial({color:singlet,roughness:.45,metalness:.05}),
    shoe:new THREE.MeshStandardMaterial({color:0x1d1f24,roughness:.5}),
    sole:new THREE.MeshStandardMaterial({color:singlet,roughness:.5}),
    hair:new THREE.MeshStandardMaterial({color:team==='A'?0x3a2a1e:0x1c1714,roughness:.9}),
    dark:new THREE.MeshStandardMaterial({color:0x222222,roughness:.4})};
}
const UPY=V(0,1,0);
function seg(group,r,mat){const geo=new THREE.CapsuleGeometry(r,1,6,12);const m=new THREE.Mesh(geo,mat);m.castShadow=true;m.receiveShadow=true;group.add(m);
  return {m,set(a,b){const d=b.clone().sub(a);const L=Math.max(d.length(),.01);m.position.copy(a).addScaledVector(d,.5);
    m.quaternion.setFromUnitVectors(UPY,d.normalize());
    if(Math.abs(m.userData.L-L)>.5||!m.userData.L){m.geometry.dispose();m.geometry=new THREE.CapsuleGeometry(r,Math.max(.1,L),6,12);m.userData.L=L}}}}
function blob(group,sx,sy,sz,mat){const m=new THREE.Mesh(new THREE.SphereGeometry(1,20,14),mat);m.scale.set(sx,sy,sz);m.castShadow=true;m.receiveShadow=true;group.add(m);return m}
function basisQuat(x,y,z){const M=new THREE.Matrix4().makeBasis(x,y,z);return new THREE.Quaternion().setFromRotationMatrix(M)}

function makeHand(group,mat,side){
  const h={side,palm:new THREE.Mesh(new THREE.BoxGeometry(8.4,2.6,9.2),mat),f:[],t:[]};
  h.palm.castShadow=true;group.add(h.palm);
  for(let k=0;k<4;k++)h.f.push([seg(group,.95,mat),seg(group,.9,mat),seg(group,.85,mat)]);
  h.t=[seg(group,1.1,mat),seg(group,1,mat)];
  return h;
}
function poseHand(h,wr,el,appr,grip){
  const a=wr.clone().sub(el).normalize();
  // il palmo guarda verso il bersaglio (o in basso/dentro a riposo)
  let n=appr.clone().sub(a.clone().multiplyScalar(appr.dot(a)));if(n.lengthSq()<1e-4)n=V(0,-1,0);n.normalize();
  // tolleranza: con presa il palmo guarda il bersaglio; senza presa ruota verso il basso
  if(grip<.5){const dn=V(0,-1,0);const nn=dn.sub(a.clone().multiplyScalar(dn.dot(a)));if(nn.lengthSq()>1e-4)n.lerp(nn.normalize(),.7).normalize()}
  const thumbSide=h.side==='R'?a.clone().cross(n):n.clone().cross(a);thumbSide.normalize();
  const pc=wr.clone().addScaledVector(a,5.2);
  h.palm.position.copy(pc);h.palm.quaternion.copy(basisQuat(thumbSide,n.clone().negate(),a));
  const lens=[[4.4,2.6,2.2],[4.8,2.9,2.3],[4.6,2.7,2.2],[3.6,2.2,1.9]];
  for(let k=0;k<4;k++){const off=1.3-k*2.6*1.05+(k>0?0:0);
    let base=pc.clone().addScaledVector(a,4.6).addScaledVector(thumbSide,2.9-k*1.95).addScaledVector(n,-.2);
    let dir=a.clone(),p=base;const c=[.55,.8,.7].map(x=>x*grip*Math.PI/2+.12);
    for(let s=0;s<3;s++){dir=dir.clone().multiplyScalar(Math.cos(c[s])).add(n.clone().multiplyScalar(Math.sin(c[s]))).normalize();
      // n si aggiorna per continuare ad arrotolarsi
      const nn=n.clone().multiplyScalar(Math.cos(c[s])).add(a.clone().multiplyScalar(-Math.sin(c[s])));
      const q=p.clone().addScaledVector(dir,lens[k][s]);h.f[k][s].set(p,q);p=q;}}
  // pollice
  let tb=pc.clone().addScaledVector(a,-2.6).addScaledVector(thumbSide,4);
  let td=a.clone().multiplyScalar(.55).add(thumbSide.clone().multiplyScalar(.75)).add(n.clone().multiplyScalar(.25+grip*.7)).normalize();
  const t1=tb.clone().addScaledVector(td,3.8);h.t[0].set(tb,t1);
  const td2=td.clone().multiplyScalar(.6).add(a.clone().multiplyScalar(.3)).add(n.clone().multiplyScalar(.2+grip*.6)).add(thumbSide.clone().multiplyScalar(-grip*.4)).normalize();
  h.t[1].set(t1,t1.clone().addScaledVector(td2,3.2));
}
function makeWrestler(scene,team){
  const M=mats(team),g=new THREE.Group();scene.add(g);
  const w={g,M,team};
  const prof=[[0,-11],[9,-10],[14.5,-5],[15.5,2],[14.6,10],[13.4,18],[14.2,26],[16.4,34],[17.2,40],[16,45],[12.5,49],[7,52],[0,53]].map(([r,y])=>new THREE.Vector2(r,y));
  w.torso=new THREE.Mesh(new THREE.LatheGeometry(prof,32),M.suit);w.torso.castShadow=true;w.torso.receiveShadow=true;g.add(w.torso);
  w.trap=blob(g,13,4.5,7,M.skin);
  w.neck=seg(g,6,M.skin);
  w.headG=new THREE.Group();g.add(w.headG);
  const hm=new THREE.Mesh(new THREE.SphereGeometry(1,24,18),M.skin);hm.scale.set(9,11,10);hm.castShadow=true;w.headG.add(hm);
  const hair=new THREE.Mesh(new THREE.SphereGeometry(1,24,18,0,Math.PI*2,0,Math.PI*.42),M.hair);hair.scale.set(9.5,11.4,10.5);hair.rotation.x=-.25;w.headG.add(hair);
  const nose=new THREE.Mesh(new THREE.ConeGeometry(1.5,4,10),M.skin);nose.rotation.x=Math.PI/2;nose.position.set(0,-1,10.2);w.headG.add(nose);
  for(const s of [-1,1]){const e=new THREE.Mesh(new THREE.SphereGeometry(1.1,10,8),M.dark);e.position.set(s*3.4,1.6,8.6);w.headG.add(e);
    const ear=new THREE.Mesh(new THREE.SphereGeometry(1,12,10),M.skin);ear.scale.set(1.4,3,2.2);ear.position.set(s*9,0,0);w.headG.add(ear);}
  const jaw=new THREE.Mesh(new THREE.SphereGeometry(1,16,12),M.skin);jaw.scale.set(7,5,7);jaw.position.set(0,-6,3);w.headG.add(jaw);
  w.limb={};
  for(const s of ['L','R']){w.limb[s]={delt:blob(g,8.2,7.6,8.2,M.skin),ua:seg(g,6.2,M.skin),fa:seg(g,5.1,M.skin),
    th:seg(g,9.6,M.suit),thLow:seg(g,8,M.skin),sh:seg(g,6.3,M.skin),knee:blob(g,6.6,6.6,6.6,M.skin),
    shoe:seg(g,4.6,M.shoe),hand:makeHand(g,M.skin,s)};}
  return w;
}
function poseWrestler(w,J,H,W){
  const j=J[W],F=j.F;const {r,u,fw}=F;
  const q=basisQuat(r,u,fw);
  const place=(m,p,qq)=>{m.position.copy(p);m.quaternion.copy(qq||q)};
  place(w.torso,j.P);w.torso.scale.set(1.18,1,.7);place(w.trap,add(j.N,u,-3,fw,-2));
  w.neck.set(add(j.N,u,-2),add(j.N,u,8));
  w.headG.position.copy(j.head);w.headG.quaternion.copy(q);
  for(const s of ['L','R']){const L=w.limb[s],h=H[W][s];
    L.delt.position.copy(j['sh'+s]);L.ua.set(j['sh'+s],h.el);L.fa.set(h.el,h.wr);
    poseHand(L.hand,h.wr,h.el,h.appr,h.grip);
    const hip=j['hip'+s],kn=j['knee'+s];const mid=hip.clone().lerp(kn,.45);
    L.th.set(hip,mid);L.thLow.set(mid,kn);L.knee.position.copy(kn);L.sh.set(kn,j['ankle'+s]);L.shoe.set(j['ankle'+s],j['toe'+s]);}
}

/* ---------- etichette S/D e frecce ---------- */
function labelSprite(txt,col){const c=document.createElement('canvas');c.width=c.height=64;const x=c.getContext('2d');
  x.fillStyle=col;x.beginPath();x.arc(32,32,28,0,7);x.fill();x.fillStyle='#fff';x.font='bold 36px Arial';x.textAlign='center';x.textBaseline='middle';x.fillText(txt,32,34);
  const s=new THREE.Sprite(new THREE.SpriteMaterial({map:new THREE.CanvasTexture(c),depthTest:false,transparent:true}));s.scale.set(7,7,1);s.renderOrder=9;return s}

/* ---------- scena ---------- */
function createView(container){
  THREE.ColorManagement.legacyMode=false;
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});renderer.setPixelRatio(Math.min(2,devicePixelRatio));
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.outputEncoding=THREE.sRGBEncoding;
  container.appendChild(renderer.domElement);
  const scene=new THREE.Scene();scene.background=new THREE.Color(0xcfd7e1);scene.fog=new THREE.Fog(0xcfd7e1,700,1500);
  const cam=new THREE.PerspectiveCamera(38,1,5,3000);cam.position.set(0,150,330);
  scene.add(new THREE.HemisphereLight(0xffffff,0x8a96a6,.75));
  const sun=new THREE.DirectionalLight(0xffffff,.85);sun.position.set(-160,420,240);sun.castShadow=true;
  sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-250,right:250,top:250,bottom:-250,near:50,far:1000});sun.shadow.bias=-.0008;scene.add(sun);
  const fill=new THREE.DirectionalLight(0xfff1e0,.3);fill.position.set(250,180,-200);scene.add(fill);
  // tappeto
  const mat=new THREE.Mesh(new THREE.CircleGeometry(450,72),new THREE.MeshStandardMaterial({color:0x2f6db5,roughness:.85}));mat.rotation.x=-Math.PI/2;mat.receiveShadow=true;scene.add(mat);
  const zone=new THREE.Mesh(new THREE.RingGeometry(400,450,72),new THREE.MeshStandardMaterial({color:0xd9822b,roughness:.85}));zone.rotation.x=-Math.PI/2;zone.position.y=.2;zone.receiveShadow=true;scene.add(zone);
  const centre=new THREE.Mesh(new THREE.RingGeometry(48,54,48),new THREE.MeshStandardMaterial({color:0xf2f2f2,roughness:.8}));centre.rotation.x=-Math.PI/2;centre.position.y=.25;scene.add(centre);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(4000,4000),new THREE.MeshStandardMaterial({color:0xc9d1db,roughness:1}));floor.rotation.x=-Math.PI/2;floor.position.y=-.5;floor.receiveShadow=true;scene.add(floor);
  const controls=new THREE.OrbitControls(cam,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;
  controls.minDistance=45;controls.maxDistance=800;controls.maxPolarAngle=Math.PI*.495;controls.target.set(0,80,0);
  const W={A:makeWrestler(scene,'A'),B:makeWrestler(scene,'B')};
  const labels=[];const lab={};
  for(const t of ['A','B'])for(const s of ['L','R'])for(const k of ['h','f']){const sp=labelSprite(s==='L'?'S':'D',t==='A'?'#c9302c':'#2457b0');scene.add(sp);lab[t+k+s]=sp;labels.push(sp)}
  const arrows=new THREE.Group();scene.add(arrows);
  const view={renderer,scene,cam,controls,W,labels,lab,arrows,showLabels:true,autoRot:false,center:V(0,80,0),
    resize(){const w=container.clientWidth,h=container.clientHeight;renderer.setSize(w,h,false);renderer.domElement.style.width='100%';renderer.domElement.style.height='100%';cam.aspect=w/h;cam.updateProjectionMatrix()},
    pose(keys,i,T){const st=stateAt(keys,i,T);for(const t of ['A','B'])poseWrestler(W[t],st.J,st.H,t);
      for(const t of ['A','B'])for(const s of ['L','R']){const h=st.H[t][s];lab[t+'h'+s].position.copy(h.wr).add(V(0,9,0));
        lab[t+'f'+s].position.copy(st.J[t]['ankle'+s]).add(V(0,14,0))}
      for(const l of labels)l.visible=view.showLabels;
      const c=st.J.A.P.clone().add(st.J.B.P).multiplyScalar(.5);c.y=Math.max(45,Math.min(95,c.y+10));view.center.lerp(c,.08);
      this.st=st;return st},
    setArrows(list,st){arrows.clear();if(!list)return;for(const A of list){const a=ptOf(A.from,st),b=ptOf(A.to,st);
      const d=b.clone().sub(a);const L=d.length();if(L<2)continue;
      const col=A.k==='a'?0xc9302c:A.k==='b'?0x2457b0:0xf0a500;
      const ar=new THREE.ArrowHelper(d.normalize(),a,L,col,Math.min(14,L*.35),Math.min(9,L*.22));ar.line.material.linewidth=3;
      ar.traverse(o=>{if(o.material){o.material.depthTest=false;o.material.transparent=true;o.renderOrder=10}});arrows.add(ar)}},
    frameOn(st){const c=st.J.A.P.clone().add(st.J.B.P).multiplyScalar(.5);c.y=80;view.center.copy(c);controls.target.copy(c)},
    camPreset(name,st){const J=st.J;const f=J.A.F.f;const r=J.A.F.r;const c=controls.target.clone();let p;
      if(name==='lato')p=c.clone().addScaledVector(r,-330).add(V(0,40,0));
      else if(name==='lato2')p=c.clone().addScaledVector(r,330).add(V(0,40,0));
      else if(name==='dietro')p=c.clone().addScaledVector(f,-320).add(V(0,70,0));
      else if(name==='davanti')p=c.clone().addScaledVector(f,320).add(V(0,70,0));
      else if(name==='alto')p=c.clone().add(V(0,380,30));
      else if(name==='mani'){const hc=st.H.A.L.wr.clone().add(st.H.A.R.wr).multiplyScalar(.5);const mid=st.J.A.P.clone().add(st.J.B.P).multiplyScalar(.5);
        let d=hc.clone().sub(mid);d.y=0;if(d.length()<8)d=r.clone().multiplyScalar(-1);d.normalize();
        controls.target.copy(hc);view.lockTarget=true;setTimeout(()=>view.lockTarget=false,4000);p=hc.clone().addScaledVector(d,125).add(V(0,35,0));}
      view.tween={from:cam.position.clone(),to:p,t:0}},
    tick(dt){if(view.tween){view.tween.t=Math.min(1,view.tween.t+dt/700);cam.position.lerpVectors(view.tween.from,view.tween.to,ease(view.tween.t));if(view.tween.t>=1)view.tween=null}
      else if(!view.lockTarget){const delta=view.center.clone().sub(controls.target).multiplyScalar(.06);controls.target.add(delta);cam.position.add(delta)}
      if(view.autoRot){const a=dt*.00035;const off=cam.position.clone().sub(controls.target);off.applyAxisAngle(UPY,a);cam.position.copy(controls.target).add(off)}
      controls.update();renderer.render(scene,cam)}};
  function ptOf(s,st){if(typeof s==='string')s=[s];if(typeof s[0]==='number')return to3(s[0],s[1],70);const [w,p]=s[0].split('.');const P=(st.J[w][p]||st.J[w].c).clone();P.x+=s[1]||0;P.z+=s[2]||0;return P}
  addEventListener('resize',()=>view.resize());view.resize();
  return view;
}
window.LOTTA3D={createView,stateAt,changed,windowOf,ELEMS};
})();
