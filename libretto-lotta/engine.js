/* Motore vista dall'alto. Unità = centimetri. Asse x verso est, y verso sud (schermo). */
(function(){
const R2D=180/Math.PI, D2R=Math.PI/180;
const lerp=(a,b,e)=>a+(b-a)*e;
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const ease=x=>x<.5?2*x*x:1-Math.pow(-2*x+2,2)/2;
function angLerp(a,b,e){let d=((b-a+540)%360)-180;return a+d*e}

// corpo: dimensioni in cm
const DIM={sh:22,hip:15,head:10.5,ua:30,fa:28,footL:26,footW:10};

/* ---- geometria di un lottatore ---- */
function frameOf(b){const a=b.a*D2R;return {P:[b.x,b.y],d:[Math.cos(a),Math.sin(a)],r:[-Math.sin(a),Math.cos(a)]}}
function toW(F,f,s){return [F.P[0]+F.d[0]*f+F.r[0]*s,F.P[1]+F.d[1]*f+F.r[1]*s]}
function bodyParts(b,feet){
  const F=frameOf(b),lean=b.lean||0,p={};
  p.c=F.P; p.hipL=toW(F,0,-DIM.hip); p.hipR=toW(F,0,DIM.hip);
  p.shL=toW(F,lean,-DIM.sh); p.shR=toW(F,lean,DIM.sh);
  p.chest=toW(F,lean+9,0); p.back=toW(F,lean-11,0); p.belly=toW(F,9,0); p.waistBack=toW(F,-10,0);
  p.sideL=toW(F,lean*.5,-DIM.sh-3); p.sideR=toW(F,lean*.5,DIM.sh+3);
  p.armpitL=toW(F,lean,-DIM.sh+6); p.armpitR=toW(F,lean,DIM.sh-6);
  const ho=b.head||[0,0]; p.head=toW(F,lean+5+ho[0],ho[1]);
  p.neck=toW(F,lean+2+ho[0]*.5,ho[1]*.5);
  if(feet){p.footL=feet.L.p;p.footR=feet.R.p;
    p.kneeL=b.kneeL||[lerp(p.hipL[0],feet.L.p[0],.55),lerp(p.hipL[1],feet.L.p[1],.55)];
    p.kneeR=b.kneeR||[lerp(p.hipR[0],feet.R.p[0],.55),lerp(p.hipR[1],feet.R.p[1],.55)];
    p.ankleL=feet.L.p;p.ankleR=feet.R.p;
    // tallone: dietro il centro del piede
    const hl=feet.L.a*D2R,hr=feet.R.a*D2R;
    p.heelL=[feet.L.p[0]-Math.cos(hl)*10,feet.L.p[1]-Math.sin(hl)*10];
    p.heelR=[feet.R.p[0]-Math.cos(hr)*10,feet.R.p[1]-Math.sin(hr)*10];}
  p.F=F; return p;
}
function armIK(sh,t,side,F){ // gomito verso l'esterno
  const l1=DIM.ua,l2=DIM.fa;let dx=t[0]-sh[0],dy=t[1]-sh[1],d=Math.hypot(dx,dy)||.01;
  const dc=clamp(d,Math.abs(l1-l2)+1,l1+l2-.5),base=Math.atan2(dy,dx),k=Math.acos((l1*l1+dc*dc-l2*l2)/(2*l1*dc));
  const c1=[sh[0]+l1*Math.cos(base+k),sh[1]+l1*Math.sin(base+k)],c2=[sh[0]+l1*Math.cos(base-k),sh[1]+l1*Math.sin(base-k)];
  const sc=p=>((p[0]-F.P[0])*F.r[0]+(p[1]-F.P[1])*F.r[1])*(side==='L'?-1:1);
  const el=sc(c1)>sc(c2)?c1:c2;const vx=t[0]-el[0],vy=t[1]-el[1],vl=Math.hypot(vx,vy)||1;
  return {el,hand:[el[0]+vx/vl*l2,el[1]+vy/vl*l2],tri:[lerp(sh[0],el[0],.6),lerp(sh[1],el[1],.6)]};
}

/* ---- risoluzione di un riferimento ---- */
function resolve(spec,ctx,self){
  if(!spec)return null;
  if(typeof spec==='string')spec=[spec];
  if(typeof spec[0]==='number')return [spec[0],spec[1]];
  const [who,part]=spec[0].split('.');const W=ctx[who];
  let p=W.parts[part]; if(!p)p=W.parts.c;
  return [p[0]+(spec[1]||0),p[1]+(spec[2]||0)];
}
function handSpec(h){return h&&h.to!==undefined?h:{to:h}}
function restHand(W,side){const b=W.parts;const F=b.F;return toW(F,(W.body.lean||0)+22,side==='L'?-16:16)}

/* ---- stato a un istante: interpolazione per elemento con finestre temporali ---- */
const ELEMS=['body','fL','fR','hL','hR'];
function changed(k0,k1,W,el){
  const g=(k,el)=>{const w=k[W];if(el==='body')return JSON.stringify([w.x,w.y,w.a,w.lean,w.head,w.kneeL,w.kneeR,w.knee]);
    if(el==='fL')return JSON.stringify(w.feet.L);if(el==='fR')return JSON.stringify(w.feet.R);
    return JSON.stringify(w[el])};
  return g(k0,el)!==g(k1,el);
}
function windowOf(k1,W,el){const tm=(k1.tm&&k1.tm[W])||{};return tm[el]||[0,1]}
function stateAt(keys,i,T){ // i = indice fase destinazione (transizione i-1 -> i), T in [0,1]
  const k1=keys[i],k0=keys[Math.max(0,i-1)];const ctx={};
  for(const W of ['A','B']){
    const e={};for(const el of ELEMS){const w=windowOf(k1,W,el);e[el]=i===0?1:ease(clamp((T-w[0])/((w[1]-w[0])||1),0,1))}
    const b0=k0[W],b1=k1[W];
    const body={x:lerp(b0.x,b1.x,e.body),y:lerp(b0.y,b1.y,e.body),a:angLerp(b0.a,b1.a,e.body),lean:lerp(b0.lean||0,b1.lean||0,e.body),
      head:[lerp((b0.head||[0,0])[0],(b1.head||[0,0])[0],e.body),lerp((b0.head||[0,0])[1],(b1.head||[0,0])[1],e.body)],
      level:e.body<.5?b0.level:b1.level};
    const feet={};
    for(const s of ['L','R']){const f0=b0.feet[s],f1=b1.feet[s],ee=e['f'+s];
      feet[s]={p:[lerp(f0.p[0],f1.p[0],ee),lerp(f0.p[1],f1.p[1],ee)],a:angLerp(f0.a,f1.a,ee),
        lift:(i>0&&changed(k0,k1,W,'f'+s))?Math.sin(Math.PI*ee):0,toe:ee<.5?f0.toe:f1.toe};}
    // ginocchia a terra
    const kn={};for(const s of ['L','R']){const K0=(b0.knee||{})[s],K1=(b1.knee||{})[s];
      const ee=e['f'+s]; if(K1&&ee>=.5)kn[s]=K1; else if(K0&&ee<.5)kn[s]=K0;}
    ctx[W]={body,feet,kn,e,b0,b1};
  }
  for(const W of ['A','B']){const c=ctx[W];c.parts=bodyParts(c.body,c.feet);
    if(c.kn.L)c.parts.kneeL=c.kn.L; if(c.kn.R)c.parts.kneeR=c.kn.R;}
  // mani: due passaggi per i riferimenti a mani/polsi avversari
  for(let pass=0;pass<2;pass++)for(const W of ['A','B']){const c=ctx[W];c.arms=c.arms||{};
    for(const s of ['L','R']){const h0=handSpec(c.b0['h'+s]),h1=handSpec(c.b1['h'+s]);const ee=c.e['h'+s];
      const p0=h0.to?resolve(h0.to,ctx):restHand(c,s),p1=h1.to?resolve(h1.to,ctx):restHand(c,s);
      const t=[lerp(p0[0],p1[0],ee),lerp(p1===p0?p0[1]:p0[1],p1[1],ee)];
      const arm=armIK(c.parts['sh'+s],t,s,c.parts.F);arm.grip=(ee<.5?h0:h1).g;arm.gripOn=!!(ee<.5?h0.to:h1.to)&&ee>.98||(!!h0.to&&!!h1.to&&JSON.stringify(h0.to)===JSON.stringify(h1.to));
      c.arms[s]=arm;c.parts['hand'+s]=arm.hand;c.parts['wr'+s]=arm.hand;c.parts['elb'+s]=arm.el;c.parts['tri'+s]=arm.tri;}}
  return ctx;
}

/* ---- disegno SVG ---- */
const NS='http://www.w3.org/2000/svg';
function el(n,a,p){const e=document.createElementNS(NS,n);for(const k in a)e.setAttribute(k,a[k]);if(p)p.appendChild(e);return e}
const f1=v=>Math.round(v*10)/10;
const FOOT='M -13 0 C -13 -4.5 -9 -5 -4 -5 C 4 -5.5 9 -5.5 12 -3 C 14.5 -1 14.5 1 12 3 C 9 5.5 4 5.5 -4 5 C -9 5 -13 4.5 -13 0 Z';
function makeStage(svg,opt){
  svg.innerHTML='';const W=opt.w,H=opt.h;
  const defs=el('defs',{},svg);
  for(const [id,col] of [['arF','var(--force)'],['arM','var(--ink)'],['arA','var(--red)'],['arB','var(--blue)']]){
    const m=el('marker',{id:opt.id+id,viewBox:'0 0 10 10',refX:7,refY:5,markerWidth:5,markerHeight:5,orient:'auto-start-reverse'},defs);
    el('path',{d:'M0,0 L10,5 L0,10 z',fill:col},m);}
  el('rect',{x:-200,y:-200,width:W+400,height:H+400,fill:'var(--mat)'},svg);
  const grid=el('g',{opacity:.5},svg);
  for(let x=-200;x<=W+200;x+=25)el('line',{x1:x,y1:-200,x2:x,y2:H+200,stroke:'var(--grid)','stroke-width':x%50?0.3:0.6},grid);
  for(let y=-200;y<=H+200;y+=25)el('line',{x1:-200,y1:y,x2:W+200,y2:y,stroke:'var(--grid)','stroke-width':y%50?0.3:0.6},grid);
  // scala 50 cm (riposizionata da fitView)
  const sc=el('g',{},svg);el('line',{x1:8,y1:H-8,x2:58,y2:H-8,stroke:'var(--muted)','stroke-width':1.2},sc);
  el('line',{x1:8,y1:H-11,x2:8,y2:H-5,stroke:'var(--muted)','stroke-width':1},sc);el('line',{x1:58,y1:H-11,x2:58,y2:H-5,stroke:'var(--muted)','stroke-width':1},sc);
  const st=el('text',{x:33,y:H-12,'text-anchor':'middle','font-size':6.5,fill:'var(--muted)','font-family':'var(--mono)'},sc);st.textContent='50 cm';
  // bussola "N" non serve: indichiamo la direzione dello sguardo
  const ghost=el('g',{opacity:.22},svg), arrows=el('g',{},svg), L={ghost,arrows};
  for(const W of ['B','A'])L[W]=el('g',{},svg);
  L.top=el('g',{},svg);L.labels=el('g',{},svg);
  return {svg,L,opt,sc};
}
function drawWrestler(g,c,W,opts){
  const col=W==='A'?'var(--red)':'var(--blue)',soft=W==='A'?'var(--redsoft)':'var(--bluesoft)';
  const p=c.parts,F=p.F,a=c.body.a;g.setAttribute('opacity',opts.under?.8:.93);
  const lab=opts.labels!==false;
  // piedi
  for(const s of ['L','R']){const f=c.feet[s];const sc=1+.18*f.lift;
    const gg=el('g',{transform:`translate(${f1(f.p[0])} ${f1(f.p[1])}) rotate(${f1(f.a)}) scale(${sc})`},g);
    if(f.lift>.05)el('ellipse',{rx:12,ry:4.5,fill:'var(--ink)',opacity:.12,transform:`translate(${2+3*f.lift} ${3*f.lift})`},gg);
    el('path',{d:FOOT,fill:f.toe?'none':soft,stroke:col,'stroke-width':1.4,'stroke-dasharray':f.toe?'2 1.5':'none'},gg);
    if(lab){const t=el('text',{x:0,y:2.3,'text-anchor':'middle','font-size':6.5,'font-weight':700,fill:col,'font-family':'var(--display)',transform:`rotate(${f1(-f.a)})`},gg);t.textContent=s==='L'?'S':'D';}}
  // ginocchia a terra
  for(const s of ['L','R'])if(c.kn[s]){const k=c.kn[s];el('circle',{cx:k[0],cy:k[1],r:5.5,fill:col,opacity:.9},g);
    const t=el('text',{x:k[0],y:k[1]+2.2,'text-anchor':'middle','font-size':5.5,fill:'var(--surface)','font-weight':700,'font-family':'var(--display)'},g);t.textContent='G';}
  // anche
  el('line',{x1:f1(p.hipL[0]),y1:f1(p.hipL[1]),x2:f1(p.hipR[0]),y2:f1(p.hipR[1]),stroke:col,'stroke-width':10,'stroke-linecap':'round',opacity:.25},g);
  // braccia lato lontano/vicino: disegniamo entrambe, poi spalle sopra
  const arms=el('g',{},g);
  // spalle (busto)
  el('line',{x1:f1(p.shL[0]),y1:f1(p.shL[1]),x2:f1(p.shR[0]),y2:f1(p.shR[1]),stroke:col,'stroke-width':13,'stroke-linecap':'round',opacity:.92},g);
  // testa con naso (direzione sguardo)
  const hd=el('g',{transform:`translate(${f1(p.head[0])} ${f1(p.head[1])}) rotate(${f1(a)})`},g);
  el('circle',{r:8.5,fill:soft,stroke:col,'stroke-width':2.2},hd);
  el('path',{d:'M 7.5 -3.5 L 13 0 L 7.5 3.5',fill:col},hd);
  for(const s of ['L','R']){const A=c.arms[s];const sh=p['sh'+s];
    el('polyline',{points:`${f1(sh[0])},${f1(sh[1])} ${f1(A.el[0])},${f1(A.el[1])} ${f1(A.hand[0])},${f1(A.hand[1])}`,fill:'none',stroke:col,'stroke-width':4,'stroke-linecap':'round','stroke-linejoin':'round'},opts.armsTop?opts.armsTop:arms);
    const hg=opts.armsTop||arms;
    el('circle',{cx:f1(A.hand[0]),cy:f1(A.hand[1]),r:4.3,fill:A.gripOn?col:'var(--surface)',stroke:col,'stroke-width':1.6},hg);
    if(lab){const t=el('text',{x:f1(A.hand[0]),y:f1(A.hand[1])+2,'text-anchor':'middle','font-size':5.6,'font-weight':700,fill:A.gripOn?'var(--surface)':col,'font-family':'var(--display)'},hg);t.textContent=s==='L'?'S':'D';}}
}
function arrowPath(a,b,bend){const mx=(a[0]+b[0])/2,my=(a[1]+b[1])/2,dx=b[0]-a[0],dy=b[1]-a[1];
  const cx=mx-dy*(bend||0),cy=my+dx*(bend||0);return `M${f1(a[0])},${f1(a[1])} Q${f1(cx)},${f1(cy)} ${f1(b[0])},${f1(b[1])}`}
function render(st,keys,i,T,showArrows){
  const ctx=stateAt(keys,i,T);const L=st.L;
  for(const k of ['ghost','arrows','A','B','top','labels'])L[k].innerHTML='';
  // fantasma della posizione precedente (solo piedi)
  if(i>0&&T<1.01){const prev=stateAt(keys,i-1,1);
    for(const W of ['A','B'])for(const s of ['L','R']){const f=prev[W].feet[s];
      el('path',{d:FOOT,fill:'none',stroke:W==='A'?'var(--red)':'var(--blue)','stroke-width':1,'stroke-dasharray':'1.5 1.5',transform:`translate(${f1(f.p[0])} ${f1(f.p[1])}) rotate(${f1(f.a)})`},L.ghost);}}
  const top=keys[i].top||'A',bot=top==='A'?'B':'A';
  drawWrestler(L[bot],ctx[bot],bot,{under:true});
  drawWrestler(L[top],ctx[top],top,{});
  // braccia di chi sta "sotto" ma afferra sopra: opzionale per fase
  if(showArrows){const ar=keys[i].arrows||[];const vis=T>=.15||i===0;
    for(const A of ar){const a=resolve(A.from,ctx),b=resolve(A.to,ctx);
      const kind=A.k||'f',col=kind==='f'?'var(--force)':kind==='a'?'var(--red)':kind==='b'?'var(--blue)':'var(--ink)';
      const mk=kind==='f'?'arF':kind==='a'?'arA':kind==='b'?'arB':'arM';
      el('path',{d:arrowPath(a,b,A.bend||0),fill:'none',stroke:col,'stroke-width':kind==='f'?3.2:1.6,'stroke-dasharray':kind==='f'?'none':'4 2.5','stroke-linecap':'round',opacity:vis?.95:.25,'marker-end':`url(#${st.opt.id+mk})`},L.arrows);
      if(A.t){const t=el('text',{x:f1(b[0]+(A.tx||0)),y:f1(b[1]+(A.ty||-5)),'text-anchor':'middle','font-size':5.6,'font-weight':700,fill:col,'font-family':'var(--body)',stroke:'var(--mat)','stroke-width':2.2,'paint-order':'stroke',opacity:vis?1:.25},L.labels);t.textContent=A.t;}}}
  return ctx;
}
function fitView(st,keys){
  let x0=1e9,y0=1e9,x1=-1e9,y1=-1e9;const add=p=>{if(!p)return;x0=Math.min(x0,p[0]);y0=Math.min(y0,p[1]);x1=Math.max(x1,p[0]);y1=Math.max(y1,p[1])};
  keys.forEach((k,i)=>{const c=stateAt(keys,i,1);for(const W of ['A','B']){const P=c[W].parts;
    ['head','shL','shR','hipL','hipR','handL','handR','elbL','elbR'].forEach(n=>add(P[n]));add(c[W].feet.L.p);add(c[W].feet.R.p)}});
  const pad=16;x0-=pad;y0-=pad;x1+=pad;y1+=pad;let w=x1-x0,h=y1-y0;const ar=1.5;
  if(w/h<ar){const nw=h*ar;x0-=(nw-w)/2;w=nw}else{const nh=w/ar;y0-=(nh-h)/2;h=nh}
  st.svg.setAttribute('viewBox',`${f1(x0)} ${f1(y0)} ${f1(w)} ${f1(h)}`);
  const u=w/300;st.sc.setAttribute('transform',`translate(${f1(x0+6*u)} ${f1(y0+h-200*u)}) scale(${f1(u)}) translate(0 0)`);
  st.sc.setAttribute('transform',`translate(${f1(x0+4*u)} ${f1(y0+h-4*u)}) translate(-8 -192)`);
}
window.TOPV={fitView,stateAt,render,makeStage,changed,windowOf,ELEMS};
})();
