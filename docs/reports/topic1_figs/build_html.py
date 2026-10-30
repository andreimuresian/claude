"""Embed the figures into topic1_template.html -> topic1_field_eo_crosstalk.html."""
import base64, os
here = os.path.dirname(os.path.abspath(__file__)); root = os.path.dirname(here)
s = open(os.path.join(root, "topic1_template.html")).read()
for k, f in (("F2", "f2_voltage.png"), ("F3", "f3_matching.png"), ("F4", "f4_xtalk.png")):
    b = base64.b64encode(open(os.path.join(here, f), "rb").read()).decode()
    s = s.replace("{{%s}}" % k, "data:image/png;base64," + b)
open(os.path.join(root, "topic1_field_eo_crosstalk.html"), "w").write(s)
