"""AVNRT vs AVRT, Motion Board pass 1: every beat in style B (white cards on soft neutral).
Writes [ID]_[name].svg into argv[1]."""
import sys, os, math

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

BG = "#FFFFFF"; SOFT = "#F7F7F5"; DIV = "#E6E4E0"; INK = "#222222"; SEC = "#6A6A6A"
CORAL = "#F0645A"; AMBER = "#E3A33B"; AMBER_DEEP = "#C9861F"; AMBER_TINT = "#FBEBD0"; CORAL_TINT = "#FDE3E1"
HEAD = "Manrope, Inter, Helvetica, Arial, sans-serif"
BODY = "Inter, Helvetica, Arial, sans-serif"

def esc(s): return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def T(x, y, s, size=30, weight=500, fill=INK, family=BODY, anchor="start", ls=None):
    lsa = f' letter-spacing="{ls}"' if ls else ""
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{lsa}>{esc(s)}</text>'

def tw(s, size, weight=500):  # rough text width
    k = 0.58 if weight >= 600 else 0.55
    return len(s) * size * k

def defs():
    return f"""<defs>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="{INK}" flood-opacity="0.10"/></filter>
  <filter id="blur"><feGaussianBlur stdDeviation="22"/></filter>
  <filter id="blurU" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="200"/></filter>
  <marker id="arr" viewBox="0 0 12 12" refX="3" refY="6" markerUnits="userSpaceOnUse" markerWidth="30" markerHeight="30" orient="auto-start-reverse"><path d="M1,1 L11,6 L1,11 Z" fill="{AMBER_DEEP}"/></marker>
  <pattern id="hatch" width="12" height="12" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="12" height="12" fill="{DIV}"/><line x1="0" y1="0" x2="0" y2="12" stroke="{SEC}" stroke-width="4" opacity="0.5"/></pattern>
</defs>"""

def svg(bid, body):
    hd = f"<defs>{heart_defs()}</defs>\n" if 'href="#MarkHeart"' in body else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">\n{defs()}\n{hd}'
            f'<rect id="Background" width="1920" height="1080" fill="{SOFT}"/>\n{body}\n'
            f'<g id="BeatID">{T(1888, 1056, bid, 22, 600, SEC, BODY, "end")}</g>\n</svg>\n')

def card(x, y, w, h, gid="Card"):
    return f'<g id="{gid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24" fill="{BG}" filter="url(#soft)"/></g>'

CHIP = {"neutral": ("#ECEAE5", INK, 500), "amber": (AMBER_TINT, "#8A5A10", 600), "coral": (CORAL, BG, 600),
        "coraltint": (CORAL_TINT, "#B83A31", 600), "dark": (INK, BG, 600), "white": (BG, INK, 500)}
def chip(x, y, s, kind="neutral", size=24, gid=None, anchor="start"):
    bg, fg, wt = CHIP[kind]
    w = tw(s, size, wt) + 36; h = size + 26
    if anchor == "end": x -= w
    if anchor == "middle": x -= w / 2
    g = gid or f"Label/{s[:20]}"
    return f'<g id="{esc(g)}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h}" rx="12" fill="{bg}"/>{T(x+18, y+h/2+size*0.36, s, size, wt, fg)}</g>', w

def header(eyebrow, title, x=120, y=132, sub=None):
    g = ['<g id="Header">']
    if eyebrow: g.append(T(x, y, eyebrow.upper(), 22, 700, SEC, HEAD, ls="2.5"))
    g.append(T(x, y + 64, title, 52, 600, INK, HEAD))
    if sub: g.append(T(x, y + 112, sub, 30, 500, SEC))
    g.append('</g>')
    return "".join(g)

def side_text(x, y, eyebrow_chip=None, title_lines=(), sub=None, chips=(), chip_kind="neutral"):
    """Right-hand column: optional chip, heading (1-3 lines), sub line, then chips stacked."""
    g = ['<g id="Header">']
    if eyebrow_chip:
        c, _ = chip(x, y, eyebrow_chip[0], eyebrow_chip[1], gid="Header/Chip"); g.append(c); y += 92
    for i, ln in enumerate(title_lines):
        g.append(T(x, y + 52 + i * 64, ln, 52, 600, INK, HEAD))
    y += 52 + (len(title_lines) - 1) * 64
    if sub:
        y += 56; g.append(T(x, y, sub, 30, 500, SEC))
    g.append('</g>')
    y += 44
    for s, k in chips:
        c, _ = chip(x, y, s, k); g.append(c); y += 74
    return "".join(g)

# ---------------- ECG ----------------
K = {
    "narrow":  [(-0.012, -0.10, 0.006), (0, 1.0, 0.009), (0.018, -0.26, 0.008), (0.15, 0.28, 0.032)],
    "pseudoS": [(-0.012, -0.10, 0.006), (0, 1.0, 0.009), (0.018, -0.26, 0.008), (0.045, -0.24, 0.009), (0.15, 0.28, 0.032)],
    "pseudoR": [(-0.012, 0.12, 0.006), (0, -0.85, 0.010), (0.024, 0.10, 0.007), (0.042, 0.30, 0.008), (0.15, -0.18, 0.032)],
    "retroP":  [(-0.012, -0.10, 0.006), (0, 1.0, 0.009), (0.018, -0.26, 0.008), (0.10, -0.20, 0.012), (0.19, 0.26, 0.030)],
    "wide":    [(0, 0.95, 0.030), (0.065, -0.45, 0.028), (0.20, -0.30, 0.045)],
    "sinus":   [(-0.16, 0.14, 0.022), (-0.012, -0.08, 0.006), (0, 1.0, 0.009), (0.018, -0.24, 0.008), (0.24, 0.30, 0.045)],
    "wpw":     [(-0.12, 0.14, 0.022), (-0.035, 0.30, 0.022), (0.005, 0.85, 0.016), (0.035, -0.22, 0.012), (0.26, -0.18, 0.045)],
    "pac":     [(-0.10, 0.12, 0.018), (-0.012, -0.10, 0.006), (0, 1.0, 0.009), (0.018, -0.26, 0.008), (0.15, 0.28, 0.032)],
}
def ecg_d(x, base, w, amp, pxs, beats):
    """beats: list of (t_center_of_R, kind[, scale]) ; pxs px per second."""
    pts = []
    n = int(w)
    for i in range(n + 1):
        t = i / pxs; v = 0.0
        for b in beats:
            tc, kind = b[0], b[1]; sc = b[2] if len(b) > 2 else 1.0
            for (o, a, s) in K[kind]:
                v += a * sc * math.exp(-((t - tc - o) ** 2) / (2 * s * s))
        pts.append((x + i, base - v * amp))
    return "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts)

def strip(x, y, w, h, beats, pxs, amp=None, grid=True, sw=4, gid="ECG", base_frac=0.62):
    amp = amp or h * 0.5
    base = y + h * base_frac
    g = [f'<g id="{gid}">']
    if grid:
        ls = [f'M{gx},{y} V{y+h}' for gx in range(int(x), int(x + w) + 1, 24)] + [f'M{x},{gy} H{x+w}' for gy in range(int(y), int(y + h) + 1, 24)]
        g.append(f'<path id="{gid}/Grid" d="{" ".join(ls)}" stroke="{DIV}" stroke-width="1" opacity="0.7"/>')
    g.append(f'<path id="{gid}/Trace" d="{ecg_d(x, base, w, amp, pxs, beats)}" stroke="{INK}" stroke-width="{sw}" fill="none" stroke-linejoin="round" stroke-linecap="round"/>')
    g.append('</g>')
    return "".join(g), base

def run(t0, rr, n, kind):
    return [(t0 + i * rr, kind) for i in range(n)]

def ring(cx, cy, r=30, color=CORAL, gid="Focus/Ring"):
    return f'<g id="{gid}"><circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="none" stroke="{color}" stroke-width="5"/></g>'

# ---------------- junction diagram ----------------
def junction(cx, cy, s=1.0, st=None):
    """Two-pathway junction (slow left, fast right). st keys:
    atria(bool box) left/right/stem/his: off|on|shade|dim ; arrows: {'left':'down'|'up','right':..,'stem':..,'his':..}
    node: none|off|on|blocked ; labels: bool ; tags: bool (Atria/AV node/His/Ventricles) ; dot: 'top'|'node'|None ; ablate: 'left'|None"""
    st = st or {}
    r = 120 * s; top = cy - r; bot = cy + r
    atr_w, atr_h = 400 * s, 90 * s
    atr_y = top - 64 * s - atr_h
    node_y = bot + 4 * s
    his_top = node_y + 24 * s; his_bot = his_top + 64 * s; br = 64 * s
    sw = 18 * s
    def stroke(state):
        if state == "on": return f'stroke="{AMBER}" stroke-width="{sw}"'
        if state == "shade": return f'stroke="url(#hatch)" stroke-width="{sw+8*s}"'
        return None
    neutral = f'stroke="{DIV}" stroke-width="{sw+10*s}" fill="none" stroke-linecap="round"'
    g = ['<g id="Diagram">']
    if st.get("atria", True):
        fill = AMBER_TINT if st.get("atria_on") else SOFT
        g.append(f'<g id="Diagram/Atria"><rect x="{cx-atr_w/2:.1f}" y="{atr_y:.1f}" width="{atr_w:.1f}" height="{atr_h:.1f}" rx="{20*s:.1f}" fill="{fill}" stroke="{DIV}" stroke-width="2"/>'
                 + (T(cx - atr_w/2 + 24*s, atr_y + atr_h/2 + 9*s, "Atria", 24, 500, SEC) if st.get("tags", True) else "") + '</g>')
    g.append(f'<g id="Diagram/Channels"><line x1="{cx}" y1="{atr_y+atr_h if st.get("atria", True) else top-70*s:.1f}" x2="{cx}" y2="{top:.1f}" {neutral}/>'
             f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" {neutral}/>'
             f'<line x1="{cx}" y1="{bot:.1f}" x2="{cx}" y2="{his_bot:.1f}" {neutral}/>'
             f'<path d="M{cx},{his_bot:.1f} L{cx-br:.1f},{his_bot+br*0.8:.1f} M{cx},{his_bot:.1f} L{cx+br:.1f},{his_bot+br*0.8:.1f}" {neutral}/></g>')
    act = ['<g id="Diagram/Active">']
    L = f'M{cx-6*s:.1f},{top:.1f} A{r:.1f},{r:.1f} 0 0 0 {cx-6*s:.1f},{bot:.1f}'
    R = f'M{cx+6*s:.1f},{bot:.1f} A{r:.1f},{r:.1f} 0 0 0 {cx+6*s:.1f},{top:.1f}'
    for name, d in (("Slow", L), ("Fast", R)):
        key = "left" if name == "Slow" else "right"
        sk = stroke(st.get(key, "off"))
        if sk: act.append(f'<path id="Diagram/{name}" d="{d}" {sk} fill="none" stroke-linecap="round"/>')
    sk = stroke(st.get("stem", "off"))
    if sk: act.append(f'<line id="Diagram/Stem" x1="{cx}" y1="{atr_y+atr_h:.1f}" x2="{cx}" y2="{top:.1f}" {sk} stroke-linecap="round"/>')
    sk = stroke(st.get("his", "off"))
    if sk: act.append(f'<path id="Diagram/His" d="M{cx},{node_y+18*s:.1f} L{cx},{his_bot:.1f} L{cx-br+8*s:.1f},{his_bot+br*0.8-6*s:.1f} M{cx},{his_bot:.1f} L{cx+br-8*s:.1f},{his_bot+br*0.8-6*s:.1f}" {sk} fill="none" stroke-linecap="round"/>')
    arrows = st.get("arrows", {})
    for side, sgn in (("left", -1), ("right", 1)):
        if side in arrows:
            ax = cx + sgn * r; d = 1 if arrows[side] == "down" else -1
            act.append(f'<path d="M{ax-17*s:.1f},{cy-12*s*d:.1f} L{ax+17*s:.1f},{cy-12*s*d:.1f} L{ax:.1f},{cy+16*s*d:.1f} Z" fill="{AMBER_DEEP}"/>')
    if "stem" in arrows:
        my = (atr_y + atr_h + top) / 2; d = 1 if arrows["stem"] == "down" else -1
        act.append(f'<path d="M{cx-17*s:.1f},{my-12*s*d:.1f} L{cx+17*s:.1f},{my-12*s*d:.1f} L{cx:.1f},{my+16*s*d:.1f} Z" fill="{AMBER_DEEP}"/>')
    act.append('</g>')
    g.append("".join(act))
    node = st.get("node", "on")
    if node != "none":
        fill = {"on": AMBER_DEEP, "off": AMBER_TINT, "blocked": INK}[node]
        fg = BG if node in ("on", "blocked") else "#8A5A10"
        g.append(f'<g id="Diagram/AVNode"><ellipse cx="{cx}" cy="{node_y:.1f}" rx="{58*s:.1f}" ry="{28*s:.1f}" fill="{fill}"/>'
                 + (T(cx, node_y + 8*s, "AV node", 22, 600, fg, BODY, "middle") if st.get("tags", True) else "") + '</g>')
    if st.get("tags", True):
        g.append(f'<g id="Diagram/Tags">{T(cx + 24*s, his_top + 40*s, "His bundle", 22, 500, SEC)}'
                 f'{T(cx, his_bot + br*0.8 + 40*s, "Ventricles", 24, 500, SEC, BODY, "middle")}</g>')
    if st.get("labels", True):
        g.append(f'<g id="Diagram/PathLabels">{T(cx-r-(62 if st.get("ablate") else 30)*s, cy+9, "Slow", 28, 600, INK, BODY, "end")}{T(cx+r+30*s, cy+9, "Fast", 28, 600, INK)}</g>')
    dot = st.get("dot")
    if dot:
        px, py = {"top": (cx, top), "node": (cx, node_y - 30*s), "stemtop": (cx, atr_y + atr_h + 6*s)}[dot]
        g.append(f'<g id="Diagram/Wave"><circle cx="{px:.1f}" cy="{py:.1f}" r="{22*s:.1f}" fill="{AMBER}" opacity="0.35"/><circle cx="{px:.1f}" cy="{py:.1f}" r="{12*s:.1f}" fill="{AMBER_DEEP}"/></g>')
    if st.get("ablate") == "left":
        ax, ay = cx - r, cy
        g.append(xmark(ax, ay, 26 * s))
    g.append('</g>')
    return "".join(g), dict(top=top, bot=bot, r=r, atr_y=atr_y, atr_h=atr_h, atr_w=atr_w, node_y=node_y, his_bot=his_bot, br=br)

_bgc = [0]
def hb_for(geo, cx, s, clip, kk=0.11):
    # Heart AV node at the centre of the ring (the ring stands for the AV node region),
    # heart atria under the Atria box; fades out from the bottom of the ring to the His bundle.
    cy = geo["top"] + geo["r"]
    return heart_backdrop(cx, cy, geo["bot"] - 20 * s, geo["his_bot"], clip, kk=kk * s)

def heart_backdrop(cx, node_y, top_y, bot_y, clip, kk=0.11, op=0.5):
    """Mark's heart behind a junction schematic: his AV node sits on the diagram's node,
    full strength over the atria, fading out by the ventricles. clip = card (x, y, w, h)."""
    _bgc[0] += 1; n = _bgc[0]
    tx, ty = cx - NODE_U[0] * kk, node_y - NODE_U[1] * kk
    x, y, w, h = clip
    return (f'<g id="HeartBackdrop"><defs><clipPath id="hbClip{n}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="24"/></clipPath>'
            f'<linearGradient id="hbFade{n}" gradientUnits="userSpaceOnUse" x1="0" y1="{top_y:.1f}" x2="0" y2="{bot_y:.1f}">'
            f'<stop offset="0" stop-color="#fff" stop-opacity="1"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<mask id="hbMask{n}" maskUnits="userSpaceOnUse" x="{x}" y="{y}" width="{w}" height="{h}"><rect x="{x}" y="{y}" width="{w}" height="{h}" fill="url(#hbFade{n})"/></mask></defs>'
            f'<g clip-path="url(#hbClip{n})" mask="url(#hbMask{n})" opacity="{op}"><g transform="translate({tx:.1f} {ty:.1f}) scale({kk})"><use href="#MarkHeart"/></g></g></g>')

def xmark(x, y, r):
    return (f'<g id="Ablation"><circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{BG}" stroke="{INK}" stroke-width="5"/>'
            f'<path d="M{x-r*0.5:.1f},{y-r*0.5:.1f} L{x+r*0.5:.1f},{y+r*0.5:.1f} M{x+r*0.5:.1f},{y-r*0.5:.1f} L{x-r*0.5:.1f},{y+r*0.5:.1f}" stroke="{INK}" stroke-width="5" stroke-linecap="round"/></g>')

# ---------------- Mark's illustrated conduction heart ----------------
# Base art: Mark's heart-conduction-system.svg (8000x8000 units), muscle + conduction groups,
# from the SVT circuit graphics he supplied (Nov 2, 2026). Overlays are drawn in the same units.
HEART_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mark_heart_body.svg")
HEART_BODY = open(HEART_SRC).read()
HVB = (1157, 564, 5685, 7005)            # tight viewBox of the art
HC = (HVB[0] + HVB[2] / 2, HVB[1] + HVB[3] / 2)
NODE_U = (3320, 3400)                     # AV node centre
AP_U = "M6295 3770 L6200 3440 L6010 3110" # left lateral accessory pathway
AP_MID_U = (6200, 3440)
_pts = [tuple(map(int, p.split())) for p in """3352 3396|3384 3385|3416 3376|3448 3372|3480 3370|3512 3374|3544 3379|3576 3380|3608 3381|3640 3384|3672 3386|3704 3391|3736 3397|3768 3405|3800 3415|3832 3429|3864 3445|3892 3463|3920 3485|3944 3508|3968 3532|3991 3556|4014 3584|4033 3612|4050 3640|4066 3672|4081 3704|4092 3736|4103 3768|4115 3800|4124 3832|4138 3864|4157 3891|4184 3913|4212 3929|4242 3951|4265 3976|4288 4004|4312 4032|4334 4060|4355 4088|4374 4116|4393 4144|4411 4172|4428 4200|4444 4228|4461 4256|4478 4288|4494 4316|4512 4348|4529 4380|4545 4412|4560 4444|4574 4476|4588 4508|4602 4540|4615 4572|4629 4604|4642 4636|4655 4668|4668 4700|4681 4732|4693 4764|4705 4796|4717 4828|4729 4860|4740 4892|4752 4924|4764 4956|4775 4988|4787 5020|4800 5052|4814 5084|4828 5116|4841 5148|4857 5180|4873 5212|4889 5244|4900 5276|4905 5308|4909 5340|4915 5372|4924 5404|4936 5436|4948 5468|4960 5500|4972 5532|4984 5564|4996 5596|5008 5628|5021 5660|5033 5692|5046 5724|5058 5756|5071 5788|5083 5820|5096 5852|5109 5884|5122 5916|5135 5948|5150 5980|5165 6012|5180 6044|5195 6076|5209 6108|5225 6140|5241 6172|5258 6204|5274 6232|5290 6260|5307 6288|5324 6316|5342 6344|5360 6372|5380 6400|5401 6428|5423 6456|5447 6484|5469 6508|5492 6531|5520 6555|5548 6576|5576 6595|5604 6612|5636 6628|5668 6641|5700 6649|5732 6652|5764 6650|5796 6644|5828 6635|5860 6623|5892 6605|5920 6585|5944 6564|5967 6540|5991 6512|6012 6484|6030 6456|6047 6428|6064 6396|6078 6364|6089 6332|6099 6300|6107 6268|6122 6237|6144 6212|6165 6184|6175 6152|6182 6120|6190 6088|6198 6056|6207 6024|6214 5992|6222 5960|6229 5928|6236 5896|6242 5864|6248 5832|6254 5800|6260 5768|6265 5736|6269 5704|6271 5672|6273 5640|6276 5608|6282 5576|6295 5544|6306 5512|6308 5480|6308 5448|6311 5416|6314 5384|6318 5352|6321 5320|6324 5288|6327 5256|6328 5224|6330 5192|6333 5160|6335 5128|6336 5096|6336 5064|6336 5032|6335 5000|6335 4968|6339 4936|6346 4904|6350 4872|6352 4840|6352 4808|6352 4776|6354 4744|6357 4712|6358 4680|6356 4648|6354 4616|6353 4584|6352 4552|6352 4520|6352 4488|6352 4456|6350 4424|6348 4392|6348 4360|6345 4328|6342 4296|6339 4264|6336 4232|6330 4200|6329 4168|6331 4136|6331 4104|6328 4072|6324 4040|6321 4008|6317 3976|6313 3944|6308 3912|6304 3880|6300 3848|6300 3820|6295 3770""".split("|")]
_low = _pts.index((5732, 6652))
DOWN_U = "M3320 3400 " + " ".join(f"L{x} {y}" for x, y in _pts[:_low + 1])
UP_U = f"M5732 6652 " + " ".join(f"L{x} {y}" for x, y in _pts[_low + 1:])
ACROSS_U = "M6010 3110 C5700 2850 4800 2950 4300 3050 C3800 3150 3450 3250 3320 3400"
# Mark's direction arrows (position, angle in degrees) for orthodromic flow
ARR_ACROSS = [(3659.2, 3210.4, 161.0), (5828.6, 3014.4, -162.2)]
ARR_DOWN = [(4344.9, 4074.6, 53.1), (5031.9, 5689.1, 69.4)]
ARR_UP = [(6092.4, 6321.1, -72.6), (6353.5, 4598.9, -91.8)]
# AV plane (fibrous rings): dashed guide between atria and ventricles, through the node and the pathway
PLANE_U = "M1330 4330 C2300 3980 2900 3700 3320 3640 C4300 3560 5300 3520 6260 3470 L6780 3420"
PLANE_L_U, PLANE_R_U = (1330, 4330), (6780, 3420)

def heart_defs():
    return f'<g id="MarkHeart">{HEART_BODY}</g>'

def heart(cx, cy, s=1.0, o=None):
    """Mark's illustrated conduction heart with overlays.
    o keys: small_loop, big ('ortho'|'anti'|'down'), pathway, plane, atria_wave, vent_glow, gate, his_on,
    node_ring, node_blocked, ablate_path"""
    o = o or {}
    k = 0.108 * s
    tx, ty = cx - HC[0] * k, cy - 10 * s - HC[1] * k
    M = lambda u: (tx + u[0] * k, ty + u[1] * k)
    sw = lambda px: f"{px / k:.0f}"           # screen px -> units
    on = f'fill="none" stroke="{AMBER}" stroke-width="{sw(7)}" stroke-linecap="round" stroke-linejoin="round"'
    def arrows(lst, flip=False, col=AMBER_DEEP, sc=0.95):
        out = []
        for x, y, a in lst:
            a = a + 180 if flip else a
            out.append(f'<path d="M-105 -84 L105 0 L-105 84 Z" fill="{col}" transform="translate({x} {y}) rotate({a:.1f}) scale({sc * 0.108 / k * s:.3f})"/>')
        return "".join(out)
    g = [f'<g id="Heart" transform="translate({tx:.1f} {ty:.1f}) scale({k:.5f})">', '<use href="#MarkHeart"/>']
    if o.get("atria_wave"):
        g.append(f'<ellipse id="Heart/AtrialWave" cx="3800" cy="2750" rx="1900" ry="850" fill="{AMBER}" opacity="0.42" filter="url(#blurU)"/>')
    if o.get("vent_glow"):
        g.append(f'<ellipse id="Heart/VentGlow" cx="4600" cy="5600" rx="1700" ry="1500" fill="{AMBER}" opacity="0.45" filter="url(#blurU)"/>')
    if o.get("plane"):
        g.append(f'<path id="Heart/FibrousRing" d="{PLANE_U}" fill="none" stroke="{BG}" stroke-width="{sw(4)}" stroke-dasharray="{sw(14)} {sw(10)}" opacity="0.95"/>')
    big = o.get("big")
    if o.get("his_on"):
        g.append(f'<path id="Heart/HisActive" d="{DOWN_U}" {on}/>')
    if big or o.get("pathway"):
        col = AMBER if big in ("ortho", "anti") else INK
        g.append(f'<g id="Heart/AccessoryPathway"><path d="{AP_U}" fill="none" stroke="{col}" stroke-width="{sw(11)}" stroke-linecap="round" stroke-linejoin="round"/>'
                 f'<path d="{AP_U}" fill="none" stroke="{BG}" stroke-width="{sw(3)}" stroke-linecap="round" stroke-dasharray="{sw(1)} {sw(6)}"/></g>')
    if big in ("ortho", "anti", "down"):
        g.append(f'<path id="Heart/Loop/Down" d="{DOWN_U}" {on}/>')
        if big == "down":
            g.append(arrows(ARR_DOWN))
        else:
            g.append(f'<path id="Heart/Loop/Up" d="{UP_U}" {on}/><path id="Heart/Loop/Across" d="{ACROSS_U}" {on}/>')
            g.append('<g id="Heart/Loop/Arrows">' + arrows(ARR_ACROSS + ARR_DOWN + ARR_UP, flip=(big == "anti")) + '</g>')
    if o.get("small_loop"):
        g.append(f'<g id="Heart/SmallLoop"><circle cx="3320" cy="3400" r="380" fill="#F0A030" opacity="0.32"/>'
                 f'<path d="M3320 3150a330 250 0 1 1 -0.1 0" {on}/>'
                 + arrows([(3553.3, 3223.2, 37.1), (3553.3, 3576.8, 142.9), (3086.7, 3576.8, -142.9), (3086.7, 3223.2, -37.1)], sc=0.6) + '</g>')
    if o.get("gate"):
        g.append(f'<circle id="Heart/Gate" cx="3320" cy="3400" r="330" fill="none" stroke="{AMBER}" stroke-width="{sw(5)}"/>')
    if o.get("node_blocked"):
        g.append(f'<ellipse id="Heart/AVNodeBlocked" cx="3320" cy="3400" rx="250" ry="190" fill="{INK}"/>')
    if o.get("node_ring"):
        g.append(f'<circle id="Focus/NodeRing" cx="3320" cy="3400" r="520" fill="none" stroke="{CORAL}" stroke-width="{sw(5)}"/>')
    g.append('</g>')
    node = M(NODE_U); ap = M(AP_MID_U)
    if o.get("ablate_path"):
        g.append(xmark(ap[0], ap[1], 26 * s))
    return "".join(g), dict(node=node, ap=ap, plane_r=M(PLANE_R_U), plane_l=M(PLANE_L_U), plane_mid=M((5000, 3545)))

def arrowhead(x, y, ang, s=1.0):
    """Filled triangle pointing along angle ang (radians, 0 = +x, screen coords)."""
    L = 20 * s; W = 15 * s
    tip = (x + math.cos(ang) * L, y + math.sin(ang) * L)
    bl = (x - math.cos(ang) * L * 0.4 + math.cos(ang + 1.57) * W, y - math.sin(ang) * L * 0.4 + math.sin(ang + 1.57) * W)
    br = (x - math.cos(ang) * L * 0.4 - math.cos(ang + 1.57) * W, y - math.sin(ang) * L * 0.4 - math.sin(ang + 1.57) * W)
    return f'<path d="M{tip[0]:.1f},{tip[1]:.1f} L{bl[0]:.1f},{bl[1]:.1f} L{br[0]:.1f},{br[1]:.1f} Z" fill="{AMBER_DEEP}"/>'

def leader(x1, y1, x2, y2):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{SEC}" stroke-width="2"/>'

# ================= layouts =================
def heart_left(o, s=1.0):
    return card(120, 120, 840, 840, "Cards/Heart") + heart(540, 560, s, o)[0]

def diag_left(st, s=1.0, cx=540, cy=600, bg=True):
    j, geo = junction(cx, cy, s, st)
    hb = hb_for(geo, cx, s, (120, 120, 840, 840)) if bg else ""
    return card(120, 120, 840, 840, "Cards/Diagram") + hb + j

F = {}
def frame(bid, name):
    def deco(fn):
        F[bid] = (name, fn); return fn
    return deco

RR = 1 / 3.0  # 180 /min

@frame("1A", "two-patients")
def _():
    b = []
    for i, (lab) in enumerate(("Patient 1", "Patient 2")):
        y = 140 + i * 450
        b.append(card(120, y, 1680, 390, f"Cards/Patient{i+1}"))
        b.append(T(170, y + 64, lab, 30, 600, INK, HEAD))
        b.append(T(1750, y + 64, "Lead II · 180 /min", 24, 500, SEC, BODY, "end"))
        st, _ = strip(170, y + 100, 1580, 250, run(0.12, RR, 9, "pseudoS" if i == 0 else "retroP"), 540, amp=120, gid=f"ECG/Patient{i+1}")
        b.append(st)
    return "".join(b)

@frame("1B", "small-loop")
def _():
    return heart_left({"small_loop": True}) + side_text(1060, 330, ("Small loop", "amber"), ["In and around", "the AV node"], "A structure about 5 mm long")

@frame("1C", "big-loop")
def _():
    return heart_left({"big": "ortho"}) + side_text(1060, 330, ("Big loop", "amber"), ["Through the atria,", "the ventricles,", "and back"])

@frame("1D", "title")
def _():
    b = [card(1000, 120, 800, 840, "Cards/Heart"), heart(1400, 560, 0.95, {"small_loop": True, "big": "ortho"})[0]]
    b.append('<g id="Title">' + T(120, 500, "AVNRT vs AVRT", 96, 700, INK, HEAD) + T(124, 580, "Small loop, big loop", 44, 600, AMBER_DEEP, HEAD) + '</g>')
    return "".join(b)

@frame("2A", "insulation")
def _():
    h, geo = heart(540, 560, 1.0, {"plane": True, "atria_wave": True})
    b = [card(120, 120, 840, 840, "Cards/Heart"), h]
    b.append(side_text(1060, 190, None, ["Atria and ventricles", "are kept apart"], None))
    x, y = geo["plane_r"]
    b.append(leader(x + 6, y, 1040, y)); c, _ = chip(1060, y - 25, "Fibrous rings", "neutral"); b.append(c)
    b.append('<g id="Eyebrow">' + T(1060, 160, "INSULATION", 22, 700, SEC, HEAD, ls="2.5") + '</g>')
    return "".join(b)

@frame("2B", "one-gate")
def _():
    h, geo = heart(540, 560, 1.0, {"plane": True, "atria_wave": True, "gate": True, "his_on": True})
    b = [card(120, 120, 840, 840, "Cards/Heart"), h]
    b.append('<g id="Eyebrow">' + T(1060, 300, "ONE GATE", 22, 700, SEC, HEAD, ls="2.5") + '</g>')
    b.append(side_text(1060, 330, None, ["The only normal", "connection"], None, [("AV node → His bundle", "amber")]))
    return "".join(b)

def open_st(**kw):
    d = dict(node="none", tags=False, atria=True, labels=True)
    d.update(kw); return d

@frame("2C", "two-pathways")
def _():
    return diag_left(open_st()) + '<g id="Eyebrow">' + T(1060, 360, "WHAT A LOOP NEEDS", 22, 700, SEC, HEAD, ls="2.5") + '</g>' + side_text(1060, 390, None, ["Two pathways,", "joined at both ends"])

@frame("2D", "properties")
def _():
    return diag_left(open_st()) + side_text(1060, 300, None, ["Two pathways that", "behave differently"], None,
                                            [("Fast · conducts quickly", "neutral"), ("Slow · conducts slowly", "neutral"), ("They recover at different speeds", "amber")])

@frame("2E", "trigger")
def _():
    b = [diag_left(open_st(dot="stemtop", stem="on", arrows={"stem": "down"}))]
    b.append('<g id="Eyebrow">' + T(1060, 200, "THEN A TRIGGER", 22, 700, SEC, HEAD, ls="2.5") + '</g>')
    b.append(side_text(1060, 230, None, ["A premature beat"]))
    b.append(card(1040, 420, 760, 400, "Cards/Strip"))
    beats = [(0.15, "sinus"), (0.15 + 0.75, "sinus"), (0.15 + 1.25, "pac")]
    st, base = strip(1080, 470, 680, 300, beats, 400, amp=130, gid="ECG")
    b.append(st)
    ex = 1080 + (0.15 + 1.25) * 400
    b.append(ring(ex, base - 60, 46, AMBER_DEEP, "Focus/EarlyBeat"))
    c, _ = chip(ex, 740, "Early beat", "amber", anchor="middle"); b.append(c)
    return "".join(b)

def full_st(**kw):
    d = dict(node="on", tags=True, atria=True, labels=True)
    d.update(kw); return d

@frame("3A", "typical-avnrt")
def _():
    return diag_left(full_st(node="off")) + side_text(1060, 330, ("Typical AVNRT", "amber"), ["The small loop"], "Slow-fast")

@frame("3B", "property-cards")
def _():
    j, geo = junction(960, 600, 1.0, full_st(node="off", labels=False))
    b = [card(600, 120, 720, 840, "Cards/Diagram"), hb_for(geo, 960, 1.0, (600, 120, 720, 840)), j]
    for i, (t1, t2, t3) in enumerate((("Slow", "conducts slowly", "recovers quickly"), ("Fast", "conducts quickly", "recovers slowly"))):
        x = 120 if i == 0 else 1380
        b.append(card(x, 440, 420, 220, f"Cards/{t1}"))
        b.append(T(x + 36, 510, t1, 36, 700, INK, HEAD) + T(x + 36, 566, t2, 28, 500, SEC) + T(x + 36, 612, t3, 28, 500, SEC))
    return "".join(b)

@frame("3C", "sinus-down-fast")
def _():
    return diag_left(full_st(stem="on", right="on", his="on", arrows={"right": "down", "stem": "down"})) + side_text(1060, 380, ("Sinus beat", "neutral"), ["Down the", "fast pathway"])

@frame("3D", "slow-instead")
def _():
    j, geo = junction(540, 600, 1.0, full_st(stem="on", left="on", right="shade", arrows={"left": "down", "stem": "down"}))
    b = [card(120, 120, 840, 840, "Cards/Diagram"), hb_for(geo, 540, 1.0, (120, 120, 840, 840)), j]
    c, _ = chip(540 + 120 + 30, 600 - 90, "recovering", "dark"); b.append(c)
    b.append(side_text(1060, 380, ("Premature beat", "amber"), ["Down the", "slow pathway"]))
    return "".join(b)

@frame("3E", "recovered")
def _():
    return diag_left(full_st(stem="on", left="on", arrows={"left": "down"}, dot="node")) + side_text(1060, 380, ("Recovered", "neutral"), ["The fast pathway", "is ready again"])

@frame("3F", "back-up-fast")
def _():
    return diag_left(full_st(left="on", right="on", arrows={"left": "down", "right": "up"}, dot="top")) + side_text(1060, 380, None, ["Back up the", "fast pathway"])

@frame("3G", "self-sustaining")
def _():
    return diag_left(full_st(left="on", right="on", arrows={"left": "down", "right": "up"})) + side_text(1060, 380, ("Re-entry loop", "amber"), ["The loop is now", "self-sustaining"])

@frame("3H", "p-wave-hides")
def _():
    b = ['<g id="Header">' + T(120, 132, "AVNRT · THE SMALL LOOP", 22, 700, SEC, HEAD, ls="2.5") + T(120, 196, "Atria and ventricles fire together", 52, 600, INK, HEAD) + '</g>']
    b.append(card(120, 250, 760, 740, "Cards/Diagram") + card(940, 250, 860, 740, "Cards/ECG"))
    j, geo = junction(420, 590, 0.95, full_st(left="on", right="on", stem="on", his="on", arrows={"left": "down", "right": "up", "stem": "up"}, labels=False, atria_on=True))
    b.append(hb_for(geo, 420, 0.95, (120, 250, 760, 740)))
    b.append(j)
    ay = geo["atr_y"] + geo["atr_h"] / 2
    c, _ = chip(420 + geo["atr_w"] / 2 + 20, ay - 25, "Up to the atria"); b.append(c)
    c, _ = chip(420 + geo["br"] + 16, geo["his_bot"] + 4, "Down to the ventricles"); b.append(c)
    b.append(T(990, 320, "Lead II", 24, 500, SEC))
    st, base = strip(990, 340, 760, 170, run(0.08, RR, 6, "pseudoS"), 380, amp=70, grid=False, sw=3, gid="ECG/Strip")
    b.append(st)
    b.append(f'<rect id="ECG/ZoomFrame" x="{990 + (0.08 + 2*RR) * 380 - 50:.1f}" y="345" width="130" height="160" rx="12" fill="none" stroke="{DIV}" stroke-width="3"/>')
    b.append(f'<rect x="1080" y="540" width="580" height="360" rx="16" fill="{BG}" stroke="{DIV}" stroke-width="2"/>')
    st2, base2 = strip(1100, 550, 540, 330, [(0.25, "pseudoS")], 1500, amp=190, gid="ECG/Zoom")
    b.append(st2)
    px = 1100 + (0.25 + 0.045) * 1500; py = base2 + 0.30 * 190
    b.append(f'<g id="Focus/PWave"><circle cx="{px:.1f}" cy="{py:.1f}" r="38" fill="none" stroke="{CORAL}" stroke-width="5"/>'
             f'<line x1="{px:.1f}" y1="{py+38:.1f}" x2="{px:.1f}" y2="922" stroke="{CORAL}" stroke-width="2"/></g>')
    c, _ = chip(px - 30, 922, "P wave hides here", "coral"); b.append(c)
    return "".join(b)

@frame("3I", "pseudo-s-r-prime")
def _():
    b = [header("AVNRT on the ECG", "Where the P wave hides")]
    for i, (lead, kind, lab, off, sign) in enumerate((("Lead II (also III, aVF)", "pseudoS", "Pseudo S", 0.045, 1), ("V1", "pseudoR", "Pseudo R′", 0.042, -1))):
        x = 120 + i * 860
        b.append(card(x, 280, 820, 640, f"Cards/{lead.split()[0]}"))
        b.append(T(x + 40, 340, lead, 24, 500, SEC))
        st, base = strip(x + 40, 370, 740, 420, run(0.15, RR, 3, kind), 700, amp=160, gid=f"ECG/{lead.split()[0]}")
        b.append(st)
        px = x + 40 + (0.15 + RR + off) * 700
        py = base + (0.24 if kind == "pseudoS" else -0.30) * 160
        b.append(ring(px, py, 34, CORAL, f"Focus/{lab}"))
        c, _ = chip(px, 830, lab, "coraltint", anchor="middle"); b.append(c)
    return "".join(b)

@frame("3J", "stat-cards")
def _():
    b = [header("AVNRT", "The most common paroxysmal SVT in adults")]
    for i, (big, small) in enumerate((("50–60%", "of SVT cases"), ("Young", "adults, most often"), ("~2 in 3", "patients are women"))):
        x = 120 + i * 570
        b.append(card(x, 420, 520, 300, f"Cards/Stat{i+1}"))
        b.append(T(x + 48, 560, big, 96, 700, AMBER_DEEP if i == 0 else INK, HEAD) + T(x + 52, 630, small, 30, 500, SEC))
    return "".join(b)

@frame("4A", "accessory-pathway")
def _():
    h, geo = heart(540, 560, 1.0, {"plane": True, "pathway": True})
    b = [card(120, 120, 840, 840, "Cards/Heart"), h]
    b.append(side_text(1060, 300, ("AVRT", "amber"), ["The big loop"], "A strand of muscle that crosses the ring"))
    x, y = geo["ap"]
    b.append(leader(x + 14, y, 1040, 640)); c, _ = chip(1060, 615, "Accessory pathway", "dark"); b.append(c)
    x2, y2 = geo["plane_mid"]
    b.append(leader(x2, y2, 1040, 740)); c, _ = chip(1060, 715, "Fibrous ring"); b.append(c)
    return "".join(b)

@frame("4B", "ortho-down-node")
def _():
    return heart_left({"plane": True, "pathway": True, "big": "down"}) + side_text(1060, 330, ("Orthodromic AVRT", "amber"), ["Down the AV node"], None,
                                                                                    [("AV node → His-Purkinje", "neutral"), ("Usually narrow QRS", "neutral")])

@frame("4C", "ortho-back-up")
def _():
    return heart_left({"plane": True, "big": "ortho", "atria_wave": True}) + side_text(1060, 330, ("Orthodromic AVRT", "amber"), ["Back up the pathway"], None,
                                                                                         [("Up the accessory pathway → atria", "neutral"), ("The large majority of AVRT", "amber")])

@frame("4D", "p-trails-qrs")
def _():
    b = [header("AVRT on the ECG", "The P wave trails the QRS")]
    b.append(card(120, 260, 1680, 600, "Cards/ECG"))
    b.append(T(170, 320, "Lead II · 180 /min", 24, 500, SEC))
    pxs = 900
    st, base = strip(170, 340, 1580, 440, run(0.12, RR, 5, "retroP"), pxs, amp=170, gid="ECG")
    b.append(st)
    k = 2; t0 = 0.12 + k * RR
    qx = 170 + (t0 - 0.025) * pxs; pxp = 170 + (t0 + 0.10 - 0.025) * pxs; pyy = base + 0.22 * 170
    b.append(ring(170 + (t0 + 0.10) * pxs, pyy, 36, CORAL, "Focus/RetroP"))
    by = base + 120
    b.append(f'<g id="Bracket/RP"><path d="M{qx:.1f},{by-20:.1f} V{by:.1f} H{pxp:.1f} V{by-20:.1f}" stroke="{AMBER_DEEP}" stroke-width="4" fill="none"/></g>')
    c, _ = chip(qx - 10, by + 14, "RP: QRS onset → P onset", "amber"); b.append(c)
    c, _ = chip(120, 900, "In the ST segment, not inside the QRS", "coraltint"); b.append(c)
    c, _ = chip(720, 900, "Longer RP than typical AVNRT · often > 70 ms"); b.append(c)
    return "".join(b)

@frame("4E", "antidromic")
def _():
    b = [heart_left({"plane": True, "big": "anti", "vent_glow": True})]
    b.append(side_text(1060, 200, ("Antidromic AVRT", "amber"), ["Down the pathway,", "up the node"], "Ventricles activated muscle to muscle"))
    b.append(card(1040, 560, 760, 300, "Cards/Strip"))
    b.append(T(1080, 616, "Lead II · wide QRS", 24, 500, SEC))
    st, _ = strip(1080, 640, 680, 190, run(0.1, RR, 5, "wide"), 420, amp=80, gid="ECG")
    b.append(st)
    c, _ = chip(1060, 900, "Less common"); b.append(c)
    return "".join(b)

@frame("4F", "two-columns")
def _():
    b = []
    for i, (tag, l1, l2, sub) in enumerate((("AVNRT", "Most common paroxysmal", "SVT in adults", None), ("AVRT", "Most common SVT", "in children", "especially younger children"))):
        x = 120 + i * 860
        b.append(card(x, 300, 820, 480, f"Cards/{tag}"))
        c, _ = chip(x + 56, 360, tag, "amber"); b.append(c)
        b.append(T(x + 56, 520, l1, 52, 600, INK, HEAD) + T(x + 56, 584, l2, 52, 600, INK, HEAD))
        if sub: b.append(T(x + 56, 650, sub, 30, 500, SEC))
    return "".join(b)

def wpw_strip(x, y, w, h, gid="ECG", n=3, pxs=520, amp=150):
    rr = 0.8
    return strip(x, y, w, h, [(0.35 + i * rr, "wpw") for i in range(n)], pxs, amp=amp, gid=gid)

@frame("5A", "delta-wave")
def _():
    b = [header("Between episodes", "The resting ECG can carry a clue")]
    b.append(card(120, 260, 1680, 640, "Cards/ECG"))
    b.append(T(170, 320, "Lead II · sinus rhythm · Wolff-Parkinson-White pattern", 24, 500, SEC))
    pxs = 640
    st, base = strip(170, 340, 1580, 460, [(0.4 + i * 0.85, "wpw") for i in range(3)], pxs, amp=200, gid="ECG")
    b.append(st)
    t = 0.4 + 0.85
    dx = 170 + (t - 0.035) * pxs; dy = base - 0.30 * 200 * 0.9
    b.append(ring(dx, dy, 34, CORAL, "Focus/Delta"))
    c, _ = chip(dx, 380, "Delta wave", "coraltint", anchor="middle"); b.append(c)
    p0 = 170 + (t - 0.12 - 0.04) * pxs; q0 = 170 + (t - 0.06) * pxs
    by = base + 70
    b.append(f'<path id="Bracket/PR" d="M{p0:.1f},{by-16} V{by} H{q0:.1f} V{by-16}" stroke="{AMBER_DEEP}" stroke-width="4" fill="none"/>')
    c, _ = chip((p0 + q0) / 2, by + 16, "Short PR", "amber", anchor="middle"); b.append(c)
    t2 = 0.4 + 2 * 0.85
    w0 = 170 + (t2 - 0.06) * pxs; w1 = 170 + (t2 + 0.06) * pxs
    b.append(f'<path id="Bracket/QRS" d="M{w0:.1f},{by-16} V{by} H{w1:.1f} V{by-16}" stroke="{AMBER_DEEP}" stroke-width="4" fill="none"/>')
    c, _ = chip((w0 + w1) / 2, by + 16, "Wide QRS", "amber", anchor="middle"); b.append(c)
    return "".join(b)

@frame("5B", "manifest-vs-concealed")
def _():
    b = []
    for i, (lab, kind) in enumerate((("Manifest: conducts forward too", "wpw"), ("Concealed: conducts backward only · no pre-excitation", "sinus"))):
        y = 120 + i * 380
        b.append(card(120, y, 1680, 340, f"Cards/{lab.split(':')[0]}"))
        b.append(T(170, y + 60, lab, 30, 600, INK, HEAD))
        st, _ = strip(170, y + 90, 1580, 220, [(0.35 + k * 0.8, kind) for k in range(5)], 400, amp=100, gid=f"ECG/{lab.split(':')[0]}")
        b.append(st)
    c, _ = chip(960, 900, "A normal resting ECG does not rule out AVRT", "coral", size=28, anchor="middle"); b.append(c)
    return "".join(b)

def two_loops(blocked=False):
    b = [card(120, 260, 820, 720, "Cards/AVNRT"), card(980, 260, 820, 720, "Cards/AVRT")]
    stt = full_st(left="dim" if blocked else "on", right="dim" if blocked else "on", arrows={} if blocked else {"left": "down", "right": "up"},
                  node="blocked" if blocked else "on", tags=False, labels=False)
    j, geo = junction(530, 650, 0.9, stt)
    b.append(hb_for(geo, 530, 0.9, (120, 260, 820, 720)))
    b.append(j)
    if not blocked:
        b.append(ring(530, geo["node_y"], 72, CORAL, "Focus/NodeRing"))
    h, hg = heart(1390, 640, 0.82, {"big": None if blocked else "ortho", "pathway": True, "node_ring": not blocked, "node_blocked": blocked})
    b.append(h)
    c, _ = chip(160, 290, "AVNRT", "amber"); b.append(c)
    c, _ = chip(1020, 290, "AVRT", "amber"); b.append(c)
    if blocked:
        c, _ = chip(530, geo["node_y"] + 50, "AV node blocked", "dark", anchor="middle"); b.append(c)
        c, _ = chip(1370, 880, "AV node blocked", "dark", anchor="middle"); b.append(c)
    return "".join(b)

@frame("6A", "node-in-both")
def _():
    return header(None, "AV node in both circuits", y=120) + two_loops()

@frame("6B", "first-steps")
def _():
    b = ['<g id="Header">']
    c, w = chip(120, 110, "Stable · regular · narrow", "dark"); b.append(c)
    c2, w2 = chip(120 + w + 16, 110, "1 Vagal maneuver (Valsalva)"); b.append(c2)
    c3, _ = chip(120 + w + w2 + 32, 110, "2 Adenosine, unless contraindicated"); b.append(c3)
    b.append('</g>')
    return "".join(b) + two_loops(blocked=True)

@frame("6C", "unstable")
def _():
    b = [header("Regular, narrow-complex tachycardia", "First steps, same for both loops")]
    b.append(card(120, 260, 1680, 300, "Cards/Steps"))
    b.append(T(170, 350, "STABLE", 22, 700, SEC, HEAD, ls="2.5") + T(170, 480, "UNSTABLE", 22, 700, SEC, HEAD, ls="2.5"))
    c, w = chip(420, 318, "1 Vagal maneuver"); b.append(c)
    c, _ = chip(420 + w + 16, 318, "2 Adenosine, unless contraindicated"); b.append(c)
    c, w = chip(420, 448, "Synchronized cardioversion", "coral"); b.append(c)
    b.append(T(420 + w + 24, 484, "when the tachycardia causes the instability", 26, 500, SEC))
    b.append(card(120, 610, 1680, 360, "Cards/Strip"))
    b.append(T(170, 666, "Lead II", 24, 500, SEC))
    beats = run(0.12, RR, 7, "pseudoS") + [(0.12 + 6 * RR + 0.9 + i * 0.8, "sinus") for i in range(3)]
    st, base = strip(170, 690, 1580, 250, beats, 400, amp=100, gid="ECG")
    b.append(st)
    bx = 170 + (0.12 + 6 * RR + 0.45) * 400
    b.append(f'<line id="Marker/Shock" x1="{bx:.1f}" y1="690" x2="{bx:.1f}" y2="940" stroke="{AMBER_DEEP}" stroke-width="3" stroke-dasharray="10 8"/>')
    c, _ = chip(bx + 14, 700, "Loop broken", "amber"); b.append(c)
    return "".join(b)

@frame("6D", "caution-wide")
def _():
    b = [card(120, 120, 1680, 380, "Cards/Caution")]
    c, _ = chip(170, 170, "Caution · wide complex", "dark"); b.append(c)
    b.append(T(170, 320, "Antidromic AVRT", 52, 600, INK, HEAD))
    c, w = chip(170, 370, "Avoid AV nodal blockers", "coraltint"); b.append(c)
    b.append(T(170 + w + 24, 406, "Procainamide is an alternative", 28, 500, INK))
    b.append(card(120, 560, 1680, 400, "Cards/Strip"))
    b.append(T(170, 620, "Lead II · regular, wide QRS · 180 /min", 24, 500, SEC))
    st, _ = strip(170, 650, 1580, 270, run(0.1, RR, 10, "wide"), 470, amp=110, gid="ECG")
    b.append(st)
    return "".join(b)

@frame("6E", "pre-excited-af")
def _():
    b = [card(120, 100, 1680, 470, "Cards/Danger")]
    c, w = chip(170, 150, "Danger", "coral"); b.append(c)
    b.append(T(170 + w + 20, 186, "A SEPARATE ARRHYTHMIA", 22, 700, SEC, HEAD, ls="2.5"))
    b.append(T(170, 290, "Pre-excited atrial fibrillation", 52, 600, INK, HEAD))
    b.append(T(170, 344, "Very fast · irregular · wide, in a patient with an accessory pathway", 30, 500, SEC))
    c, w1 = chip(170, 400, "Avoid AV nodal blockers, including adenosine", "coraltint"); b.append(c)
    c, w2 = chip(170, 474, "Stable: procainamide"); b.append(c)
    c, _ = chip(170 + w2 + 16, 474, "Unstable: electrical cardioversion"); b.append(c)
    b.append(card(120, 620, 1680, 360, "Cards/Strip"))
    b.append(T(170, 676, "Lead II · irregularly irregular, wide", 24, 500, SEC))
    import random
    rnd = random.Random(7); t = 0.08; beats = []
    while t < 3.3:
        beats.append((t, "wide", rnd.uniform(0.7, 1.15))); t += rnd.uniform(0.2, 0.42)
    st, _ = strip(170, 700, 1580, 250, beats, 470, amp=100, gid="ECG")
    b.append(st)
    return "".join(b)

@frame("6F", "ablate-slow")
def _():
    return diag_left(full_st(right="on", left="dim", ablate="left", node="on")) + side_text(1060, 380, ("AVNRT", "amber"), ["Ablate the", "slow pathway"], None, [("Success above 95%", "neutral")])

@frame("6G", "ablate-pathway")
def _():
    return heart_left({"plane": True, "pathway": True, "ablate_path": True}) + side_text(1060, 380, ("AVRT", "amber"), ["Ablate the", "accessory pathway"])

@frame("7A", "clue-not-rule")
def _():
    b = []
    for i, (tag, line, kind) in enumerate((("Small loop", "Typical AVNRT: P usually hidden in the QRS", "pseudoS"), ("Big loop", "Orthodromic AVRT: P usually trails the QRS", "retroP"))):
        y = 110 + i * 400
        b.append(card(120, y, 1680, 360, f"Cards/{tag.replace(' ', '')}"))
        c, w = chip(170, y + 34, tag, "amber"); b.append(c)
        b.append(T(170 + w + 20, y + 72, line, 30, 600, INK, HEAD))
        b.append(T(1750, y + 72, "Lead II · 180 /min", 24, 500, SEC, BODY, "end"))
        st, base = strip(170, y + 110, 1580, 220, run(0.12, RR, 9, kind), 540, amp=100, gid=f"ECG/{tag.replace(' ', '')}")
        b.append(st)
        for k in range(9):
            t = 0.12 + k * RR
            px = 170 + (t + (0.045 if kind == "pseudoS" else 0.10)) * 540
            if px < 1745:
                b.append(f'<circle cx="{px:.1f}" cy="{base + 0.22*100:.1f}" r="16" fill="none" stroke="{CORAL}" stroke-width="3"/>')
    c, _ = chip(960, 920, "A clue, not a rule", "dark", size=30, anchor="middle"); b.append(c)
    return "".join(b)

for bid, (name, fn) in F.items():
    with open(os.path.join(OUT, f"{bid}_{name}.svg"), "w") as f:
        f.write(svg(bid, fn()))
print(len(F))
