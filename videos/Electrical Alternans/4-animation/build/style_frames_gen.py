"""Style frames for Pulsus Paradoxus, beat 3C end state (tamponade: septum bowed into LV, gauge past threshold).
Heart modeled on Mark's short-axis cross-section (assets/reference/short_axis_reference.jpg):
thick LV ring with two papillary muscles, thin-walled RV crescent wrapping the septal side (upper-left),
epicardial fat band with coronary vessels. Built in polar form so the septal bow is one parameter.
Three looks: A line, B solid, C spotlight. Layer groups match the motion notes (Group/Sublayer)."""
import math, sys, os

W, H = 1920, 1080
BG, FG, ACC, GREY = "#151515", "#F2F2F2", "#FF4057", "#6E6E6E"
FONT = "Helvetica, 'Helvetica Neue', Arial, 'Liberation Sans', sans-serif"
N = 360  # samples around the heart, one per degree


def g(theta, mu, width):
    """Wrapped gaussian bump on angle (degrees)."""
    d = (theta - mu + 180) % 360 - 180
    return math.exp(-0.5 * (d / width) ** 2)


def window(theta, a, b):
    """Smooth 0..1 window between angles a and b (degrees, a<b, b may exceed 360)."""
    t = theta if theta >= a else theta + 360
    if not (a <= t <= b):
        return 0.0
    return math.sin(math.pi * (t - a) / (b - a)) ** 2


# Angles: 0 = right (3 o'clock), 90 = down, 180 = left, 270 = up (SVG y-down).
RV_A, RV_B = 130, 290          # RV wraps from ~8 o'clock round the left to ~1 o'clock
SEPT_MID = 205                 # centre of the septum (faces upper-left, toward the RV)


def radii(bow):
    """bow 0 = normal, 1 = tamponade inspiration (septum pushed into LV).
    Per angle: (theta, LV cavity r, heart outline r, RV side of septum r, RV free-wall inner r)."""
    out = []
    for i in range(N):
        th = float(i)
        shift = bow * 46 * g(th, SEPT_MID, 26)           # whole septum moves into the LV
        rc = 112 - 40 * g(th, 8, 12) - 36 * g(th, 128, 12) - shift   # LV cavity with papillary muscles
        lv_out = 236
        w = window(th, RV_A, RV_B)
        bulge = 96 * w * (1 + 0.12 * bow)
        r_out = lv_out + bulge                            # heart outline incl. RV free wall
        r_sept = lv_out - shift if w > 0 else lv_out      # RV side of septum = LV epicardium, shifted
        r_rvin = r_out - 22 if w > 0 else 0               # RV free wall inner edge (none outside the RV)
        out.append((th, rc, r_out, r_sept, r_rvin))
    return out


def heart(cx, cy, s, bow=1.0, fluid=58):
    R = radii(bow)
    P = lambda th, r: f"{cx + r*s*math.cos(math.radians(th)):.1f},{cy + r*s*math.sin(math.radians(th)):.1f}"
    ring = lambda pts: "M" + " L".join(P(th, r) for th, r in pts) + " Z"
    lv = ring([(t[0], t[1]) for t in R])
    outline = ring([(t[0], t[2]) for t in R])
    fat = ring([(t[0], t[2] + 12) for t in R])
    sac = ring([(t[0], t[2] + 12 + fluid) for t in R])
    order = lambda th: (th - RV_A) % 360
    seg = sorted([(th, rs, ri) for th, rc, ro, rs, ri in R if ri - rs > 6], key=lambda t: order(t[0]))
    rv = "M" + " L".join(P(th, ri) for th, rs, ri in seg) + " L" + " L".join(P(th, rs) for th, rs, ri in reversed(seg)) + " Z"
    lo, hi = seg[0][0], seg[-1][0]
    span = (hi - lo) % 360
    sep_pts = sorted([(t[0], t[1]) for t in R if (t[0] - lo) % 360 <= span], key=lambda t: (t[0] - lo) % 360)
    sept_line = "M" + " L".join(P(th, rc) for th, rc in sep_pts)
    rs_map = {th: rs for th, rs, ri in seg}
    def taper(th):  # lens-shaped septum: full thickness in the middle, pointed where the RV cavity ends
        d = min((th - lo) % 360, (hi - th) % 360)
        t = min(1.0, d / 28.0)
        return t * t * (3 - 2 * t)
    sept_wall = ("M" + " L".join(P(th, rc) for th, rc in sep_pts) + " L" +
                 " L".join(P(th, rc + (rs_map.get(th, rc) - rc) * taper(th)) for th, rc in reversed(sep_pts)) + " Z")
    rv_wall = "M" + " L".join(P(t[0], t[2]) for t in sorted(R, key=lambda t: order(t[0])) if order(t[0]) <= RV_B - RV_A)
    rof = {int(t[0]): t for t in R}
    xy = lambda th, r: (cx + r * s * math.cos(math.radians(th)), cy + r * s * math.sin(math.radians(th)))
    vessels = [xy(292, rof[292][2] + 5), xy(118, rof[118][2] + 4), xy(127, rof[127][2] + 5)]
    anchors = dict(septum=xy(SEPT_MID, rof[SEPT_MID][1]), lv=xy(0, 0), rv=xy(205, (rof[205][3] + rof[205][4]) / 2),
                   rv_wall=xy(168, rof[168][2]), fluid=xy(40, rof[40][2] + 12 + fluid / 2))
    return dict(lv=lv, outline=outline, fat=fat, sac=sac, rv=rv, sept_line=sept_line, sept_wall=sept_wall,
                rv_wall=rv_wall, vessels=vessels, anchors=anchors)


def gauge(cx, cy, r, mmhg_drop, style):
    """Dial reading the inspiratory systolic drop, 0-30 mmHg over 240 deg; threshold arc from 10."""
    ang = lambda v: math.radians(150 + v / 30 * 240)
    out = ['<g id="Gauge">',
           f'<circle id="Face" cx="{cx}" cy="{cy}" r="{r}" fill="{"none" if style == "A" else "#1E1F20"}" stroke="{GREY}" stroke-width="2"/>']
    ticks = []
    for v in range(0, 31):
        a = ang(v); major = v % 5 == 0; r1 = r - (26 if major else 14)
        ticks.append(f'<line x1="{cx + (r-6)*math.cos(a):.1f}" y1="{cy + (r-6)*math.sin(a):.1f}" x2="{cx + r1*math.cos(a):.1f}" '
                     f'y2="{cy + r1*math.sin(a):.1f}" stroke="{FG if major else GREY}" stroke-width="{3 if major else 1.5}"/>')
    out.append('<g id="Major_ticks">' + "".join(ticks) + "</g>")
    out.append('<g id="Dial_numbers">' + "".join(
        f'<text x="{cx + (r-52)*math.cos(ang(v)):.1f}" y="{cy + (r-52)*math.sin(ang(v))+9:.1f}" text-anchor="middle" '
        f'font-size="26" fill="{GREY}">{v}</text>' for v in range(0, 31, 10)) + "</g>")
    t0, t1, ra = ang(10), ang(30), r + 14
    out.append(f'<path id="Threshold_line" d="M{cx + ra*math.cos(t0):.1f},{cy + ra*math.sin(t0):.1f} A{ra},{ra} 0 0 1 '
               f'{cx + ra*math.cos(t1):.1f},{cy + ra*math.sin(t1):.1f}" fill="none" stroke="{ACC}" stroke-width="6" stroke-linecap="round"/>')
    a = ang(mmhg_drop)
    out.append(f'<line id="Needle" x1="{cx}" y1="{cy}" x2="{cx + (r-34)*math.cos(a):.1f}" y2="{cy + (r-34)*math.sin(a):.1f}" '
               f'stroke="{ACC}" stroke-width="6" stroke-linecap="round"/>')
    out.append(f'<circle id="Hub" cx="{cx}" cy="{cy}" r="12" fill="{FG}"/>')
    out.append(f'<text id="Readout" x="{cx}" y="{cy + r*0.62:.1f}" text-anchor="middle" font-size="40" font-weight="700" fill="{FG}">'
               f'{"−" if mmhg_drop else ""}{mmhg_drop} <tspan font-size="22" font-weight="400" fill="{GREY}">mmHg</tspan></text>')
    out.append(f'<text id="Caption" x="{cx}" y="{cy + r + 58}" text-anchor="middle" font-size="20" letter-spacing="3" '
               f'fill="{GREY}">INSPIRATORY SYSTOLIC DROP</text>'
               f'<text id="Caption_note" x="{cx}" y="{cy + r + 86}" text-anchor="middle" font-size="16" letter-spacing="2" fill="{GREY}">SCHEMATIC</text></g>')
    return "\n".join(out)


def label(x, y, text, tx, ty, style, accent=False):
    col = ACC if accent else FG
    tx, ty = int(tx), int(ty)
    if style == "B":
        w = len(text) * 13.5 + 36
        lx = x if tx < x else x + w
        return (f'<line x1="{lx:.0f}" y1="{y-9}" x2="{tx}" y2="{ty}" stroke="{GREY}" stroke-width="1.5"/>'
                f'<circle cx="{tx}" cy="{ty}" r="5" fill="{FG}"/>'
                f'<rect x="{x}" y="{y-32}" width="{w:.0f}" height="46" rx="23" fill="#232425" stroke="{col if accent else GREY}" stroke-width="1.5"/>'
                f'<text x="{x + 18}" y="{y}" font-size="24" fill="{col}">{text}</text>')
    lx = x + 12 + len(text) * 13 + 10 if tx > x else x
    return (f'<line x1="{lx}" y1="{y-9}" x2="{tx}" y2="{ty}" stroke="{GREY}" stroke-width="1.5"/>'
            f'<circle cx="{tx}" cy="{ty}" r="5" fill="{FG}"/>'
            f'<text x="{x + 12}" y="{y}" font-size="26" fill="{col}">{text}</text>')


def frame(style):
    if style == "C":
        cx, cy, s, (gx, gy, gr) = 700, 560, 1.32, (1600, 300, 130)
    elif style == "B":
        cx, cy, s, (gx, gy, gr) = 800, 650, 0.98, (1560, 330, 170)
    else:
        cx, cy, s, (gx, gy, gr) = 780, 560, 1.08, (1560, 330, 170)
    h = heart(cx, cy, s)
    A = h["anchors"]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">',
         f'<rect id="Background" width="{W}" height="{H}" fill="{BG}"/>']
    if style == "C":
        grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W, 80))
        grid += "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 80))
        o.append(f'<g id="Grid" stroke="#1F2021" stroke-width="1">{grid}</g>')

    # look: fluid, sac, fat, myocardium, cavity
    if style == "A":
        fl, flo, sac, fat, fat_st, myo, myo_st, cav, cav_st = "#F2F2F2", 0.07, FG, "none", "#5A5550", BG, FG, BG, FG
    elif style == "B":
        fl, flo, sac, fat, fat_st, myo, myo_st, cav, cav_st = "#9FB3C8", 0.20, "#C9D3DD", "#4A4640", "none", "#3C3D40", "none", "#161718", "none"
    else:
        fl, flo, sac, fat, fat_st, myo, myo_st, cav, cav_st = "#9FB3C8", 0.08, "#4A4B4C", "#2E2C29", "none", "#26272A", "#4A4B4C", "#141414", "#4A4B4C"

    o.append(f'<g id="Pericardium"><path id="Fluid" d="{h["sac"]}" fill="{fl}" fill-opacity="{flo}"/>'
             f'<path id="Sac" d="{h["sac"]}" fill="none" stroke="{sac}" stroke-width="{4 if style == "C" else 5}" stroke-linejoin="round"/></g>')
    vessels = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{7*s:.1f}" fill="{BG}" stroke="{GREY}" stroke-width="2"/>' for x, y in h["vessels"])
    lv_fill, lv_op, lv_st, lv_w = (ACC, 0.14, ACC, 3) if style == "C" else (cav, 1, cav_st, 2)
    o.append('<g id="Heart">'
             f'<path id="Epicardial_fat" d="{h["fat"]}" fill="{fat}" stroke="{fat_st}" stroke-width="1.5" stroke-dasharray="{"4 6" if style == "A" else "none"}"/>'
             f'<path id="Myocardium" d="{h["outline"]}" fill="{myo}" stroke="{myo_st}" stroke-width="2" stroke-linejoin="round"/>'
             f'<path id="RV" d="{h["rv"]}" fill="{cav}" stroke="{cav_st}" stroke-width="2" stroke-linejoin="round"/>'
             f'<path id="LV" d="{h["lv"]}" fill="{lv_fill}" fill-opacity="{lv_op}" stroke="{lv_st}" stroke-width="{lv_w}" stroke-linejoin="round"/>')
    if style == "B":
        o.append(f'<path id="Septum" d="{h["sept_wall"]}" fill="{ACC}"/>')
    elif style == "C":
        o.append(f'<path id="Septum_glow" d="{h["sept_line"]}" fill="none" stroke="{ACC}" stroke-opacity="0.28" stroke-width="28" stroke-linecap="round"/>'
                 f'<path id="Septum" d="{h["sept_line"]}" fill="none" stroke="{ACC}" stroke-width="8" stroke-linecap="round"/>')
    else:
        o.append(f'<path id="Septum" d="{h["sept_line"]}" fill="none" stroke="{ACC}" stroke-width="7" stroke-linecap="round"/>')
    o.append(f'<path id="RV_free_wall" d="{h["rv_wall"]}" fill="none" stroke="none"/><g id="Coronaries">{vessels}</g></g>')

    tag = GREY if style != "C" else "#8A8B8C"
    (lvx, lvy), (rvx, rvy) = A["lv"], A["rv"]
    o.append(f'<g id="Chamber_tags" font-size="30" font-weight="700" fill="{tag}">'
             f'<text x="{rvx:.0f}" y="{rvy + 10:.0f}" text-anchor="middle">RV</text>'
             f'<text x="{lvx:.0f}" y="{lvy + 10:.0f}" text-anchor="middle" fill="{ACC if style == "C" else tag}">LV</text></g>')

    (sx, sy), (wx, wy), (fx, fy) = A["septum"], A["rv_wall"], A["fluid"]
    if style == "C":
        lab = (label(1180, 640, "septum bows left", sx, sy, style, True) + label(1180, 700, "LV filling ↓↓", lvx, lvy + 40, style) +
               label(80, 1010, "RV free wall pinned", wx, wy, style) + label(1180, 760, "pericardial effusion", fx, fy, style))
    else:
        lab = (label(1180, 640, "septum bows left", sx, sy, style, True) + label(1180, 710, "LV filling ↓↓", lvx, lvy + 40, style) +
               label(110, 1000, "RV free wall pinned", wx, wy, style) + label(1180, 1000, "pericardial effusion", fx, fy, style))
    o.append(f'<g id="Label">{lab}</g>')
    o.append(gauge(gx, gy, gr, 24, style))

    if style == "B":
        o.append(f'<g id="Breath"><rect id="Chip" x="80" y="70" width="128" height="52" rx="26" fill="{ACC}"/>'
                 f'<text x="144" y="106" text-anchor="middle" font-size="26" font-weight="700" fill="{BG}">IN</text></g>')
        o.append(f'<g id="Title"><text id="Mechanism" x="80" y="230" font-size="64" font-weight="700" fill="{FG}">'
                 f'Ventricular <tspan fill="{ACC}">interdependence</tspan></text></g>')
    else:
        o.append(f'<g id="Breath"><rect id="Chip" x="80" y="70" width="128" height="52" rx="6" fill="none" stroke="{ACC}" stroke-width="2"/>'
                 f'<text x="144" y="106" text-anchor="middle" font-size="26" font-weight="700" letter-spacing="4" fill="{ACC}">IN</text></g>')
        if style == "A":
            o.append(f'<g id="Title"><text id="Mechanism" x="1180" y="840" font-size="52" font-weight="700" fill="{ACC}" letter-spacing="1">VENTRICULAR</text>'
                     f'<text x="1180" y="900" font-size="52" font-weight="700" fill="{ACC}" letter-spacing="1">INTERDEPENDENCE</text></g>')
        else:
            o.append(f'<g id="Title"><text id="Mechanism" x="1180" y="900" font-size="44" font-weight="300" fill="{FG}" letter-spacing="2">VENTRICULAR</text>'
                     f'<text x="1180" y="955" font-size="44" font-weight="700" fill="{ACC}" letter-spacing="2">INTERDEPENDENCE</text></g>')
    o.append(f'<text id="Beat_ID" x="{W-40}" y="{H-32}" text-anchor="end" font-size="18" fill="{GREY}">3C · style {style}</text></svg>')
    return "\n".join(o)


if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k, n in {"A": "style_A_line.svg", "B": "style_B_solid.svg", "C": "style_C_spotlight.svg"}.items():
        open(os.path.join(out, n), "w").write(frame(k)); print(n)
