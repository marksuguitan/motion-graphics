# Beat frames for Sinus Tach vs SVT, Motion Board pass 1, style A (Warm Clinical, white ground).
# Usage: python3 -I make_beats.py <art.json> <Loops.tsx> <out dir>
# One SVG per beat at the end state of its Intent, 1920x1080, layers named Group/Sublayer.
import sys, os, math, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import heartart

ART, LOOPS, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
HEART, COND = heartart.load(ART)
SA, AV = heartart.SA, heartart.AV

C = dict(bg="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A",
         coral="#F0645A", coralInk="#C2443B", coralSoft="#FDE3E0",
         teal="#2E9C8F", tealInk="#1F7A70", tealSoft="#DDF0EE",
         amber="#E3A33B", amberInk="#8A5A12", amberSoft="#FBEBD2",
         muted="#E8DED6", grid="#F2F0EC", gridBig="#E6E4E0")
HF = "font-family:Manrope"; BF = "font-family:Inter"
L = lambda s: s.replace("/", "_x2F_")

# ---------------------------------------------------------------- text and chips
def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def kicker(text, col=None, x=120, y=104):
    return f'<g id="{L("Header/Kicker")}"><text x="{x}" y="{y}" style="{HF};font-size:23px;font-weight:700;letter-spacing:3px" fill="{col or C["ink2"]}">{esc(text)}</text></g>'

def heading(parts, x=120, y=168, size=56, anchor="start", layer="Header/Title"):
    """parts: list of (text, color or None)."""
    sp = "".join(f'<tspan fill="{c or C["ink"]}">{esc(t)}</tspan>' for t, c in parts)
    return f'<g id="{L(layer)}"><text x="{x}" y="{y}" text-anchor="{anchor}" style="{HF};font-size:{size}px;font-weight:600">{sp}</text></g>'

def textw(s, size, weight=500): return len(s) * size * (0.56 if weight >= 600 else 0.53)

CHIP = dict(teal=(C["tealSoft"], C["tealInk"], None), coral=(C["coralSoft"], C["coralInk"], None),
            amber=(C["amberSoft"], C["amberInk"], None), plain=(C["bg"], C["ink"], C["div"]), dark=(C["ink"], "#FFFFFF", None))

def chip(x, y, text, kind="plain", size=28, weight=500):
    bg, fg, stroke = CHIP[kind]
    w = textw(text, size, weight) + 44; h = size + 26
    st = f' stroke="{stroke}" stroke-width="2"' if stroke else ""
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="12" fill="{bg}"{st}/>'
            f'<text x="{x+22}" y="{y+h/2+size*0.36:.0f}" style="{BF};font-size:{size}px;font-weight:{weight}" fill="{fg}">{esc(text)}</text>'), w

def chips(x, y, items, layer, gap=16, vertical=True, size=28):
    g = [f'<g id="{L(layer)}">']
    for text, kind in items:
        s, w = chip(x, y, text, kind, size)
        g.append(s)
        if vertical: y += size + 26 + gap
        else: x += w + gap
    g.append('</g>')
    return "\n".join(g)

def para(x, y, text, width_chars, size=30, col=None, layer="Text/Body", weight=400):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width_chars and cur: lines.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    lines.append(cur)
    ts = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else size*1.35:.0f}">{esc(l)}</tspan>' for i, l in enumerate(lines))
    return f'<g id="{L(layer)}"><text x="{x}" y="{y}" style="{BF};font-size:{size}px;font-weight:{weight}" fill="{col or C["ink2"]}">{ts}</text></g>'

def label(x, y, text, anchor="start", layer="Labels/Label", size=28, col=None):
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="{BF};font-size:{size}px;font-weight:500" fill="{col or C["ink"]}">{esc(text)}</text>'

def leader(p, q, text, anchor, layer):
    return (f'<g id="{L(layer)}"><line x1="{p[0]:.0f}" y1="{p[1]:.0f}" x2="{q[0]:.0f}" y2="{q[1]:.0f}" stroke="{C["ink2"]}" stroke-width="2"/>'
            + label(q[0] + (-12 if anchor == "end" else 12), q[1] + 10, text, anchor) + '</g>')

# ---------------------------------------------------------------- the heart
HB = (1250, 650)   # top-left of the heart art in art units

def heart_defs():
    body = "\n".join(f'<path d="{d}" fill="{f}" stroke="{f}" stroke-width="0.73"/>' for d, f in HEART)
    cond = "".join(f'<symbol id="cond-{k}" viewBox="0 0 8000 8000" width="8000" height="8000">' + "".join(f'<path d="{d}"/>' for d in v) + '</symbol>' for k, v in COND.items())
    return f'<symbol id="heart" viewBox="0 0 8000 8000" width="8000" height="8000">{body}</symbol>{cond}'

def cond_layers(prefix, lit, faded=()):
    g = []
    for k, name in (("atria", "Atria"), ("sa", "SANode"), ("av", "AVNode"), ("his", "HisPurkinje")):
        col = C["amber"] if k in lit else C["muted"]
        op = ' opacity="0.45"' if k in faded else ""
        g.append(f'<g id="{L(prefix + "/" + name)}" fill="{col}" stroke="{col}" stroke-width="0.73"{op}><use href="#cond-{k}"/></g>')
    return "".join(g)

def heart(x, y, s, lit, faded=(), layer="Heart", glow=()):
    """Place the heart with its art top-left at stage (x, y), scale s (stage px per art unit)."""
    tx, ty = x - HB[0]*s, y - HB[1]*s
    g = [f'<g id="{L(layer + "/Group")}" transform="translate({tx:.1f} {ty:.1f}) scale({s:.5f})">',
         f'<g id="{L(layer + "/Body")}"><use href="#heart"/></g>', cond_layers(layer, lit, faded)]
    for k in glow:
        p = SA if k == "sa" else AV
        g.append(f'<g id="{L(layer + "/Glow")}"><circle cx="{p[0]}" cy="{p[1]}" r="360" fill="{C["amber"]}" opacity="0.28"/></g>')
    g.append('</g>')
    stage = lambda u, v: (tx + u*s, ty + v*s)
    return "\n".join(g), stage

# ---------------------------------------------------------------- loops (geometry from Loops.tsx)
ACC = "M6295 3770 L6200 3440 L6010 3110"
RX, RY = 330, 250
AVNRT_D = f"M{AV[0]} {AV[1]-RY}a{RX} {RY} 0 1 1 -0.1 0"
AVRT_D = re.search(r"AVRT_D = `([^`]+)`", open(LOOPS).read()).group(1)

def sample(d):
    tok = re.findall(r"[MLCZ]|-?\d*\.?\d+", d)
    i, cmd, cur, start, pts = 0, "", (0, 0), (0, 0), []
    def num():
        nonlocal i; i += 1; return float(tok[i-1])
    while i < len(tok):
        if tok[i] in "MLCZ": cmd = tok[i]; i += 1
        if cmd == "M": cur = (num(), num()); start = cur; pts.append(cur); cmd = "L"; continue
        if cmd == "L": cur = (num(), num()); pts.append(cur); continue
        if cmd == "C":
            a, b, p = (num(), num()), (num(), num()), (num(), num())
            for k in range(1, 41):
                u = k/40; m = 1-u
                pts.append((m**3*cur[0]+3*m*m*u*a[0]+3*m*u*u*b[0]+u**3*p[0], m**3*cur[1]+3*m*m*u*a[1]+3*m*u*u*b[1]+u**3*p[1]))
            cur = p; continue
        if cmd == "Z": pts.append(start); cur = start; cmd = ""
    return pts

def at(pts, f):
    Ls = [0]
    for k in range(1, len(pts)): Ls.append(Ls[-1] + math.dist(pts[k], pts[k-1]))
    s = (f % 1) * Ls[-1]
    for k in range(1, len(Ls)):
        if Ls[k] >= s:
            t = (s - Ls[k-1]) / ((Ls[k]-Ls[k-1]) or 1)
            return (pts[k-1][0]+(pts[k][0]-pts[k-1][0])*t, pts[k-1][1]+(pts[k][1]-pts[k-1][1])*t), math.degrees(math.atan2(pts[k][1]-pts[k-1][1], pts[k][0]-pts[k-1][0]))
    return pts[-1], 0

AVRT_PTS = sample(AVRT_D)
AVNRT_PTS = [(AV[0]+RX*math.sin(2*math.pi*k/200), AV[1]-RY*math.cos(2*math.pi*k/200)) for k in range(201)]

def arrow(p, ang, size, col):
    x, y = p
    return (f'<path d="M{size*1.1:.0f},0 L{-size*0.8:.0f},{-size*0.95:.0f} L{-size*0.45:.0f},0 L{-size*0.8:.0f},{size*0.95:.0f} Z" fill="{col}" stroke="#FFFFFF" '
            f'stroke-width="{size*0.28:.0f}" stroke-linejoin="round" transform="translate({x:.0f} {y:.0f}) rotate({ang:.1f})"/>')

def loop_card(uid, kind, x, y, w, h, view=None, center=None, block=False, lit=("sa", "atria", "av", "his")):
    view = view or (6600 if kind == "avrt" else 4200)
    cx, cy = center or ((4500, 4500) if kind == "avrt" else (4200, 3900))
    S = w / view
    tx, ty = w/2 - cx*S, h/2 - cy*S
    px = lambda v: v / S
    pts, d = (AVRT_PTS, AVRT_D) if kind == "avrt" else (AVNRT_PTS, AVNRT_D)
    g = [f'<g id="{L("Loop" + uid + "/Card")}">',
         f'<clipPath id="clip-{uid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24"/></clipPath>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{C["soft"]}"/>',
         f'<g clip-path="url(#clip-{uid})"><g transform="translate({x+tx:.2f} {y+ty:.2f}) scale({S:.5f})">',
         f'<g id="{L("Loop" + uid + "/Heart")}"><use href="#heart"/></g>', cond_layers("Loop" + uid, lit)]
    col = C["ink2"] if block else C["coral"]
    if kind == "avrt":
        g.append(f'<g id="{L("Loop" + uid + "/AccessoryPathway")}"><path d="{ACC}" fill="none" stroke="{C["coral"]}" stroke-width="{px(16):.0f}" stroke-linecap="round"/>'
                 f'<path d="{ACC}" fill="none" stroke="#FFFFFF" stroke-width="{px(5):.0f}" stroke-linecap="round" stroke-dasharray="{px(2):.0f} {px(10):.0f}"/></g>')
    dash = f' stroke-dasharray="{px(6):.0f} {px(9):.0f}"' if block else ""
    g.append(f'<g id="{L("Loop" + uid + "/Circuit")}"><path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="{px(15):.0f}" stroke-linecap="round" opacity="0.95"/>'
             f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{px(8):.0f}" stroke-linecap="round"{dash}/>')
    if not block:
        for f in ([0.12, 0.45, 0.80] if kind == "avrt" else [0.25, 0.75]):
            p, ang = at(pts, f); g.append(arrow(p, ang, px(18), C["coral"]))
    g.append('</g>')
    if not block:
        p, _ = at(pts, 0.62 if kind == "avrt" else 0.5)
        g.append(f'<g id="{L("Loop" + uid + "/Pulse")}"><circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="{px(16):.0f}" fill="{C["amber"]}" stroke="#FFFFFF" stroke-width="{px(5):.0f}"/></g>')
    g.append('</g></g>')
    if block:
        bx, by = x + tx + AV[0]*S, y + ty + AV[1]*S
        g.append(f'<g id="{L("Loop" + uid + "/Blocked")}"><rect x="{bx-74:.0f}" y="{by-20:.0f}" width="148" height="40" rx="10" fill="{C["ink"]}"/>'
                 f'<text x="{bx:.0f}" y="{by+8:.0f}" text-anchor="middle" style="{BF};font-size:20px;font-weight:700;letter-spacing:1px" fill="#FFFFFF">BLOCKED</text></g>')
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="none" stroke="{C["div"]}" stroke-width="2"/></g>')
    return "\n".join(g)

def schematic(x, y, w, h, block=False, layer="Schematic"):
    """Atria above, a ring at the AV node, His bundle below splitting to the ventricles."""
    cx = x + w/2; ry = y + h*0.30; r = 70
    col = C["ink2"] if block else C["coral"]
    g = [f'<g id="{L(layer + "/Card")}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{C["soft"]}" stroke="{C["div"]}" stroke-width="2"/></g>',
         f'<g id="{L(layer + "/Paths")}" fill="none" stroke-linecap="round" stroke-linejoin="round">',
         f'<path d="M{cx} {y+60} V{ry-r}" stroke="{C["div"]}" stroke-width="22"/>',
         f'<path d="M{cx} {ry+r} V{y+h*0.58} L{cx-w*0.22} {y+h-70} M{cx} {y+h*0.58} L{cx+w*0.22} {y+h-70}" stroke="{C["div"]}" stroke-width="22"/>',
         f'<path d="M{cx} {ry+r} V{y+h*0.58} L{cx-w*0.22} {y+h-70} M{cx} {y+h*0.58} L{cx+w*0.22} {y+h-70}" stroke="{C["amber"] if not block else C["div"]}" stroke-width="8"/>',
         f'<circle cx="{cx}" cy="{ry}" r="{r}" stroke="{C["div"]}" stroke-width="22"/>',
         f'<circle cx="{cx}" cy="{ry}" r="{r}" stroke="{col}" stroke-width="8"' + (' stroke-dasharray="6 10"' if block else '') + '/>', '</g>']
    if block:
        g.append(f'<g id="{L(layer + "/Blocked")}"><rect x="{cx-74}" y="{ry-20}" width="148" height="40" rx="10" fill="{C["ink"]}"/>'
                 f'<text x="{cx}" y="{ry+8}" text-anchor="middle" style="{BF};font-size:20px;font-weight:700;letter-spacing:1px" fill="#FFFFFF">BLOCKED</text></g>')
    else:
        a = math.radians(-35)
        g.append(f'<g id="{L(layer + "/Pulse")}"><circle cx="{cx + r*math.cos(a):.0f}" cy="{ry + r*math.sin(a):.0f}" r="15" fill="{C["amber"]}" stroke="#FFFFFF" stroke-width="5"/></g>')
    g.append(f'<g id="{L(layer + "/Labels")}">' + label(cx, y+48, "Atria", "middle", size=24, col=C["ink2"])
             + label(cx - r - 20, ry + 9, "AV node", "end", size=24, col=C["ink2"])
             + label(cx + 26, y + h*0.52, "His bundle", "start", size=24, col=C["ink2"])
             + label(cx, y + h - 26, "Ventricles", "middle", size=24, col=C["ink2"]) + '</g>')
    return "\n".join(g)

# ---------------------------------------------------------------- ECG (port of ecg.ts)
PXS, PXMV = 280, 112
def g_(t, c, s, a): return a * math.exp(-((t-c)**2) / (2*s*s))
def beatV(t, rr, kind):
    qt = 0.40 * math.sqrt(rr); tc = 0.72*qt; ts = 0.11*qt; v = 0
    if kind == "sinus": v += g_(t, -0.10, 0.024, 0.16)
    v += g_(t, 0.012, 0.0055, -0.08) + g_(t, 0.030, 0.0095, 1.25) + g_(t, 0.052, 0.0075, -0.28)
    if kind == "avnrt": v += g_(t, 0.080, 0.0095, -0.14)
    return v + g_(t, tc, ts, 0.30)
def place(segs):
    beats, t = [], 0.25
    for kind, bpm, dur in segs:
        start, end = t, t + dur
        if kind == "pause": t = end; continue
        while t < end:
            rr = 60/bpm; beats.append((t, rr, kind)); t += rr
    return beats
STRIPS = dict(open170=[("sinus", 170, 14)], sinus130=[("sinus", 130, 14)], sinus75=[("sinus", 75, 14)],
              avnrt180=[("avnrt", 180, 14)], avnrt130=[("avnrt", 130, 14)],
              onset=[("sinus", 80, 2.6), ("avnrt", 180, 4.2), ("sinus", 80, 8)],
              convert=[("avnrt", 180, 1.4), ("pause", 0, 1.3), ("sinus", 78, 18)])

def strip_card(x, y, w, h, name, layer, label_txt=None, rate=None, markers=(), dim=0.0, t0=0.0):
    beats = place(STRIPS[name])
    v = lambda t: sum(beatV(t-b, rr, k) for b, rr, k in beats if -0.25 < t-b < 0.6)
    hb = 56 if (label_txt or rate) else 0
    by = y + hb + (h - hb)*0.62
    dur = w / PXS
    path = "M" + " L".join(f"{x + (i*0.002)*PXS:.1f} {by - v(t0 + i*0.002)*PXMV:.1f}" for i in range(int(dur/0.002)+1))
    small = PXS/25; big = small*5
    g = [f'<g id="{L(layer + "/Card")}">',
         f'<clipPath id="clip-{layer}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18"/></clipPath>',
         f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="#FFFFFF"/>', '</g>',
         f'<g id="{L(layer + "/Grid")}" clip-path="url(#clip-{layer})" stroke-width="1">']
    k = 0; xx = x
    while xx <= x + w:
        g.append(f'<line x1="{xx:.1f}" y1="{y+hb}" x2="{xx:.1f}" y2="{y+h}" stroke="{C["gridBig"] if k % 5 == 0 else C["grid"]}"/>'); xx += small; k += 1
    yy = by; k = 0
    while yy <= y + h:
        g.append(f'<line x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" stroke="{C["gridBig"] if k % 5 == 0 else C["grid"]}"/>'); yy += small; k += 1
    yy = by - small; k = 1
    while yy >= y + hb:
        g.append(f'<line x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}" stroke="{C["gridBig"] if k % 5 == 0 else C["grid"]}"/>'); yy -= small; k += 1
    g.append('</g>')
    op = f' opacity="{1-0.65*dim:.2f}"' if dim else ""
    g.append(f'<g id="{L(layer + "/Trace")}" clip-path="url(#clip-{layer})"{op}><path d="{path}" fill="none" stroke="{C["ink"]}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/></g>')
    mk = [f'<g id="{L(layer + "/Markers")}"{op}>']
    for m in markers:
        kind = m[0]
        if kind in ("P", "noP"):
            for b, rr, kk in beats:
                tx = x + (b - t0 + m[1])*PXS
                if x + 20 < tx < x + w - 20:
                    py = by - 0.16*PXMV
                    if kind == "P" and kk == "sinus":
                        mk.append(f'<text x="{tx:.0f}" y="{py-16:.0f}" text-anchor="middle" style="{BF};font-size:24px;font-weight:700" fill="{C["teal"]}">P</text>')
                    if kind == "noP" and kk == "avnrt":
                        mk.append(f'<circle cx="{tx:.0f}" cy="{py-22:.0f}" r="12" fill="none" stroke="{C["coral"]}" stroke-width="2.5"/><line x1="{tx-8:.0f}" y1="{py-14:.0f}" x2="{tx+8:.0f}" y2="{py-30:.0f}" stroke="{C["coral"]}" stroke-width="2.5"/>')
        if kind == "bracket":
            _, ta, tb, text = m
            xa, xb = x + (ta-t0)*PXS, x + (tb-t0)*PXS; yb = by + 0.42*PXMV
            mk.append(f'<path d="M{xa:.0f} {yb-10:.0f}v10h{xb-xa:.0f}v-10" stroke="{C["amber"]}" stroke-width="3" fill="none"/>'
                      f'<text x="{(xa+xb)/2:.0f}" y="{yb+32:.0f}" text-anchor="middle" style="{BF};font-size:22px;font-weight:600" fill="{C["amberInk"]}">{esc(text)}</text>')
        if kind == "tick":
            _, tt, text, col, colInk = m
            xt = x + (tt-t0)*PXS
            mk.append(f'<line x1="{xt:.0f}" y1="{y+hb+10:.0f}" x2="{xt:.0f}" y2="{y+h-10:.0f}" stroke="{col}" stroke-width="3" stroke-dasharray="8 8"/>'
                      f'<text x="{xt+12:.0f}" y="{y+h-22:.0f}" style="{BF};font-size:22px;font-weight:700" fill="{colInk}">{esc(text)}</text>')
    mk.append('</g>')
    g += mk
    if hb:
        g.append(f'<g id="{L(layer + "/Header")}"><line x1="{x}" y1="{y+hb}" x2="{x+w}" y2="{y+hb}" stroke="{C["div"]}" stroke-width="1.5"/>')
        if label_txt: g.append(f'<text x="{x+22}" y="{y+37}" style="{BF};font-size:22px;font-weight:500" fill="{C["ink2"]}">{esc(label_txt)}</text>')
        if rate: g.append(f'<text x="{x+w-22}" y="{y+39}" text-anchor="end" style="{BF};font-size:30px;font-weight:600;font-variant-numeric:tabular-nums" fill="{C["ink"]}">{rate}<tspan style="font-size:20px;font-weight:500" fill="{C["ink2"]}"> /min</tspan></text>')
        g.append('</g>')
    g.append(f'<g id="{L(layer + "/Edge")}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="none" stroke="{C["div"]}" stroke-width="2"/></g>')
    return "\n".join(g), beats

# ---------------------------------------------------------------- frame
def frame(beat, name, body):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
             f'<defs>{heart_defs()}</defs>',
             f'<g id="{L("Background/Fill")}"><rect width="1920" height="1080" fill="{C["bg"]}"/></g>',
             body,
             f'<g id="{L("Meta/BeatID")}"><text x="1880" y="1052" text-anchor="end" style="{BF};font-size:22px;font-weight:500" fill="{C["ink2"]}" opacity="0.6">{beat}</text></g>',
             '</svg>']
    open(os.path.join(OUT, f"{beat}_{name}.svg"), "w").write("\n".join(parts))

ALL = ("sa", "atria", "av", "his")
B = {}

# Scene 1
s, _ = strip_card(160, 390, 1600, 300, "open170", "Strip", "Lead II · 25 mm/s", 170)
B["1A"] = ("strip", s)
B["1B"] = ("question", "\n".join([heading([("Answering a call,", C["teal"])], 160, 340, layer="Question/Answering"), s,
                                   heading([("or stuck in a loop?", C["coral"])], 160, 780, layer="Question/Looping")]))
s2, _ = strip_card(360, 570, 1200, 260, "open170", "Strip", "Lead II · 25 mm/s", 170, dim=0.6)
B["1C"] = ("title", "\n".join([heading([("Sinus tach ", None), ("vs ", C["ink2"]), ("SVT", None)], 960, 420, 88, "middle", "Title/Main"),
                                f'<g id="{L("Title/Sub")}"><text x="960" y="484" text-anchor="middle" style="{BF};font-size:32px;font-weight:400" fill="{C["ink2"]}">Answering, or looping?</text></g>', s2]))

# Scene 2: the heart, full frame
HS = 0.122
hx, hy = 960 - 5500*HS/2, 110
def full_heart(lit, labels, faded=(), chip_av=False, glow=()):
    h, st = heart(hx, hy, HS, lit, faded, glow=glow)
    out = [h]
    sa, av = st(*SA), st(*AV)
    if "sa" in labels: out.append(leader((sa[0]-30, sa[1]-10), (hx - 60, sa[1]-60), "SA node", "end", "Labels/SANode"))
    if "av" in labels: out.append(leader((av[0]-40, av[1]+10), (hx - 60, av[1]+90), "AV node", "end", "Labels/AVNode"))
    if chip_av:
        c, _ = chip(hx - 280, av[1] + 118, "holds ≈ 0.1 s", "amber", 26); out.append(f'<g id="{L("Labels/AVHold")}">{c}</g>')
    if "his" in labels:
        hp = st(4900, 5300); out.append(leader((hp[0]+10, hp[1]), (hx + 5500*HS + 80, hp[1]), "His-Purkinje", "start", "Labels/HisPurkinje"))
    return "\n".join(out)
B["2A"] = ("sa-node", full_heart(("sa",), ("sa",), glow=("sa",)))
B["2B"] = ("atria", full_heart(("sa", "atria"), ("sa",)))
B["2C"] = ("av-node", full_heart(("sa", "atria", "av"), ("sa", "av"), faded=("atria",), chip_av=True, glow=("av",)))
B["2D"] = ("his-purkinje", full_heart(ALL, ("sa", "av", "his")))
h, _ = heart(150, 190, 0.1, ALL)
qb = 0.25 + 0.8   # second beat of sinus75
s, _ = strip_card(980, 330, 800, 300, "sinus75", "Strip", "Lead II", None, markers=[("bracket", qb - 0.005, qb + 0.07, "QRS < 120 ms")], t0=0.0)
c, _ = chip(980, 680, "Fast lane → narrow QRS", "amber")
B["2E"] = ("narrow-qrs", "\n".join([h, s, f'<g id="{L("Labels/FastLane")}">{c}</g>']))
h, st = heart(140, 150, 0.11, ALL)
avy = st(*AV)[1]
dash = f'<g id="{L("Level/Line")}"><line x1="80" y1="{avy:.0f}" x2="920" y2="{avy:.0f}" stroke="{C["ink"]}" stroke-width="3" stroke-dasharray="14 12"/></g>'
B["2F"] = ("at-or-above", "\n".join([h, dash,
    heading([("Both rhythms start ", None), ("at or above", C["coral"])], 1040, 330, 48, layer="Level/Heading"),
    heading([("the AV node", None)], 1040, 392, 48, layer="Level/Heading2"),
    chips(1040, 450, [("Narrow QRS", "dark"), ("→ ventricles still use the fast lane", "plain"), ("→ origin at or above the AV node", "plain")], "Level/Chips")]))

# Scene 3: sinus tach
def st_head(title_parts): return kicker("SINUS TACHYCARDIA", C["tealInk"]) + "\n" + heading(title_parts)
h, _ = heart(470, 230, 0.105, ALL)
B["3A"] = ("answering", "\n".join([st_head([("The heart ", None), ("answering", C["teal"])]), h,
    chips(1180, 380, [("SA node firing > 100 /min", "teal"), ("same route, just faster", "plain")], "Answering/Chips"),
    para(1180, 560, "because the body is asking for more output", 30, 30, layer="Answering/Reason")]))
h, _ = heart(180, 230, 0.105, ALL)
harmless = kicker("HARMLESS", C["tealInk"], 900, 330) + chips(900, 360, [("Exercise", "teal"), ("Stress", "teal"), ("Pain", "teal"), ("Anxiety", "teal")], "Causes/Harmless")
serious = kicker("SERIOUS", C["coralInk"], 1260, 330) + chips(1260, 360, [("Low oxygen", "coral"), ("Blood loss", "coral"), ("Dehydration", "coral"), ("Sepsis", "coral")], "Causes/Serious")
B["3B"] = ("harmless", "\n".join([st_head([("The heart ", None), ("answering", C["teal"])]), h, harmless]))
B["3C"] = ("serious", "\n".join([st_head([("The heart ", None), ("answering", C["teal"])]), h, harmless, serious,
    para(900, 760, "A fast resting heart rate can be one of the earliest signs that something is wrong.", 46, 30, C["ink"], "Causes/Warning")]))
s, _ = strip_card(160, 300, 1600, 300, "sinus130", "Strip", "Lead II · 25 mm/s", 130, markers=[("P", -0.10)])
B["3D"] = ("sinus-ecg", "\n".join([st_head([("A normal beat, only faster", None)]), s,
    chips(160, 660, [("Upright P in I, II and aVL", "teal"), ("One P before every QRS", "teal")], "ECG/Chips", vertical=False)]))

# Scene 4: SVT
def svt_head(parts): return kicker("SVT", C["coralInk"]) + "\n" + heading(parts)
card = loop_card("AVNRT", "avnrt", 120, 236, 1000, 640)
B["4A"] = ("re-entry", "\n".join([svt_head([("The heart in a ", None), ("loop", C["coral"])]), card,
    chips(1200, 300, [("Re-entry", "coral")], "Loop/Chips"),
    para(1200, 440, "A signal caught in a circuit, going around and around.", 30, 30, layer="Loop/Text")]))
B["4B"] = ("avnrt", "\n".join([svt_head([("The heart in a ", None), ("loop", C["coral"])]), card,
    chips(1200, 300, [("AVNRT", "coral"), ("circuit inside the AV node", "plain"), ("the most common type", "plain")], "Loop/Chips")]))
def two_loops():
    out = [svt_head([("Two kinds of ", None), ("loop", C["coral"])]),
           loop_card("AVNRT", "avnrt", 120, 236, 800, 620), loop_card("AVRT", "avrt", 1000, 236, 800, 620)]
    for x, tag, txt in ((120, "AVNRT", "circuit inside the AV node"), (1000, "AVRT", "down the AV node, back up an extra pathway")):
        c1, w1 = chip(x, 880, tag, "coral", 26, 700)
        out.append(f'<g id="{L("Labels/" + tag)}">{c1}<text x="{x+w1+20:.0f}" y="{880+26+13*0.9+9:.0f}" style="{BF};font-size:30px;font-weight:500" fill="{C["ink"]}">{esc(txt)}</text></g>')
    return "\n".join(out)
B["4C"] = ("two-loops", two_loops())
s, _ = strip_card(720, 290, 1080, 300, "avnrt180", "Strip", "Lead II · 25 mm/s", 180)
B["4D"] = ("every-lap", "\n".join([svt_head([("Every lap fires the ventricles", None)]), schematic(120, 236, 520, 620),
    s, chips(720, 640, [("one lap → one QRS", "coral")], "Strip/Chips")]))
onset_t = 0.25 + 2.6 + (0.0)   # first AVNRT beat lands on the next RR after 2.6 s of sinus at 80
ob = [b for b, rr, k in place(STRIPS["onset"]) if k == "avnrt"][0]
s, _ = strip_card(160, 300, 1600, 300, "onset", "Strip", "Lead II · 25 mm/s", None, markers=[("tick", ob - 0.12, "starts suddenly", C["coral"], C["coralInk"])])
B["4E"] = ("switch", "\n".join([svt_head([("A switch, not a dial", None)]), s,
    chips(160, 660, [("Starts suddenly", "coral"), ("150 – 220 /min, regular", "coral"), ("Stops abruptly", "coral")], "Strip/Chips", vertical=False)]))

# Scene 5: side by side
def table(rows):
    X1, X2 = 520, 1200
    out = [kicker("SIDE BY SIDE"),
           f'<g id="{L("Table/Columns")}"><text x="{X1}" y="190" style="{HF};font-size:44px;font-weight:600"><tspan fill="{C["tealInk"]}">Sinus tach</tspan><tspan fill="{C["ink2"]}" style="font-weight:500"> · answering</tspan></text>'
           f'<text x="{X2}" y="190" style="{HF};font-size:44px;font-weight:600"><tspan fill="{C["coralInk"]}">SVT</tspan><tspan fill="{C["ink2"]}" style="font-weight:500"> · looping</tspan></text>'
           f'<line x1="120" y1="222" x2="1800" y2="222" stroke="{C["div"]}" stroke-width="2"/></g>']
    if rows >= 1:
        a, _ = chip(X1, 262, "A reason you can find", "teal"); b, _ = chip(X2, 250, "Often none", "coral")
        out.append(f'<g id="{L("Table/Trigger")}">' + kicker("TRIGGER", None, 120, 300) + a + b
                   + f'<text x="{X2}" y="346" style="{BF};font-size:26px;font-weight:400" fill="{C["ink2"]}">sometimes caffeine, stimulants, stress</text>'
                   + f'<line x1="120" y1="384" x2="1800" y2="384" stroke="{C["div"]}" stroke-width="2"/></g>')
    if rows >= 2:
        a, _ = chip(X1, 414, "Follows the reason", "teal"); b, _ = chip(X2, 414, "Switches on and off", "coral")
        out.append(f'<g id="{L("Table/StartStop")}">' + kicker("START AND STOP", None, 120, 452) + a + b
                   + f'<line x1="120" y1="508" x2="1800" y2="508" stroke="{C["div"]}" stroke-width="2"/></g>')
    if rows >= 3:
        s1, _ = strip_card(X1, 540, 640, 230, "sinus130", "StripSinus", markers=[("P", -0.10)])
        s2, _ = strip_card(X2, 540, 600, 230, "avnrt130", "StripAVNRT", markers=[("noP", 0.0)])
        a, _ = chip(X1, 796, "Upright P before every QRS", "teal"); b, _ = chip(X2, 796, "Hidden inside the QRS", "coral")
        out.append(f'<g id="{L("Table/PWaves")}">' + kicker("P WAVES", None, 120, 668) + s1 + s2 + a + b + '</g>')
    return "\n".join(out)
B["5A"] = ("trigger", table(1)); B["5B"] = ("start-stop", table(2)); B["5C"] = ("p-waves", table(3))

# Scene 6: the AV node is the key
def key_head(): return kicker("BREAKING THE LOOP", C["coralInk"]) + "\n" + heading([("The AV node is the key", None)])
B["6A"] = ("block-node", "\n".join([key_head(), schematic(120, 236, 440, 620, block=True),
    loop_card("Blocked", "avnrt", 600, 236, 520, 620, view=2500, center=(3650, 3950), block=True, lit=()),
    chips(1200, 300, [("Vagal maneuvers", "dark"), ("Adenosine", "dark"), ("→ slow conduction through the AV node", "plain")], "Block/Chips", size=26),
    para(1200, 560, "Block the node for a moment and the loop breaks.", 30, 30, layer="Block/Text")]))
cb = place(STRIPS["convert"]); first_pause = [b for b, rr, k in cb if k == "avnrt"][-1] + 60/180
s, _ = strip_card(120, 300, 1000, 300, "convert", "Strip", "Lead II · 25 mm/s", None, markers=[("tick", first_pause, "adenosine", C["amber"], C["amberInk"])])
steps = [kicker("STABLE", C["tealInk"], 1200, 330)]
for i, (a, b) in enumerate((("1 · Vagal maneuver", "Valsalva, lying flat"), ("2 · Adenosine", "rapid IV push"))):
    c, w = chip(1200, 352 + i*74, a, "plain"); steps.append(c + f'<text x="{1200+w+16:.0f}" y="{352+i*74+37:.0f}" style="{BF};font-size:26px" fill="{C["ink2"]}">{esc(b)}</text>')
steps.append(kicker("UNSTABLE", C["coralInk"], 1200, 552)); c, _ = chip(1200, 574, "Synchronized cardioversion", "coral"); steps.append(c)
B["6B"] = ("treatment", "\n".join([key_head(), s, f'<g id="{L("Steps/List")}">' + "".join(steps) + '</g>']))
h, _ = heart(470, 230, 0.105, ALL)
B["6C"] = ("treat-cause", "\n".join([st_head([("No loop to break", None)]), h,
    heading([("Treat the cause", C["tealInk"])], 1180, 470, 56, layer="Cause/Heading"),
    para(1180, 530, "Slowing the rate doesn't fix the reason it's fast.", 30, 30, layer="Cause/Text")]))

# Scene 7
s, _ = strip_card(160, 390, 1600, 300, "open170", "Strip", "Lead II · 25 mm/s", 170)
B["7A"] = ("close", "\n".join([heading([("Answering?", C["teal"])], 160, 340, layer="Close/Answering"), s,
                               heading([("Looping?", C["coral"])], 1760, 780, anchor="end", layer="Close/Looping")]))

for beat, (name, body) in B.items(): frame(beat, name, body)
print(len(B), "frames")
