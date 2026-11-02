"""AVNRT vs AVRT: get the locked beat SVGs ready for Illustrator (build_ai.jsx).

Reads 3-board/art/<beat>_<name>.svg (never changes them) and writes build/ai_src/<beat>.svg plus build/ai_src/layers.json.
Only the structure changes, never the look:
- every animatable piece becomes one top-level group L001, L002... (Illustrator mangles ids); layers.json maps each to its
  layer name. The groups the build animates inside (Heart, Diagram, Diagram/Active, ECG/*, Ablation) are split into their
  named children, each keeping the parent's transform. Unnamed siblings are merged and named after the last named layer
  ("Text/Patient1", "Dots/Smallloop"); unnamed children of a split group become "<group>/Base" (Mark's heart) or "<group>/Rest".
- <use href="#MarkHeart…"> is inlined (Illustrator and After Effects have no use of their own)
- filters are dropped and listed in layers.json, so After Effects adds them as effects: "soft" -> Drop Shadow on the card,
  "blurU" -> Gaussian Blur on the glow (Illustrator would rasterize them at 72 ppi)
- paint-order="stroke" halos (Illustrator ignores paint-order) become a stroked copy under a plain copy
- font-family + font-weight become the installed PostScript name (Inter-SemiBold, Manrope-SemiBold...)
- Meta: BeatID never goes in
Run: python3 prep_ai.py   (from anywhere)
"""
import copy, json, re, pathlib
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
VIDEO = HERE.parent.parent
ART = VIDEO / "3-board" / "art"
OUT = HERE / "ai_src"
NS = "http://www.w3.org/2000/svg"
Q = lambda t: f"{{{NS}}}{t}"
ET.register_namespace("", NS)
FACE = {("Inter", "400"): "Inter-Regular", ("Inter", "500"): "Inter-Medium", ("Inter", "600"): "Inter-SemiBold",
        ("Inter", "700"): "Inter-Bold", ("Manrope", "600"): "Manrope-SemiBold", ("Manrope", "700"): "Manrope-Bold"}
SPLIT = re.compile(r"^(Heart|Diagram|Diagram/Active|ECG(/.*)?|Ablation)$")
KIND = {"text": "Text", "circle": "Dots", "line": "Leader", "rect": "Box", "path": "Shape", "ellipse": "Shape", "g": "Group"}
BLUR = {"blurU": 200, "blur": 22}           # stdDeviation in the element's own units


def scale_of(transform):
    m = re.search(r"scale\(([\d.]+)", transform or "")
    return float(m.group(1)) if m else 1.0


def fonts(el):
    for t in el.iter(Q("text")):
        fam = t.attrib.pop("font-family", "Inter").split(",")[0].strip().strip("'\"")
        w = t.attrib.pop("font-weight", "400")
        st = [f"font-family:{FACE[(fam, w)]}"]
        for k in ("font-size", "letter-spacing"):
            if k in t.attrib: st.append(f"{k}:{t.attrib.pop(k)}" + ("px" if k == "font-size" else ""))
        t.set("style", ";".join(st))


def halos(el):
    """paint-order=stroke on a group or a text: a stroked copy (fill = stroke colour) under a plain copy."""
    for parent in list(el.iter()):
        for i, c in enumerate(list(parent)):
            po = c.get("paint-order")
            if po != "stroke": continue
            stroke, sw, lj = c.get("stroke"), c.get("stroke-width"), c.get("stroke-linejoin", "round")
            plain = copy.deepcopy(c)
            for k in ("paint-order", "stroke", "stroke-width", "stroke-linejoin"): plain.attrib.pop(k, None)
            halo = copy.deepcopy(plain)
            halo.set("id", (c.get("id") or "") + "_halo") if c.get("id") else None
            for t in halo.iter(Q("text")):
                t.set("fill", stroke); t.set("stroke", stroke); t.set("stroke-width", sw); t.set("stroke-linejoin", lj)
            wrap = ET.Element(Q("g"))
            if c.get("id"): wrap.set("id", c.get("id")); plain.attrib.pop("id", None); halo.attrib.pop("id", None)
            wrap.extend([halo, plain])
            parent.remove(c); parent.insert(i, wrap)


def strip_filters(el, fx, k):
    for e in el.iter():
        f = e.attrib.pop("filter", None)
        if not f: continue
        name = f[5:-1]
        if name == "soft": fx["shadow"] = True
        elif name in BLUR: fx["blur"] = round(BLUR[name] * k, 1)


def main():
    OUT.mkdir(exist_ok=True)
    allmap = {}
    for f in sorted(ART.glob("[1-7][A-Z]_*.svg")):
        if "mark-illustrator" in f.stem: continue           # Mark's placement file, not a beat
        beat = f.stem.split("_")[0]
        root = ET.parse(f).getroot()
        defs = {}
        for d in root.findall(Q("defs")):
            for c in d:
                if c.get("id"): defs[c.get("id")] = c
        for parent in list(root.iter()):                      # inline <use>
            for i, c in enumerate(list(parent)):
                if c.tag == Q("use"):
                    ref = (c.get("href") or c.get("{http://www.w3.org/1999/xlink}href"))[1:]
                    g = copy.deepcopy(defs[ref]); g.attrib.pop("id", None)
                    parent.remove(c); parent.insert(i, g)
        keep_defs = ET.Element(Q("defs"))
        if "hatch" in defs: keep_defs.append(defs["hatch"])
        body = [c for c in root if c.tag != Q("defs")]
        for c in list(root): root.remove(c)
        root.append(keep_defs)
        spec = []

        def add(name, el, fx):
            lid = f"L{len(spec) + 1:03d}"
            base, j = name, 2
            while any(x["name"] == name for x in spec): name = f"{base} {j}"; j += 1
            g = el if el.tag == Q("g") and not el.get("transform") and not el.get("opacity") else None
            if g is None:
                g = ET.Element(Q("g")); g.append(el)
            g.set("id", lid)
            root.append(g)
            spec.append({"id": lid, "name": name, **({"fx": fx} if fx else {})})

        def walk(children, parent_tf, k, group_name, last_named):
            pending = []
            def flush():
                if not pending: return
                tag = pending[0].tag.split("}")[1]
                if group_name:
                    nm = f"{group_name}/Base" if any(e.tag == Q("g") and len(list(e.iter(Q("path")))) > 50 for e in pending) else f"{group_name}/Rest"
                else:
                    nm = f"{KIND.get(tag, 'Shape')}/{(last_named[0] or 'Frame').split('/')[-1]}"
                n0, nm2 = nm, nm
                j = 2
                while any(s["name"] == nm2 for s in spec): nm2 = f"{n0} {j}"; j += 1
                g = ET.Element(Q("g"))
                if parent_tf: g.set("transform", parent_tf)
                fx = {}
                for e in pending: strip_filters(e, fx, k); g.append(e)
                add(nm2, g, fx)
                pending.clear()
            for c in children:
                cid = c.get("id")
                if cid == "BeatID": continue
                if cid and SPLIT.match(cid) and c.tag == Q("g") and any(x.get("id") for x in c):
                    flush()
                    tf = " ".join(x for x in (parent_tf, c.get("transform")) if x)
                    attrs = {a: c.get(a) for a in ("opacity", "clip-path", "mask") if c.get(a)}
                    if attrs:    # split groups carry no opacity/clip/mask in this art; say so if one ever does
                        raise SystemExit(f"{beat} {cid}: split group with {attrs}")
                    walk(list(c), tf, k * scale_of(c.get("transform")), cid, last_named)
                    last_named[0] = cid
                elif cid:
                    flush()
                    fx = {}
                    strip_filters(c, fx, k * scale_of(c.get("transform")))
                    if parent_tf:
                        g = ET.Element(Q("g")); g.set("transform", parent_tf); g.append(c); el = g
                    else: el = c
                    el_name = cid
                    add(el_name, el, fx)
                    last_named[0] = cid
                else:
                    if pending and pending[-1].tag != c.tag and not group_name: flush()
                    pending.append(c)
            flush()

        walk(body, "", 1.0, None, [None])
        for g in root:
            if g.tag == Q("g"):
                for e in g.iter():
                    if e is not g and e.get("id") and e.tag not in (Q("g"), Q("clipPath"), Q("mask"), Q("linearGradient"), Q("pattern")): e.attrib.pop("id", None)
        halos(root)
        fonts(root)
        for e in root.iter():                                  # ids inside layers can clash with L001...; Illustrator renames them anyway
            if e.get("id") and not re.fullmatch(r"L\d{3}|hatch|hb\w+", e.get("id")): e.attrib.pop("id")
        txt = ET.tostring(root, encoding="unicode")
        dst = OUT / f"{beat}.svg"
        if not dst.exists() or dst.read_text(encoding="utf-8") != txt:   # untouched beats keep their date, so build_ai.jsx skips them
            dst.write_text(txt, encoding="utf-8")
            print("updated", beat)
        allmap[beat] = {"file": f.name, "layers": spec}
    (OUT / "layers.json").write_text(json.dumps(allmap, indent=1, ensure_ascii=False), encoding="utf-8")
    for b, v in allmap.items():
        print(b, len(v["layers"]), " | ".join(x["name"] + (f" {x['fx']}" if "fx" in x else "") for x in v["layers"]))


if __name__ == "__main__":
    main()
