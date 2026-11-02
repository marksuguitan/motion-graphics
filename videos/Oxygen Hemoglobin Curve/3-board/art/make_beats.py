# Motion Board pass 1 beat frames, Oxygen Hemoglobin Curve, Style C (card stage).
# One SVG per beat at the end state of its Intent. Layers: id = Group_x2F_Sublayer (Illustrator reads it as Group/Sublayer).
import sys, os, math
OUT = sys.argv[1]
N = 2.7
def S(p, p50): return 0.0 if p <= 0 else 100 * p**N / (p**N + p50**N)
def L(s): return s.replace("/", "_x2F_")
C = dict(white="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A", mute="#B9B5AE",
         coral="#F0645A", coralsoft="#FDE3E0", teal="#2E9C8F", tealsoft="#DDF0ED", red="#C94A44", deoxy="#8A3C6B",
         alert="#E53935")  # alert: bright red highlight (heme circles, Mark Nov 2, 2026)
H = "font-family:Manrope"; B = "font-family:Inter"
def SUB(s, size=None):
    k=int((size or 30)*0.68)
    return s.replace("O2", f'O<tspan font-size="{k}" baseline-shift="sub">2</tspan>').replace("P50", f'P<tspan font-size="{k}" baseline-shift="sub">50</tspan>')

def text(x, y, s, size=28, weight=400, fill=C["ink"], font=B, anchor="start", ls=None, sub=True):
    style = f"{font};font-size:{size}px;font-weight:{weight}" + (f";letter-spacing:{ls}px" if ls else "")
    body = SUB(s, size) if sub else s
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" style="{style}" fill="{fill}">{body}</text>'

def group(name, *items): return f'<g id="{L(name)}">' + "\n".join(items) + '</g>'

def card(x, y, w, h, fill=C["white"], r=24, shadow=True):
    s = ""
    if shadow: s += f'<rect x="{x}" y="{y+8}" width="{w}" height="{h}" rx="{r}" fill="#222222" opacity="0.08" filter="url(#soft)"/>'
    return s + f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>'

def chip(x, y, w, s, fill=C["white"], stroke=C["div"], col=C["ink"], size=28, weight=500, h=56):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}"' + (f' stroke="{stroke}" stroke-width="2"' if stroke else "") + '/>'
            + text(x+20, y+h/2+size*0.36, s, size, weight, col))

class Frame:
    def __init__(s, beat, name, kicker="THE OXYHEMOGLOBIN DISSOCIATION CURVE"):
        s.beat, s.name, s.parts = beat, name, []
        s.parts.append(group("Background/Fill", f'<rect width="1920" height="1080" fill="{C["soft"]}"/>'))
        if kicker: s.parts.append(group("Header/Kicker", text(120, 96, kicker, 23, 700, C["ink2"], H, ls=3)))
    def add(s, *p): s.parts += p
    def save(s):
        s.parts.append(group("Meta/BeatID", text(1880, 1052, s.beat, 22, 500, C["ink2"], anchor="end")))
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'
               '<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="12"/></filter></defs>\n'
               + "\n".join(s.parts) + "\n</svg>")
        open(os.path.join(OUT, f"{s.beat}_{s.name}.svg"), "w").write(svg)

# ---------- graph ----------
GX, GY, GW, GH = 300, 210, 820, 600
X = lambda p: GX + GW * p / 100
Y = lambda v: GY + GH - GH * v / 100
def curve_path(p50, p0=0, p1=100):
    pts = [f"{X(p0 + (p1-p0)*i/300):.1f},{Y(S(p0 + (p1-p0)*i/300, p50)):.1f}" for i in range(301)]
    return "M" + " L".join(pts)
def stage(): return group("Background/Stage", card(96, 150, 1080, 840))
def axes(xaxis=True, yaxis=True, grid=True, ticks=True):
    g = []
    if grid:
        gl = []
        for v in range(0, 101, 20):
            gl.append(f'<line x1="{X(v):.1f}" y1="{GY}" x2="{X(v):.1f}" y2="{GY+GH}" stroke="{C["div"]}" stroke-width="2"/>')
            gl.append(f'<line x1="{GX}" y1="{Y(v):.1f}" x2="{GX+GW}" y2="{Y(v):.1f}" stroke="{C["div"]}" stroke-width="2"/>')
        g.append(group("Graph/Grid", *gl))
    a = []
    if xaxis:
        a.append(f'<line x1="{GX}" y1="{GY+GH}" x2="{GX+GW}" y2="{GY+GH}" stroke="{C["ink"]}" stroke-width="3" stroke-linecap="round"/>')
        if ticks: a += [text(X(v), GY+GH+44, str(v), 26, 500, C["ink2"], anchor="middle") for v in range(0, 101, 20)]
        a.append(text(GX+GW/2, GY+GH+98, "PO2 (mmHg)", 30, 500, anchor="middle"))
    if yaxis:
        a.append(f'<line x1="{GX}" y1="{GY}" x2="{GX}" y2="{GY+GH}" stroke="{C["ink"]}" stroke-width="3" stroke-linecap="round"/>')
        if ticks: a += [text(GX-18, Y(v)+9, str(v), 26, 500, C["ink2"], anchor="end") for v in range(0, 101, 20)]
        a.append(f'<text transform="translate({GX-92},{GY+GH/2}) rotate(-90)" text-anchor="middle" style="{B};font-size:30px;font-weight:500" fill="{C["ink"]}">Hemoglobin saturation (%)</text>')
    g.append(group("Graph/Axes", *a))
    return "\n".join(g)
def normal_curve(col=C["teal"], label=False, opacity=1, p50=26.8, name="Curves/Normal"):
    g = [f'<path d="{curve_path(p50)}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round" opacity="{opacity}"/>']
    if label: g.append(text(X(p50)-14, Y(50)-22, label, 26, 600, col, anchor="end"))
    return group(name, *g)
def point(p, v, col, label=None, side="right", dy=0, r=11):
    g = [f'<circle cx="{X(p):.1f}" cy="{Y(v):.1f}" r="{r}" fill="{col}" stroke="#FFFFFF" stroke-width="4"/>']
    if label:
        g.append(text(X(p)+(22 if side=="right" else -22), Y(v)+9+dy, label, 26, 600, col, anchor="start" if side=="right" else "end"))
    return "\n".join(g)
def guides(p, v, col, dash="6 8"):
    return (f'<path d="M{X(p):.1f},{Y(0):.1f} V{Y(v):.1f} H{X(0):.1f}" fill="none" stroke="{col}" stroke-width="3" stroke-dasharray="{dash}" stroke-linecap="round"/>')
def side_card(kicker, heading, lines=(), y=290, h=None, chips=None, hl=None):
    h = h or (190 + 74*len(lines) + (78*len(chips) if chips else 0))
    g = [card(1240, y, 600, h), text(1288, y+62, kicker, 23, 700, C["ink2"], H, ls=3), text(1288, y+124, heading, 46, 600, C["ink"], H)]
    yy = y + 196
    for i, ln in enumerate(lines):
        col = C["ink"] if not hl or i in hl else C["ink2"]
        g.append(text(1288, yy, ln, 28, 400, col)); yy += 50
    if chips:
        yy -= 20
        for c in chips:
            g.append(c(1280, yy)); yy += 78
    return group("Panel/Card", *g)
def note(x, y, s, col=C["ink2"]): return text(x, y, s, 22, 400, col)

def F(beat, name, **k): return Frame(beat, name, **k)

# ---------- Scene 1 ----------
def capillary(y=540, x0=140, x1=1780):
    return group("Vessel/Capillary",
        f'<rect x="{x0}" y="{y-110}" width="{x1-x0}" height="220" rx="110" fill="#F6E7E4"/>',
        f'<rect x="{x0}" y="{y-110}" width="{x1-x0}" height="220" rx="110" fill="none" stroke="#E7C9C3" stroke-width="4"/>')
def rbc(cx, cy, col, scale=1.0, o2=0, name="Cell/RBC"):
    rx, ry = 110*scale, 70*scale
    g = [f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{col}"/>',
         f'<ellipse cx="{cx}" cy="{cy}" rx="{rx*0.48}" ry="{ry*0.42}" fill="#FFFFFF" opacity="0.22"/>']
    for i in range(o2):
        a = -math.pi/2 + i*2*math.pi/8
        g.append(o2dot(cx + (rx+30)*math.cos(a)*0.95, cy + (ry+30)*math.sin(a)))
    return group(name, *g)
def o2dot(x, y, col=C["red"]):
    return (f'<g><circle cx="{x-9:.1f}" cy="{y:.1f}" r="10" fill="{col}"/><circle cx="{x+9:.1f}" cy="{y:.1f}" r="10" fill="{col}"/></g>')

f = F("1A", "red-cell", kicker=None)
f.add(group("Background/Stage", card(96, 150, 1728, 780)), capillary(), rbc(960, 540, C["deoxy"]),
      group("Label/Title", text(960, 300, "Every red blood cell has two jobs", 56, 600, C["ink"], H, anchor="middle")))
f.save()


# Simple line icons (drawn for this video, 100x100 box, Nov 2, 2026)
LUNGS_D = ["M50 6 V36 M50 36 L40 45 M50 36 L60 45",
           "M42 24 C29 25 14 48 12 76 C11 87 19 92 29 88 L41 83 C44 81 45 77 45 73 V31 C45 27 44 24 42 24 Z",
           "M58 24 C71 25 86 48 88 76 C89 87 81 92 71 88 L59 83 C56 81 55 77 55 73 V31 C55 27 56 24 58 24 Z",
           "M40 45 L27 57 M33 51 L31 42 M27 57 L19 58 M27 57 L26 68",
           "M60 45 L73 57 M67 51 L69 42 M73 57 L81 58 M73 57 L74 68"]
# Flexed arm: Mark's drawing (arm-flex.svg, Nov 2, 2026; 4000-unit art board), fitted into the 100-unit icon box
# by ARM_FIT = (scale, dx, dy): bbox x 1442.7-2557.3, y 1267.3-2735.7 -> 88 units tall, centred on x 50, top at y 4.
ARM_D = ["M1442.68,2129.28c220.45-167.33,585.04-90.76,757.39,238.18",
         "M2027.72,2158.66s279.21-243.51,206.37-509.33",
         "M1442.68,2657.91c517.88,175.11,1054.39,0,1054.39,0,127.21-495.07,16.69-1080.19-4.07-1202.75-2.43-14.35-10.09-27.31-21.6-36.21-46.56-36.02-215.82-124.4-460.17-151.36-19.88-2.19-38.63,9.7-45.05,28.65l-67.59,212.77,56.86,95.04",
         "M1531.13,2418.41c127.77,63.89,225.28,78.49,348.2,67.25",
         "M2097.06,1535.11l-181.51,88.35c-23.6,14.24-22.31,48.88,2.27,61.34,0,0,131.65-2.49,174.99,3.51,27.55,3.82,139.72,17.17,139.72,17.17"]
ARM_FIT = (0.05993, -69.86, -71.95)
def line_icon(name, paths, cx, top, size, col, weight=5.5, fit=None):
    k = size/100
    body = "".join(f'<path d="{d}"/>' for d in paths)
    sw = weight/k
    if fit:  # art drawn on another board: map it into the 100-unit box, keeping the same on-screen line weight
        sc, dx, dy = fit
        body = f'<g transform="translate({dx},{dy}) scale({sc})">{body}</g>'
        sw = weight/(k*sc)
    return group(name, f'<g transform="translate({cx-50*k:.1f},{top}) scale({k:.3f})" fill="none" stroke="{col}" stroke-width="{sw:.2f}" stroke-linecap="round" stroke-linejoin="round">{body}</g>')
f = F("1B", "lungs-tissues", kicker=None)
f.add(group("Background/Stage", card(96, 150, 1728, 780)), capillary(),
      group("Zone/Lungs", f'<rect x="140" y="430" width="700" height="220" rx="110" fill="{C["red"]}" opacity="0.08"/>', text(490, 862, "Lungs: pick up O2", 32, 600, C["red"], anchor="middle")),
      group("Zone/Tissues", f'<rect x="1080" y="430" width="700" height="220" rx="110" fill="{C["deoxy"]}" opacity="0.08"/>', text(1430, 862, "Tissues: let it go", 32, 600, C["deoxy"], anchor="middle")),
      rbc(490, 540, C["red"], o2=8, name="Cell/Lungs"), rbc(1430, 540, C["deoxy"], o2=6, name="Cell/Tissues"),
      line_icon("Icon/Lungs", LUNGS_D, 490, 680, 120, C["red"]), line_icon("Icon/Tissues", ARM_D, 1430, 680, 120, C["deoxy"], fit=ARM_FIT),
      group("Cell/Released", o2dot(1640, 400, C["red"]), o2dot(1700, 690, C["red"])),
      group("Label/Arrow", f'<path d="M700,540 H1200" stroke="{C["ink2"]}" stroke-width="4" stroke-dasharray="2 14" stroke-linecap="round"/>', f'<path d="M1190,524 l18,16 l-18,16" fill="none" stroke="{C["ink2"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'),
      group("Readout/SO2", chip(400, 300, 180, "SO2 97%", C["white"], C["div"], C["red"], 28, 600), chip(1340, 300, 180, "SO2 75%", C["white"], C["div"], C["deoxy"], 28, 600)))
f.save()

f = F("1C", "title", kicker=None)
f.add(group("Background/Stage", card(96, 150, 1728, 780)),
      group("Title/Text", text(960, 500, "The oxyhemoglobin", 84, 600, C["ink"], H, anchor="middle"), text(960, 600, "dissociation curve", 84, 600, C["ink"], H, anchor="middle")),
      group("Title/Fact", chip(660, 680, 600, "Hemoglobin carries 98% of blood O2", C["soft"], None, C["ink2"], 28, 500)))
f.save()

# ---------- Scene 2 ----------
# Mark 2026-11-02 (v9): the axes come apart so each piece can arrive on its word (line, tick numbers, gridlines), and the
# notes move out from under the axes into a side card to the right of the graph, as in later scenes. Wording unchanged.
def axes_parts(yaxis=True):
    g = [group("Graph/GridV", *[f'<line x1="{X(v):.1f}" y1="{GY}" x2="{X(v):.1f}" y2="{GY+GH}" stroke="{C["div"]}" stroke-width="2"/>' for v in range(20, 101, 20)])]
    if yaxis: g.append(group("Graph/GridH", *[f'<line x1="{GX}" y1="{Y(v):.1f}" x2="{GX+GW}" y2="{Y(v):.1f}" stroke="{C["div"]}" stroke-width="2"/>' for v in range(20, 101, 20)]))
    g.append(group("Graph/AxisX", f'<line x1="{GX}" y1="{GY+GH}" x2="{GX+GW}" y2="{GY+GH}" stroke="{C["ink"]}" stroke-width="3" stroke-linecap="round"/>',
                   text(GX+GW/2, GY+GH+98, "PO2 (mmHg)", 30, 500, anchor="middle")))
    g.append(group("Graph/TicksX", *[text(X(v), GY+GH+44, str(v), 26, 500, C["ink2"], anchor="middle") for v in range(0, 101, 20)]))
    if yaxis:
        g.append(group("Graph/AxisY", f'<line x1="{GX}" y1="{GY}" x2="{GX}" y2="{GY+GH}" stroke="{C["ink"]}" stroke-width="3" stroke-linecap="round"/>',
                       f'<text transform="translate({GX-92},{GY+GH/2}) rotate(-90)" text-anchor="middle" style="{B};font-size:30px;font-weight:500" fill="{C["ink"]}">Hemoglobin saturation (%)</text>'))
        g.append(group("Graph/TicksY", *[text(GX-18, Y(v)+9, str(v), 26, 500, C["ink2"], anchor="end") for v in range(0, 101, 20)]))
    return g
def axes_card(y_note=True):
    g = [group("Panel/Card", card(1240, 290, 600, 384), text(1288, 352, "THE AXES", 23, 700, C["ink2"], H, ls=3)),
         group("Note/XTerm", text(1288, 424, "PO2", 40, 600, C["ink"], H)),
         group("Note/XDef", text(1288, 484, "= dissolved O2", 28, 400, C["ink"]))]
    if y_note: g.append(group("Note/Y", text(1288, 566, "SO2", 40, 600, C["ink"], H), text(1288, 626, "= Hb binding sites filled", 28, 400, C["ink"])))
    return g
f = F("2A", "x-axis"); f.add(stage(), *[x for x in axes_parts(yaxis=False)], *axes_card(y_note=False))
f.save()
f = F("2B", "y-axis"); f.add(stage(), *axes_parts(), *axes_card())
f.save()

# ---------- Scene 3: tetramer ----------
def tetramer(cx, cy, bound=(), rings=(), co=None, scale=1.0, name="Hb/Tetramer", labels=True, split=False):
    # Mark (Nov 2, 2026): all four subunits red (was alpha pink, beta blue). split=True gives one top-level layer per subunit
    # ("Hb/α1" ...) so the T to R shape change can move them separately.
    subs = []
    sub = [("α1", -1, -1), ("β1", 1, -1), ("β2", -1, 1), ("α2", 1, 1)]
    for i, (lab, sx, sy) in enumerate(sub):
        g = []
        x, y = cx + sx*130*scale, cy + sy*110*scale
        g.append(f'<rect x="{x-120*scale:.1f}" y="{y-100*scale:.1f}" width="{240*scale:.1f}" height="{200*scale:.1f}" rx="{90*scale:.1f}" fill="{HB_FILL}"/>')
        hx, hy = x + sx*30*scale, y + sy*20*scale
        g.append(f'<rect x="{hx-34*scale:.1f}" y="{hy-34*scale:.1f}" width="{68*scale:.1f}" height="{68*scale:.1f}" rx="{14*scale:.1f}" fill="#FFFFFF" stroke="{C["ink2"]}" stroke-width="{3*scale:.1f}"/>')
        g.append(f'<circle cx="{hx:.1f}" cy="{hy:.1f}" r="{9*scale:.1f}" fill="{C["ink2"]}"/>')
        if i in rings: g.append(f'<rect x="{hx-48*scale:.1f}" y="{hy-48*scale:.1f}" width="{96*scale:.1f}" height="{96*scale:.1f}" rx="{20*scale:.1f}" fill="none" stroke="{C["coral"]}" stroke-width="{5*scale:.1f}"/>')
        if i in bound: g.append(o2dot(hx + sx*62*scale, hy - 0*scale))
        if co is not None and i == co:
            g.append(f'<circle cx="{hx + sx*62*scale:.1f}" cy="{hy:.1f}" r="{34*scale:.1f}" fill="{C["mute"]}"/>' + text(hx + sx*62*scale, hy+10*scale, "CO", 30*scale, 700, "#FFFFFF", anchor="middle", sub=False))
        if labels: g.append(text(x - sx*52*scale, y + 10*scale, lab, 30*scale, 600, C["ink"], anchor="middle", sub=False))
        subs.append((lab, g))
    if split: return "\n".join(group(f"Hb/{lab}", *g) for lab, g in subs)
    return group(name, *[e for _, g in subs for e in g])
HB_FILL = "#F1DCD6"
def heme_xy(cx, cy, i, scale=1.0):
    sx, sy = [(-1, -1), (1, -1), (-1, 1), (1, 1)][i]
    return cx + sx*160*scale, cy + sy*130*scale
def o2_mol(name, x, y, label=True):
    # a free O2 with its label above; AE moves it onto its heme (bound spot = heme x -/+ 62)
    return group(name, o2dot(x, y), *( [text(x, y-34, "O2", 30, 700, C["red"], H, anchor="middle")] if label else []))

f = F("3A", "four-subunits"); f.add(group("Background/Stage", card(96, 150, 1080, 840)),
      group("Label/Header", text(636, 250, "Adult hemoglobin (HbA)", 48, 600, C["ink"], H, anchor="middle", sub=False)),
      tetramer(636, 590),
      # Mark (Nov 2, 2026): on "heme" a bright red circle draws around each heme and draws itself out
      *[group(f"Heme/Circle {lab}", f'<circle cx="{heme_xy(636, 590, i)[0]:.1f}" cy="{heme_xy(636, 590, i)[1]:.1f}" r="50" fill="none" stroke="{C["alert"]}" stroke-width="6" stroke-linecap="round"/>')
        for i, lab in enumerate(["α1", "β1", "β2", "α2"])],
      # Mark (Nov 2, 2026): an O2 appears at the right on "bind" and travels to α1's heme (bound spot 414,460)
      o2_mol("O2/First", 1060, 590),
      side_card("STRUCTURE", "4 subunits", ["Each holds one heme", "Each heme binds one O2"]))
f.save()
f = F("3B", "cooperative"); f.add(group("Background/Stage", card(96, 150, 1080, 840)),
      group("Label/Header", text(636, 250, "Adult hemoglobin (HbA)", 48, 600, C["ink"], H, anchor="middle", sub=False)),
      tetramer(636, 590, bound=(0,), rings=(1, 2, 3), split=True),
      # Mark (Nov 2, 2026): after the shape change the next O2s bind more easily: they come in fast to β1 (858,460), β2 (414,720), α2 (858,720)
      o2_mol("O2/Next β1", 1060, 470), o2_mol("O2/Next β2", 1060, 590), o2_mol("O2/Next α2", 1060, 710),
      side_card("COOPERATIVE BINDING", "T state → R state", ["First O2 binds, shape changes"], chips=[lambda x, y: chip(x, y, 520, "Remaining sites: higher O2 affinity", C["coralsoft"], None, C["ink"], 26, 600)]))
f.save()
f = F("3C", "straight-line"); f.add(stage(), axes(),
      group("Curves/Straight", f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(100)}" y2="{Y(100)}" stroke="{C["mute"]}" stroke-width="5" stroke-dasharray="14 12" stroke-linecap="round"/>', text(X(62), Y(70), "Not a straight line", 26, 600, C["ink2"])))
f.save()
f = F("3D", "sigmoid"); f.add(stage(), axes(),
      group("Curves/Straight", f'<line x1="{X(0)}" y1="{Y(0)}" x2="{X(100)}" y2="{Y(100)}" stroke="{C["mute"]}" stroke-width="4" stroke-dasharray="14 12" opacity="0.5"/>'),
      normal_curve(), group("Label/Sigmoid", chip(X(46), Y(48), 210, "S-shaped", C["tealsoft"], None, C["ink"], 28, 600)),
      side_card("THE SHAPE", "Sigmoid curve", ["Cooperative binding", "makes it S-shaped"]))
f.save()

# ---------- Scene 4 ----------
def band():
    return group("Band/Unloaded", f'<rect x="{GX}" y="{Y(S(100,26.8)):.1f}" width="{GW}" height="{Y(75)-Y(S(100,26.8)):.1f}" fill="{C["coral"]}" opacity="0.10"/>')
f = F("4A", "arterial"); f.add(stage(), axes(), normal_curve(),
      group("Point/Arterial", guides(100, 97, C["coral"]), point(100, 97, C["coral"], "Arterial", "left", dy=-30)),
      side_card("LEAVING THE LUNGS", "Arterial blood", ["PO2 ≈ 100 mmHg", "SO2 ≈ 97%"]))
f.save()
f = F("4B", "mixed-venous"); f.add(stage(), axes(), normal_curve(),
      group("Point/Arterial", point(100, 97, C["coral"], "Arterial", "left", dy=-30)),
      group("Point/Venous", guides(40, 75, C["coral"]), point(40, 75, C["coral"], "Mixed venous", "right", dy=40)),
      side_card("AFTER RESTING TISSUES", "Mixed venous", ["PO2 ≈ 40 mmHg", "SO2 ≈ 75%"]))
f.save()
f = F("4C", "quarter"); f.add(stage(), axes(), band(), normal_curve(),
      group("Point/Arterial", point(100, 97, C["coral"], "Arterial", "left", dy=-30)),
      group("Point/Venous", point(40, 75, C["coral"], "Mixed venous", "right", dy=40)),
      side_card("AT REST, PER PASS", "About 1/4 unloaded", ["(97 − 75) / 97 ≈ 23%"]))
f.save()

# ---------- Scene 5 ----------
f = F("5A", "halfway"); f.add(stage(), axes(), normal_curve(),
      group("Guide/Fifty", f'<line x1="{X(0)}" y1="{Y(50)}" x2="{X(26.8):.1f}" y2="{Y(50)}" stroke="{C["coral"]}" stroke-width="3" stroke-dasharray="6 8" stroke-linecap="round"/>', point(26.8, 50, C["coral"])),
      side_card("A LANDMARK", "P50", ["PO2 at 50% saturation"]))
f.save()
f = F("5B", "p50-value"); f.add(stage(), axes(), normal_curve(),
      group("Guide/Fifty", guides(26.8, 50, C["coral"]), point(26.8, 50, C["coral"]), text(X(26.8)+14, Y(0)-16, "27", 28, 700, C["coral"])),
      side_card("NORMAL ADULT BLOOD", "P50 ≈ 27 mmHg", [], h=170))
f.save()

# ---------- Scene 6 ----------
def marker_bars(p0, p1, p50=26.8, col=C["coral"]):
    s0, s1 = S(p0, p50), S(p1, p50)
    return group("Marker/Bars",
        f'<path d="{curve_path(p50, p1, p0)}" fill="none" stroke="{col}" stroke-width="12" stroke-linecap="round" opacity="0.35"/>',
        f'<line x1="{X(p1):.1f}" y1="{Y(0)+18}" x2="{X(p0):.1f}" y2="{Y(0)+18}" stroke="{col}" stroke-width="10" stroke-linecap="round"/>',
        f'<line x1="{X(0)-18}" y1="{Y(s0):.1f}" x2="{X(0)-18}" y2="{Y(s1):.1f}" stroke="{col}" stroke-width="10" stroke-linecap="round"/>',
        point(p1, s1, col))
f = F("6A", "flat-top"); f.add(stage(), axes(), normal_curve(), marker_bars(100, 60),
      side_card("THE PLATEAU", "Relatively flat", ["PO2 100 → 60 mmHg", f"SO2 97% → {S(60,26.8):.0f}%"]))
f.save()
f = F("6B", "plateau-steep"); f.add(stage(), axes(),
      group("Region/Plateau", f'<rect x="{X(60):.1f}" y="{GY}" width="{X(100)-X(60):.1f}" height="{GH}" fill="{C["teal"]}" opacity="0.07"/>', text(X(80), GY-18, "Plateau", 26, 600, C["teal"], anchor="middle")),
      group("Region/Steep", f'<rect x="{X(10):.1f}" y="{GY}" width="{X(60)-X(10):.1f}" height="{GH}" fill="{C["coral"]}" opacity="0.07"/>', text(X(35), GY-18, "Steep", 26, 600, C["coral"], anchor="middle")),
      normal_curve(),
      side_card("THE SHAPE", "Two jobs, two parts", ["Plateau protects loading", "Below 60, it gets steep"]))
f.save()
f = F("6C", "steep-unloading"); f.add(stage(), axes(), normal_curve(), marker_bars(40, 30),
      side_card("IN THE TISSUES", "Efficient unloading", ["PO2 40 → 30 mmHg", f"SO2 75% → {S(30,26.8):.0f}%"]))
f.save()

# ---------- Scene 7 ----------
f = F("7A", "shifts"); f.add(stage(), axes(),
      group("Curves/Ghosts", f'<path d="{curve_path(20)}" fill="none" stroke="{C["mute"]}" stroke-width="4" stroke-dasharray="10 10"/>', f'<path d="{curve_path(36)}" fill="none" stroke="{C["mute"]}" stroke-width="4" stroke-dasharray="10 10"/>'),
      normal_curve(), group("Marker/P50", point(26.8, 50, C["coral"]),
      # Mark (Nov 2, 2026): the arrows sat 40 px above the dot. P50 is read at 50% saturation, so they now run along the
      # 50% line from the dot to the left-shift (P50 20) and right-shift (P50 36) ghost curves.
      f'<path d="M{X(26.8)-18:.1f},{Y(50):.1f} H{X(20)+6:.1f} m12,-10 l-12,10 l12,10 M{X(26.8)+18:.1f},{Y(50):.1f} H{X(36)-6:.1f} m-12,-10 l12,10 l-12,10" fill="none" stroke="{C["coral"]}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'),
      side_card("SHIFTS", "Watch the P50", ["It shows which way", "affinity has changed"]))
f.save()

# ---------- Scene 8 ----------
def shifted(p50, col=C["coral"], label=None, name="Curves/Shift", below=True):
    g = [f'<path d="{curve_path(p50)}" fill="none" stroke="{col}" stroke-width="7" stroke-linecap="round"/>',
         f'<line x1="{X(26.8):.1f}" y1="{Y(50):.1f}" x2="{X(p50):.1f}" y2="{Y(50):.1f}" stroke="{col}" stroke-width="3" stroke-dasharray="2 9" stroke-linecap="round"/>',
         point(p50, 50, col, r=9)]
    if label:  # "\n" stacks the label (Mark, Nov 2, 2026: left-side labels overlapped the y axis); lines grow upward when above
        lines = label.split("\n")
        for i, ln in enumerate(lines):
            dy = 38 + i*30 if below else -24 - (len(lines)-1-i)*30
            g.append(text(X(p50)+(18 if below else -18), Y(50)+dy, ln, 26, 600, col, anchor="start" if below else "end"))
    return group(name, *g)
def factor_chips(rows, bohr_rows=(), accent=C["coral"], bohr=False, y0=486):
    g = []
    for i, (arrow, lab) in enumerate(rows):
        ty = y0 + i*78
        g.append(f'<rect x="1280" y="{ty-46}" width="290" height="62" rx="12" fill="#FFFFFF" stroke="{C["div"]}" stroke-width="2"/>')
        g.append(text(1300, ty, arrow, 32, 600, accent if i in bohr_rows or not bohr else C["ink2"]))
        g.append(text(1340, ty, lab, 32, 600 if (i in bohr_rows or not bohr) else 400, C["ink"] if (i in bohr_rows or not bohr) else C["ink2"], sub=False))
    out = [group("Factors/List", *g)]
    if bohr:
        by0, by1, bx = y0-34, y0+78+10, 1590
        out.append(group("Factors/Bohr", f'<path d="M{bx},{by0} h18 V{by1} h-18" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>',
            f'<rect x="{bx+40}" y="{(by0+by1)/2-31}" width="190" height="62" rx="12" fill="{accent}"/>', text(bx+135, (by0+by1)/2+10, "Bohr effect", 27, 700, "#FFFFFF", H, anchor="middle")))
    return "\n".join(out)
CO2 = 'CO<tspan font-size="22" baseline-shift="sub">2</tspan>'
RIGHT = [("↓", "pH"), ("↑", CO2), ("↑", "2,3-DPG"), ("↑", "Temperature")]
LEFT = [("↑", "pH"), ("↓", CO2), ("↓", "2,3-DPG"), ("↓", "Temperature")]
def factor_card(kicker, heading, rows, bohr=False):
    return "\n".join([group("Panel/Card", card(1240, 290, 600, 520), text(1288, 352, kicker, 23, 700, C["ink2"], H, ls=3), text(1288, 414, heading, 46, 600, C["ink"], H)),
                      factor_chips(rows, (0, 1) if bohr else (), bohr=bohr)])
NL = "Normal · P50 27"
f = F("8A", "right-shift"); f.add(stage(), axes(), normal_curve(label=NL), shifted(36, label="Right shift · P50 36*"),
      side_card("RIGHT SHIFT", "Lower affinity", ["O2 let go more easily", "P50 rises"]), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()
f = F("8B", "right-factors"); f.add(stage(), axes(), normal_curve(label=NL), shifted(36, label="Right shift · P50 36*"),
      factor_card("RIGHT SHIFT", "Four common factors", RIGHT), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()
f = F("8C", "bohr"); f.add(stage(), axes(), normal_curve(label=NL), shifted(36, label="Right shift · P50 36*"),
      factor_card("RIGHT SHIFT", "Lower affinity", RIGHT, bohr=True), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()
s40n, s40r = S(40, 26.8), S(40, 36)
f = F("8D", "exercising-muscle"); f.add(stage(), axes(), normal_curve(), shifted(36),
      group("Marker/Extra", f'<line x1="{X(40):.1f}" y1="{Y(0)}" x2="{X(40):.1f}" y2="{Y(s40n):.1f}" stroke="{C["ink2"]}" stroke-width="3" stroke-dasharray="6 8"/>',
            f'<line x1="{X(40):.1f}" y1="{Y(s40n):.1f}" x2="{X(40):.1f}" y2="{Y(s40r):.1f}" stroke="{C["coral"]}" stroke-width="12" stroke-linecap="round"/>',
            point(40, s40n, C["teal"], f"{s40n:.0f}%", "left"), point(40, s40r, C["coral"], f"{s40r:.0f}%", "right", dy=10),
            text(X(40)+26, (Y(s40n)+Y(s40r))/2+10, "Extra O2 released", 26, 600, C["coral"])),
      side_card("EXERCISING MUSCLE", "Release where needed", ["Warm, acidic, high CO2", "At PO2 40 mmHg"]), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()

# ---------- Scene 9 ----------
GHOSTR = group("Curves/RightGhost", f'<path d="{curve_path(36)}" fill="none" stroke="{C["mute"]}" stroke-width="4" stroke-dasharray="10 10"/>')
f = F("9A", "left-shift"); f.add(stage(), axes(), GHOSTR, normal_curve(label=False), shifted(20, label="Left shift\nP50 20*", below=False),
      side_card("LEFT SHIFT", "Higher affinity", ["O2 held more tightly", "P50 falls"]), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()
f = F("9B", "left-factors"); f.add(stage(), axes(), normal_curve(), shifted(20, label="Left shift\nP50 20*", below=False),
      factor_card("LEFT SHIFT", "The opposite factors", LEFT), group("Footnote/Text", note(1240, 900, "*Shifted curve illustrative (Hill equation, n = 2.7).")))
f.save()
f = F("9C", "fetal-hb"); f.add(stage(), axes(), normal_curve(), shifted(20, label="Fetal Hb\nsits left", below=False),
      side_card("FETAL HEMOGLOBIN", "HbF: 2α + 2γ", ["Binds 2,3-DPG poorly", "Pulls O2 from the", "mother's blood"]))
f.save()
f = F("9D", "carbon-monoxide"); f.add(stage(), axes(), normal_curve(),
      group("Panel/Card", card(1240, 210, 600, 700), text(1288, 272, "CARBON MONOXIDE", 23, 700, C["ink2"], H, ls=3), text(1288, 334, "Different", 46, 600, C["ink"], H)),
      tetramer(1540, 500, bound=(1, 2), co=0, rings=(), scale=0.55, name="Hb/COTetramer", labels=False),
      group("Panel/Lines", text(1288, 700, "Blocks O2 binding sites → O2 capacity ↓", 24, 500), text(1288, 748, "Remaining sites hold O2 tighter → unloading ↓", 24, 500)),
      group("Footnote/Text", note(1288, 860, "Curve shown is for normal Hb; with CO the"), note(1288, 890, "maximum O2 content also falls.")))
f.save()

# ---------- Scene 10 ----------
def final_graph():
    return [stage(), axes(), normal_curve(), shifted(36, name="Curves/Right"), shifted(20, col=C["coral"], name="Curves/Left").replace('stroke-width="7"', 'stroke-width="5" stroke-dasharray="14 10"', 1)]
def sum_card(y, kicker, heading, line, active):
    fill = C["white"] if active else C["soft"]
    return group(f"Panel/{kicker.title().replace(' ', '')}", card(1240, y, 600, 230, fill, shadow=active),
                 text(1288, y+60, kicker, 23, 700, C["coral"] if active else C["ink2"], H, ls=3), text(1288, y+118, heading, 36, 600, C["ink"] if active else C["ink2"], H), text(1288, y+176, line, 26, 400, C["ink"] if active else C["ink2"]))
f = F("10A", "summary-right"); f.add(*final_graph(), sum_card(220, "RIGHT SHIFT", "Lower affinity, P50 ↑", "More O2 released at the same PO2", True), sum_card(490, "LEFT SHIFT", "Higher affinity, P50 ↓", "O2 held more tightly", False)); f.save()
f = F("10B", "summary-left"); f.add(*final_graph(), sum_card(220, "RIGHT SHIFT", "Lower affinity, P50 ↑", "More O2 released at the same PO2", False), sum_card(490, "LEFT SHIFT", "Higher affinity, P50 ↓", "O2 held more tightly", True)); f.save()
f = F("10C", "right-means-release"); f.add(*final_graph(), sum_card(220, "RIGHT SHIFT", "Lower affinity, P50 ↑", "More O2 released at the same PO2", False), sum_card(490, "LEFT SHIFT", "Higher affinity, P50 ↓", "O2 held more tightly", False),
      group("Takeaway/Text", chip(1240, 760, 600, "Right means release", C["coral"], None, "#FFFFFF", 40, 700, 84)),
      group("Footnote/Text", note(1240, 900, "Total O2 delivery also depends on blood flow,"), note(1240, 930, "Hb concentration and lung loading. Shifted curves illustrative.")))
f.save()
print("done", len(os.listdir(OUT)))
