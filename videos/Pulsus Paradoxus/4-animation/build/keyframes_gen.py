"""Rough key frames for Pulsus Paradoxus, style C (spotlight). One SVG per beat, drawn at the END state of
that beat's motion notes. Layer groups use the motion-note names (Group/Sublayer -> nested <g id>).
Reuses the heart model and drop gauge from style_frames_gen.py."""
import math, re, os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
from gen import heart, gauge, radii, RV_A, W, H, BG, FG, ACC, GREY, FONT
from thorax_final import HCX, HCY, HS

DIM = "#8A8B8C"
MYO, CAV, LINE = "#26272A", "#141414", "#4A4B4C"
# heart restyle to match Electrical Alternans (Mark 2026-10-23): grey-pink muscle and fat, red epicardium, striations
H_MUSCLE, H_EDGE, H_FAT, H_STRIA = "#A6979A", "#7D6F72", "#958689", "#7A6B6E"
STRIA_LV = [(0.18, "22 9 12 7", 3), (0.34, "15 8 26 10", 11), (0.50, "30 11 9 8", 6), (0.66, "12 6 20 9", 15), (0.82, "26 10 14 7", 9)]
STRIA_RV = [(0.33, "22 9 12 7", 5), (0.67, "15 8 26 10", 13)]
FLUID = "#9FB3C8"
EFF = "#5E9BD6"   # effusion accent (blue; was blue-grey #8FA7C2), Mark 2026-10-23: pericardial fluid, its sac highlight and its labels


# ---------- primitives ----------
def svg(beat, body):
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W, 80))
    grid += "".join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H, 80))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}">'
            f'<rect id="Background" width="{W}" height="{H}" fill="{BG}"/><g id="Grid" stroke="#1F2021" stroke-width="1">{grid}</g>'
            f'{body}<text id="Beat_ID" x="{W-40}" y="{H-32}" text-anchor="end" font-size="18" fill="{GREY}">{beat}</text></svg>')


def chip(state):
    return (f'<g id="Breath"><rect id="Chip" x="80" y="70" width="128" height="52" rx="6" fill="none" stroke="{ACC}" stroke-width="2"/>'
            f'<text x="144" y="106" text-anchor="middle" font-size="26" font-weight="700" letter-spacing="4" fill="{ACC}">{state}</text></g>')


def chip2(state):
    """Mark 2026-10-25: the breath label is one chip at a time, INSPIRATION or EXPIRATION, top-left. In AE (engine action
    "breath") the current chip slides out to the left and the next one slides in from the left into the same spot on each
    breath. Both chips are drawn in the same place; the inactive one ships hidden (AE switches it on)."""
    o = '<g id="Breath">'
    for t, st in (("INSPIRATION", "IN"), ("EXPIRATION", "OUT")):
        hid = "" if st == state else ' data-hidden="1" visibility="hidden"'
        solid = st == "OUT"                    # Mark 2026-10-27: EXPIRATION is a solid red chip with white text; INSPIRATION stays outlined
        o += (f'<g id="{t.title()}"{hid}>'
              f'<rect x="80" y="70" width="{CHIP_W}" height="52" rx="6" fill="{ACC if solid else "none"}" stroke="{ACC}" stroke-width="2"/>'
              f'<text x="{80 + CHIP_W / 2:.0f}" y="106" text-anchor="middle" font-size="26" font-weight="700" letter-spacing="4" fill="{"#FFFFFF" if solid else ACC}">{t}</text></g>')
    return o + '</g>'
CHIP_W, CHIP_ROW = 236, 64


def lab(gid, x, y, text, tx=None, ty=None, accent=False, size=26, color=None, side=None):
    col = color or (ACC if accent else FG)
    lead = ""
    if tx is not None:
        right = side == "right" if side else tx > x       # side forces where the leader leaves the text (keeps leaders from crossing)
        lx = x + len(text) * size * 0.5 + 18 if right else x - 6
        lead = (f'<line x1="{lx:.0f}" y1="{y-9}" x2="{tx:.0f}" y2="{ty:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                f'<circle cx="{tx:.0f}" cy="{ty:.0f}" r="5" fill="{color or FG}"/>')
    return f'<g id="{gid}">{lead}<text x="{x}" y="{y}" font-size="{size}" fill="{col}">{text}</text></g>'


def title_pair(light, bold, x, y, size=44, gid="Title", bold_col=None):
    return (f'<g id="{gid}"><text x="{x}" y="{y}" font-size="{size}" font-weight="300" fill="{FG}" letter-spacing="2">{light}</text>'
            f'<text x="{x}" y="{y + size*1.25:.0f}" font-size="{size}" font-weight="700" fill="{bold_col or ACC}" letter-spacing="2">{bold}</text></g>')


def card(gid, x, y, w, h, lines, accent_first=True, split=None):
    """split=("Card/Stat", "Card/Action"): rect + first line in one layer, the other lines in the second."""
    if split:
        texts = [f'<text x="{x+32}" y="{y + 64 + i*64}" font-size="{40 if i == 0 else 30}" font-weight="{700 if i == 0 else 400}" '
                 f'fill="{ACC if (i == 0 and accent_first) else FG}">{s}</text>' for i, s in enumerate(lines)]
        return (f'<g id="{gid}"><g id="{split[0]}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#1C1D1E" stroke="{LINE}" stroke-width="2"/>{texts[0]}</g>'
                f'<g id="{split[1]}">{"".join(texts[1:])}</g></g>')
    t = "".join(f'<text x="{x+32}" y="{y + 64 + i*64}" font-size="{40 if i == 0 else 30}" font-weight="{700 if i == 0 else 400}" '
                f'fill="{ACC if (i == 0 and accent_first) else FG}">{s}</text>' for i, s in enumerate(lines))
    return f'<g id="{gid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#1C1D1E" stroke="{LINE}" stroke-width="2"/>{t}</g>'


# ---------- heart ----------
def striations(cx, cy, s, bow):
    """Faint muscle fibres: broken arcs following the wall, built from radii(bow) so they move with the septum.
    LV: 5 fibres from the LV cavity edge (rc) to the LV epicardium (rs: the RV side of the septum, or the outer wall);
    RV free wall: 2 fibres between its inner (ri) and outer (ro) edge. Hearts under scale 0.5: 2 LV + 1 RV."""
    R = radii(bow)
    P = lambda th, r: f"{cx + r*s*math.cos(math.radians(th)):.1f} {cy + r*s*math.sin(math.radians(th)):.1f}"
    k = max(s, 0.5)                                  # dash lengths follow the heart's scale
    dash = lambda d: " ".join(f"{float(x)*k:.1f}" for x in d.split())
    lv = STRIA_LV if s >= 0.5 else [STRIA_LV[1], STRIA_LV[3]]
    rv = STRIA_RV if s >= 0.5 else [(0.5, STRIA_RV[0][1], STRIA_RV[0][2])]
    out = []
    for f, d, off in lv:
        pts = [P(th, rc + (rs - rc) * f) for th, rc, ro, rs, ri in R]
        out.append(f'<path d="M{" L".join(pts)} Z" stroke-dasharray="{dash(d)}" stroke-dashoffset="{off*k:.1f}"/>')
    order = lambda th: (th - RV_A) % 360
    seg = sorted([t for t in R if t[4] - t[3] > 6], key=lambda t: order(t[0]))
    for f, d, off in rv:
        pts = [P(th, ri + (ro - ri) * f) for th, rc, ro, rs, ri in seg]
        out.append(f'<path d="M{" L".join(pts)}" stroke-dasharray="{dash(d)}" stroke-dashoffset="{off*k:.1f}"/>')
    return (f'<g id="Myocardium_striations" fill="none" stroke="{H_STRIA}" stroke-opacity="0.28" stroke-linecap="round" '
            f'stroke-width="{max(0.8, 1.6*s):.2f}">{"".join(out)}</g>')


def heart_group(cx, cy, s, bow=0.0, fluid=0, rv_scale=1.0, lv_scale=1.0, hi=None, opacity=1.0, sac_w=3):
    """hi: which structure carries the accent: 'septum', 'rv', 'lv', 'sac' or None."""
    h = heart(cx, cy, s, bow=bow, fluid=fluid)
    A = h["anchors"]
    rx, ry = A["rv"]; lx, ly = A["lv"]
    rv_t = f'translate({rx:.0f} {ry:.0f}) scale({rv_scale}) translate({-rx:.0f} {-ry:.0f})'
    lv_t = f'translate({lx:.0f} {ly:.0f}) scale({lv_scale}) translate({-lx:.0f} {-ly:.0f})'
    sac_col = LINE   # Mark 2026-10-23: no accent on the sac
    big = s >= 1.0          # Scene 3 close-up gets the final detail pass (Stage 5); Scene 2/4 axial heart unchanged
    o = [f'<g id="Pericardium" opacity="{opacity}">']
    if fluid:
        o.append(f'<path id="Fluid" d="{h["sac"]}" fill="{EFF}" fill-opacity="{0.30 if big else 0.22}"/>')
        if big:
            rip = "".join(f'<path d="{heart(cx, cy, s, bow=bow, fluid=fluid*f)["sac"]}"/>' for f in (0.35, 0.68))
            o.append(f'<g id="Fluid_ripples" fill="none" stroke="{EFF}" stroke-opacity="0.45" stroke-width="1.5" stroke-dasharray="14 18">{rip}</g>')
    if big and fluid:
        o.append(f'<path id="Serous_layer" d="{heart(cx, cy, s, bow=bow, fluid=fluid-5)["sac"]}" fill="none" stroke="#5A5B60" stroke-width="1.5"/>')
    o.append(f'<path id="Sac" d="{h["sac"]}" fill="none" stroke="{sac_col}" stroke-width="{sac_w}" stroke-linejoin="round"/></g>')
    o.append(f'<g id="Heart" opacity="{opacity}"><path id="Epicardial_fat" d="{h["fat"]}" fill="{H_FAT}"/>'
             f'<path id="Myocardium" d="{h["outline"]}" fill="{H_MUSCLE}"/>')   # no outer stroke: the red epicardium is the only edge (Mark 2026-10-23)
    o.append(striations(cx, cy, s, bow))
    # cavities stay near-black; a highlight (rv / lv / septum) tints the cavity on top of that
    rv_hi = hi == "rv"
    o.append(f'<g id="RV" transform="{rv_t}"><path d="{h["rv"]}" fill="{CAV}"/>'
             f'<path d="{h["rv"]}" fill="{ACC if rv_hi else CAV}" fill-opacity="{0.16 if rv_hi else 0}" '
             f'stroke="{ACC if rv_hi else H_EDGE}" stroke-width="{3 if rv_hi else 2}" stroke-linejoin="round"/></g>')
    lv_hi = hi in ("lv", "septum")
    o.append(f'<g id="LV" transform="{lv_t}"><path d="{h["lv"]}" fill="{CAV}"/>'
             f'<path d="{h["lv"]}" fill="{ACC if lv_hi else CAV}" fill-opacity="{0.14 if lv_hi else 0}" '
             f'stroke="{ACC if lv_hi else H_EDGE}" stroke-width="{3 if lv_hi else 2}"/></g>')
    if hi == "septum":
        o.append(f'<path id="Septum_glow" d="{h["sept_line"]}" fill="none" stroke="{ACC}" stroke-opacity="0.28" stroke-width="{28*s/1.32:.0f}" stroke-linecap="round"/>'
                 f'<path id="Septum" d="{h["sept_line"]}" fill="none" stroke="{ACC}" stroke-width="{max(4, 8*s/1.32):.0f}" stroke-linecap="round"/>')
    else:
        o.append(f'<path id="Septum" d="{h["sept_line"]}" fill="none" stroke="none"/>')
    vs = list(h["vessels"])
    if big:
        R = radii(bow)
        rof = {int(t[0]): t for t in R}
        for th in (20, 60, 330, 250, 95):
            vs.append((cx + (rof[th][2] + 6) * s * math.cos(math.radians(th)), cy + (rof[th][2] + 6) * s * math.sin(math.radians(th))))
    # coronary vessel dots removed (Mark 2026-10-23: detail not useful here)
    o.append(f'<path id="RV_free_wall" d="{h["rv_wall"]}" fill="none" stroke="none"/>')
    # epicardium (Mark 2026-10-23, every heart): red line on the fat band's outer edge, so effusion reads as the gap to the sac
    o.append(f'<path id="Epicardium_line" d="{h["fat"]}" fill="none" stroke="{ACC}" stroke-width="3.5" stroke-linejoin="round" stroke-opacity="0.95"/>')
    tag = max(18, int(30 * s / 1.32))
    o.append(f'<g id="Chamber_tags" font-size="{tag}" font-weight="700" fill="{DIM}">'
             f'<text x="{rx:.0f}" y="{ry + tag/3:.0f}" text-anchor="middle">RV</text>'
             f'<text x="{lx:.0f}" y="{ly + tag/3:.0f}" text-anchor="middle" fill="{ACC if hi in ("lv", "septum") else DIM}">LV</text></g></g>')
    return "".join(o), A


# ---------- thorax, axial section (scenes 2 and 4), modeled on Mark's reference ----------
CX, CY = 760, 560


def chest(insp=0.0, deep=False, hi_vessels=False, narrow=False, flow=None, rv_scale=1.0, lv_scale=1.0, heart_hi=None,
          hi_bronchi=False, chest_scale=1.0, bow=0.0, fluid_hidden=False, bronchi=True):
    """Axial section seen from below (patient's right on the viewer's left). insp 0 = end-expiration, 1 = inspiration.
    The diaphragm is not in this plane; inspiration reads as the chest wall and lungs expanding."""
    from thorax_final import thorax
    o = [thorax(insp, deep, hi_vessels, narrow, hi_bronchi, chest_scale, bronchi)]
    # heart: anterior, slightly to the patient's left; RV anterior-right = viewer's upper-left, as in the reference
    from thorax_final import HCX, HCY, HS
    hg, A = heart_group(HCX, HCY, HS, bow=bow, rv_scale=rv_scale, lv_scale=lv_scale, hi=heart_hi, sac_w=2)
    if fluid_hidden:
        # 4A starts with Scene 3's effusion and drains it: the layer ships hidden (end state), AE turns it on
        o.append(f'<path id="Pericardium/Fluid" data-hidden="1" visibility="hidden" d="{heart(HCX, HCY, HS, bow=bow, fluid=24)["sac"]}" fill="{EFF}" fill-opacity="0.3"/>')
    o.append(hg)
    # (Heart/Emphasis white outline removed, Mark 2026-10-23: the red epicardium is the heart's outer edge)
    if flow == "venous":
        rx, ry = A["rv"]
        o.append(f'<g id="Flow"><path id="Venous_dots" d="M{rx-120:.0f} {ry-150:.0f} C{rx-80:.0f} {ry-60:.0f} {rx-40:.0f} {ry-30:.0f} {rx:.0f} {ry-12:.0f}" fill="none" stroke="{FG}" '
                 f'stroke-width="5" stroke-dasharray="2 14" stroke-linecap="round"/>'
                 f'<path d="M{rx-22:.0f} {ry-30:.0f} L{rx:.0f} {ry-10:.0f} L{rx-2:.0f} {ry-40:.0f}" fill="none" stroke="{FG}" stroke-width="4"/></g>')
    if flow == "pulmonary":
        rx, ry = A["rv"]
        o.append(f'<g id="Flow"><path id="Pulmonary_dots" d="M{rx:.0f} {ry:.0f} C{rx-60:.0f} {ry+120:.0f} 700 640 640 660" fill="none" stroke="{FG}" '
                 f'stroke-width="5" stroke-dasharray="2 14" stroke-linecap="round"/>'
                 f'<path d="M{rx:.0f} {ry:.0f} C{rx+160:.0f} {ry+140:.0f} 860 640 900 662" fill="none" stroke="{FG}" stroke-width="5" stroke-dasharray="2 14" stroke-linecap="round"/></g>')
    return "".join(o), A


# ---------- thorax, coronal view (2A inset): Mark's human silhouette + State of Health lungs, restyled ----------
LUNG_R = ("M 420.2 321.9 C 378.7 307.6 340.4 350.4 324.5 407.4 C 295.7 504.3 273.4 624 276.6 720.9 C 278.2 755.1 302.1 772.2 334 766.5 "
          "C 388.3 749.4 436.2 738 477.7 749.4 C 487.2 709.5 482.5 652.5 472.9 598.3 C 463.3 541.3 471.3 490 460.1 444.4 C 452.1 401.7 445.8 341.8 420.2 321.9 Z")
LUNG_L = ("M 592.6 321.9 C 634.1 307.6 672.4 350.4 688.3 407.4 C 717.1 504.3 739.4 624 736.2 720.9 C 734.6 755.1 710.7 772.2 678.8 766.5 "
          "C 624.5 749.4 576.6 738 535.1 749.4 C 543.1 718 573.4 695.2 565.5 652.5 C 559.1 615.5 546.3 575.5 543.1 538.5 C 541.5 498.6 544.7 475.8 552.7 444.4 "
          "C 560.7 401.7 567 341.8 592.6 321.9 Z")
TRACHEA = ("M 490.4 225 V 364.6 C 490.4 384.6 468.1 401.7 433 424.5 M 522.4 225 V 364.6 C 522.4 384.6 544.7 401.7 579.8 424.5 "
           "M 445.8 441.6 C 474.5 421.7 496.8 404.5 506.4 384.6 C 516 404.5 538.3 421.7 567 441.6")
RINGS = "".join(f"M 492 {y:.1f} Q 506.4 {y+5.7:.1f} 520.8 {y:.1f} " for y in [242.1 + 14.25 * i for i in range(9)])
FISS_R = "M 480.9 475.8 Q 413.8 635.4 267 703.8 M 267 556.7 Q 346.5 568.1 426.1 573.8"
FISS_L = "M 531.9 470.1 Q 605.4 632.5 745.8 706.6"
LUNG_SY, LUNG_SX, DIAPH_DROP = 1.13, 1.06, 58      # inspiration: lungs 104 % wide / 110 % tall from the apex, diaphragm down 40 px (native)
APEX_R, APEX_L = (380, 322), (632, 322)


# diaphragm (coronal): one smooth curve, two domes (right higher over the liver), flat centre (central tendon)
# under the heart, ends attached to the lower ribs. Native coords = the lungs above.
def dia_curve(insp=0.0):
    r = 752 + 58 * insp        # right dome (viewer's left)
    l = 764 + 58 * insp        # left dome
    c = 784 + 48 * insp        # central tendon
    e = 824 + 14 * insp        # rib attachments (costophrenic angles)
    return (f"M256 {e:.1f} C262 {r+22:.1f} 306 {r:.1f} 380 {r:.1f} C440 {r:.1f} 470 {c:.1f} 506 {c:.1f} "
            f"C542 {c:.1f} 572 {l:.1f} 632 {l:.1f} C706 {l:.1f} 750 {l+22:.1f} 756 {e:.1f}")


def diaphragm_d(drop=0.0, flat=0.0):           # ghost outline (top surface)
    return dia_curve(flat)


def diaphragm(insp, hi=False):
    d = dia_curve(insp)
    col = ACC if hi else FG
    return (f'<g id="Diaphragm" transform="translate(0 9)">'
            f'<path id="Outline" d="{d}" fill="none" stroke="{col}" stroke-width="22" stroke-linecap="round"/>'
            f'<path id="Muscle" d="{d}" fill="none" stroke="#3A3B3F" stroke-width="16" stroke-linecap="round"/>'
            f'<path id="Central_tendon" d="{d}" pathLength="100" fill="none" stroke="#9A9B9E" stroke-width="16" '
            f'stroke-dasharray="0 43 14 43" stroke-linecap="butt" opacity="0.55"/></g>')


def coronal_ribs():
    arcs = []
    for i in range(9):
        y0 = 268 + i * 64
        for k in (-1, 1):
            x0 = 506 + k * 34
            x1, y1 = 506 + k * (236 + min(i, 4) * 6), y0 + 26
            x2, y2 = 506 + k * (250 - max(i - 5, 0) * 10), y0 + 74
            arcs.append(f"M{x0} {y0} C{506 + k*140} {y0 - 14} {x1} {y1 - 18} {x1} {y1} C{x1 + k*4} {y1 + 22} {x2 + k*6} {y2 - 18} {x2} {y2}")
    costal = "M262 862 C330 900 430 880 506 820 C582 880 682 900 750 862"
    return (f'<g id="Ribs" fill="none" stroke="#2E2F33" stroke-width="9" stroke-linecap="round">{"".join(f"<path d=\"{a}\"/>" for a in arcs)}</g>'
            f'<path id="Costal_margin" d="{costal}" fill="none" stroke="#34353A" stroke-width="7" stroke-linecap="round"/>')


def abdomen(insp):
    dy = 50 * insp
    return (f'<g id="Abdomen" opacity="0.9"><path id="Liver" d="M250 {870+dy:.0f} C260 {800+dy:.0f} 320 {778+dy:.0f} 390 {776+dy:.0f} C460 {780+dy:.0f} 520 {800+dy:.0f} 560 {830+dy:.0f} '
            f'C600 {860+dy:.0f} 600 {900+dy:.0f} 560 {930+dy:.0f} L250 {940+dy:.0f} Z" fill="#26272B"/>'
            f'<ellipse id="Stomach_bubble" cx="640" cy="{820+dy:.0f}" rx="56" ry="30" fill="#1A1B1D" stroke="#2E2F33" stroke-width="2"/></g>')


BODY = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "body_silhouette.txt")).read().strip()   # traced from Mark's reference (2026-10-24)


COR_MX, COR_Y, COR_S = 1440, 380, 0.55               # Mark 2026-10-24: coronal view enlarged beside the axial section (2A); midline x, head-top y, scale
COR4_MX, COR4_Y, COR4_S = 1320, 400, 0.50            # 4B: a little smaller and left, clear of the drop graph
COR_X, COR4_X = COR_MX - 506 * COR_S, COR4_MX - 506 * COR4_S   # native midline is x = 506


def coronal(insp=1.0, x=COR_X, y=COR_Y, s=COR_S, ghost=True, plane_y=None, dia_hi=False):
    """Coronal thorax, front view (patient's right on the viewer's left). Native coords = State of Health 2A lungs.
    insp 0 = end-expiration, 1 = end-inspiration. ghost draws the expiration outlines dashed under the inspiration state."""
    o = [f'<g id="Coronal" transform="translate({x} {y}) scale({s})">',
         '<defs><linearGradient id="cor_fade" x1="0" y1="0" x2="0" y2="1"><stop offset="0.840" stop-color="#fff"/><stop offset="0.978" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         '<mask id="cor_mask" maskUnits="userSpaceOnUse" x="-100" y="-520" width="1212" height="1460"><rect x="-100" y="-520" width="1212" height="1460" fill="url(#cor_fade)"/></mask>'
         f'<clipPath id="cor_clipR"><path d="{LUNG_R}"/></clipPath><clipPath id="cor_clipL"><path d="{LUNG_L}"/></clipPath></defs>']
    body = ("M456 196 C420 226 300 232 214 262 C150 286 122 330 118 410 L104 940 L908 940 L894 410 C890 330 862 286 798 262 "
            "C712 232 592 226 556 196 Z")
    # Mark 2026-10-24: human silhouette traced from his reference (head, neck, shoulders, arms hanging at the sides)
    o.append(f'<g id="Silhouette" mask="url(#cor_mask)"><path id="Body" d="{BODY}" fill="#1C1D1F" stroke="{LINE}" stroke-width="4" stroke-linejoin="round"/></g>')
    o.append(f'<g id="Thoracic_cage" mask="url(#cor_mask)">{coronal_ribs()}</g>')
    o.append(f'<g mask="url(#cor_mask)">{abdomen(insp)}</g>')
    # heart sits on the central tendon in the cardiac notch (context only, dim)
    o.append(f'<path id="Heart" d="M470 556 C502 526 572 538 592 598 C612 660 594 730 544 752 C502 766 470 748 462 712 C450 660 455 600 470 556 Z" '
             f'transform="translate(0 {48 * insp + 4:.0f})" fill="{MYO}" stroke="{LINE}" stroke-width="2"/>')

    def lung(gid, d, fiss, clip, apex, k):
        sx, sy = 1 + (LUNG_SX - 1) * insp, 1 + (LUNG_SY - 1) * insp
        ax, ay = apex
        return (f'<g id="Lungs/{gid}" transform="translate({ax} {ay}) scale({sx:.3f} {sy:.3f}) translate({-ax} {-ay})">'
                f'<path id="Fill" d="{d}" fill="#2A2B2E"/>'
                f'<path id="Fissure" d="{fiss}" fill="none" stroke="{GREY}" stroke-width="3" stroke-linecap="round" clip-path="url(#{clip})"/>'
                f'<path id="Outline" d="{d}" fill="none" stroke="{FG}" stroke-width="4.5" stroke-linejoin="round"/></g>')
    if ghost and insp > 0:
        o.append(f'<g id="Ghost_expiration" fill="none" stroke="{DIM}" stroke-width="4" stroke-dasharray="12 10">'
                 f'<path d="{LUNG_R}"/><path d="{LUNG_L}"/><path d="{diaphragm_d(0, 0)}"/></g>')
    o.append(f'<g id="Trachea" fill="none" stroke="{DIM}" stroke-linecap="round" stroke-linejoin="round"><path id="Tube" d="{TRACHEA}" stroke-width="4.5"/>'
             f'<path id="Rings" d="{RINGS}" stroke-width="2.5" opacity="0.75"/></g>')
    o.append(f'<g id="Lungs">{lung("R", LUNG_R, FISS_R, "cor_clipR", APEX_R, -1)}{lung("L", LUNG_L, FISS_L, "cor_clipL", APEX_L, 1)}</g>')
    o.append(diaphragm(insp, hi=dia_hi))
    if insp > 0:
        ar = "".join(f'<path d="M{ax} {(752 if ax < 506 else 764) + 58*insp + 44:.0f} v46 m-16 -18 l16 18 l16 -18" fill="none" stroke="{ACC}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
                     for ax in (378, 634))
        o.append(f'<g id="Diaphragm_arrows">{ar}</g>')
        la = "".join(f'<path d="M{x0} 560 h{k*40} m{-k*16} -16 l{k*16} 16 l{-k*16} 16" fill="none" stroke="{ACC}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/>'
                     for x0, k in ((262, -1), (750, 1)))
        o.append(f'<g id="Lung_arrows">{la}</g>')
    if plane_y is not None:
        o.append(f'<g id="Axial_plane"><line x1="150" y1="{plane_y}" x2="862" y2="{plane_y}" stroke="{GREY}" stroke-width="3" stroke-dasharray="14 10"/></g>')
    o.append("</g>")
    return "".join(o)


# ---------- arterial trace (3E, 4C) ----------
def arterial(x0, y0, w, h, sys_drop, dia_drop, label_text, gid="Trace", label_dy=110, label_id="Shape"):
    beats, bw = 4, w / 4
    pts = []
    for b in range(beats):
        insp = b >= 2
        top = y0 + (sys_drop if insp else 0)
        bot = y0 + h + (dia_drop if insp else 0)
        bx = x0 + b * bw
        pts.append(f"{'M' if b == 0 else 'L'}{bx:.0f} {bot:.0f} C{bx + bw*0.12:.0f} {bot:.0f} {bx + bw*0.15:.0f} {top:.0f} {bx + bw*0.25:.0f} {top:.0f} "
                   f"C{bx + bw*0.4:.0f} {top:.0f} {bx + bw*0.45:.0f} {top + h*0.35:.0f} {bx + bw*0.5:.0f} {top + h*0.42:.0f} "
                   f"C{bx + bw*0.6:.0f} {top + h*0.32:.0f} {bx + bw*0.8:.0f} {bot - 10:.0f} {bx + bw:.0f} {bot:.0f}")
    o = [f'<g id="{gid}">']
    o.append(f'<rect id="Insp_band" x="{x0 + 2*bw:.0f}" y="{y0 - 60}" width="{2*bw:.0f}" height="{h + 120 + max(dia_drop, 0)}" fill="{FG}" fill-opacity="0.04"/>'
             f'<text x="{x0 + 3*bw:.0f}" y="{y0 - 74}" text-anchor="middle" font-size="22" letter-spacing="4" fill="{DIM}">INSPIRATION</text>'
             f'<text x="{x0 + bw:.0f}" y="{y0 - 74}" text-anchor="middle" font-size="22" letter-spacing="4" fill="{DIM}">EXPIRATION</text>')
    o.append(f'<path id="Arterial" d="{" ".join(pts)}" fill="none" stroke="{FG}" stroke-width="4" stroke-linejoin="round"/>')
    # dashed guides: step at the inspiration boundary
    xm = x0 + 2 * bw
    o.append(f'<path id="Systolic_line" d="M{x0} {y0} H{xm:.0f} V{y0 + sys_drop} H{x0 + w}" fill="none" stroke="{ACC}" stroke-width="2.5" stroke-dasharray="10 8"/>'
             f'<path id="Diastolic_line" d="M{x0} {y0 + h} H{xm:.0f} V{y0 + h + dia_drop} H{x0 + w}" fill="none" stroke="{GREY}" stroke-width="2.5" stroke-dasharray="10 8"/>')
    o.append(f'<text x="{x0 - 20}" y="{y0 + 8}" text-anchor="end" font-size="22" fill="{ACC}">systolic</text>'
             f'<text x="{x0 - 20}" y="{y0 + h + 8}" text-anchor="end" font-size="22" fill="{DIM}">diastolic</text>')
    if label_text:
        o.append(f'<text id="{label_id}" x="{x0 + w/2:.0f}" y="{y0 + h + max(dia_drop, 0) + label_dy}" text-anchor="middle" font-size="34" fill="{FG}">{label_text}</text>')
    o.append('</g>')
    return "".join(o)


# ---------- sphygmomanometer (scene 5, restyled Korotkoff gauge: 1 mmHg = 1 deg) ----------
def sphyg(cx, cy, r, value):
    ang = lambda v: math.radians(120 + v)   # 0 at lower-left, 300 at lower-right
    t = []
    for v in range(0, 301, 2):
        a = ang(v); major = v % 20 == 0; mid = v % 10 == 0
        r1 = r - (34 if major else 22 if mid else 12)
        t.append(f'<line x1="{cx + (r-8)*math.cos(a):.1f}" y1="{cy + (r-8)*math.sin(a):.1f}" x2="{cx + r1*math.cos(a):.1f}" y2="{cy + r1*math.sin(a):.1f}" '
                 f'stroke="{FG if major else GREY}" stroke-width="{3 if major else 1.2}"/>')
    n = "".join(f'<text x="{cx + (r-66)*math.cos(ang(v)):.1f}" y="{cy + (r-66)*math.sin(ang(v)) + 9:.1f}" text-anchor="middle" font-size="24" '
                f'fill="{DIM}">{v}</text>' for v in range(0, 301, 20))
    a = ang(value)
    return (f'<g id="Gauge"><circle id="Face" cx="{cx}" cy="{cy}" r="{r}" fill="#1C1D1E" stroke="{LINE}" stroke-width="3"/>'
            f'<g id="Minor_ticks">{"".join(t)}</g><g id="Dial_numbers">{n}</g>'
            f'<text x="{cx}" y="{cy + r*0.45:.0f}" text-anchor="middle" font-size="22" letter-spacing="4" fill="{DIM}">mmHg</text>'
            f'<line id="Needle" x1="{cx - 40*math.cos(a):.1f}" y1="{cy - 40*math.sin(a):.1f}" x2="{cx + (r-40)*math.cos(a):.1f}" y2="{cy + (r-40)*math.sin(a):.1f}" '
            f'stroke="{ACC}" stroke-width="7" stroke-linecap="round"/><circle id="Hub" cx="{cx}" cy="{cy}" r="16" fill="{FG}"/></g>')


def tap_wave(x0, y0, w, mode, playhead=1.0, dim=1.0):
    """mode: 'none' (no taps), 'exp' (taps only on expiration), 'all' (every beat). 2 breaths, 16 beats."""
    nb = 16
    o = [f'<g id="Waveform" opacity="{dim}">',
         f'<text id="Trace_label" x="{x0}" y="{y0 - 110}" font-size="20" letter-spacing="4" fill="{DIM}">KOROTKOFF SOUNDS</text>']
    # breath bands: OUT, IN, OUT, IN
    seg = w / 4
    for i in range(4):
        st = "OUT" if i % 2 == 0 else "IN"
        if st == "IN":
            o.append(f'<rect x="{x0 + i*seg:.0f}" y="{y0 - 70}" width="{seg:.0f}" height="130" fill="{FG}" fill-opacity="0.04"/>')
        o.append(f'<text x="{x0 + i*seg + seg/2:.0f}" y="{y0 - 80}" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">{st}</text>')
    path = [f"M{x0} {y0}"]
    for b in range(nb):
        bx = x0 + (b + 0.5) * w / nb
        if bx > x0 + w * playhead:
            break
        insp = int((bx - x0) // seg) % 2 == 1
        tap = mode == "all" or (mode == "exp" and not insp)
        if tap:
            path.append(f"L{bx-10:.0f} {y0} L{bx-4:.0f} {y0-52} L{bx+4:.0f} {y0+26} L{bx+10:.0f} {y0}")
    path.append(f"L{x0 + w*playhead:.0f} {y0}")
    o.append(f'<path id="Trace" d="{" ".join(path)}" fill="none" stroke="{ACC}" stroke-width="3" stroke-linejoin="round"/>')
    if playhead < 1:
        o.append(f'<line id="Playhead" x1="{x0 + w*playhead:.0f}" y1="{y0-60}" x2="{x0 + w*playhead:.0f}" y2="{y0+50}" stroke="{FG}" stroke-width="2"/>')
    o.append("</g>")
    return "".join(o)



# ---------- Korotkoff arm rig and sphygmomanometer (Mark's asset, restyled) ----------
_ARM_SRC = open(os.path.join(os.path.dirname(__file__), "arm.svg")).read() if os.path.exists(os.path.join(os.path.dirname(__file__), "arm.svg")) else open("/Users/dumarkus/Desktop/Pulsus Paradoxus/assets/reference/korotkoff_arm_rig.svg").read()
_STYLE = re.search(r"<style>(.*?)</style>", _ARM_SRC, re.S).group(1)
_STYLE = (_STYLE.replace("#e8553e", ACC).replace("'Courier New'", "Helvetica, Arial, sans-serif").replace("CourierNewPSMT", "Helvetica")
          .replace("TimesNewRomanPS-ItalicMT", "Helvetica").replace("'Times New Roman'", "Helvetica, Arial, sans-serif")
          .replace("#edeae3", FG).replace("#b9b5ac", DIM).replace("#8a877f", GREY))
_STYLE = re.sub(r"\s+", " ", _STYLE)
_DEFS = f"<defs><style>{_STYLE}</style></defs>"
_ARM = _ARM_SRC[_ARM_SRC.index('<g id="Arm_rig">'):_ARM_SRC.index('<path id="Cuff_tube"')]
_ARM = _ARM.replace('id="Arm_rig"', 'id="Arm_rig" class="rig"')
_TUBE = re.search(r'(<path id="Cuff_tube".*?/>)', _ARM_SRC, re.S).group(1)
_STETH = '<g id="Stethoscope">' + _ARM_SRC[_ARM_SRC.index('<path id="Stethoscope_tubing"'):_ARM_SRC.index('<g id="Labels">')]
_STETH = _STETH[:_STETH.rstrip().rfind('</g>')]  # drop the outer group's closing tag, keep Chestpiece's
_STETH += '</g>' * (len(re.findall(r'<g[ >]', _STETH)) - _STETH.count('</g>'))  # close Stethoscope (was left open, so 1B's title sat inside the 30% rig)
_GAUGE_BODY = re.search(r'<g id="Gauge">(.*?)<g id="Needle">', _ARM_SRC, re.S).group(1)
_HUB = re.search(r'(<g id="Hub">.*?</g>)', _ARM_SRC, re.S).group(1)


def korotkoff_gauge(value, cx=836, cy=256, scale=1.0, gid="Gauge"):
    """Mark's dial: 0 at 120 deg, 1 deg per mmHg, 300 mmHg sweep. Needle computed for `value`."""
    a = math.radians(120 + value)
    r = 133.6
    needle = (f'<g id="Needle"><line x1="{836 - 20*math.cos(a):.1f}" y1="{256 - 20*math.sin(a):.1f}" '
              f'x2="{836 + (r-25)*math.cos(a):.1f}" y2="{256 + (r-25)*math.sin(a):.1f}" stroke="{ACC}" stroke-width="2.8" stroke-linecap="round"/></g>')
    return (f'{_DEFS}<g id="{gid}" transform="translate({cx} {cy}) scale({scale}) translate(-836 -256)">{_GAUGE_BODY}{needle}{_HUB}</g>')


def arm_rig(x=0, y=0, s=1.0, with_gauge=True, gauge_value=120, steth=True, opacity=1.0, gauge_scale=1.0):
    # gauge_scale: Scene 1 draws the dial 25 % larger about its own centre so the numbers read (Mark 2026-10-24)
    g = korotkoff_gauge(gauge_value, scale=gauge_scale) if with_gauge else ""
    return (f'{_DEFS}<g id="Arm_scene" opacity="{opacity}" transform="translate({x} {y}) scale({s})">{_ARM}{_TUBE}'
            f'{_STETH if steth else ""}{g}</g>')

# ---------- scene 1 ----------
TL5 = {"5B": 188.797, "5C": 196.204, "5D": 203.626, "5E": 210.549}    # beat ends (s, animatic v4 timeline): 5B-5D next start, 5E VO end

# Scene 1 sound wave (Mark 2026-10-24): drawn from Cue A v2's own audio, as in the Korotkoff Sounds video.
# Grey-white unplayed wave, white played wave revealed left to right in time with the cue, accent playhead.
CUE_A_T = 13.251                                   # Cue A v2 length (s) = the wave's width
CUE_A_START, CUE_A_RATE = 143.6, 2.0               # cuff mmHg at 0 s, deflation mmHg/s
_ENV = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cueA_env780.json")))
WX0, WY0, WW = 1060, 760, 780
wx = lambda t: WX0 + WW * t / CUE_A_T


def sound_wave(played=1.0, dim=1.0, playhead=None, env=None, x0=None, y0=None, w=None, T=None, bands=None, clip_id="playclip"):
    """Korotkoff-video style sound wave. Defaults are Scene 1 (Cue A v2); Scene 5 passes Cue B's."""
    env = env or _ENV; T = T or CUE_A_T
    WX0, WY0, WW = (x0 if x0 is not None else globals()["WX0"]), (y0 if y0 is not None else globals()["WY0"]), (w or globals()["WW"])
    wx = lambda t: WX0 + WW * t / T
    amp = 58
    step = WW / len(env)
    top = [(WX0 + (i + 0.5) * step, WY0 - max(1.2, amp * v)) for i, v in enumerate(env)]
    bot = [(x, 2 * WY0 - y) for x, y in reversed(top)]
    d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in top + bot) + " Z"
    o = [f'<g id="Waveform" opacity="{dim}">',
         f'<text id="Trace_label" x="{WX0}" y="{WY0 - 110}" font-size="20" letter-spacing="4" fill="{DIM}">KOROTKOFF SOUNDS</text>']
    bands = bands or [(0, 3, "OUT"), (3, 5, "IN"), (5, 8, "OUT"), (8, 10, "IN"), (10, CUE_A_T, "OUT")]   # Cue A breathing
    lab = []
    for a, b, st in bands:
        if st == "IN":
            o.append(f'<rect x="{wx(a):.0f}" y="{WY0 - 70}" width="{wx(b) - wx(a):.0f}" height="140" fill="{FG}" fill-opacity="0.04"/>')
        if wx(b) - wx(a) >= 50:              # no label on a sliver of a band at either end
            lab.append(f'<text x="{(wx(a) + wx(b)) / 2:.0f}" y="{WY0 - 80}" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">{st}</text>')
    o.append(f'<g id="Band_labels">{"".join(lab)}</g>')
    o.append(f'<path id="Unplayed" d="{d}" fill="{FG}" fill-opacity="0.16"/>')
    if played >= 1:
        o.append(f'<path id="Played" d="{d}" fill="{FG}"/>')
    else:
        o.append(f'<clipPath id="{clip_id}"><rect x="{WX0}" y="{WY0 - 80}" width="{WW * played:.1f}" height="160"/></clipPath>'
                 f'<path id="Played" d="{d}" fill="{FG}" clip-path="url(#{clip_id})"/>')
    if playhead is not None:
        x = WX0 + WW * playhead
        o.append(f'<line id="Playhead" x1="{x:.1f}" y1="{WY0 - 75}" x2="{x:.1f}" y2="{WY0 + 75}" stroke="{ACC}" stroke-width="3"/>')
    o.append("</g>")
    return "".join(o)


G1 = 1.25                                          # Scene 1 dial size
UL_X0, UL_W, UL_WHY_Y, UL_HOW_Y = 1082, 132, 494, 732   # underlines under "Why" and "How" (Helvetica Bold 64: both words ~2.11 em)


def s1(beat):
    v_end = round(CUE_A_START - CUE_A_RATE * CUE_A_T)          # needle where the cue ends (117)
    trace = sound_wave()
    if beat == "1A_mid":                                        # storyboard only: mid-beat at 8.6 s (inspiration)
        t = 8.6
        return chip2("IN") + arm_rig(0, 60, 1.0, gauge_value=CUE_A_START - CUE_A_RATE * t, gauge_scale=G1) + sound_wave(t / CUE_A_T, playhead=t / CUE_A_T)
    if beat == "1A":
        # end state: wave fully played; the playhead ships as a hidden layer at the left edge (AE slides it with the cue)
        ph = f'<line id="Waveform/Playhead" data-hidden="1" visibility="hidden" x1="{WX0}" y1="{WY0 - 75}" x2="{WX0}" y2="{WY0 + 75}" stroke="{ACC}" stroke-width="3"/>'
        return chip2("OUT") + arm_rig(0, 60, 1.0, gauge_value=v_end, gauge_scale=G1) + trace + ph
    if beat == "1B":
        return (chip2("OUT") + arm_rig(0, 60, 1.0, gauge_value=v_end, opacity=0.18, gauge_scale=G1) + sound_wave(dim=0.4) +
                f'<g id="Title"><text id="Pulsus_paradoxus" x="960" y="470" text-anchor="middle" font-size="110" font-weight="700" fill="{ACC}" letter-spacing="4">PULSUS PARADOXUS</text>'
                f'<text id="Definition" x="960" y="550" text-anchor="middle" font-size="34" fill="{DIM}">a drop in systolic pressure of more than 10 mmHg with inspiration</text></g>'
                f'<g id="Waveform/Gap_bracket"><path d="M{wx(8):.0f} 700 V680 H{wx(10):.0f} V700" fill="none" stroke="{ACC}" stroke-width="3"/>'
                f'<text x="{wx(9):.0f}" y="665" text-anchor="middle" font-size="26" font-weight="700" fill="{ACC}">&gt; 10 mmHg</text></g>')
    # Mark 2026-10-24: red underline under both "Why" and "How", each drawn in (left to right) as the word is narrated;
    # the "Why" underline is what curls into the heart's epicardium at the start of Scene 2.
    return (arm_rig(-60, 420, 0.62, gauge_value=v_end, gauge_scale=G1) +
            f'<g id="Promise"><g id="Promise/Why"><text x="1080" y="400" font-size="26" letter-spacing="4" fill="{DIM}">PART 1</text>'
            f'<text x="1080" y="470" font-size="64" font-weight="700" fill="{FG}">Why it happens</text></g>'
            f'<rect id="Promise/Why_underline" x="{UL_X0}" y="{UL_WHY_Y}" width="{UL_W}" height="6" fill="{ACC}"/>'
            f'<g id="Promise/Catch"><text x="1080" y="640" font-size="26" letter-spacing="4" fill="{DIM}">PART 2</text>'
            f'<text x="1080" y="710" font-size="64" font-weight="700" fill="{FG}">How to catch it</text>'
            f'<text x="1080" y="770" font-size="30" fill="{DIM}">a cuff and a stethoscope</text></g>'
            f'<rect id="Promise/How_underline" x="{UL_X0}" y="{UL_HOW_Y}" width="{UL_W}" height="6" fill="{ACC}"/></g>')


# ---------- scenes ----------
# ---------- inspiratory systolic drop: two-bar graph (Mark 2026-10-24, option A; replaces the drop dial in Scenes 2-4) ----------
def bar_geom(cx, cy, r):
    """plot geometry shared with the AE plan: expiration level 5 mmHg below the top, 45 mmHg of headroom below it."""
    f = r / 120.0
    top, bot = cy - r, cy + r + 10 * f
    k = (bot - top) / 50.0
    w = round(58 * f)
    return dict(top=top, bot=bot, k=k, f=f, y=lambda dv: top + 5 * k + dv * k, w=w, xe=cx - round(76 * f), xi=cx + round(18 * f))


def bars(cx, cy, r, drop, dip=None, start0=False):
    """OUT bar at the expiration level, IN bar lowered by `drop` mmHg, the missing part outlined in accent.
    dip: a temporary drop the beat shows and takes back (2D): drawn as hidden layers Bars/Drop and Bars/Readout_dip.
    Mark 2026-10-24: panel 80 % of the first version, plain straight baseline (axis break removed)."""
    g = bar_geom(cx, cy, r); y, bot, w, xe, xi, f = g["y"], g["bot"], g["w"], g["xe"], g["xi"], g["f"]
    fs = lambda n: round(n * f, 1)
    def readout(v, gid, hidden=False):
        hid = ' data-hidden="1" visibility="hidden"' if hidden else ""
        return (f'<text id="{gid}"{hid} x="{cx}" y="{g["top"] - fs(26):.1f}" text-anchor="middle" font-size="{fs(40)}" font-weight="700" fill="{FG}">'
                f'{"−" if v else ""}{v} <tspan font-size="{fs(22)}" font-weight="400" fill="{GREY}">mmHg</tspan></text>')
    o = ['<g id="Bars">']
    o.append(f'<line id="Axis" x1="{cx-r+20*f:.1f}" y1="{bot:.1f}" x2="{cx+r-20*f:.1f}" y2="{bot:.1f}" stroke="{GREY}" stroke-width="2"/>')
    o.append(f'<rect id="Bar_expiration" x="{xe}" y="{y(0):.1f}" width="{w}" height="{bot-y(0):.1f}" fill="{LINE}"/>')
    o.append(f'<line id="Ref_expiration" x1="{xe}" y1="{y(0):.1f}" x2="{xi+w}" y2="{y(0):.1f}" stroke="{DIM}" stroke-width="2" stroke-dasharray="4 6"/>')
    o.append(f'<g id="Threshold_line"><line x1="{cx-r+20*f:.1f}" y1="{y(10):.1f}" x2="{cx+r-20*f:.1f}" y2="{y(10):.1f}" stroke="{ACC}" stroke-width="3" stroke-dasharray="10 8"/>'
             f'<text x="{cx+r-16*f:.1f}" y="{y(10)+6:.1f}" font-size="{fs(20)}" fill="{ACC}">10</text></g>')
    dv = drop or dip
    if dv:
        hid = "" if drop else ' data-hidden="1" visibility="hidden"'
        o.append(f'<rect id="Drop"{hid} x="{xi}" y="{y(0):.1f}" width="{w}" height="{y(dv)-y(0):.1f}" fill="none" stroke="{ACC}" stroke-width="2" stroke-dasharray="5 5"/>')
    o.append(f'<rect id="Bar_inspiration" x="{xi}" y="{y(drop):.1f}" width="{w}" height="{bot-y(drop):.1f}" fill="{FG}"/>')
    o.append(f'<g id="Bar_labels"><text x="{xe+w/2}" y="{bot+fs(30):.1f}" text-anchor="middle" font-size="{fs(18)}" letter-spacing="3" fill="{GREY}">OUT</text>'
             f'<text x="{xi+w/2}" y="{bot+fs(30):.1f}" text-anchor="middle" font-size="{fs(18)}" letter-spacing="3" fill="{GREY}">IN</text></g>')
    o.append(readout(drop, "Readout"))
    if dip:
        o.append(readout(dip, "Readout_dip", hidden=True))
    if start0:                                    # 4C (2026-10-25): the graph first appears here, so it carries its own "0" readout
        o.append(readout(0, "Readout_start", hidden=True))
    o.append(f'<text id="Caption" x="{cx}" y="{bot+fs(70):.1f}" text-anchor="middle" font-size="{fs(20)}" letter-spacing="3" fill="{GREY}">INSPIRATORY SYSTOLIC DROP</text>'
             f'<text id="Caption_note" x="{cx}" y="{bot+fs(98):.1f}" text-anchor="middle" font-size="{fs(16)}" letter-spacing="2" fill="{GREY}">SCHEMATIC</text></g>')
    return "".join(o)


BARS2, BARS3 = (1640, 230, 96), (1600, 260, 104)   # panel placement, Scene 4 and Scene 3 (Scene 3 has no graph since 2026-10-25)
BARS2S = (1600, 270, 128)                           # Scene 2 (Mark 2026-10-25: larger, ~1.33x)
SX, NX, NY = 0.86, 690, 560                         # full-frame axial section, Scenes 2 and 4A: 86 %, centred at (690, 560) (Mark 2026-10-24)
ax_full = lambda body: f'<g transform="translate({NX} {NY}) scale({SX}) translate({-CX} {-CY})">{body}</g>'
mpx = lambda px, py: (NX + (px - CX) * SX, NY + (py - CY) * SX)


LX, LY1, LY2, LS = 1270, 820, 890, 38              # Scene 2 label column (lower right) and size


def lung_arrows():
    """2A: eight short accent arrows around the lungs, pointing outward toward the chest wall (native axial coords)."""
    import math as _m
    cx0, cy0, rx, ry = 768, 542, 560, 345
    o = ['<g id="Axial/Lung_arrows" data-hidden="1" visibility="hidden">']
    for deg in (22, 55, 125, 158, 202, 235, 305, 338):
        a = _m.radians(deg); ux, uy = _m.cos(a), _m.sin(a)
        x0, y0 = cx0 + rx * 0.84 * ux, cy0 + ry * 0.84 * uy
        x1, y1 = cx0 + rx * 1.0 * ux, cy0 + ry * 1.0 * uy
        px, py = -uy, ux
        o.append(f'<path d="M{x0:.0f} {y0:.0f} L{x1:.0f} {y1:.0f} M{x1 - 18*ux + 14*px:.0f} {y1 - 18*uy + 14*py:.0f} L{x1:.0f} {y1:.0f} L{x1 - 18*ux - 14*px:.0f} {y1 - 18*uy - 14*py:.0f}" '
                 f'fill="none" stroke="{ACC}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append("</g>")
    return "".join(o)


def frames():
    F = {}
    F.update({k: s1(k) for k in ("1A", "1A_mid", "1B", "1C")})
    g0 = lambda v, **k: bars(*BARS2, v, **k)
    g2 = lambda v, **k: bars(*BARS2S, v, **k)

    c, A = chest(insp=1, bronchi=False)
    # 2A: axial section shrunk to 72 % and moved up-left; coronal inset bottom-right (Mark 2026-10-22)
    AX, AY, AS = 560, 470, 0.72
    axp = lambda px, py: (AX + (px - CX) * AS, AY + (py - CY) * AS)
    # Mark 2026-10-24 (Scene 2 pass): no drop graph or pressure label in 2A-2C; coronal view enlarged beside the axial section;
    # Axial/Lung_arrows (hidden, flashed on "breathe in") radiate from the lungs toward the chest wall as the lungs expand
    F["2A"] = (chip2("IN") + f'<g id="Axial" transform="translate({AX} {AY}) scale({AS}) translate({-CX} {-CY})">{c}{lung_arrows()}</g>' +
               f'<text id="Tag/Axial" x="{AX}" y="830" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">AXIAL SECTION</text>' +
               coronal(insp=1, plane_y=600) +
               f'<text id="Tag/Coronal" x="{COR_MX}" y="930" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">CORONAL VIEW</text>')
    c, A = chest(insp=1, rv_scale=1.12, heart_hi="rv", bronchi=False)
    # 2B-2D labels: larger, lower right, with a leader to what they name (Mark 2026-10-24); no flow arrows
    F["2B"] = chip2("IN") + ax_full(c) + lab("Label/RV", LX, LY1, "RV filling ↑", *mpx(*A["rv"]), accent=True, size=LS)
    c, A = chest(insp=1, hi_vessels=True, rv_scale=1.12, bronchi=False)
    F["2C"] = chip2("IN") + ax_full(c) + lab("Label/RV", LX, LY1, "RV filling ↑", *mpx(*A["rv"]), size=LS) + \
        lab("Label/Lungs", LX, LY2, "pulmonary vessels hold blood", accent=True, size=LS)   # no leader (Mark 2026-10-24)
    c, A = chest(insp=0, heart_hi="lv", bronchi=False)
    F["2D"] = chip2("OUT") + ax_full(c) + g2(0, dip=8) + lab("Label/LV", LX, LY1, "LV filling ↓", *mpx(*A["lv"]), size=LS) + \
        lab("Label/Systolic", LX, LY2, "systolic ↓ &lt; 10 mmHg", accent=True, size=LS)
    c, A = chest(insp=0, bronchi=False)
    F["2E"] = chip2("OUT") + f'<g opacity="0.5">{ax_full(c)}</g>' + g2(16) + \
        f'<g id="Title"><text id="Threshold" x="1360" y="660" font-size="44" font-weight="700" fill="{ACC}">&gt; 10 mmHg =</text>' \
        f'<text x="1360" y="720" font-size="44" font-weight="700" fill="{ACC}">PULSUS PARADOXUS</text></g>'

    big = lambda **k: heart_group(700, 560, 1.32, **k)

    def head(p2, p3, col, size=22):
        # chevron arrowhead at p3, pointing along p2 -> p3 (last control point to end)
        ang = math.atan2(p3[1] - p2[1], p3[0] - p2[0])
        pts = [(p3[0] - size * math.cos(ang + d), p3[1] - size * math.sin(ang + d)) for d in (0.5, -0.5)]
        return (f'<path d="M{pts[0][0]:.0f} {pts[0][1]:.0f} L{p3[0]:.0f} {p3[1]:.0f} L{pts[1][0]:.0f} {pts[1][1]:.0f}" '
                f'fill="none" stroke="{col}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')

    def venous3(A):
        # Scene 3 (Mark 2026-10-23): venous return dots run in from the upper left (SVC side) into the RV
        rx, ry = A["rv"]
        c2, end = (rx - 120, ry - 150), (rx - 30, ry - 62)
        return (f'<g id="Flow/Venous_dots"><path d="M150 150 C230 190 {c2[0]} {c2[1]} {end[0]} {end[1]}" fill="none" stroke="{FG}" '
                f'stroke-width="6" stroke-dasharray="2 16" stroke-linecap="round"/>{head(c2, end, FG)}</g>')

    def aortic3(A, dx=260):
        # Scene 3: fewer dots leave the LV (half density) toward the aorta, up and out to the right (dx: heart centred, 2026-10-25)
        lx, ly = A["lv"]
        c2, end = (900 + dx, 220), (990 + dx, 110)
        return (f'<g id="Flow/Aortic_dots"><path d="M{lx+10:.0f} {ly-60:.0f} C{lx+40:.0f} {ly-220:.0f} {c2[0]} {c2[1]} {end[0]} {end[1]}" fill="none" stroke="{ACC}" '
                f'stroke-width="6" stroke-dasharray="2 32" stroke-linecap="round"/>{head(c2, end, ACC)}</g>')

    g3 = lambda v, **k: bars(*BARS3, v, **k)
    # Mark 2026-10-25: 3A heart centred; anatomy labels (and later "pressure in the sac") in a right column, PERICARDIAL
    # EFFUSION on the left. The anatomy labels come in just after the heart, over the empty pericardium (before the VO),
    # and stay while the cavity fills; the pericardium and pericardial-cavity leaders are drawn in AE so they can follow
    # the sac as it moves out (their end points are written to leaders3a.json for the AE plan).
    H3X, H3Y, H3S = 960, 560, 1.32
    RX3, LX3 = 1450, 90
    R0 = {int(t[0]): t for t in radii(0)}
    P3 = lambda th, r: (H3X + r * H3S * math.cos(math.radians(th)), H3Y + r * H3S * math.sin(math.radians(th)))
    big3 = lambda **k: heart_group(H3X, H3Y, H3S, **k)
    ANAT = [  # gid, y, text, end point empty (sac at fluid 4), end point full (fluid 58)
        ("Label/Pericardium", 470, "pericardium", P3(330, R0[330][2] + 12 + 4), P3(330, R0[330][2] + 12 + 58)),
        ("Label/Pericardial_cavity", 530, "pericardial cavity", P3(350, R0[350][2] + 12 + 2), P3(350, R0[350][2] + 12 + 29)),
        ("Label/Myocardium", 590, "myocardium", P3(12, (R0[12][1] + R0[12][2]) / 2), None)]
    json.dump({gid: {"from": [RX3 - 6, y - 9], "empty": list(e), "full": list(f) if f else None} for gid, y, _, e, f in ANAT},
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "leaders3a.json"), "w"), indent=1)
    def anatomy3(visible, state="empty"):
        hid = "" if visible else ' data-hidden="1" visibility="hidden"'
        out = ""
        for gid, y, text, e, f in ANAT:
            pt = e if (f is None or state == "empty") else f
            if not visible and f is not None:            # AE draws these two leaders (they follow the sac)
                g = lab(gid, RX3, y, text)
            else:
                g = lab(gid, RX3, y, text, *pt)
            out += g.replace(f'<g id="{gid}">', f'<g id="{gid}"{hid}>', 1)
        return out
    eff = P3(160, R0[160][2] + 12 + 29)                  # PERICARDIAL EFFUSION: left, leader to the fluid band, lower left
    hg, A = big3(bow=0, fluid=58, hi="sac", sac_w=6)
    F["3A"] = hg + anatomy3(False) + (f'<g id="Label/Effusion"><line x1="436" y1="691" x2="{eff[0]:.0f}" y2="{eff[1]:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
         f'<circle cx="{eff[0]:.0f}" cy="{eff[1]:.0f}" r="5" fill="{EFF}"/><text x="424" y="700" text-anchor="end" font-size="26" fill="{EFF}">PERICARDIAL EFFUSION</text></g>') + \
        lab("Label/Pressure", RX3, 680, "pressure in the sac ↑")
    empty = re.sub(r'<path id="Fluid"[^>]*/>|<g id="Fluid_ripples".*?</g>', '', big3(bow=0, fluid=4, hi="sac", sac_w=6)[0], flags=re.S)
    F["3A_start"] = empty
    F["3A_anatomy"] = empty + anatomy3(True)                 # 1.5 s: labels on, before the VO
    # Mark 2026-10-25: the heart stays centred from 3A through 3D (no move at 3B); 3B/3C keep 3A's PERICARDIAL EFFUSION
    # label (left); the white venous arrow is gone; 3C's aortic arrow is labelled "↓ Stroke volume"; 3E scales the heart
    # from the centre to the top left (AE) and draws the guides, then the trace.
    effl = (f'<g id="Label/Effusion"><line x1="436" y1="691" x2="{eff[0]:.0f}" y2="{eff[1]:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
            f'<circle cx="{eff[0]:.0f}" cy="{eff[1]:.0f}" r="5" fill="{EFF}"/><text x="424" y="700" text-anchor="end" font-size="26" fill="{EFF}">PERICARDIAL EFFUSION</text></g>')
    hg, A = big3(bow=1, fluid=58, hi="septum")
    F["3B"] = chip2("IN") + hg + effl + \
        lab("Label/Pinned", 90, 610, "RV free wall pinned", *A["rv_wall"]) + lab("Label/Septum", RX3, 560, "septum bows left", *A["septum"], accent=True)
    hg, A = big3(bow=1, fluid=58, hi="septum")
    _, ay = 0, 110
    F["3C"] = chip2("IN") + hg + aortic3(A) + \
        f'<g id="Label/Stroke_volume"><text x="{990 + 260 + 30}" y="{ay + 12}" font-size="34" fill="{ACC}">↓ Stroke volume</text></g>' + \
        lab("Label/Septum", RX3, 560, "septum bows left", *A["septum"], accent=True) + \
        lab("Label/LV", RX3, 620, "LV filling ↓↓", A["lv"][0], A["lv"][1] + 40) + lab("Label/Pinned", 90, 610, "RV free wall pinned", *A["rv_wall"]) + \
        effl + title_pair("VENTRICULAR", "INTERDEPENDENCE", 1400, 860, gid="Title/Mechanism")
    hg, A = big3(bow=1, fluid=58, opacity=0.4)
    F["3D"] = hg + card("Card", 1100, 540, 760, 240, ["effusion + pulsus paradoxus", "→ urgent assessment, bedside echo", "absence does not rule it out"], split=("Card/Stat", "Card/Action"))
    hg, A = heart_group(380, 330, 0.55, bow=1, fluid=58, opacity=0.4)
    F["3E"] = hg + arterial(300, 640, 1400, 160, 60, 6, "") + \
        f'<g id="Label/PP"><text x="1000" y="916" text-anchor="middle" font-size="34" fill="{FG}">systolic ↓ · diastolic ≈ · pulse pressure narrows  (schematic)</text><path d="M1745 700 V{640+160}" stroke="{ACC}" stroke-width="3"/><path d="M1730 700 H1760 M1730 800 H1760" stroke="{ACC}" stroke-width="3"/></g>'

    c, A = chest(insp=0, narrow=True, hi_bronchi=True, fluid_hidden=True)
    # Mark 2026-10-25: no drop graph before 4C; ASTHMA / COPD in the inflammation green
    from thorax_final import SLIME
    F["4A"] = ax_full(c) + title_pair("SEVERE", "ASTHMA / COPD", 1360, 640, gid="Title/Cause", bold_col=SLIME)
    c, A = chest(insp=1, deep=True, narrow=True)
    # 4B: same layout as 2A (Mark 2026-10-23); deep breath = bigger chest/lung expansion and a deeper diaphragm drop
    F["4B"] = (f'<g id="Axial" transform="translate({AX} {AY}) scale({AS}) translate({-CX} {-CY})">{c}</g>' +
               f'<text id="Tag/Axial" x="{AX}" y="830" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">AXIAL SECTION</text>' +
               coronal(insp=1.5, plane_y=600, dia_hi=True, x=COR4_X, y=COR4_Y, s=COR4_S) +
               f'<text id="Tag/Coronal" x="{COR4_MX}" y="{COR4_Y + 1000 * COR4_S:.0f}" text-anchor="middle" font-size="20" letter-spacing="4" fill="{DIM}">CORONAL VIEW</text>' +
               f'<g id="Readout"><text id="Pressure" x="120" y="975" font-size="110" font-weight="700" fill="{ACC}">−40</text>'
               f'<g id="Label/Pressure"><text x="350" y="935" font-size="28" fill="{FG}">intrathoracic pressure, severe case</text>'
               f'<text x="350" y="972" font-size="20" letter-spacing="2" fill="{DIM}">ILLUSTRATIVE, NOT A THRESHOLD</text></g></g>')
    c, A = chest(insp=1, narrow=True, heart_hi="lv", bow=0.6)
    lx, ly = A["lv"]
    # transmural pressure: the more negative pressure around the LV (red dashed ring, arrows pulling outward)
    fr = HS / 0.5 * 0.8                      # the ring scales with the heart (drawn for the 0.5 heart; Mark's larger heart 2026-10-24)
    arrows = (f'<g id="Heart/LV_arrow"><circle cx="{lx:.0f}" cy="{ly:.0f}" r="{92*fr:.0f}" fill="none" stroke="{ACC}" stroke-width="3" stroke-dasharray="8 8"/>'
              + "".join(f'<path d="M{lx + 96*fr*math.cos(math.radians(a)):.0f} {ly + 96*fr*math.sin(math.radians(a)):.0f} '
                        f'l{26*math.cos(math.radians(a)):.0f} {26*math.sin(math.radians(a)):.0f}" stroke="{ACC}" stroke-width="4" stroke-linecap="round"/>' for a in range(0, 360, 45))
              + '</g>')
    # Mark 2026-10-25: the small red text on the heart was hard to read; 4C labels now sit in the right column at 36 px, the
    # pressure-round-the-LV label in white with a leader to the ring; the line graph comes in late in 4C (AE)
    T4 = lambda x, y: ((x + 140) * 0.72, y * 0.72 - 40)          # 4C section transform
    ring_pt = T4(lx + 92 * fr * math.cos(math.radians(-20)), ly + 92 * fr * math.sin(math.radians(-20)))
    L4X, L4S = 1180, 36
    # Mark 2026-10-25: label the inspiratory drop in diastolic pressure (the point of the 4C graph): the expiration diastolic
    # level carried on as a faint dashed reference across the inspiration band, a bracket to the lowered line, "diastolic ↓"
    xg0, yg0, wg, hg_, dd = 300, 820, 1400, 80, 24
    xmid = xg0 + wg / 2
    dia_label4 = (f'<g id="Label/Diastolic"><path d="M{xmid:.0f} {yg0 + hg_} H{xg0 + wg}" fill="none" stroke="{FG}" stroke-opacity="0.45" stroke-width="2" stroke-dasharray="4 8"/>'
                  f'<path d="M{xg0 + wg + 14} {yg0 + hg_} h12 v{dd} h-12" fill="none" stroke="{FG}" stroke-width="2.5"/>'
                  f'<text x="{xg0 + wg + 36}" y="{yg0 + hg_ + dd/2 + 10:.0f}" font-size="30" fill="{FG}">diastolic ↓</text></g>')
    F["4C"] = f'<g transform="translate(0 -40) scale(0.72) translate(140 0)">{c}{arrows}</g>' + g0(20, start0=True) + \
        (f'<g id="Label/Interdependence"><text x="{L4X}" y="500" font-size="{L4S}" fill="{FG}">RV fills more, septum shifts</text>'
         f'<text x="{L4X}" y="546" font-size="{L4S}" fill="{FG}">→ LV filling ↓</text></g>') + \
        lab("Label/LV_pressure", L4X, 616, "pressure around LV ↓↓", *ring_pt, size=L4S) + \
        lab("Label/Afterload", L4X, 686, "LV afterload ↑", accent=True, size=40) + \
        arterial(300, 820, 1400, 80, 40, 24, "systolic ↓ · diastolic ↓  (schematic)", gid="Trace", label_dy=70, label_id="Label/Shape") + \
        dia_label4

    G = lambda v: korotkoff_gauge(v, cx=560, cy=470, scale=2.45)
    # 5A final pass: show the actual rig (same art as Scene 1); the gauge then scales up to full screen for 5B
    F["5A"] = chip("OUT") + arm_rig(-40, 140, 0.92, gauge_value=160) + card("Card/Setup", 1060, 640, 760, 120, ["MANUAL CUFF + STETHOSCOPE"]) + \
        card("Card/Breathing", 1060, 790, 760, 120, ["normal breathing"], accent_first=False)
    # Scene 5 sound wave (Mark 2026-10-24): Cue B's own audio, x 160-1760 = cue 0-27.58 s (end of 5E), played part white
    TB, B0V, T0B = 27.582, 182.968, 5.729
    envB = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cueB_env1600.json")))
    bandsB, t = [], 0.0
    for k in range(-1, 6):
        a_, b_ = T0B - 2 + 5 * k, T0B + 5 * k
        if b_ <= 0: continue
        if max(a_, 0) > t: bandsB.append((t, max(a_, 0), "OUT"))
        bandsB.append((max(a_, 0), min(b_, TB), "IN")); t = min(b_, TB)
    if t < TB: bandsB.append((t, TB, "OUT"))
    end = {b: TL5[b] - B0V for b in ("5B", "5C", "5D", "5E")}            # cue time at each beat's end
    cuffB = lambda c: max(144.5 - 2.0 * c, 100.0)
    wave5 = lambda b, dim=1.0: sound_wave(min(1, end[b] / TB), dim, None if b == "5E" else min(1, end[b] / TB), envB, 160, 940, 1600, TB, bandsB, "playclip5")
    F["5B"] = chip("IN") + G(round(cuffB(end["5B"]))) + wave5("5B")
    RX5 = 960   # Mark 2026-10-25: readout block moved left (was 1080) so the 5E header clears the frame edge
    def readout(e, b2, kick):
        return (f'<g id="Readout"><text id="Kicker" x="{RX5}" y="300" font-size="30" fill="{FG}">{kick}</text>'
                f'<text x="{RX5}" y="370" font-size="22" letter-spacing="3" fill="{DIM}">CUFF PRESSURE AT FIRST TAPS (EXPIRATION ONLY)</text>'
                f'<text id="Expiration_value" x="{RX5}" y="470" font-size="100" font-weight="700" fill="{ACC}">{e}</text>'
                f'<text x="{RX5}" y="580" font-size="22" letter-spacing="3" fill="{DIM}">CUFF PRESSURE WHEN TAPS ON EVERY BEAT</text>'
                f'<text id="Both_value" x="{RX5}" y="680" font-size="100" font-weight="700" fill="{FG if b2 != "—" else DIM}">{b2}</text></g>')
    F["5C"] = chip("OUT") + G(round(cuffB(end["5C"]))) + wave5("5C") + readout("132", "—", "taps on EXPIRATION only")
    F["5D"] = chip("IN") + G(round(cuffB(end["5D"]))) + wave5("5D") + readout("132", "116", "taps on EVERY beat")
    F["5E"] = chip("OUT") + G(round(cuffB(end["5E"]))) + wave5("5E", 0.4) + \
        f'<g id="Readout"><text x="{RX5}" y="340" font-size="22" letter-spacing="3" fill="{DIM}">CUFF PRESSURE, FIRST TAPS − CUFF PRESSURE, EVERY BEAT</text>' \
        f'<text id="Equation" x="{RX5}" y="420" font-size="72" font-weight="700" fill="{FG}">132 − 116 = 16 mmHg</text>' \
        f'<text id="Threshold" x="{RX5}" y="540" font-size="44" font-weight="700" fill="{ACC}">&gt; 10 mmHg = PULSUS PARADOXUS</text></g>'
    rules = [("Rule_1", "inspiration → systolic dips", False), ("Rule_2", "tight pericardium / straining chest → dip grows", False),
             ("Rule_3", "effusion + pulsus paradoxus → think TAMPONADE", True)]
    F["5F"] = "".join(f'<g id="{g}"><rect x="240" y="{300 + i*190}" width="10" height="120" fill="{ACC if a else GREY}"/>'
                      f'<text x="290" y="{378 + i*190}" font-size="56" font-weight="{700 if a else 300}" fill="{ACC if a else FG}">{t}</text></g>'
                      for i, (g, t, a) in enumerate(rules))
    return F


NAMES = {"1A": "1A_cuff", "1A_mid": "1A_mid", "1B": "1B_title", "1C": "1C_promise", "2A": "2A_inhale", "2B": "2B_rv-fills", "2C": "2C_lungs-hold",
         "2D": "2D_lv-dips", "2E": "2E_threshold", "3A": "3A_effusion", "3A_start": "3A_start", "3A_anatomy": "3A_anatomy", "3B": "3B_septum-bows", "3C": "3C_interdependence",
         "3D": "3D_clinical", "3E": "3E_pulse-pressure", "4A": "4A_airways", "4B": "4B_suction", "4C": "4C_afterload",
         "5A": "5A_setup", "5B": "5B_deflate", "5C": "5C_first-taps", "5D": "5D_every-beat", "5E": "5E_difference", "5F": "5F_recap"}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for k, body in frames().items():
        open(os.path.join(out, NAMES[k] + ".svg"), "w").write(svg(k.replace("_start", " · 0 s").replace("_anatomy", " · 1.5 s").replace("_mid", " · 8.6 s"), body))
    print(len(NAMES), "frames")
