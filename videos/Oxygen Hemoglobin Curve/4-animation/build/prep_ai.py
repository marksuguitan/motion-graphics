"""Oxygen Hemoglobin Curve: get the approved beat SVGs ready for Illustrator (build_ai.jsx).

Reads 3-board/art/<beat>_<name>.svg (never changes them) and writes build/ai_src/<beat>.svg:
- each top-level group gets id L001, L002... (Illustrator mangles ids); layers.json maps them to the
  layer names, Group_x2F_Sublayer -> Group/Sublayer
- font-family + font-weight become the installed PostScript name (Inter-Medium, Manrope-Bold...), so
  Illustrator picks the right face instead of guessing from the weight
Run: python3 prep_ai.py   (from anywhere)
"""
import json, re, pathlib
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
VIDEO = HERE.parent.parent
ART = VIDEO / "3-board" / "art"
OUT = HERE / "ai_src"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
FACE = {("Inter", "400"): "Inter-Regular", ("Inter", "500"): "Inter-Medium", ("Inter", "600"): "Inter-SemiBold",
        ("Inter", "700"): "Inter-Bold", ("Manrope", "600"): "Manrope-SemiBold", ("Manrope", "700"): "Manrope-Bold"}


def face(m):
    st = dict(kv.split(":", 1) for kv in m.group(1).split(";") if ":" in kv)
    ps = FACE[(st.pop("font-family"), st.pop("font-weight"))]
    return 'style="' + ";".join([f"font-family:{ps}"] + [f"{k}:{v}" for k, v in st.items()]) + '"'


def main():
    OUT.mkdir(exist_ok=True)
    allmap = {}
    for f in sorted(ART.glob("*.svg")):
        beat = f.stem.split("_")[0]
        root = ET.parse(f).getroot()
        spec = []
        for c in root:
            if c.tag == f"{{{NS}}}g":
                lid = f"L{len(spec) + 1:03d}"
                spec.append({"id": lid, "name": c.get("id").replace("_x2F_", "/")})
                c.set("id", lid)
        txt = ET.tostring(root, encoding="unicode")
        txt = re.sub(r'style="([^"]*font-family:[^"]*)"', face, txt)
        dst = OUT / f"{beat}.svg"
        if not dst.exists() or dst.read_text(encoding="utf-8") != txt:   # untouched beats keep their date, so build_ai.jsx skips them
            dst.write_text(txt, encoding="utf-8")
            print("updated", beat)
        allmap[beat] = {"file": f.name, "layers": spec}
    (OUT / "layers.json").write_text(json.dumps(allmap, indent=1), encoding="utf-8")
    for b, v in allmap.items():
        print(b, len(v["layers"]), ", ".join(x["name"] for x in v["layers"]))


if __name__ == "__main__":
    main()
