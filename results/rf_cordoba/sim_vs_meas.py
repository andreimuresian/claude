import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np, copy
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
# --- chart: % change, sim vs measured
labs=["n$_m$","Z$_0$","α @ 30 GHz"]
sim=[0.68,-0.64,0.64]; w62=[1.6,-1.0,6.0]; w63=[1.8,-0.6,1.4]
x=np.arange(3); fig,ax=plt.subplots(figsize=(5.6,3.2),dpi=200)
for k,(v,c,l) in enumerate([(sim,"#0E2268","Simulation (2D FEM)"),(w62,"#F20013","4CA0162"),(w63,"#F2A900","4CA0163")]):
    b=ax.bar(x+(k-1)*0.26,v,0.26,color=c,label=l)
    ax.bar_label(b,[f"{u:+.1f}" for u in v],fontsize=7,padding=2)
ax.axhline(0,color="k",lw=0.6); ax.set_xticks(x,labs); ax.set_ylabel("Change ALD − no ALD (%)")
ax.set_ylim(-2,7); ax.legend(fontsize=7,frameon=False,loc="upper left"); ax.spines[["top","right"]].set_visible(False)
ax.set_title("40 nm ALD: relative change",fontsize=9); fig.tight_layout(); fig.savefig("sim_vs_meas.png")
# --- slide
p=Presentation("in.pptx"); ref=p.slides[7]; s=p.slides.add_slide(ref.slide_layout)
for ph in list(s.placeholders): ph._element.getparent().remove(ph._element)
def tb(x,y,w,h,paras):
    t=s.shapes.add_textbox(Emu(x),Emu(y),Emu(w),Emu(h)).text_frame; t.word_wrap=True
    for i,(txt,sz,b,col) in enumerate(paras):
        pa=t.paragraphs[0] if i==0 else t.add_paragraph(); r=pa.add_run(); r.text=txt
        r.font.size=Pt(sz); r.font.bold=b; r.font.name="Arial"; r.font.color.rgb=RGBColor.from_string(col)
def box(x,y,w,h,fill,line=None):
    r=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Emu(x),Emu(y),Emu(w),Emu(h)); r.fill.solid(); r.fill.fore_color.rgb=RGBColor.from_string(fill)
    if line: r.line.color.rgb=RGBColor.from_string(line)
    else: r.line.fill.background()
    r.adjustments[0]=0.05; r.shadow.inherit=False
tb(502920,384048,11000000,640080,[("Simulation vs measurement",28,False,"1A1A1A")])
tb(548640,932688,10789920,365760,[("2D FEM (volumetric gold, ALD εr 9.8, lossless) vs per-line median change, CORDOBA 8 mm",15,True,"0E2268")])
rows=[("FOM","Simulation","4CA0162","4CA0163","Agreement"),
 ("Δnm @ 60 GHz","+0.014 (+0.68 %)","+0.034 (+1.6 %)","+0.038 (+1.8 %)","sign ✓, ~2.5× low"),
 ("ΔZ0 (Ω)","−0.23 (−0.64 %)","−0.41 (−1.0 %)","−0.26 (−0.6 %)","✓ good"),
 ("Δα @ 30 GHz (dB/cm)","≈ +0.02–0.03","+0.26","+0.06","4CA0163 ✓, 4CA0162 ~10×"),
 ("Δα @ 60 GHz (dB/cm)","+0.035 (+0.64 %)","+0.21","−0.06 (±0.07)","4CA0163 ✓, 4CA0162 ✗"),
 ("Δα, tan δ = 0.05","+0.07 @ 60 GHz","—","—","upper bound, still < 0.21")]
tbl=s.shapes.add_table(len(rows),5,Emu(411480),Emu(1371600),Emu(6035040),Emu(2414016)).table
for j,wd in enumerate([1500000,1250000,1050000,1050000,1185040]): tbl.columns[j].width=Emu(wd)
for i,r in enumerate(rows):
    tbl.rows[i].height=Emu(402336)
    for j,v in enumerate(r):
        c=tbl.cell(i,j); c.fill.solid(); c.fill.fore_color.rgb=RGBColor.from_string("0E2268" if i==0 else ("F6F7FA" if i%2 else "FFFFFF"))
        c.margin_left=c.margin_right=Emu(50000)
        pa=c.text_frame.paragraphs[0]; pa.text=""; ru=pa.add_run(); ru.text=v; ru.font.size=Pt(9.5); ru.font.name="Arial"
        ru.font.bold=(i==0 or j==0); ru.font.color.rgb=RGBColor.from_string("FFFFFF" if i==0 else "1A1A1A")
box(411480,4000000,2926080,2263000,"F1F3F8")
tb(548640,4070000,2651760,2150000,[("Agree",13.5,True,"2E8B57"),
 ("All signs: nm ↑, Z0 ↓, α ↑",12,False,"1A1A1A"),("Z0: −0.64 % sim vs −0.6…−1.0 %",12,False,"1A1A1A"),
 ("→ ALD capacitance (εr 9.8) captured",12,False,"1A1A1A"),("α on 4CA0163 within ±0.07 dB/cm",12,False,"1A1A1A")])
box(3520440,4000000,2926080,2263000,"F1F3F8")
tb(3657600,4070000,2651760,2150000,[("Differ",13.5,True,"F20013"),
 ("Δnm 2.5× larger than sim; Δn/n + ΔZ/Z ≈ +1 % → L also rises: not a cross-section effect",12,False,"1A1A1A"),
 ("Δα on 4CA0162: 10× sim; ALD tan δ cannot explain it",12,False,"1A1A1A")])
box(6629400,1371600,5212080,3108960,"FFFFFF","D9DCE3")
s.shapes.add_picture("sim_vs_meas.png",Emu(6675120),Emu(1440000),Emu(5120640),Emu(2926080))
box(6629400,4617720,5212080,1645920,"F1F3F8")
tb(6766560,4690872,4937760,1536192,[("Likely cause of the gaps",13.5,True,"0E2268"),
 ("Pads/tees are inside the 8 mm de-embedding; the 2D model has the uniform line only.",12,False,"1A1A1A"),
 ("Pad ripple 0.6 → 2.3 Ω after ALD: the ends changed.",12,False,"1A1A1A"),
 ("Wafer-dependent α: probe contact / gold process, not ALD loss.",12,False,"1A1A1A"),
 ("Next: multi-length or TRL extraction before/after ALD.",12,False,"1A1A1A")])
# move new slide before conclusions (index 8)
lst=p.slides._sldIdLst; el=lst[-1]; lst.remove(el); lst.insert(8,el)
p.save("Cordoba_ALD_RF_impact.pptx")
