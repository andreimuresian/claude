"""Writes madrid1_predictor.html: fully offline (no server, no internet), GP maths re-implemented in JavaScript
from models/model_card.json, live cross-section.  Run: python3 make_gui.py"""
import json
card = json.load(open("models/model_card.json"))
html = r"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Madrid 1 Predictor</title>
<style>
:root{--bg:#f6f8fb;--card:#fff;--ink:#1d2733;--mut:#5f6b7a;--navy:#1f4e79;--red:#c0392b;--ok:#1e8449;--line:#d5dde6;--au:#f2c14e;--ox:#a9d3f5;--ln:#6b7b8c}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#11161d;--card:#1a212b;--ink:#e6edf3;--mut:#9aa7b4;--navy:#7fb2e5;--line:#2c3644;--ok:#58c98a;--red:#ff7b6b}}
:root[data-theme="dark"]{--bg:#11161d;--card:#1a212b;--ink:#e6edf3;--mut:#9aa7b4;--navy:#7fb2e5;--line:#2c3644;--ok:#58c98a;--red:#ff7b6b}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
main{max-width:1180px;margin:0 auto;padding:18px 16px 40px}h1{font-size:22px;margin:0 0 2px}.sub{color:var(--mut);margin:0 0 16px}
.grid{display:grid;grid-template-columns:330px 1fr;gap:16px}@media(max-width:860px){.grid{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px}
.p{margin-bottom:12px}.p label{display:flex;justify-content:space-between;font-weight:600}.p label span{font-variant-numeric:tabular-nums;color:var(--navy)}
.p input[type=range]{width:100%}.p small{color:var(--mut)}
.out{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:14px}@media(max-width:600px){.out{grid-template-columns:1fr 1fr}}
.stat .big{font-size:26px;font-weight:700;font-variant-numeric:tabular-nums}.stat .lab{color:var(--mut);font-size:12px}.stat .ci{color:var(--mut);font-size:12px;font-variant-numeric:tabular-nums}
.flag{padding:8px 10px;border-radius:8px;margin-top:8px;font-size:13px}.bad{background:rgba(192,57,43,.12);color:var(--red)}.good{background:rgba(30,132,73,.12);color:var(--ok)}
svg{width:100%;height:auto;display:block}table{border-collapse:collapse;width:100%;font-size:12.5px}td,th{padding:4px 6px;border-bottom:1px solid var(--line);text-align:left}
button{font:inherit;padding:5px 10px;border-radius:6px;border:1px solid var(--line);background:var(--card);color:var(--ink);cursor:pointer}
</style></head><body><main>
<h1>Madrid 1 (tri-galvanic) predictor · with rib width</h1>
<p class="sub">Gaussian-process surrogate of the femwell FEM · λ = 1625 nm · no ALD · trained on <b id="n"></b> simulations (<span id="created"></span>). Runs offline.</p>
<div class="grid"><div class="card" id="ctrl"></div><div>
<div class="out">
<div class="card stat"><div class="lab">Vπ·L (V·cm)</div><div class="big" id="v"></div><div class="ci" id="vci"></div></div>
<div class="card stat"><div class="lab">IL (dB/cm)</div><div class="big" id="il"></div><div class="ci" id="ilci"></div></div>
<div class="card stat"><div class="lab">Vπ·L, buffer −40 nm</div><div class="big" id="vw"></div><div class="ci">process worst case</div></div>
<div class="card stat"><div class="lab">IL, buffer −40 nm</div><div class="big" id="ilw"></div><div class="ci">process worst case</div></div></div>
<div class="card"><svg id="xs" viewBox="0 0 900 330" role="img" aria-label="cross-section"></svg><div id="flags"></div></div>
<div class="card" style="margin-top:14px"><b>Model</b> <span class="sub" id="mod"></span>
<table id="cvt"></table><p class="sub" style="margin:8px 0 0">95 % intervals are the GP's own uncertainty (log-space for IL). Fixed: signal 10 × 10 µm, ground tongue 10 µm + 10 × 10 µm, film 550 nm / etch 275 nm, BOX 4.7 µm. Rib width WG 1.0–1.5 µm; cap width ≥ 2·WG.</p></div>
</div></div></main>
<script>
const C=__CARD__;
const P=[{k:"GAP",lab:"GAP",u:"µm",min:3.0,max:4.5,step:0.01,v:3.2,d:2},{k:"BUFFER_H",lab:"BUFFER_H",u:"nm",min:50,max:200,step:1,v:100,d:0,s:1e-3},
{k:"CAP_W",lab:"CAP_W (≥ 2·WG)",u:"µm",min:2.0,max:4.5,step:0.01,v:3.0,d:2},{k:"CAP_H",lab:"CAP_H",u:"µm",min:0.5,max:1.4,step:0.01,v:0.5,d:2},{k:"MTX_SMALL",lab:"MTX_small",u:"µm",min:0.5,max:1.0,step:0.01,v:1.0,d:2},{k:"WG",lab:"WG (rib top width)",u:"µm",min:1.0,max:1.5,step:0.01,v:1.4,d:2}];
const ctrl=document.getElementById("ctrl");
P.forEach(p=>{const d=document.createElement("div");d.className="p";d.innerHTML=`<label>${p.lab}<span id="l_${p.k}"></span></label><input type="range" id="s_${p.k}" min="${p.min}" max="${p.max}" step="${p.step}" value="${p.v}"><small>${p.min}–${p.max} ${p.u}</small>`;ctrl.appendChild(d)});
ctrl.insertAdjacentHTML("beforeend",`<button id="best">Load robust best (gap ≥ 3.5, FEM-checked)</button> <button id="base">Baseline</button>`);
document.getElementById("n").textContent=C.n_samples;document.getElementById("created").textContent=C.created;
const O={};for(const k in C.outputs){const m=C.outputs[k];O[k]=m}
function kern(a,b,m){let s=0;for(let i=0;i<a.length;i++){const t=(a[i]-b[i])/m.length_scales[i];s+=t*t}const d=Math.sqrt(s);
 if(m.nu===2.5)return m.const*(1+Math.sqrt(5)*d+5*d*d/3)*Math.exp(-Math.sqrt(5)*d);if(m.nu===1.5)return m.const*(1+Math.sqrt(3)*d)*Math.exp(-Math.sqrt(3)*d);return m.const*Math.exp(-0.5*d*d)}
function pred(x){const z=x.map((v,i)=>(v-C.lo[i])/(C.hi[i]-C.lo[i]));const r={};
 for(const k in O){const m=O[k],n=m.alpha.length,ks=new Array(n);let mt=0;for(let i=0;i<n;i++){ks[i]=kern(z,m.Xtrain_u[i],m);mt+=ks[i]*m.alpha[i]}
  const v=new Array(n);let vv=0;for(let i=0;i<n;i++){let s=ks[i];const Li=m.L[i];for(let j=0;j<i;j++)s-=Li[j]*v[j];v[i]=s/Li[i];vv+=v[i]*v[i]}
  const sd=m.sd*Math.sqrt(Math.max(m.const+m.noise-vv,0));let t=m.beta[0]+m.mu+m.sd*mt;for(let i=0;i<z.length;i++)t+=m.beta[i+1]*z[i];
  r[k]=m.log10?{mean:10**t,lo:10**(t-1.96*sd),hi:10**(t+1.96*sd)}:{mean:t,lo:t-1.96*sd,hi:t+1.96*sd}}return r}
const g=id=>document.getElementById(id),val=k=>parseFloat(g("s_"+k).value);
function draw(G,B,CW,CH,MS,WG){const hw=WG/2;const sx=19,ox=450,yb=270,vy=110;const X=x=>ox+x*sx,Y=y=>yb-y*vy;const sl=0.275,rh=0.275,bt=0.275/Math.tan(Math.PI/3),xg=G/2;
 let s=`<rect x="0" y="${Y(0)}" width="900" height="${330-Y(0)}" fill="var(--ox)"/><rect x="0" y="${Y(sl)}" width="900" height="${sl*vy}" fill="var(--ln)"/>`;
 s+=`<rect x="0" y="${Y(sl+B)}" width="900" height="${B*vy}" fill="var(--ox)" stroke="#557" stroke-width=".5"/>`;
 s+=`<rect x="${X(-CW/2)}" y="${Y(sl+B+CH)}" width="${CW*sx}" height="${CH*vy}" fill="var(--ox)" stroke="#557" stroke-width=".8"/>`;
 s+=`<polygon points="${X(-hw-bt)},${Y(sl)} ${X(hw+bt)},${Y(sl)} ${X(hw)},${Y(sl+rh)} ${X(-hw)},${Y(sl+rh)}" fill="var(--ln)" stroke="#333" stroke-width=".8"/>`;
 const top=2.35;s+=`<rect x="${X(xg)}" y="${Y(top)}" width="${10*sx}" height="${(top-sl-B)*vy}" fill="var(--au)" stroke="#8a6d1a"/>`;
 s+=`<rect x="${X(-xg-10)}" y="${Y(sl+B+MS)}" width="${10*sx}" height="${MS*vy}" fill="var(--au)" stroke="#8a6d1a"/><rect x="${X(-xg-20)}" y="${Y(top)}" width="${10*sx}" height="${(top-sl-B)*vy}" fill="var(--au)" stroke="#8a6d1a"/>`;
 const ar=(x0,x1,y,t)=>`<line x1="${X(x0)}" y1="${Y(y)}" x2="${X(x1)}" y2="${Y(y)}" stroke="currentColor" marker-start="url(#a)" marker-end="url(#a)"/><text x="${(X(x0)+X(x1))/2}" y="${Y(y)-5}" text-anchor="middle" font-size="12" fill="currentColor">${t}</text>`;
 s+=ar(-xg,xg,2.0,`GAP ${G.toFixed(2)} µm`)+ar(-CW/2,CW/2,sl+B+CH+0.12,`CAP_W ${CW.toFixed(2)}`);
 s+=`<text x="${X(-xg-9.7)}" y="${Y(sl+B+MS)+14}" font-size="12">MTX_small ${MS.toFixed(2)} µm</text><text x="${X(CW/2)+4}" y="${Y(sl+B+CH/2)}" font-size="12" fill="currentColor">CAP_H ${CH.toFixed(2)}</text>`;
 s+=`<text x="${X(xg)+8}" y="${Y(2.1)}" font-size="12">signal 10 µm (tall)</text><text x="8" y="${Y(sl/2)+4}" font-size="11" fill="#fff">LN slab 275 nm</text><text x="8" y="${Y(0)+16}" font-size="11">BOX SiO₂</text><text x="${X(xg)+8}" y="${Y(sl+B/2)+4}" font-size="11">buffer ${(B*1e3).toFixed(0)} nm · vertical ×5.8</text>`;
 g("xs").innerHTML=`<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10z" fill="currentColor"/></marker></defs>`+s;}
function upd(){const G=val("GAP"),WG=val("WG");const cw=g("s_CAP_W");cw.max=G;cw.min=Math.min(2*WG,G);if(parseFloat(cw.value)>G)cw.value=G;if(parseFloat(cw.value)<2*WG)cw.value=Math.min(2*WG,G);
 const B=val("BUFFER_H")*1e-3,CW=val("CAP_W"),CH=val("CAP_H"),MS=val("MTX_SMALL");P.forEach(p=>g("l_"+p.k).textContent=(+g("s_"+p.k).value).toFixed(p.d)+" "+p.u);
 const dd=G-2*WG,f=dd<1e-6?0:(G-CW)/dd,x=[G,B,f,CH,MS,WG],r=pred(x),xw=[G,B-0.04,f,CH,MS,WG],rw=pred(xw);
 g("v").textContent=r.VpiL.mean.toFixed(3);g("vci").textContent=`95 %: ${r.VpiL.lo.toFixed(3)}–${r.VpiL.hi.toFixed(3)}`;
 g("il").textContent=r.IL.mean.toFixed(3);g("il").style.color=r.IL.hi>0.4?"var(--red)":"var(--ok)";g("ilci").textContent=`95 %: ${r.IL.lo.toFixed(3)}–${r.IL.hi.toFixed(3)}`;
 g("vw").textContent=rw.VpiL.mean.toFixed(3);g("ilw").textContent=rw.IL.mean.toFixed(3);
 const fl=[];if(B-0.04<C.lo[1])fl.push("worst-case buffer below the trained range (50 nm): extrapolated");if(B<0.1)fl.push("nominal buffer below the 100 nm process minimum");
 if(r.IL.hi>0.4)fl.push("IL upper 95 % bound above 0.4 dB/cm");
 g("flags").innerHTML=fl.length?fl.map(t=>`<div class="flag bad">${t}</div>`).join(""):`<div class="flag good">Inside the trained space · IL ≤ 0.4 dB/cm with 95 % confidence</div>`;draw(G,B,CW,CH,MS,WG)}
P.forEach(p=>g("s_"+p.k).addEventListener("input",upd));
function setv(o){const c=g("s_CAP_W");c.max=4.5;c.min=2.0;for(const k in o){if(k!=="CAP_W")g("s_"+k).value=o[k]}c.value=o.CAP_W;upd()}
g("base").onclick=()=>setv({GAP:3.2,BUFFER_H:100,CAP_W:3.0,CAP_H:0.5,MTX_SMALL:1.0,WG:1.4});g("best").onclick=()=>setv(__BEST__);
g("mod").textContent=Object.entries(C.outputs).map(([k,m])=>`${k}: ${m.kernel}${m.linear_mean?" + linear mean":""}${m.log10?", log10":""}`).join(" · ");
g("cvt").innerHTML="<tr><th>10-fold CV</th><th>R²</th><th>MAPE</th><th>max error</th><th>95 % coverage</th></tr>"+Object.entries(C.outputs).map(([k,m])=>`<tr><td>${k}</td><td>${m.cv.R2_phys.toFixed(4)}</td><td>${m.cv.MAPE_pct.toFixed(2)} %</td><td>${m.cv.maxAPE_pct.toFixed(1)} %</td><td>${m.cv.cover95_pct.toFixed(0)} %</td></tr>`).join("");
upd();
</script></body></html>"""
try:
    t = json.load(open("optimum_robust_IL0.4_gap3.5.json"))[0]
    best = dict(WG=t["WG"], GAP=t["GAP"], BUFFER_H=round(t["BUFFER_H"] * 1e3), CAP_W=t["CAP_W"], CAP_H=t["CAP_H"], MTX_SMALL=t["MTX_SMALL"])
except Exception:
    best = dict(WG=1.4, GAP=3.2, BUFFER_H=100, CAP_W=3.0, CAP_H=0.5, MTX_SMALL=1.0)
open("madrid1_predictor.html", "w").write(html.replace("__CARD__", json.dumps(card, separators=(",", ":"))).replace("__BEST__", json.dumps(best)))
print("written madrid1_predictor.html")
