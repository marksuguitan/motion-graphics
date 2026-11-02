"""Flatten a key-frame SVG into one top-level group per After Effects layer.

A node becomes its own layer when its name (or a suffix of its path) is a layer named in the
motion notes; every ancestor of such a node is opened up so its other children become layers too
("Parent/child"). Unnamed leftovers stay together in a layer named after their parent.
Ancestor transforms and presentation attributes are kept by nesting copies of the ancestor
<g> (minus id) around each pulled-out child, so the picture does not change.
Class-based CSS is inlined, the storyboard-only Beat_ID is dropped.
Output top-level groups carry id="L001"...; layers.json maps them to names (Illustrator mangles ids).
"""
import json, re, sys, copy
import xml.etree.ElementTree as ET

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
T = lambda t: f"{{{NS}}}{t}"
DROP = {"Beat_ID"}
NONRENDER = {"clipPath", "mask", "filter", "linearGradient", "radialGradient", "pattern", "symbol", "marker", "defs", "style"}


def segs(path, cid):
    """path segments + this id's segments, collapsing a repeat ('Lungs' + 'Lungs/R' -> Lungs/R)."""
    out = list(path)
    for p in cid.split("/"):
        if not (out and out[-1] == p):
            out.append(p)
    return out


def inline_css(root):
    rules = []
    for st in root.iter(T("style")):
        for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", st.text or ""):
            decl = [d.strip() for d in body.split(";") if d.strip()]
            for s in sel.split(","):
                s = s.strip()
                if re.fullmatch(r"\.[\w-]+", s):
                    rules.append((s[1:], decl))
    for el in root.iter():
        cls = (el.get("class") or "").split()
        if not cls:
            continue
        d = {}
        for c, decl in rules:
            if c in cls:
                for kv in decl:
                    k, v = kv.split(":", 1)
                    d[k.strip()] = v.strip()
        old = el.get("style")
        if old:
            for kv in old.split(";"):
                if ":" in kv:
                    k, v = kv.split(":", 1); d[k.strip()] = v.strip()
        if d:
            el.set("style", "; ".join(f"{k}: {v}" for k, v in d.items()))
        el.attrib.pop("class", None)
    for parent in list(root.iter()):
        for c in list(parent):
            if c.tag == T("style"):
                parent.remove(c)
            if c.tag == T("defs") and len(c) == 0:
                parent.remove(c)


def tidy(name):
    """Readable layer names: drop the 'Axial/' container, and 'Chest/' in front of parts the notes name bare."""
    if name.startswith("Axial/") and name != "Axial/Chest":
        name = name[6:]
    for p in ("Chest/Lungs", "Chest/Hilum", "Chest/Inflammation"):
        if name.startswith(p):
            name = name[6:]
    return name


def flatten(svg_in, svg_out, refs):
    tree = ET.parse(svg_in); root = tree.getroot()
    inline_css(root)
    refs = set(refs)

    def target_name(path):
        # longest suffix of the path (as "A/B/C") that the motion notes name
        for i in range(len(path)):
            s = "/".join(path[i:])
            if s in refs:
                return s
        return None

    def wanted_desc(el, path):
        """True if a descendant below el (not el itself) is a named layer target."""
        for c in el:
            if c.get("id"):
                if wanted(c, segs(path, c.get("id"))):
                    return True
            elif c.tag == T("g") and wanted_desc(c, path):
                return True
        return False

    def wanted(el, path):
        return bool(target_name(path)) or wanted_desc(el, path)

    layers = []  # (name, element, wrappers)

    def emit(el, name, wrappers):
        layers.append((name, el, wrappers))

    def visit(el, path, disp, wrappers):
        # el is a group being opened: each child becomes a layer or is opened further
        loose = []
        for c in list(el):
            cid = c.get("id")
            if cid in DROP:
                continue
            if c.tag.split("}")[-1] in NONRENDER:
                hoisted.append(c); continue
            if not cid:
                if c.tag == T("g") and wanted_desc(c, path):
                    # id-less wrapper (e.g. an opacity group): see through it
                    if loose:
                        emit(loose, f"{disp}/Other" if disp else "Base", wrappers); loose = []
                    w = copy.copy(c); w[:] = []
                    visit(c, path, disp, wrappers + [w])
                else:
                    loose.append(c)
                continue
            cpath = segs(path, cid)
            cname = target_name(cpath) or "/".join(segs(disp.split("/") if disp else [], cid))
            sub_wanted = c.tag == T("g") and wanted_desc(c, cpath)
            if sub_wanted:
                if loose:
                    emit(loose, f"{disp}/Other" if disp else "Base", wrappers); loose = []
                w = copy.copy(c); w.attrib = {k: v for k, v in c.attrib.items() if k != "id"}; w[:] = []
                visit(c, cpath, cname, wrappers + [w])
            else:
                if loose:
                    emit(loose, f"{disp}/Other" if disp else "Base", wrappers); loose = []
                emit([c], cname, wrappers)
        if loose:
            emit(loose, f"{disp}/Other" if disp else "Base", wrappers)

    hoisted = []
    visit(root, [], "", [])
    # rebuild root
    keep = {k: v for k, v in root.attrib.items()}
    root[:] = []
    if hoisted:
        dd = ET.SubElement(root, T("defs"))
        for d in hoisted:
            if d.tag == T("defs"):
                dd.extend(list(d))
            else:
                dd.append(d)
    out_names = []
    seen = {}
    for i, (name, els, wrappers) in enumerate(layers):
        name = tidy(name)
        n = name
        if n in seen:
            seen[n] += 1; n = f"{name} {seen[name]}"
        else:
            seen[n] = 1
        lid = f"L{i+1:03d}"
        top = ET.SubElement(root, T("g"), {"id": lid})
        wrap_masked = any(w.get("mask") for w in wrappers)
        cur = top
        for w in wrappers:
            ww = copy.copy(w); ww[:] = []; ww.attrib.pop("mask", None); cur.append(ww); cur = ww
        for e in els:
            cur.append(e)
        # the played half of a sound wave is clipped only for the storyboard frame; the .ai keeps the whole wave (AE wipes it)
        for e in els:
            for x in e.iter():
                if "playclip" in (x.get("clip-path") or ""):
                    x.attrib.pop("clip-path")
        hidden = any(e.get("data-hidden") == "1" for e in els)
        # Illustrator drops SVG <mask> content on import: remove the mask here, AE puts the soft bottom edge back
        masked = False
        for e in els:
            for x in e.iter():
                if x.get("mask"):
                    x.attrib.pop("mask"); masked = True
        masked = masked or wrap_masked
        for e in els:
            if e.attrib.pop("data-hidden", None):
                e.attrib.pop("visibility", None)   # visible in the .ai; the JSX hides the layer
        out_names.append({"id": lid, "name": n, **({"hidden": True} if hidden else {}), **({"fade_bottom": True} if masked else {})})
    tree.write(svg_out, encoding="unicode")
    # Helvetica has no arrow glyphs in Illustrator: set arrows in Arial (same look at these sizes)
    txt = open(svg_out, encoding="utf-8").read()
    txt = re.sub(r">([^<]*)<", lambda m: ">" + re.sub("([\u2190-\u2193])", r'<tspan font-family="Arial">\1</tspan>', m.group(1)) + "<", txt)
    # Arial has no Light face: in light (300) text the arrow takes Arial Regular
    txt = re.sub(r'(<text[^>]*font-weight="300"[^>]*>)(.*?)(</text>)',
                 lambda m: m.group(1) + m.group(2).replace('<tspan font-family="Arial">', '<tspan font-family="Arial" font-weight="400">') + m.group(3), txt, flags=re.S)
    open(svg_out, "w", encoding="utf-8").write(txt)
    return out_names


if __name__ == "__main__":
    refs = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    allmap = {}
    for f in sys.argv[3:]:
        base = f.split("/")[-1]
        allmap[base[:-4]] = flatten(f, f"{outdir}/{base}", refs)
    json.dump(allmap, open(f"{outdir}/layers.json", "w"), indent=1)
    for k, v in allmap.items():
        print(k, len(v), ", ".join(x["name"] for x in v))
