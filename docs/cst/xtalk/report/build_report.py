"""Build crosstalk_briefing.html: self-contained (images inlined as base64)."""
import base64, os, sys
IMG = sys.argv[1] if len(sys.argv) > 1 else "."
OUT = sys.argv[2] if len(sys.argv) > 2 else "crosstalk_briefing.html"
def img(name, alt, w="100%"):
    p = os.path.join(IMG, name); mime = "image/jpeg" if name.endswith(".jpg") else "image/png"
    b = base64.b64encode(open(p, "rb").read()).decode()
    return f'<img src="data:{mime};base64,{b}" alt="{alt}" style="width:{w}">'
HTML = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"), encoding="utf-8").read()
for key, (name, alt) in {
    "IMG_MODES": ("modes.jpg", "CST 2-D port modes"),
    "IMG_LINE": ("line_from_s4p.png", "line from 3-D runs"),
    "IMG_VALID": ("modal_vs_s4p_v3.png", "model vs 3-D CST"),
    "IMG_GUI4": ("gui4.png", "the four GUI graphs"),
    "IMG_NULLS": ("nulls.png", "NEXT nulls"),
    "IMG_LENGTH": ("length.png", "length dependence"),
}.items():
    HTML = HTML.replace("{{" + key + "}}", img(name, alt))
open(OUT, "w", encoding="utf-8").write(HTML)
print(OUT, os.path.getsize(OUT) // 1024, "kB")
