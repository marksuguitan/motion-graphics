# Style frames for Oxygen Hemoglobin Curve, beat 8C (Bohr effect), three Warm Clinical variants.
import sys, os
OUT = sys.argv[1]
N = 2.7
def S(p, p50): return 0 if p <= 0 else 100 * p**N / (p**N + p50**N)
def L(s): return s.replace("/", "_x2F_")

C = dict(white="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A",
         coral="#F0645A", teal="#2E9C8F", paper="#F3EEE5", papercard="#FBF8F2")
H = "font-family:Manrope"; B = "font-family:Inter"

def curve(x0, y0, w, h, p50, pmax=100):
    pts = []
    for i in range(0, 401):
        p = pmax * i / 400
        pts.append(f"{x0 + w*p/pmax:.1f},{y0 + h - h*S(p,p50)/100:.1f}")
    return "M" + " L".join(pts)

def graph(x0, y0, w, h, grid, axis_col, label_col):
    X = lambda p: x0 + w*p/100
    Y = lambda s: y0 + h - h*s/100
    g = [f'<g id="{L("Graph/Grid")}">']
    for v in range(0, 101, 20):
        g.append(f'<line x1="{X(v):.1f}" y1="{y0}" x2="{X(v):.1f}" y2="{y0+h}" stroke="{grid}" stroke-width="2"/>')
        g.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{x0+w}" y2="{Y(v):.1f}" stroke="{grid}" stroke-width="2"/>')
    g.append('</g>')
    g.append(f'<g id="{L("Graph/Axes")}">')
    g.append(f'<path d="M{x0},{y0} V{y0+h} H{x0+w}" fill="none" stroke="{axis_col}" stroke-width="3" stroke-linecap="round"/>')
    for v in range(0, 101, 20):
        g.append(f'<text x="{X(v):.1f}" y="{y0+h+44}" text-anchor="middle" style="{B};font-size:26px;font-weight:500" fill="{label_col}">{v}</text>')
        g.append(f'<text x="{x0-18}" y="{Y(v)+9:.1f}" text-anchor="end" style="{B};font-size:26px;font-weight:500" fill="{label_col}">{v}</text>')
    g.append(f'<text x="{x0+w/2}" y="{y0+h+98}" text-anchor="middle" style="{B};font-size:30px;font-weight:500" fill="{C["ink"]}">PO<tspan font-size="20" dy="6">2</tspan><tspan dy="-6"> (mmHg)</tspan></text>')
    g.append(f'<text transform="translate({x0-92},{y0+h/2}) rotate(-90)" text-anchor="middle" style="{B};font-size:30px;font-weight:500" fill="{C["ink"]}">Hemoglobin saturation (%)</text>')
    g.append('</g>')
    return "\n".join(g), X, Y

def curves(x0, y0, w, h, X, Y, normal_col, shift_col, faded=False):
    g = [f'<g id="{L("Curves/Normal")}">',
         f'<path d="{curve(x0,y0,w,h,26.8)}" fill="none" stroke="{normal_col}" stroke-width="7" stroke-linecap="round" opacity="{0.55 if faded else 1}"/>',
         f'<circle cx="{X(26.8):.1f}" cy="{Y(50):.1f}" r="9" fill="{normal_col}"/>',
         f'<text x="{X(26.8)-14:.1f}" y="{Y(50)-22:.1f}" text-anchor="end" style="{B};font-size:26px;font-weight:600" fill="{normal_col}">Normal · P<tspan font-size="18" dy="6">50</tspan><tspan dy="-6"> 27</tspan></text>',
         '</g>',
         f'<g id="{L("Curves/RightShift")}">',
         f'<path d="{curve(x0,y0,w,h,36)}" fill="none" stroke="{shift_col}" stroke-width="7" stroke-linecap="round"/>',
         f'<line x1="{X(26.8):.1f}" y1="{Y(50):.1f}" x2="{X(36):.1f}" y2="{Y(50):.1f}" stroke="{shift_col}" stroke-width="3" stroke-dasharray="2 9" stroke-linecap="round"/>',
         f'<circle cx="{X(36):.1f}" cy="{Y(50):.1f}" r="9" fill="{shift_col}"/>',
         f'<text x="{X(36)+18:.1f}" y="{Y(50)+38:.1f}" style="{B};font-size:26px;font-weight:600" fill="{shift_col}">Right shift · P<tspan font-size="18" dy="6">50</tspan><tspan dy="-6"> 36*</tspan></text>',
         '</g>']
    return "\n".join(g)

def factors_card(x, y, w, card_fill, shadow, kicker_col, accent, radius=24, chips=False):
    rows = [("↓", "pH", True), ("↑", "CO<tspan font-size=\"22\" dy=\"7\">2</tspan>", True), ("↑", "2,3-DPG", False), ("↑", "Temperature", False)]
    h = 520
    g = [f'<g id="{L("Factors/Card")}">']
    if shadow:
        g.append(f'<rect x="{x}" y="{y+8}" width="{w}" height="{h}" rx="{radius}" fill="#222222" opacity="0.08" filter="url(#soft)"/>')
    g.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{card_fill}"/>')
    g.append(f'<text x="{x+48}" y="{y+70}" style="{H};font-size:23px;font-weight:700;letter-spacing:3px" fill="{kicker_col}">RIGHT SHIFT</text>')
    g.append(f'<text x="{x+48}" y="{y+132}" style="{H};font-size:50px;font-weight:600" fill="{C["ink"]}">Lower affinity</text>')
    g.append('</g>')
    g.append(f'<g id="{L("Factors/List")}">')
    for i, (arrow, lab, bohr) in enumerate(rows):
        ty = y + 222 + i * 78
        col = C["ink"] if bohr else C["ink2"]
        if chips:
            g.append(f'<rect x="{x+40}" y="{ty-46}" width="{290}" height="62" rx="12" fill="{C["white"]}" stroke="{C["div"]}" stroke-width="2"/>')
        g.append(f'<text x="{x+60}" y="{ty}" style="{B};font-size:32px;font-weight:600" fill="{accent if bohr else col}">{arrow}</text>')
        g.append(f'<text x="{x+100}" y="{ty}" style="{B};font-size:32px;font-weight:{600 if bohr else 400}" fill="{col}">{lab}</text>')
    g.append('</g>')
    # Bohr bracket: the focal element of 8C
    by0, by1 = y + 222 - 34, y + 222 + 78 + 10
    bx = x + 350
    g.append(f'<g id="{L("Factors/Bohr")}">')
    g.append(f'<path d="M{bx},{by0} h18 V{by1} h-18" fill="none" stroke="{accent}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    g.append(f'<rect x="{bx+40}" y="{(by0+by1)/2-31}" width="190" height="62" rx="12" fill="{accent}"/>')
    g.append(f'<text x="{bx+135}" y="{(by0+by1)/2+10}" text-anchor="middle" style="{H};font-size:27px;font-weight:700" fill="#FFFFFF">Bohr effect</text>')
    g.append('</g>')
    return "\n".join(g)

def frame(name, bg, stage=None, grid=C["div"], card_fill=C["soft"], shadow=False, chips=False, note=""):
    defs = '<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="12"/></filter></defs>'
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">', defs,
             f'<g id="{L("Background/Fill")}"><rect width="1920" height="1080" fill="{bg}"/></g>']
    if stage:
        parts.append(f'<g id="{L("Background/Stage")}"><rect x="96" y="150" width="1080" height="840" rx="24" fill="#222222" opacity="0.08" filter="url(#soft)" transform="translate(0,8)"/><rect x="96" y="150" width="1080" height="840" rx="24" fill="{stage}"/></g>')
    parts.append(f'<g id="{L("Header/Kicker")}"><text x="120" y="96" style="{H};font-size:23px;font-weight:700;letter-spacing:3px" fill="{C["ink2"]}">THE OXYHEMOGLOBIN DISSOCIATION CURVE</text></g>')
    x0, y0, w, h = 300, 210, 820, 600
    gtxt, X, Y = graph(x0, y0, w, h, grid, C["ink"], C["ink2"])
    parts.append(gtxt)
    parts.append(curves(x0, y0, w, h, X, Y, C["teal"], C["coral"]))
    parts.append(factors_card(1240, 290, 600, card_fill, shadow, C["ink2"], C["coral"], chips=chips))
    parts.append(f'<g id="{L("Footnote/Text")}"><text x="1240" y="900" style="{B};font-size:22px" fill="{C["ink2"]}">*Shifted curve illustrative (Hill equation, n = 2.7).</text></g>')
    parts.append(f'<g id="{L("Meta/BeatID")}"><text x="1880" y="1052" text-anchor="end" style="{B};font-size:22px;font-weight:500" fill="{C["ink2"]}" opacity="0.6">8C · {note}</text></g>')
    parts.append('</svg>')
    open(os.path.join(OUT, name), "w").write("\n".join(parts))

frame("style_A_warm-clinical.svg", C["white"], note="Style A")
frame("style_B_warm-ground.svg", C["paper"], grid="#E3DBCF", card_fill=C["papercard"], note="Style B")
frame("style_C_card-stage.svg", C["soft"], stage=C["white"], card_fill=C["white"], shadow=True, chips=True, note="Style C")
print("ok")
