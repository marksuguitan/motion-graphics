"""Rough key frames for Electrical Alternans, Pulsus Paradoxus style C (spotlight).
One SVG per beat, 1920x1080, drawn at the END state of that beat's motion notes.
Layer groups use the motion-note names (Group/Sublayer -> nested <g id>).
ECG traces are drawn from a beat model patterned on Mark's two reference ECGs
(assets/reference/IMG_9236.png, IMG_9238.jpeg): sinus tachycardia, every other QRS shorter.
Heart model and drop gauge come from style_frames_gen.py (Pulsus Paradoxus).
Usage: python3 keyframes_gen.py <out_dir>"""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from style_frames_gen import heart, radii, gauge, W, H, BG, FG, ACC, GREY, FONT

DIM = "#8A8B8C"
MYO, CAV, LINE = "#A6979A", "#141414", "#4A4B4C"   # MYO: grey-pink myocardium (Mark 2026-10-23)
MYO_LINE, FAT, FIBRE = "#7D6F72", "#958689", "#7A6B6E"
EFF = "#5E9BD6"          # effusion blue, as in Pulsus Paradoxus
PAPER, PAPER_LINE = "#18191A", "#242628"
CARD = "#1C1D1E"
RR = 0.52                # s, ~115 bpm sinus tachycardia (schematic)
ALT = 0.55               # short-beat QRS amplitude as a fraction of the tall beat


# ---------------- primitives ----------------
def svg(beat, body):
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W, 80))
    grid += "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 80))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect id="Background" width="{W}" height="{H}" fill="{BG}"/><g id="Grid" stroke="#1F2021" stroke-width="1">{grid}</g>'
            f'{body}<text id="Beat_ID" x="{W-40}" y="{H-32}" text-anchor="end" font-size="18" fill="{GREY}">{beat}</text></svg>')


def G(gid, body, extra=""):
    return f'<g id="{gid}"{extra}>{body}</g>'


def T(x, y, s, size=26, fill=FG, weight=400, anchor="start", ls=0, gid=None, extra=""):
    i = f' id="{gid}"' if gid else ""
    return (f'<text{i} x="{x:.0f}" y="{y:.0f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{ls}"{extra}>{s}</text>')


def title_pair(light, bold, x, y, size=44, gid="Title", anchor="start"):
    return G(gid, T(x, y, light, size, FG, 300, anchor, 2) + T(x, y + size * 1.25, bold, size, ACC, 700, anchor, 2))


def card(gid, x, y, w, h, lines, accent_first=True, opacity=1.0, size0=40, size1=30):
    t = "".join(T(x + 32, y + 64 + i * 58, s, size0 if i == 0 else size1, ACC if (i == 0 and accent_first) else FG,
                  700 if i == 0 else 400) for i, s in enumerate(lines))
    return G(gid, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>{t}',
             f' opacity="{opacity}"')


def arrow(x1, y1, x2, y2, col=FG, w=3, head=14):
    a = math.atan2(y2 - y1, x2 - x1)
    p1 = (x2 - head * math.cos(a - 0.45), y2 - head * math.sin(a - 0.45))
    p2 = (x2 - head * math.cos(a + 0.45), y2 - head * math.sin(a + 0.45))
    return (f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'
            f'<path d="M{p1[0]:.1f} {p1[1]:.1f} L{x2:.1f} {y2:.1f} L{p2[0]:.1f} {p2[1]:.1f}" fill="none" stroke="{col}" '
            f'stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"/>')


def tick(x, y, col, h=34, w=6):
    return f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x:.0f}" y2="{y-h:.0f}" stroke="{col}" stroke-width="{w}" stroke-linecap="round"/>'


# ---------------- ECG model ----------------
# per lead: (P, Q, R, S, T) amplitudes as fractions of the strip's amp; R carries the alternation
LEADS = {
    "I": (0.08, -0.04, 0.40, -0.10, 0.12), "II": (0.12, -0.05, 0.55, -0.12, 0.16), "III": (0.05, 0, 0.22, -0.10, 0.05),
    "aVR": (-0.09, 0.04, -0.42, 0.08, -0.13), "aVL": (0.04, 0, 0.14, -0.06, 0.04), "aVF": (0.08, -0.03, 0.38, -0.10, 0.10),
    "V1": (0.07, 0, 0.14, -0.85, 0.04), "V2": (0.08, 0, 0.24, -1.05, 0.14), "V3": (0.08, 0, 0.60, -0.62, 0.18),
    "V4": (0.10, -0.05, 1.00, -0.30, 0.22), "V5": (0.10, -0.05, 1.00, -0.16, 0.20), "V6": (0.10, -0.04, 0.80, -0.10, 0.18),
}
R_T = 0.235  # s from beat start to R peak


def gs(t, mu, w):
    return math.exp(-0.5 * ((t - mu) / w) ** 2)


def wave(tt, lead, f, total):
    p, q, r, s, t = lead
    fp = f if total else 1.0
    return (fp * p * gs(tt, 0.11, 0.022) + f * (q * gs(tt, 0.212, 0.006) + r * gs(tt, R_T, 0.0085) + s * gs(tt, 0.258, 0.008))
            + fp * t * gs(tt, 0.40, 0.042))


def ecg(x0, y0, w, sec, lead="V5", amp=80, alt=ALT, total=False, phase=0.0, first_tall=True, rr=RR, rr_fn=None, amp_fn=None):
    """Returns (path d, beats) where beats = [(x of R peak, y of R peak, tall?)]. rr_fn(k)->beat start time overrides rr."""
    L = LEADS[lead] if isinstance(lead, str) else lead
    pps = w / sec
    starts = [rr_fn(k) for k in range(-2, 60)] if rr_fn else [k * rr for k in range(-2, 60)]
    pts, beats = [], []
    for i in range(int(w / 2) + 1):
        t = i * 2 / pps + phase
        v = 0.0
        for k, st in enumerate(starts):
            tt = t - st
            if -0.3 < tt < 0.9:
                kk = k - 2
                tall = (kk % 2 == 0) == first_tall
                f = amp_fn(kk) if amp_fn else (1.0 if tall else alt)
                v += wave(tt, L, f, total)
        pts.append((x0 + i * 2, y0 - v * amp))
    for k, st in enumerate(starts):
        kk = k - 2
        x = x0 + (st + R_T - phase) * pps
        if x0 + 4 <= x <= x0 + w - 4:
            tall = (kk % 2 == 0) == first_tall
            f = amp_fn(kk) if amp_fn else (1.0 if tall else alt)
            beats.append((x, y0 - L[2] * f * amp, tall))
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts), beats


def paper(x, y, w, h, step=35, gid="Paper"):
    lines = "".join(f'<line x1="{xx:.1f}" y1="{y}" x2="{xx:.1f}" y2="{y+h}"/>' for xx in [x + i * step for i in range(int(w / step) + 1)])
    lines += "".join(f'<line x1="{x}" y1="{yy:.1f}" x2="{x+w}" y2="{yy:.1f}"/>' for yy in [y + i * step for i in range(int(h / step) + 1)])
    return G(gid, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{PAPER}"/><g stroke="{PAPER_LINE}" stroke-width="1">{lines}</g>')


def trace(d, col=FG, wdt=3, gid="Trace", extra=""):
    return f'<path id="{gid}" d="{d}" fill="none" stroke="{col}" stroke-width="{wdt}" stroke-linejoin="round" stroke-linecap="round"{extra}/>'


def strip_group(x, y, w, sec, lead="V5", amp=110, marks=True, gid="Strip", mark_h=40, opacity=1.0, extra="", total=False):
    d, beats = ecg(x, y, w, sec, lead, amp, total=total)
    body = paper(x - 20, y - amp * 1.45, w + 40, amp * 2.1) + trace(d)
    if marks:
        top = min(b[1] for b in beats) - 26
        tall = "".join(tick(bx, top, ACC) for bx, by, t in beats if t)
        short = "".join(tick(bx, top, GREY) for bx, by, t in beats if not t)
        body += G("Marks_tall", tall) + G("Marks_short", short)
    return G(gid, body, f' opacity="{opacity}"{extra}'), beats


def twelve_lead(x, y, w, h, amp=44, dim_except=None, gid="ECG"):
    """3x4 grid + lead II rhythm strip, 2.5 s per column. Returns (svg, info)."""
    rows = [["I", "aVR", "V1", "V4"], ["II", "aVL", "V2", "V5"], ["III", "aVF", "V3", "V6"]]
    rh = h / 4
    cw = w / 4
    out = [paper(x, y, w, h, step=cw / 12.5)]
    info = {}
    leads_svg = []
    for r, row in enumerate(rows):
        for c, ld in enumerate(row):
            cx0 = x + c * cw + 6
            cy0 = y + rh * (r + 0.62)
            d, beats = ecg(cx0, cy0, cw - 12, 2.5, ld, amp, phase=c * 2.5)
            op = 1.0 if (dim_except is None or ld in dim_except) else 0.4
            leads_svg.append(G(f"Lead_{ld}", trace(d, wdt=2, gid=f"Trace_{ld}") + T(cx0 + 4, y + rh * r + 28, ld, 20, DIM, 700), f' opacity="{op}"'))
            info[ld] = (x + c * cw, y + rh * r, cw, rh)
            if c:
                out.append(f'<line x1="{x + c*cw:.0f}" y1="{y + rh*r + 20:.0f}" x2="{x + c*cw:.0f}" y2="{y + rh*(r+1) - 12:.0f}" stroke="{DIM}" stroke-width="2"/>')
    d, beats = ecg(x + 6, y + rh * 3.62, w - 12, 10, "II", amp)
    op = 1.0 if (dim_except is None or "Strip" in dim_except) else 0.4
    leads_svg.append(G("Lead_II_strip", trace(d, wdt=2, gid="Trace_strip") + T(x + 10, y + rh * 3 + 28, "II", 20, DIM, 700), f' opacity="{op}"'))
    info["Strip"] = (x, y + rh * 3, w, rh)
    info["strip_beats"] = beats
    out.append(G("Leads", "".join(leads_svg)))
    return G(gid, "".join(out)), info


# ---------------- heart in its sac (style C), swinging ----------------
def striations(cx, cy, s):
    """Faint muscle fibres: broken arcs that follow the wall, through the LV wall and the RV free wall."""
    R = radii(0.0)
    fr = (0.18, 0.34, 0.5, 0.66, 0.82) if s >= 0.5 else (0.35, 0.7)
    P = lambda th, r: f"{cx + r*s*math.cos(math.radians(th)):.1f} {cy + r*s*math.sin(math.radians(th)):.1f}"
    paths = []
    for i, f in enumerate(fr):                     # LV wall, septum included: cavity edge -> LV epicardium (236)
        paths.append((P(R[0][0], R[0][1] + (236 - R[0][1]) * f) + "".join(
            f" L{P(t[0], t[1] + (236 - t[1]) * f)}" for t in R[1:] + R[:1]), i))
    for j, f in enumerate((0.33, 0.67) if s >= 0.5 else (0.5,)):   # RV free wall: inner edge -> outline
        seg = [t for t in R if t[4] > 0 and t[2] - t[4] > 6]
        seg.sort(key=lambda t: (t[0] - 130) % 360)
        paths.append(("M" + P(seg[0][0], seg[0][4] + (seg[0][2] - seg[0][4]) * f)[0:] + "".join(
            f" L{P(t[0], t[4] + (t[2] - t[4]) * f)}" for t in seg[1:]), j + 7))
    dash = ("22 9 12 7", "15 8 26 10", "30 11 9 8", "12 6 20 9", "26 10 14 7")
    w = max(0.8, 1.6 * s)
    out = "".join(f'<path d="{"M" + d if not d.startswith("M") else d}" stroke-dasharray="{dash[k % 5]}" stroke-dashoffset="{k * 13}"/>' for d, k in paths)
    return f'<g id="Myocardium_striations" fill="none" stroke="{FIBRE}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-opacity="0.28">{out}</g>'


def heart_in_sac(cx, cy, s, fluid=110, angle=0.0, ghost=None, pivot_dy=-300, show_fluid=True, sac_fluid=None, gid_prefix=""):
    """Sac is fixed; the heart rotates by `angle` about a pivot above it (great vessels) -> pendulum swing."""
    sf = fluid if sac_fluid is None else sac_fluid
    h0 = heart(cx, cy, s, bow=0.0, fluid=sf)
    px, py = cx, cy + pivot_dy * s
    o = []
    peri = [f'<path id="Fluid" d="{h0["sac"]}" fill="{EFF}" fill-opacity="{0.30 if show_fluid else 0}"/>',
            f'<path id="Sac" d="{h0["sac"]}" fill="none" stroke="{LINE}" stroke-width="3" stroke-linejoin="round"/>']
    o.append(G("Sac", "".join(peri)))

    def body(a, op, gid):
        h = heart(cx, cy, s, bow=0.0, fluid=sf)
        A = h["anchors"]
        v = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{6*s:.1f}" fill="#3A2224" stroke="{GREY}" stroke-width="2"/>' for x, y in h["vessels"])
        (lx, ly), (rx, ry) = A["lv"], A["rv"]
        tag = max(18, int(30 * s))
        return G(gid, f'<path id="Epicardial_fat" d="{h["fat"]}" fill="{FAT}"/>'
                      f'<path id="Myocardium" d="{h["outline"]}" fill="{MYO}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      + striations(cx, cy, s) +
                      f'<path id="RV" d="{h["rv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      f'<path id="LV" d="{h["lv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2"/>'
                      f'<path id="Epicardium_line" d="{h["fat"]}" fill="none" stroke="{ACC}" stroke-width="3.5" stroke-opacity="0.95"/>'
                      f'<g id="Chamber_tags" font-size="{tag}" font-weight="700" fill="{DIM}">'
                      f'<text x="{rx:.0f}" y="{ry + tag/3:.0f}" text-anchor="middle">RV</text>'
                      f'<text x="{lx:.0f}" y="{ly + tag/3:.0f}" text-anchor="middle">LV</text></g>',
                 f' transform="rotate({a:.1f} {px:.0f} {py:.0f})" opacity="{op}"')
    if ghost is not None:
        o.append(body(ghost, 0.22, "Heart_ghost"))
    o.append(body(angle, 1.0, "Heart"))
    return "".join(o), (px, py), h0


def rot(x, y, a, px, py):
    r = math.radians(a)
    return (px + (x - px) * math.cos(r) - (y - py) * math.sin(r), py + (x - px) * math.sin(r) + (y - py) * math.cos(r))


CW_R, CW_A0, CW_A1, EL_A = 560, -80, -12, -42      # chest wall arc around the heart (px, degrees); electrode angle


def chest_wall(cx, cy, s=1.0):
    """Arc of chest wall above-right of the heart with the V5 electrode pad on it. Returns (svg, electrode xy)."""
    P = lambda a, r=CW_R: (cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
    (x0, y0), (x1, y1) = P(CW_A0), P(CW_A1)
    wall = (f'<path id="Wall" d="M{x0:.0f} {y0:.0f} A{CW_R} {CW_R} 0 0 1 {x1:.0f} {y1:.0f}" fill="none" stroke="{DIM}" stroke-width="10" stroke-linecap="round" stroke-opacity="0.35"/>'
            f'<path d="M{x0:.0f} {y0:.0f} A{CW_R} {CW_R} 0 0 1 {x1:.0f} {y1:.0f}" fill="none" stroke="{DIM}" stroke-width="2" stroke-linecap="round"/>')
    ex, ey = P(EL_A, CW_R + 18)
    pad = (f'<g id="Electrode" transform="rotate({EL_A + 90} {ex:.0f} {ey:.0f})">'
           f'<rect x="{ex - 34:.0f}" y="{ey - 18:.0f}" width="68" height="36" rx="10" fill="{CARD}" stroke="{FG}" stroke-width="2.5"/>'
           f'<circle cx="{ex:.0f}" cy="{ey:.0f}" r="8" fill="{FG}"/></g>')
    lab = G("Electrode_label", T(ex + 56, ey + 4, "V5 electrode", 26, FG, 700) + T(ex + 56, ey + 36, "on the chest wall", 22, DIM))
    tx, ty = P(CW_A0 + 6, CW_R - 30)
    wl = T(tx, ty, "chest wall", 20, DIM, 400, "end")
    return G("Chest_wall", wall + wl) + pad + lab, P(EL_A, CW_R - 6)


def electrode(x, y, label="V5"):
    return G("Electrode", f'<circle cx="{x}" cy="{y}" r="26" fill="{CARD}" stroke="{FG}" stroke-width="3"/>'
                          f'<line x1="{x-10}" y1="{y}" x2="{x+10}" y2="{y}" stroke="{FG}" stroke-width="3"/>'
                          f'<line x1="{x}" y1="{y-10}" x2="{x}" y2="{y+10}" stroke="{FG}" stroke-width="3"/>'
                          + T(x, y - 42, f"electrode · {label}", 22, DIM, 400, "middle", 1))


def mini_heart(cx, cy, s=0.32, angle=10, gid="Heart_mini"):
    body, _, _ = heart_in_sac(cx, cy, s, fluid=110, angle=angle)
    return G(gid, body)


# ---------------- patient ----------------
SIL_PATH = "M71 1000 L65 1000 L59 996 L48 985 L41 973 L27 960 L26 956 L27 945 L30 937 L29 922 L32 906 L32 890 L19 806 L18 785 L23 747 L17 717 L17 644 L6 594 L4 532 L2 529 L-3 530 L-5 532 L-4 567 L-16 648 L-17 679 L-27 722 L-25 754 L-27 807 L-32 854 L-37 884 L-37 900 L-34 919 L-36 943 L-34 950 L-35 958 L-47 971 L-54 987 L-67 998 L-74 998 L-82 995 L-93 995 L-103 993 L-109 990 L-112 983 L-112 977 L-108 970 L-99 959 L-83 945 L-73 927 L-73 906 L-88 814 L-90 779 L-89 748 L-84 721 L-86 700 L-85 673 L-96 623 L-104 569 L-103 509 L-96 462 L-81 404 L-79 378 L-78 358 L-81 337 L-88 314 L-90 312 L-93 314 L-98 332 L-96 354 L-99 391 L-117 445 L-126 466 L-133 491 L-133 495 L-123 507 L-114 522 L-109 540 L-109 554 L-112 560 L-118 560 L-121 554 L-122 544 L-125 545 L-129 561 L-130 588 L-132 594 L-138 597 L-142 603 L-145 603 L-149 597 L-154 595 L-156 589 L-162 582 L-165 549 L-163 501 L-164 450 L-163 424 L-152 364 L-142 338 L-138 320 L-137 236 L-132 203 L-126 190 L-112 176 L-89 164 L-59 156 L-45 147 L-38 140 L-35 134 L-35 122 L-41 112 L-45 100 L-52 92 L-55 80 L-56 67 L-49 62 L-51 49 L-50 32 L-45 20 L-35 10 L-22 3 L-7 -0 L14 2 L24 6 L35 15 L42 28 L45 44 L44 65 L52 68 L52 81 L48 92 L41 100 L37 113 L32 120 L33 127 L40 141 L46 147 L56 153 L102 167 L113 171 L125 183 L132 201 L134 224 L135 293 L140 328 L147 357 L148 458 L155 482 L155 500 L165 529 L165 548 L162 559 L157 570 L139 588 L131 591 L126 591 L123 585 L128 574 L131 564 L127 536 L124 533 L119 535 L120 552 L117 555 L113 554 L110 550 L107 539 L109 519 L121 490 L122 485 L116 461 L102 422 L96 399 L92 370 L92 331 L89 318 L86 329 L81 417 L96 464 L104 553 L93 627 L78 692 L78 723 L82 769 L76 834 L66 895 L65 931 L79 953 L99 976 L101 980 L101 986 L98 991 L89 998 L71 1000 Z"
SIL_K, SIL_TOP, PCX = 0.9, 110, 860          # silhouette path is 1000 units tall, x centred on 0


def ppt(x, y, cx=PCX):
    """Point on the patient, in silhouette units -> frame px."""
    return cx + x * SIL_K, SIL_TOP + y * SIL_K


def patient(cx=PCX, op=1.0):
    return G("Patient", f'<path d="{SIL_PATH}" transform="translate({cx} {SIL_TOP}) scale({SIL_K})" fill="#25262A" '
                        f'stroke="{DIM}" stroke-width="{2.5 / SIL_K:.2f}" stroke-linejoin="round"/>', f' opacity="{op}"')


# ---------------- beats ----------------
B = {}


def beat(fn):
    B[fn.__name__.replace("b_", "").replace("__", "-")] = fn
    return fn


@beat
def b_1A_strip():
    s, _ = strip_group(80, 600, 1760, 4.6, "V5", 150)
    cap = G("Caption", T(960, 900, "tall · short · tall · short", 40, FG, 300, "middle", 4))
    return s + cap


@beat
def b_1B_title():
    s, _ = strip_group(100, 820, 1720, 4.6, "V5", 105)
    title = G("Title", T(960, 330, "ELECTRICAL", 96, FG, 300, "middle", 10) + T(960, 450, "ALTERNANS", 96, ACC, 700, "middle", 10))
    return title + s


def axis_dial(gid, cx, cy, deg, col, ghost=None, r=70):
    ring = (f'<circle cx="{cx:.0f}" cy="{cy}" r="{r}" fill="none" stroke="{LINE}" stroke-width="2"/>'
            f'<line x1="{cx - r:.0f}" y1="{cy}" x2="{cx + r:.0f}" y2="{cy}" stroke="{LINE}" stroke-width="1.5"/>'
            f'<line x1="{cx:.0f}" y1="{cy - r}" x2="{cx:.0f}" y2="{cy + r}" stroke="{LINE}" stroke-width="1.5"/>')
    tip = lambda d: (cx + (r - 8) * math.cos(math.radians(d)), cy + (r - 8) * math.sin(math.radians(d)))
    g = ""
    if ghost is not None:
        gx, gy = tip(ghost)
        g = (f'<line x1="{cx:.0f}" y1="{cy}" x2="{gx:.0f}" y2="{gy:.0f}" stroke="{GREY}" stroke-width="3" stroke-dasharray="5 5"/>'
             f'<path d="M{cx + 40*math.cos(math.radians(ghost)):.1f} {cy + 40*math.sin(math.radians(ghost)):.1f} A40 40 0 0 0 '
             f'{cx + 40*math.cos(math.radians(deg)):.1f} {cy + 40*math.sin(math.radians(deg)):.1f}" fill="none" stroke="{ACC}" stroke-width="2.5"/>')
    tx, ty = tip(deg)
    return G(gid, ring + g + arrow(cx, cy, tx, ty, col, 4, 14))


def big_pair(x1, x2, base, amp, second_rot=0, notch=False, second_f=ALT, total=False, extra2=""):
    L = LEADS["V5"]

    def cx_path(x0, f, notched):
        pts = []
        for i in range(0, 361, 2):
            tt = 0.05 + i / 360 * 0.50
            v = wave(tt, L, f, total)
            if notched:
                v += f * 0.28 * gs(tt, 0.247, 0.006)
            pts.append((x0 + i * 1.6, base - v * amp))
        return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    r_x = lambda x0: x0 + (R_T - 0.05) / 0.50 * 360 * 1.6
    q1 = trace(cx_path(x1, 1.0, False), wdt=5, gid="QRS_1")
    q2 = trace(cx_path(x2, second_f, notch), wdt=5, gid="QRS_2",
               extra=(f' transform="rotate({second_rot} {r_x(x2):.0f} {base})"' if second_rot else "") + extra2)
    base_line = f'<line x1="{x1-40}" y1="{base}" x2="{x2+620}" y2="{base}" stroke="{LINE}" stroke-width="1.5" stroke-dasharray="6 8"/>'
    return base_line + q1 + q2, r_x(x1), r_x(x2)


@beat
def b_2A_definition():
    base, amp = 760, 420
    pair, r1, r2 = big_pair(260, 1040, base, amp, notch=True)
    top1 = base - amp * 1.0
    top2 = base - amp * ALT
    labels = (G("Amplitude", f'<path d="M{r2+130:.0f} {top1:.0f} L{r2+150:.0f} {top1:.0f} L{r2+150:.0f} {top2:.0f} L{r2+130:.0f} {top2:.0f}" '
                             f'fill="none" stroke="{ACC}" stroke-width="3"/>'
                             f'<line x1="{r1:.0f}" y1="{top1:.0f}" x2="{r2+150:.0f}" y2="{top1:.0f}" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="4 8"/>'
                             + T(r2 + 175, (top1 + top2) / 2 + 10, "AMPLITUDE", 30, ACC, 700, "start", 3))
              + G("Axis", axis_dial("Vector_1", r1, base + 170, 60, FG) + axis_dial("Vector_2", r2, base + 170, 45, ACC, ghost=60)
                  + T(r2 + 110, base + 182, "AXIS", 30, ACC, 700, "start", 3))
              + G("Shape", f'<circle cx="{r2 + 22:.0f}" cy="{top2 + 70:.0f}" r="44" fill="none" stroke="{ACC}" stroke-width="2.5" stroke-dasharray="6 6"/>'
                  + T(r2 - 230, top2 + 20, "SHAPE", 30, ACC, 700, "start", 3)))
    return G("Pair", pair) + G("Labels", labels) + T(80, 120, "beat-to-beat change in the QRS", 30, DIM, 400)


@beat
def b_2B_total():
    base, amp = 700, 300
    pair, r1, r2 = big_pair(240, 1000, base, amp, total=True)
    xs = lambda x0, tt: x0 + (tt - 0.05) / 0.50 * 360 * 1.6
    hl = ""
    for x0, f in ((240, 1.0), (1000, ALT)):
        hl += f'<circle cx="{xs(x0, 0.11):.0f}" cy="{base - 0.10*f*amp - 10:.0f}" r="34" fill="none" stroke="{ACC}" stroke-width="3"/>'
        hl += f'<circle cx="{xs(x0, 0.40):.0f}" cy="{base - 0.20*f*amp - 14:.0f}" r="52" fill="none" stroke="{ACC}" stroke-width="3"/>'
        hl += f'<rect x="{xs(x0, 0.20):.0f}" y="{base - amp*f - 24:.0f}" width="{xs(x0,0.275)-xs(x0,0.20):.0f}" height="{amp*f + 90:.0f}" rx="8" fill="none" stroke="{ACC}" stroke-width="3"/>'
    lab = G("Labels", T(960, 900, "P · QRS · T", 40, FG, 400, "middle", 6))
    title = G("Title", T(960, 170, "TOTAL ELECTRICAL ALTERNANS", 60, ACC, 700, "middle", 6))
    return title + G("Pair", pair) + G("Highlight", hl) + lab


@beat
def b_2C_sign():
    pair, _, _ = big_pair(0, 760, 520, 300)
    c = (f'<rect x="420" y="250" width="760" height="420" rx="14" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>'
         f'<g transform="translate(500 270) scale(0.4)">{pair}</g>')
    lab = G("Label", T(800, 760, "A sign, not a diagnosis", 48, FG, 400, "middle", 1))
    q = G("Question", T(1500, 640, "?", 420, ACC, 700, "middle"))
    return G("Card", c + lab) + q


def two_cards(electrics_op=1.0, electrics_scale=1.0, with_list=False):
    ex, ey, w, h = 140, 300, 760, 480
    lst = ""
    if with_list:
        lst = G("List", "".join(T(ex + 40, ey + 190 + i * 70, s, 34, FG, 400) for i, s in
                                enumerate(["supraventricular tachycardia", "ischemia", "T-wave alternans · long QT"])))
    sc = f' transform="translate({ex + w/2:.0f} {ey + h/2:.0f}) scale({electrics_scale}) translate({-(ex + w/2):.0f} {-(ey + h/2):.0f})"'
    e = G("Electrics", f'<rect x="{ex}" y="{ey}" width="{w}" height="{h}" rx="12" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>'
                       + T(ex + 40, ey + 90, "THE ELECTRICS", 44, FG, 700, "start", 4) + T(ex + 40, ey + 136, "the conduction system is unstable", 28, DIM)
                       + lst, f' opacity="{electrics_op}"{sc}')
    mx = 1020
    hb, _, _ = heart_in_sac(mx + w / 2, ey + 300, 0.28, fluid=110, angle=10)
    m = G("Motion", f'<rect x="{mx}" y="{ey}" width="{w}" height="{h}" rx="12" fill="{CARD}" stroke="{ACC}" stroke-width="2"/>'
                    + T(mx + 40, ey + 90, "THE MOTION", 44, ACC, 700, "start", 4) + T(mx + 40, ey + 136, "the whole heart is moving", 28, DIM) + hb)
    return G("Cards", e + m)


@beat
def b_3A_two__buckets():
    return two_cards() + T(960, 190, "two kinds of reasons", 36, DIM, 300, "middle", 3)


@beat
def b_3B_electrical():
    return two_cards(0.4, 0.9, True) + T(960, 190, "two kinds of reasons", 36, DIM, 300, "middle", 3)


SC_CX, SC_CY, SC_S = 760, 470, 0.70


@beat
def b_3C_effusion():
    fl = 120
    hs, _, h0 = heart_in_sac(SC_CX, SC_CY, SC_S, fluid=fl)
    P = lambda th, r: (SC_CX + r * SC_S * math.cos(math.radians(th)), SC_CY + r * SC_S * math.sin(math.radians(th)))
    sac_pt, epi_pt, flu_pt = P(-6, 236 + 12 + fl), P(14, 236 + 12), P(36, 236 + 12 + fl / 2)
    def leader(gid, pt, ly, text, col):
        return G(gid, f'<line x1="1240" y1="{ly - 9}" x2="{pt[0]:.0f}" y2="{pt[1]:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                      f'<circle cx="{pt[0]:.0f}" cy="{pt[1]:.0f}" r="6" fill="{col}"/>' + T(1250, ly, text, 34, col, 700))
    lab = G("Labels", leader("Sac_label", sac_pt, 430, "pericardial sac", FG) + leader("Epicardium_label", epi_pt, 530, "epicardium", ACC)
            + leader("Effusion_label", flu_pt, 630, "pericardial effusion", EFF))
    cw, _ = chest_wall(SC_CX, SC_CY)
    return G("Cross_section", hs) + cw + lab + T(80, 120, "a heart swinging in a bag of fluid", 30, DIM)


@beat
def b_3D_swing():
    ang = 12
    hs, (px, py), h0 = heart_in_sac(SC_CX, SC_CY, SC_S, fluid=120, angle=ang, ghost=-ang)
    cw, (ex, ey) = chest_wall(SC_CX, SC_CY)
    hx, hy = rot(SC_CX, SC_CY, ang, px, py)
    gx, gy = rot(SC_CX, SC_CY, -ang, px, py)
    vec = G("Vector_arrow", arrow(hx, hy, hx + (ex - hx) * 0.62, hy + (ey - hy) * 0.62, ACC, 6, 22)
            + arrow(gx, gy, gx + (ex - gx) * 0.28, gy + (ey - gy) * 0.28, GREY, 4, 16))
    labels = G("Labels", G("Beat1", T(1250, 470, "beat 1 → toward", 34, ACC, 700)) + G("Beat2", T(1250, 520, "beat 2 → away", 34, GREY, 700)))
    s, _ = strip_group(160, 990, 1600, 3.2, "V5", 62, mark_h=26)
    return G("Cross_section", hs) + cw + vec + labels + s


@beat
def b_3E_drain():
    hs, _, h0 = heart_in_sac(SC_CX, SC_CY, SC_S, fluid=18, show_fluid=True)
    r_sac = (236 + 12 + 18) * SC_S
    tipx, tipy = SC_CX + r_sac * math.cos(math.radians(40)), SC_CY + r_sac * math.sin(math.radians(40))
    hx, hy = tipx + 300, tipy + 190
    needle = G("Needle", f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{tipx:.0f}" y2="{tipy:.0f}" stroke="{FG}" stroke-width="5" stroke-linecap="round"/>'
                         f'<rect x="{hx - 10:.0f}" y="{hy - 24:.0f}" width="150" height="48" rx="6" fill="{CARD}" stroke="{FG}" stroke-width="2" transform="rotate(32 {hx:.0f} {hy:.0f})"/>')
    cw, _ = chest_wall(SC_CX, SC_CY)
    d, beats = ecg(160, 990, 1600, 3.2, "V5", 62, alt=1.0)
    s = G("Strip", paper(140, 990 - 62 * 1.45, 1640, 62 * 2.1) + trace(d))
    return G("Cross_section", hs) + cw + needle + s + T(1250, 470, "drained · swing stops", 34, DIM, 700)


TW = (80, 140, 1760, 860)


@beat
def b_4A_every__other():
    ecgsvg, info = twelve_lead(*TW, dim_except={"Strip"})
    beats = info["strip_beats"]
    x, y, w, h = info["Strip"]
    top = y + 34
    odd = "".join(f'<circle cx="{bx:.0f}" cy="{top:.0f}" r="9" fill="{ACC}"/>' for i, (bx, by, t) in enumerate(beats) if t)
    even = "".join(f'<circle cx="{bx:.0f}" cy="{top+26:.0f}" r="9" fill="{GREY}"/>' for i, (bx, by, t) in enumerate(beats) if not t)
    tx = [b[0] for b in beats if b[2]]; sx = [b[0] for b in beats if not b[2]]
    br = (f'<g id="Odd"><line x1="{tx[0]:.0f}" y1="{top:.0f}" x2="{tx[-1]:.0f}" y2="{top:.0f}" stroke="{ACC}" stroke-width="2"/></g>'
          f'<g id="Even"><line x1="{sx[0]:.0f}" y1="{top+26:.0f}" x2="{sx[-1]:.0f}" y2="{top+26:.0f}" stroke="{GREY}" stroke-width="2"/></g>')
    lab = G("Label", T(1840, 110, "odd beats match · even beats match · the two sets don't", 26, FG, 400, "end")
            + T(1840, 80, "that's alternans", 34, ACC, 700, "end"))
    return ecgsvg + G("Marks", G("Odd", odd) + G("Even", even)) + G("Brackets", br) + lab


@beat
def b_4B_leads():
    ecgsvg, info = twelve_lead(*TW)
    spots = ""
    for ld in ("V2", "V3", "V5"):
        x, y, w, h = info[ld]
        spots += f'<rect x="{x+4:.0f}" y="{y+6:.0f}" width="{w-8:.0f}" height="{h-12:.0f}" rx="8" fill="{ACC}" fill-opacity="0.07" stroke="{ACC}" stroke-width="3"/>'
    x, y, w, h = info["Strip"]
    spots += f'<rect x="{x+4:.0f}" y="{y+6:.0f}" width="{w-8:.0f}" height="{h-12:.0f}" rx="8" fill="none" stroke="{ACC}" stroke-width="3"/>'
    dim = "".join(f'<rect x="{info[ld][0]:.0f}" y="{info[ld][1]:.0f}" width="{info[ld][2]:.0f}" height="{info[ld][3]:.0f}" fill="{BG}" fill-opacity="0.45"/>'
                  for ld in ("I", "II", "III", "aVR", "aVL", "aVF", "V1", "V4", "V6"))
    return ecgsvg + G("Spotlight", dim + spots) + G("Labels", G("Leads", T(1840, 100, "V2 · V3 · V5", 40, ACC, 700, "end", 4)))


@beat
def b_4C_companions():
    ecgsvg, info = twelve_lead(*TW)
    e = f'<g transform="translate(40 230) scale(0.6) translate(-80 -140)">{ecgsvg}</g>'
    rate = G("Rate", f'<rect x="1180" y="230" width="660" height="230" rx="12" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>'
                     + T(1220, 300, "sinus tachycardia", 40, ACC, 700) + T(1220, 360, "regular · rate over 100", 30, FG)
                     + T(1220, 410, "P before every QRS", 26, DIM))
    d, _ = ecg(1500, 650, 300, 0.9, "I", 34, phase=0.0)
    volt = G("Voltage", f'<rect x="1180" y="500" width="660" height="230" rx="12" fill="{CARD}" stroke="{LINE}" stroke-width="2"/>'
                        + T(1220, 570, "low voltage", 40, ACC, 700) + T(1220, 630, "small QRS in", 30, FG) + T(1220, 670, "the limb leads", 30, FG)
                        + trace(d, wdt=3) + f'<line x1="1820" y1="650" x2="1820" y2="{650 - 5*7.04*0.9:.0f}" stroke="{ACC}" stroke-width="3"/>'
                        + T(1812, 700, "5 mm", 20, DIM, 400, "end"))
    icon_x, icon_y = 1510, 900
    hb, _, _ = heart_in_sac(icon_x, icon_y, 0.17, fluid=120, angle=8)
    arr = G("Arrow", arrow(1360, 740, icon_x - 90, icon_y - 20, FG, 3) + arrow(1660, 740, icon_x + 90, icon_y - 20, FG, 3)
            + hb + T(icon_x + 140, icon_y + 10, "large effusion", 28, EFF, 700))
    return G("ECG", e) + G("Panel", rate + volt + arr)


def person(x, y, col, s=1.0):
    return (f'<circle cx="{x}" cy="{y}" r="{28*s:.0f}" fill="{col}"/>'
            f'<path d="M{x-46*s:.0f} {y+130*s:.0f} C{x-46*s:.0f} {y+50*s:.0f} {x+46*s:.0f} {y+50*s:.0f} {x+46*s:.0f} {y+130*s:.0f} Z" fill="{col}"/>')


@beat
def b_4D_numbers():
    figs = G("Figures", G("Four", "".join(person(220 + i * 130, 320, ACC if i == 0 else "#3A3B3E") for i in range(4)))
             + T(415, 520, "with tamponade, alternans in about 1 in 4", 28, DIM, 400, "middle"))
    sens = G("Number", G("Sens", T(1060, 280, "SENSITIVITY", 34, DIM, 700, "start", 5) + T(1060, 480, "23 %", 190, FG, 700))
             + G("Spec", T(1060, 640, "SPECIFICITY", 34, DIM, 700, "start", 5) + T(1060, 840, "98 %", 190, ACC, 700)))
    src = T(80, 1020, "Argula et al., Clin Cardiol 2015 · tamponade in malignant effusion", 20, GREY)
    return figs + sens + src


def rules(op=1.0):
    r1 = G("Rule_1", f'<rect x="300" y="300" width="14" height="190" fill="{ACC}"/>' + T(350, 420, "See it → believe it", 72, FG, 700))
    r2 = G("Rule_2", f'<rect x="300" y="570" width="14" height="190" fill="{GREY}"/>' + T(350, 690, "Don't see it → ruled out nothing", 72, FG, 300))
    return G("Rules", r1 + r2, f' opacity="{op}"')


@beat
def b_4E_rule():
    return rules()


@beat
def b_4F_bigeminy():
    # bigeminy: normal beat + early PVC-like beat with a pause after; alternans: equal spacing
    starts_b = []
    t = 0.0
    for k in range(-2, 60):
        starts_b.append(t)
        t += 0.42 if k % 2 == 0 else 0.86
    bd, bb = ecg(140, 400, 1640, 4.0, "V5", 110, rr_fn=lambda k: starts_b[k + 2] - 0.6, amp_fn=lambda k: 1.0 if k % 2 == 0 else 0.6)
    ad, ab = ecg(140, 840, 1640, 4.0, "V5", 110)
    def calipers(beats, y, col):
        out = ""
        for (x1, _, _), (x2, _, _) in zip(beats, beats[1:]):
            out += (f'<path d="M{x1:.0f} {y+20} L{x1:.0f} {y} L{x2:.0f} {y} L{x2:.0f} {y+20}" fill="none" stroke="{col}" stroke-width="2.5"/>')
        return out
    top = G("Bigeminy", paper(120, 400 - 160, 1680, 230) + trace(bd, gid="Strip") + G("Calipers", calipers(bb, 210, GREY))
            + T(140, 190, "BIGEMINY", 40, FG, 700, "start", 5) + T(1780, 190, "irregular · uneven pairs", 30, DIM, 400, "end"))
    bot = G("Alternans", paper(120, 840 - 160, 1680, 230) + trace(ad, gid="Strip") + G("Calipers", calipers(ab, 650, ACC))
            + T(140, 630, "ALTERNANS", 40, ACC, 700, "start", 5) + T(1780, 630, "regular · equal spacing", 30, FG, 400, "end"))
    return G("Strips", top + bot)


# ---------- scene 5 ----------
def beck_icons(op=1.0, cx=PCX):
    # right internal jugular: the patient's right side of the neck (viewer's left)
    v0, v1 = ppt(-22, 112, cx), ppt(-26, 150, cx)
    jvd = G("JVD", f'<path d="M{v0[0]:.0f} {v0[1]:.0f} C{v0[0] + 6:.0f} {v0[1] + 14:.0f} {v1[0] - 6:.0f} {v1[1] - 14:.0f} {v1[0]:.0f} {v1[1]:.0f}" '
                   f'fill="none" stroke="{EFF}" stroke-width="7" stroke-linecap="round"/>'
                   + f'<line x1="{v0[0] - 14:.0f}" y1="{(v0[1] + v1[1]) / 2:.0f}" x2="{cx - 240:.0f}" y2="{(v0[1] + v1[1]) / 2:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                   + T(cx - 250, (v0[1] + v1[1]) / 2 - 6, "distended", 32, FG, 400, "end") + T(cx - 250, (v0[1] + v1[1]) / 2 + 32, "neck veins", 32, FG, 400, "end"))
    # stethoscope on the precordium (patient's left chest = viewer's right)
    sx, sy = ppt(38, 268, cx)
    snd = G("Sounds", f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="20" fill="{BG}" stroke="{FG}" stroke-width="3"/>'
                      f'<path d="M{sx:.0f} {sy - 20:.0f} C{sx:.0f} {sy - 70:.0f} {sx - 30:.0f} {sy - 90:.0f} {sx - 46:.0f} {sy - 118:.0f}" fill="none" stroke="{FG}" stroke-width="3"/>'
                      + f'<line x1="{sx + 26:.0f}" y1="{sy:.0f}" x2="{cx + 230:.0f}" y2="{sy:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                      + T(cx + 240, sy + 10, "muffled heart sounds", 32, FG))
    # cuff on the upper arm (patient's left arm = viewer's right)
    ax, ay = ppt(120, 375, cx)
    bp = G("BP", f'<rect x="{ax - 36:.0f}" y="{ay - 40:.0f}" width="72" height="80" rx="10" fill="{BG}" stroke="{FG}" stroke-width="3"/>'
                 f'<line x1="{ax - 36:.0f}" y1="{ay - 14:.0f}" x2="{ax + 36:.0f}" y2="{ay - 14:.0f}" stroke="{FG}" stroke-width="2"/>'
                 + f'<line x1="{ax + 42:.0f}" y1="{ay:.0f}" x2="{cx + 230:.0f}" y2="{ay:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                 + T(cx + 240, ay + 10, "hypotension", 32, FG))
    return G("Icons", bp + jvd + snd, f' opacity="{op}"')


@beat
def b_5A_bedside():
    return mini_heart(200, 190) + patient() + T(1180, 420, "Is it being squeezed?", 52, FG, 300) + T(1180, 490, "the vitals", 32, DIM)


@beat
def b_5B_beck():
    return mini_heart(200, 190) + patient() + beck_icons() + G("Title", T(1840, 120, "BECK'S TRIAD", 56, ACC, 700, "end", 6))


def bars(items, x=1160, y=420, w=600, label_w=0, op=1.0):
    out = ""
    for i, (gid, name, frac, txt) in enumerate(items):
        yy = y + i * 120
        out += G(gid, T(x, yy - 14, name, 30, FG) + f'<rect x="{x}" y="{yy}" width="{w}" height="34" rx="4" fill="#26272A"/>'
                 f'<rect x="{x}" y="{yy}" width="{w*frac:.0f}" height="34" rx="4" fill="{ACC}"/>'
                 + T(x + w + 20, yy + 28, txt, 30, FG, 700))
    return G("Bars", out, f' opacity="{op}"')


COMMON = [("Dyspnea", "shortness of breath", 0.88, "~9 / 10"), ("Tachy", "fast heart rate", 0.77, "~8 / 10"),
          ("JVP", "raised neck veins", 0.76, "~3 / 4")]


@beat
def b_5C_common():
    triad = (patient() + beck_icons() + G("Title", T(PCX, 70, "BECK'S TRIAD", 56, FG, 700, "middle", 6))
             + G("Uncommon", f'<rect x="{PCX - 170}" y="96" width="340" height="76" rx="6" fill="{BG}" stroke="{ACC}" stroke-width="4" transform="rotate(-6 {PCX} 134)"/>'
                 + T(PCX, 152, "UNCOMMON", 44, ACC, 700, "middle", 8, extra=f' transform="rotate(-6 {PCX} 134)"')))
    return (mini_heart(200, 190) + G("Beck", f'<g opacity="0.45">{triad}</g>', ' transform="translate(20 300) scale(0.6)"')
            + T(1060, 330, "what's actually common", 34, DIM, 300) + bars(COMMON, x=1060, y=440, w=560))


def breath_and_gauge(drop=14):
    g = G("Cuff", gauge(1500, 360, 150, drop, "C"))
    x0, x1 = 1180, 1840
    br = lambda x: math.sin((x - x0) / (x1 - x0) * 2 * math.pi * 1.5 - math.pi / 2)   # +1 = full inspiration
    xs = list(range(x0, x1 + 1, 3))
    breath = "M" + " L".join(f"{x} {930 - 40*br(x):.1f}" for x in xs)
    sbp = "M" + " L".join(f"{x} {700 + 30*max(0, br(x)) - 18*abs(math.sin((x - x0)/11)):.1f}" for x in xs)
    ins_x = x0 + (x1 - x0) / 3 * 1.0
    b = G("Breath", G("Curve", trace(breath, DIM, 3)) + T(x0, 1010, "breathing", 22, DIM)
          + G("Insp", T(ins_x, 870, "inspiration", 24, ACC, 700, "middle")))
    thr = G("Threshold", f'<line x1="{x0}" y1="682" x2="{x1}" y2="682" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="6 8"/>'
            f'<path d="M{ins_x + 56:.0f} 682 L{ins_x + 70:.0f} 682 L{ins_x + 70:.0f} 730 L{ins_x + 56:.0f} 730" fill="none" stroke="{ACC}" stroke-width="3"/>'
            + T(ins_x, 785, "> 10 mmHg drop", 28, ACC, 700, "middle"))
    return g + G("Pressure", trace(sbp, FG, 2.5) + T(x1, 650, "systolic pressure", 22, DIM, 400, "end")) + thr + b + G("Title", T(1180, 120, "PULSUS PARADOXUS", 48, ACC, 700, "start", 5))


@beat
def b_5D_pulsus():
    return mini_heart(200, 190) + bars(COMMON, x=120, y=420, w=420) + breath_and_gauge()


@beat
def b_5E_odds():
    items = COMMON + [("Pulsus", "pulsus paradoxus", 0.82, "~8 / 10")]
    odds = G("Odds", G("Up", arrow(700, 620, 700, 470, ACC, 6, 22) + T(740, 530, "> 10 → ~3× more likely", 34, ACC, 700))
             + G("Down", arrow(700, 720, 700, 870, GREY, 6, 22) + T(740, 820, "≤ 10 → very unlikely", 34, FG, 700)))
    src = T(80, 1020, "Roy et al., JAMA 2007", 20, GREY)
    return mini_heart(200, 190) + bars(items, x=120, y=420, w=420) + breath_and_gauge() + odds + src


@beat
def b_5F_link():
    card_ = G("Card", f'<rect x="1300" y="860" width="540" height="140" rx="12" fill="{CARD}" stroke="{ACC}" stroke-width="2"/>'
                      + T(1340, 920, "WATCH", 24, DIM, 700, "start", 5) + T(1340, 970, "Pulsus Paradoxus", 40, FG, 700)
                      + T(1820, 970, "↗", 40, ACC, 700, "end"))
    items = COMMON + [("Pulsus", "pulsus paradoxus", 0.82, "~8 / 10")]
    return (mini_heart(200, 190) + G("Dim", bars(items, x=120, y=420, w=420) + breath_and_gauge(), ' opacity="0.45"') + card_
            + T(1840, 836, "link in the description", 26, FG, 400, "end"))


# ---------- scene 6 ----------
@beat
def b_6A_recap__strip():
    s, _ = strip_group(80, 600, 1760, 4.6, "V5", 150)
    return s + G("Caption", T(960, 900, "tall · short · tall · short", 40, FG, 300, "middle", 4)) + T(960, 960, "fast · regular", 30, DIM, 300, "middle", 4)


def checks(n=3):
    items = [("JVP", "neck veins"), ("Pulsus", "pulsus"), ("Echo", "echo")]
    out = ""
    for i, (gid, t) in enumerate(items[:n]):
        y = 380 + i * 140
        out += G(gid, f'<rect x="1000" y="{y-50}" width="60" height="60" rx="8" fill="none" stroke="{ACC}" stroke-width="3"/>'
                      f'<path d="M1012 {y-20} L1026 {y-6} L1050 {y-38}" fill="none" stroke="{ACC}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
                 + T(1100, y, t, 56, FG, 700))
    return G("Check", out)


@beat
def b_6B_checklist():
    hb, _, _ = heart_in_sac(520, 540, 0.62, fluid=120, angle=12, ghost=-12)
    return G("Heart_mini", hb) + checks() + T(1000, 200, "think swinging heart", 34, DIM, 300, "start", 3)


@beat
def b_6C_end():
    l1 = G("Line_1", T(240, 430, "Swinging?", 96, FG, 300) + T(900, 430, "→ ECG", 96, ACC, 700))
    l2 = G("Line_2", T(240, 620, "Squeezed?", 96, FG, 300) + T(900, 620, "→ bedside", 96, ACC, 700))
    end = G("End_screen", f'<rect x="1380" y="860" width="460" height="140" rx="12" fill="none" stroke="{LINE}" stroke-width="2" stroke-dasharray="10 10"/>'
                          + T(1610, 945, "Motion Library end screen", 24, DIM, 400, "middle"))
    return l1 + l2 + end


NAMES = {"1A": "strip", "1B": "title", "2A": "definition", "2B": "total", "2C": "sign", "3A": "two-buckets", "3B": "electrical",
         "3C": "effusion", "3D": "swing", "3E": "drain", "4A": "every-other", "4B": "leads", "4C": "companions", "4D": "numbers",
         "4E": "rule", "4F": "bigeminy", "5A": "bedside", "5B": "beck", "5C": "common", "5D": "pulsus", "5E": "odds", "5F": "link",
         "6A": "recap-strip", "6B": "checklist", "6C": "end"}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for key, fn in B.items():
        bid = key.split("_")[0]
        name = f"{bid}_{NAMES[bid]}"
        open(os.path.join(out, name + ".svg"), "w").write(svg(bid, fn()))
        print(name)
