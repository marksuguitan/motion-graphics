# Style frames for Sinus Tach vs SVT, beat 4C ("two kinds of loop"), three Warm Clinical variants.
# Usage: python3 make_style_frames.py <art.json> <out dir>
# art.json is Mark's heart-conduction-system art (8000x8000 units) from the Remotion reference:
# 1-brief/reference/remotion v5/src/data/art.json. Loop geometry follows src/Loops.tsx.
import sys, os, json, math, re

ART, OUT = sys.argv[1], sys.argv[2]
A = json.load(open(ART))

C = dict(white="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A",
         coral="#F0645A", amber="#E3A33B", paper="#F3EEE5", papercard="#FBF8F2", paperline="#E3DBCF")
H = "font-family:Manrope"; B = "font-family:Inter"
L = lambda s: s.replace("/", "_x2F_")   # Illustrator-safe layer names: Group/Sublayer

AV = (3320, 3400)
ACC = "M6295 3770 L6200 3440 L6010 3110"
RX, RY = 330, 250
AVNRT_D = f"M{AV[0]} {AV[1]-RY}a{RX} {RY} 0 1 1 -0.1 0"
LOOPS_TSX = os.path.join(os.path.dirname(ART), "..", "Loops.tsx")
AVRT_D = re.search(r"AVRT_D = `([^`]+)`", open(LOOPS_TSX).read()).group(1)

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
            p = (pts[k-1][0]+(pts[k][0]-pts[k-1][0])*t, pts[k-1][1]+(pts[k][1]-pts[k-1][1])*t)
            q = pts[k]
            return p, math.degrees(math.atan2(q[1]-pts[k-1][1], q[0]-pts[k-1][0]))
    return pts[-1], 0

AVRT_PTS = sample(AVRT_D)
AVNRT_PTS = [(AV[0]+RX*math.sin(2*math.pi*k/200), AV[1]-RY*math.cos(2*math.pi*k/200)) for k in range(201)]

heart_sym = "\n".join(f'<path d="{d}" fill="{f}" stroke="{f}" stroke-width="0.73"/>' for d, f in A["heart"])
cond_sym = "\n".join(f'<path d="{d}"/>' for d, _ in A["cond"])

def chevron(p, ang, size, col):
    # filled arrowhead with a white edge so it reads on top of the coral circuit line
    x, y = p
    return (f'<path d="M{size*1.1:.0f},0 L{-size*0.8:.0f},{-size*0.95:.0f} L{-size*0.45:.0f},0 L{-size*0.8:.0f},{size*0.95:.0f} Z" '
            f'fill="{col}" stroke="#FFFFFF" stroke-width="{size*0.28:.0f}" stroke-linejoin="round" '
            f'transform="translate({x:.0f} {y:.0f}) rotate({ang:.1f})"/>')

def loop_card(uid, kind, x, y, w, h, fill, line, shadow, label_tag, label_txt, label_bg):
    view = 6600 if kind == "avrt" else 4200
    cx, cy = (4500, 4500) if kind == "avrt" else (4200, 3900)
    S = w / view
    tx, ty = w/2 - cx*S, h/2 - cy*S
    px = lambda v: v / S          # stage px -> heart units
    pts, d = (AVRT_PTS, AVRT_D) if kind == "avrt" else (AVNRT_PTS, AVNRT_D)
    g = [f'<g id="{L("Loops/" + uid)}">']
    if shadow:
        g.append(f'<rect x="{x}" y="{y+8}" width="{w}" height="{h}" rx="24" fill="#222222" opacity="0.10" filter="url(#soft)"/>')
    g.append(f'<clipPath id="clip-{uid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24"/></clipPath>')
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{fill}"/>')
    g.append(f'<g clip-path="url(#clip-{uid})"><g transform="translate({x+tx:.2f} {y+ty:.2f}) scale({S:.5f})">')
    g.append(f'<g id="{L(uid + "/Heart")}"><use href="#heart"/></g>')
    g.append(f'<g id="{L(uid + "/Conduction")}" fill="{C["amber"]}" stroke="{C["amber"]}" stroke-width="0.73"><use href="#cond"/></g>')
    if kind == "avrt":
        g.append(f'<g id="{L(uid + "/AccessoryPathway")}"><path d="{ACC}" fill="none" stroke="{C["coral"]}" stroke-width="{px(16):.0f}" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="{ACC}" fill="none" stroke="#FFFFFF" stroke-width="{px(5):.0f}" stroke-linecap="round" stroke-dasharray="{px(2):.0f} {px(10):.0f}"/></g>')
    g.append(f'<g id="{L(uid + "/Circuit")}"><path d="{d}" fill="none" stroke="#FFFFFF" stroke-width="{px(15):.0f}" stroke-linecap="round" opacity="0.95"/>'
             f'<path d="{d}" fill="none" stroke="{C["coral"]}" stroke-width="{px(8):.0f}" stroke-linecap="round"/>')
    for f in ([0.12, 0.45, 0.80] if kind == "avrt" else [0.25, 0.75]):
        p, ang = at(pts, f)
        g.append(chevron(p, ang, px(18), C["coral"]))
    g.append('</g>')
    p, _ = at(pts, 0.62 if kind == "avrt" else 0.5)
    g.append(f'<g id="{L(uid + "/Pulse")}"><circle cx="{p[0]:.0f}" cy="{p[1]:.0f}" r="{px(16):.0f}" fill="{C["amber"]}" stroke="#FFFFFF" stroke-width="{px(5):.0f}"/></g>')
    g.append('</g></g>')
    if not shadow:
        g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="none" stroke="{line}" stroke-width="2"/>')
    # label under the card: tag chip + one short line
    ly = y + h + 44
    tw = 22 + 19*len(label_tag)
    g.append(f'<g id="{L("Labels/" + uid)}"><rect x="{x}" y="{ly-36}" width="{tw}" height="52" rx="12" fill="{label_bg}"/>'
             f'<text x="{x+tw/2}" y="{ly}" text-anchor="middle" style="{H};font-size:26px;font-weight:700" fill="{C["coral"]}">{label_tag}</text>'
             f'<text x="{x+tw+22}" y="{ly}" style="{B};font-size:30px;font-weight:500" fill="{C["ink"]}">{label_txt}</text></g>')
    g.append('</g>')
    return "\n".join(g)

def frame(name, bg, card_fill, line, shadow, label_bg, note, stage=None):
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">',
             '<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="12"/></filter>',
             f'<symbol id="heart" viewBox="0 0 8000 8000" width="8000" height="8000">{heart_sym}</symbol>',
             f'<symbol id="cond" viewBox="0 0 8000 8000" width="8000" height="8000">{cond_sym}</symbol></defs>',
             f'<g id="{L("Background/Fill")}"><rect width="1920" height="1080" fill="{bg}"/></g>']
    if stage:
        parts.append(f'<g id="{L("Background/Stage")}"><rect x="72" y="208" width="1776" height="760" rx="24" fill="#222222" opacity="0.08" filter="url(#soft)" transform="translate(0,8)"/>'
                     f'<rect x="72" y="208" width="1776" height="760" rx="24" fill="{stage}"/></g>')
    parts.append(f'<g id="{L("Header/Kicker")}"><text x="120" y="104" style="{H};font-size:23px;font-weight:700;letter-spacing:3px" fill="{C["ink2"]}">SVT</text></g>')
    parts.append(f'<g id="{L("Header/Title")}"><text x="120" y="168" style="{H};font-size:56px;font-weight:600" fill="{C["ink"]}">Two kinds of <tspan fill="{C["coral"]}">loop</tspan></text></g>')
    top = 236
    cw, ch = 800, 620
    parts.append(loop_card("AVNRT", "avnrt", 120, top, cw, ch, card_fill, line, shadow, "AVNRT", "circuit inside the AV node", label_bg))
    parts.append(loop_card("AVRT", "avrt", 1000, top, cw, ch, card_fill, line, shadow, "AVRT", "down the AV node, back up an extra pathway", label_bg))
    parts.append(f'<g id="{L("Meta/BeatID")}"><text x="1880" y="1052" text-anchor="end" style="{B};font-size:22px;font-weight:500" fill="{C["ink2"]}" opacity="0.6">4C · {note}</text></g>')
    parts.append('</svg>')
    open(os.path.join(OUT, name), "w").write("\n".join(parts))

frame("style_A_warm-clinical.svg", C["white"], C["soft"], C["div"], False, "#FDE3E0", "Style A")
frame("style_B_warm-ground.svg", C["paper"], C["papercard"], C["paperline"], False, "#F9DCD6", "Style B")
frame("style_C_card-stage.svg", C["soft"], C["white"], C["div"], True, "#FDE3E0", "Style C")
print("ok")
