"""Final-quality axial thorax (Scenes 2 and 4) and coronal diaphragm, Pulsus Paradoxus, style C.

Modeled on Mark's thorax cross-section reference (assets/reference/thorax_cross-section.jpg), viewed from below:
patient's right on the viewer's left. Same call signature and group names as the rough chest() in keyframes.py, so the
motion notes keep working; new detail lives in new sublayers.

Layer tree (Group/Sublayer, as the motion notes use them):
  Chest                       whole section; scales on inspiration (chest-wall expansion)
    Skin, Fat, Muscles        body wall from outside in (Muscles/Septa = fascial lines between muscles)
    Cavity                    pleural cavity floor (dark)
    Lungs/R, Lungs/L          each: Lobe, Fissure, Vessels (branching + cut vessels), Bronchi
    Wall                      inner chest wall over the lung edges; Pleura line on its inner edge
    Ribs, Costal_cartilage, Sternum, Spine, Descending_aorta, Esophagus, Azygos
    Hilum/R, Hilum/L          bronchus + artery + vein at each lung root
    Pulmonary_arteries        trunk and both branches, heart base to hila
  Pericardium, Heart          from heart_group() (unchanged)
  Flow                        venous / pulmonary dot paths (unchanged names)
"""
import math, random

CX, CY = 760, 560
SKIN, FAT, FAT_LINE = "#252629", "#1D1E20", "#2A2B2E"
MUSCLE, FIBER, SEPTUM = "#2B2C2F", "#343539", "#45464A"
SLIME = "#9BD63A"   # inflammation / mucus in narrowed airways (Mark 2026-10-23)
CAV, LUNG, LUNG_TEX = "#141516", "#27282C", "#303135"
MEDIA_FILL = "#1E1F21"
BONE, MARROW, CART = "#3B3C40", "#4A4B50", "#33363A"


def superellipse(cx, cy, a, b, n, steps=180, mod=None):
    pts = []
    for i in range(steps):
        t = 2 * math.pi * i / steps
        c, s = math.cos(t), math.sin(t)
        x = cx + a * math.copysign(abs(c) ** (2 / n), c)
        y = cy + b * math.copysign(abs(s) ** (2 / n), s)
        if mod:
            x, y = mod(x, y)
        pts.append((x, y))
    return pts


def smooth(pts, closed=True):
    """Catmull-Rom through points -> cubic Bezier path."""
    n = len(pts)
    q = pts if closed else [pts[0]] + pts + [pts[-1]]
    d = f"M{q[0][0]:.1f} {q[0][1]:.1f}" if closed else f"M{pts[0][0]:.1f} {pts[0][1]:.1f}"
    rng = range(n) if closed else range(1, len(q) - 2)
    for k in rng:
        if closed:
            a, b, c, e = pts[(k - 1) % n], pts[k], pts[(k + 1) % n], pts[(k + 2) % n]
        else:
            a, b, c, e = q[k - 1], q[k], q[k + 1], q[k + 2]
        d += (f" C{b[0] + (c[0] - a[0]) / 6:.1f} {b[1] + (c[1] - a[1]) / 6:.1f} "
              f"{c[0] - (e[0] - b[0]) / 6:.1f} {c[1] - (e[1] - b[1]) / 6:.1f} {c[0]:.1f} {c[1]:.1f}")
    return d + (" Z" if closed else "")


def body_mod(depth_front=26, bulge_back=16):
    def mod(x, y):
        if y < CY:   # anterior: notch at the sternum, flatter shoulders
            y += depth_front * math.exp(-((x - CX) / 70) ** 2)
        else:        # posterior: paraspinal bulges either side, groove at the spine
            y += bulge_back * (math.exp(-((x - 640) / 95) ** 2) + math.exp(-((x - 880) / 95) ** 2))
            y -= 14 * math.exp(-((x - CX) / 30) ** 2)
        return x, y
    return mod


BODY = superellipse(CX, CY, 625, 415, 3.0, mod=body_mod())
FAT_IN = superellipse(CX, CY, 585, 378, 2.9, mod=body_mod(22, 12))
MUSC_IN = superellipse(CX, CY + 2, 538, 336, 2.7, mod=body_mod(10, 0))


def cavity_pts():
    def mod(x, y):
        if y > CY:   # posterior gutter: the cavity wraps round the spine
            y -= 120 * math.exp(-((x - CX) / 62) ** 2)
        else:
            y += 22 * math.exp(-((x - CX) / 80) ** 2)
        return x, y
    return superellipse(CX, CY - 10, 508, 318, 2.6, mod=mod)


CAVITY = cavity_pts()

# lungs: medial borders follow the heart (x 594-943, y 261-583 at this scale), the hila and the posterior mediastinum
LUNG_R = [(585, 248), (470, 232), (360, 258), (290, 318), (258, 410), (252, 520), (266, 630), (305, 735), (380, 812),
          (490, 852), (600, 860), (668, 838), (688, 790), (676, 735), (650, 690), (628, 655), (600, 625), (583, 585),
          (575, 520), (570, 440), (572, 340)]
LUNG_L = [(950, 250), (1060, 232), (1165, 258), (1232, 318), (1264, 410), (1270, 520), (1256, 630), (1218, 735),
          (1142, 812), (1030, 852), (918, 860), (878, 838), (880, 800), (902, 740), (912, 700), (902, 662), (930, 625),
          (958, 580), (968, 510), (966, 420), (958, 330)]
HILUM_R, HILUM_L = (640, 660), (900, 662)


def path_d(pts):
    return "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + " Z"


def fat_lobules(rng):
    out = []
    for i in range(140):
        t = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.1, 0.9)
        a = BODY[int(t / (2 * math.pi) * len(BODY)) % len(BODY)]
        b = FAT_IN[int(t / (2 * math.pi) * len(FAT_IN)) % len(FAT_IN)]
        x, y = a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r
        rx, ry = rng.uniform(6, 13), rng.uniform(4, 8)
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rx:.0f}" ry="{ry:.0f}" transform="rotate({math.degrees(t)+90:.0f} {x:.0f} {y:.0f})"/>')
    return "".join(out)


def muscle_fibers(rng):
    out = []
    for i in range(260):
        t = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.15, 0.85)
        k = int(t / (2 * math.pi) * len(FAT_IN)) % len(FAT_IN)
        a, b = FAT_IN[k], MUSC_IN[k]
        x, y = a[0] + (b[0] - a[0]) * r, a[1] + (b[1] - a[1]) * r
        ang = math.degrees(t) + 90 + rng.uniform(-25, 25)
        L = rng.uniform(10, 22)
        dx, dy = L * math.cos(math.radians(ang)), L * math.sin(math.radians(ang))
        out.append(f'<path d="M{x-dx/2:.0f} {y-dy/2:.0f} q{dx/2+3:.0f} {dy/2-3:.0f} {dx:.0f} {dy:.0f}"/>')
    return "".join(out)


def septa():
    # fascial planes between pectoralis, serratus/latissimus and paraspinal groups (by angle round the wall)
    out = []
    for deg in (-118, -62, -152, -28, 160, 20, 118, 62, 100, 80):
        t = math.radians(deg)
        k = int(((t % (2 * math.pi)) / (2 * math.pi)) * len(FAT_IN)) % len(FAT_IN)
        a, b = FAT_IN[k], MUSC_IN[k]
        out.append(f'<path d="M{a[0]:.0f} {a[1]:.0f} Q{(a[0]+b[0])/2+6:.0f} {(a[1]+b[1])/2-6:.0f} {b[0]:.0f} {b[1]:.0f}"/>')
    return "".join(out)


def media_lobules(rng):
    out = []
    for i in range(90):
        x, y = rng.uniform(560, 960), rng.uniform(220, 800)
        out.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{rng.uniform(7,13):.0f}" ry="{rng.uniform(4,8):.0f}" transform="rotate({rng.uniform(0,180):.0f} {x:.0f} {y:.0f})"/>')
    return "".join(out)


def ribs():
    out = []
    ring = superellipse(CX, CY - 4, 528, 328, 2.7, mod=body_mod(8, 0))
    angles = [-150, -132, -112, -68, -48, -30, -8, 8, 28, 50, 72, 108, 130, 152, 172, -172]
    for deg in angles:
        t = math.radians(deg)
        k = int(((t % (2 * math.pi)) / (2 * math.pi)) * len(ring)) % len(ring)
        x, y = ring[k]
        x2, y2 = ring[(k + 1) % len(ring)]
        rot = math.degrees(math.atan2(y2 - y, x2 - x))
        out.append(f'<g transform="translate({x:.0f} {y:.0f}) rotate({rot:.0f})"><ellipse rx="26" ry="10" fill="{BONE}" stroke="#55565B" stroke-width="1.4"/>'
                   f'<ellipse rx="18" ry="5" fill="{MARROW}" opacity="0.6"/></g>')
    # rib heads beside the vertebra
    for sgn in (-1, 1):
        x = CX + sgn * 92
        out.append(f'<ellipse cx="{x}" cy="808" rx="24" ry="11" transform="rotate({sgn*-20} {x} 808)" fill="{BONE}" stroke="#55565B" stroke-width="1.4"/>')
    return "".join(out)


def sternum_and_cartilage():
    s = (f'<g id="Costal_cartilage" fill="{CART}" stroke="#4E5054" stroke-width="1.2">'
         f'<path d="M705 214 Q640 222 560 236 L556 250 Q640 238 706 232 Z"/>'
         f'<path d="M815 214 Q880 222 960 236 L964 250 Q880 238 814 232 Z"/></g>'
         f'<g id="Sternum"><rect x="706" y="206" width="108" height="30" rx="8" fill="{BONE}" stroke="#55565B" stroke-width="1.5"/>'
         f'<rect x="716" y="213" width="88" height="16" rx="5" fill="{MARROW}" opacity="0.55"/></g>')
    return s


def spine():
    return (f'<g id="Spine" transform="translate(0 -34)">'
            f'<path id="Vertebra" d="M708 820 C708 784 812 784 812 820 C812 858 796 878 760 878 C724 878 708 858 708 820 Z" fill="{BONE}" stroke="#55565B" stroke-width="1.6"/>'
            f'<path d="M722 822 C722 798 798 798 798 822 C798 848 786 864 760 864 C734 864 722 848 722 822 Z" fill="{MARROW}" opacity="0.5"/>'
            f'<path id="Posterior_arch" d="M728 878 L716 912 L688 918 L686 930 L722 926 L748 958 L760 990 L772 958 L798 926 L834 930 L832 918 L804 912 L792 878 Z" '
            f'fill="{BONE}" stroke="#55565B" stroke-width="1.6"/>'
            f'<circle id="Spinal_canal" cx="760" cy="902" r="15" fill="{CAV}" stroke="#55565B" stroke-width="1.2"/>'
            f'<circle cx="760" cy="902" r="7" fill="#2E2F33"/></g>')


# mediastinum (Mark 2026-10-24, from his axial reference): the heart sits just behind the sternum and the lungs wrap
# tightly round it; behind the heart only the oesophagus and descending aorta sit in front of the spine.
HCX, HCY, HS = 775, 506, 0.92   # Mark 2026-10-24 (his SVG edit): the heart spans the mediastinum, just behind the sternum down to the spine


def _media_pts():
    import sys, os, re
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from gen import heart
    sac = heart(HCX, HCY, HS, bow=0.0, fluid=0)["fat"]        # the epicardium (red line) itself
    pts = [tuple(map(float, m)) for m in re.findall(r"(-?[\d.]+),(-?[\d.]+)", sac)]
    out = []
    for x, y in pts:                                   # the heart outline itself (+3 units for the stroke)
        dx, dy = x - HCX, y - HCY; r = math.hypot(dx, dy) or 1
        ox, oy = x + dx / r * 3, y + dy / r * 3      # Mark 2026-10-24: no gap, the lungs mould to the heart
        out.append((ox, oy))
    out.sort(key=lambda p: math.atan2(p[1] - HCY, p[0] - HCX))   # clockwise from the left-bottom, over the top, to the right-bottom
    i0 = max(range(len(out)), key=lambda i: out[i][1] if out[i][0] < HCX else -1)
    out = out[i0:] + out[:i0]
    # Mark 2026-10-24: no mediastinal space at all; the lungs fill everything round the heart (oesophagus and aorta drawn over them)
    return out[::6]


MEDIA = _media_pts()
HILUM_R, HILUM_L = (640, 648), (902, 640)


def _inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-9) + x1:
            c = not c
    return c


def in_lung(k, x, y, margin=12):
    if (x - CX) * k <= margin or not _inside(CAVITY, x, y):
        return False
    for dx, dy in ((0, 0), (margin, 0), (-margin, 0), (0, margin), (0, -margin)):
        if _inside(MEDIA, x + dx, y + dy) or not _inside(CAVITY, x + dx, y + dy):
            return False
    return True


def lung(gid, k, hil, ls, hi_vessels, hi_bronchi, narrow, seed, bronchi=True):
    """One lung = the pleural cavity on its side of the midline; the mediastinum is drawn over it, so the lung
    fills every space the mediastinum doesn't. Vessels and airways are clipped to the cavity half."""
    from gen import ACC
    rng = random.Random(seed)
    vcol, vw = (ACC, 8.5) if hi_vessels else ("#64656A", 3.4)   # 2C: highlighted vessels drawn dilated, exaggerated (Mark 2026-10-24)
    bcol = "#F2F2F2" if hi_bronchi else "#8A8B8C"   # airways highlight in white; red stays for blood (Mark 2026-10-23)
    tree = []

    # Mark 2026-10-25: vessel trees symmetric left/right and reaching close to the lung edges. Each tree starts at the hilum
    # (the heart's lateral border, slightly posterior) and every segment is sized from the room left to the lung edge along
    # its direction, so both lungs fill to their margins whatever their size.
    def room(x, y, ang):
        d = 0.0
        while d < 700:
            if not in_lung(k, x + (d + 6) * math.cos(ang), y + (d + 6) * math.sin(ang), 5):
                return d
            d += 6
        return d

    def branch(x, y, ang, w, depth):
        r = room(x, y, ang)
        if r < 14 or depth == 0:
            return
        L = r * (0.88 if depth == 1 or r < 60 else rng.uniform(0.40, 0.52))
        x2, y2 = x + L * math.cos(ang), y + L * math.sin(ang)
        mx, my = (x + x2) / 2 + rng.uniform(-6, 6), (y + y2) / 2 + rng.uniform(-6, 6)
        tree.append((f"M{x:.0f} {y:.0f} Q{mx:.0f} {my:.0f} {x2:.0f} {y2:.0f}", w))
        if r < 60:
            return
        for da in (-0.40, 0.40):
            branch(x2, y2, ang + da + rng.uniform(-0.10, 0.10), max(w * 0.68, 0.35), depth - 1)

    hx, hy = hil
    # the hilum: lateral edge of the heart outline at hilar height, just outside it
    band = [p for p in MEDIA if HCY - 10 <= p[1] <= HCY + 120]
    ex = min(band, key=lambda p: p[0] * -k) if k < 0 else max(band, key=lambda p: p[0])
    hx, hy = ex[0] + k * 8, ex[1]
    while not in_lung(k, hx, hy, 5) and abs(hx - CX) < 700:
        hx += k * 4
    # spread the trunks over every direction that has room, evenly
    cand = [i * math.pi / 36 for i in range(72)]
    ok = [t for t in cand if room(hx, hy, t) > 70]
    # contiguous arc of free directions (they wrap round the lateral side), then 7 evenly spaced trunks inside it
    lat = 0.0 if k > 0 else math.pi
    ok.sort(key=lambda t: (t - lat + math.pi) % (2 * math.pi) - math.pi)
    rel = [((t - lat + math.pi) % (2 * math.pi)) - math.pi for t in ok]
    lo, hi_ = min(rel), max(rel)
    for i in range(7):
        t = lat + lo + (hi_ - lo) * (i + 0.5) / 7
        branch(hx, hy, t + rng.uniform(-0.05, 0.05), 1.0, 5)
    vessels = "".join(f'<path d="{p}" stroke-width="{vw*w:.1f}"/>' for p, w in tree)
    cuts, airways, tex, infl = [], [], [], []
    tries = 0
    while len(cuts) < 30 and tries < 4000:
        tries += 1
        x, y = rng.uniform(CX + k * 20, CX + k * 520), rng.uniform(230, 860)
        if in_lung(k, x, y, 16) and math.hypot(x - hil[0], y - hil[1]) > 50:
            r = rng.uniform(3, 7.5)
            cuts.append(f'<ellipse cx="{x:.0f}" cy="{y:.0f}" rx="{r:.1f}" ry="{r*rng.uniform(0.6,1):.1f}" fill="#45464B" stroke="none"/>')
            if len(airways) < 10 and rng.random() < 0.4 and in_lung(k, x + r + 12, y, 14):
                ar = r + 3.5
                if narrow:
                    infl.append(f'<circle cx="{x+ar+4:.0f}" cy="{y:.0f}" r="{ar+7:.1f}" fill="{SLIME}" opacity="0.45" filter="url(#slimeblur)"/>'
                                f'<circle cx="{x+ar+4:.0f}" cy="{y:.0f}" r="{ar*0.62:.1f}" fill="{SLIME}" opacity="0.85"/>')
                airways.append(f'<circle cx="{x+ar+4:.0f}" cy="{y:.0f}" r="{ar:.1f}" fill="none" stroke="{bcol}" stroke-width="{4 if narrow else 3}"/>'
                               f'<circle cx="{x+ar+4:.0f}" cy="{y:.0f}" r="{ar*(0.35 if narrow else 0.62):.1f}" fill="{CAV}"/>'
                               + (cartilage_plates(x + ar + 4, y, ar * 0.8) if ar >= 8.5 else ""))
    while len(tex) < 90:
        x, y = rng.uniform(CX + k * 20, CX + k * 520), rng.uniform(230, 860)
        if in_lung(k, x, y, 8):
            tex.append(f"M{x:.0f} {y:.0f} q4 -5 8 0 t8 0")
    fiss = ("M250 575 C340 560 430 585 520 620 C560 636 600 646 640 650" if k < 0 else
            "M1270 575 C1180 560 1095 585 1010 620 C975 636 940 642 902 642")
    half = (f'<rect x="{0 if k < 0 else CX}" y="0" width="{CX}" height="1200"/>')
    return (f'<clipPath id="lunghalf{gid}">{half}</clipPath>'
            f'<g id="Lungs/{gid}" clip-path="url(#lunghalf{gid})"><g transform="translate({hil[0]} {hil[1]}) scale({ls:.3f}) translate({-hil[0]} {-hil[1]})">'
            f'<path id="Lobe" d="{smooth(CAVITY)}" fill="{LUNG}"/>'
            f'<path id="Texture" d="{" ".join(tex)}" fill="none" stroke="{LUNG_TEX}" stroke-width="1.2"/>'
            f'<path id="Fissure" d="{fiss}" fill="none" stroke="#4A4B50" stroke-width="2.4" stroke-linecap="round"/>'
            f'<g id="Vessels" fill="none" stroke="{vcol}" stroke-linecap="round">{vessels}{"".join(cuts)}</g>' +
            (f'<g id="Bronchi">{"".join(airways)}</g>' if bronchi else '') + '</g></g>',   # Scene 2 has no airway rings (Mark 2026-10-25)
            f'<g id="Inflammation/{gid}" clip-path="url(#lunghalf{gid})"><g transform="translate({hil[0]} {hil[1]}) scale({ls:.3f}) translate({-hil[0]} {-hil[1]})">{"".join(infl)}</g></g>')


TRUNK_TOP = 516          # pulmonary trunk now runs up under the heart (Mark 2026-10-24: it read as separated from the heart)
CART_COL = "#C9CACD"     # airway cartilage (Mark 2026-10-24: cartilage rings mark the larger airways)


def cartilage_c(cx, cy, r, w):
    """C-shaped cartilage ring in a bronchus wall, open at the back (posterior = down in this view)."""
    a0, a1 = math.radians(120), math.radians(420)        # 300 degrees of ring, gap centred on 90 deg (down)
    p0 = (cx + r * math.cos(a0), cy + r * math.sin(a0)); p1 = (cx + r * math.cos(a1), cy + r * math.sin(a1))
    return (f'<path d="M{p0[0]:.1f} {p0[1]:.1f} A{r} {r} 0 1 1 {p1[0]:.1f} {p1[1]:.1f}" fill="none" stroke="{CART_COL}" '
            f'stroke-width="{w}" stroke-linecap="round"/>')


def cartilage_plates(cx, cy, r):
    """Smaller bronchi: irregular cartilage plates in the wall instead of full rings."""
    o = []
    for a_deg, span in ((15, 70), (125, 60), (215, 80), (315, 30)):
        a0, a1 = math.radians(a_deg), math.radians(a_deg + span)
        o.append(f'M{cx + r*math.cos(a0):.1f} {cy + r*math.sin(a0):.1f} A{r:.1f} {r:.1f} 0 0 1 {cx + r*math.cos(a1):.1f} {cy + r*math.sin(a1):.1f}')
    return f'<path d="{" ".join(o)}" fill="none" stroke="{CART_COL}" stroke-width="1.8" stroke-linecap="round"/>'


def hilum(gid, x, y, k, hi_bronchi, narrow):
    from gen import ACC
    bcol = "#F2F2F2" if hi_bronchi else "#9A9B9E"
    lumen = 5 if narrow else 8
    infl = (f'<circle cx="{x + k*6:.0f}" cy="{y + 14:.0f}" r="25" fill="{SLIME}" opacity="0.45" filter="url(#slimeblur)"/>' if narrow else "")
    mucus = (f'<circle cx="{x + k*6:.0f}" cy="{y + 14:.0f}" r="{lumen*0.8:.1f}" fill="{SLIME}" opacity="0.85"/>' if narrow else "")
    return (f'<g id="Hilum/{gid}">{infl}<circle id="Bronchus" cx="{x + k*6:.0f}" cy="{y + 14:.0f}" r="17" fill="#4A4B50" stroke="{bcol}" stroke-width="2.5"/>'
            f'{cartilage_c(x + k*6, y + 14, 12.5, 3.6)}'
            f'<circle cx="{x + k*6:.0f}" cy="{y + 14:.0f}" r="{lumen}" fill="{CAV}"/>{mucus}'
            f'<circle id="Artery" cx="{x - k*14:.0f}" cy="{y - 8:.0f}" r="12" fill="#3A3B40" stroke="#6A6B70" stroke-width="1.5"/>'
            f'<circle id="Vein" cx="{x + k*22:.0f}" cy="{y - 14:.0f}" r="9" fill="#303136" stroke="#5A5B60" stroke-width="1.2"/></g>')


def thorax(insp=0.0, deep=False, hi_vessels=False, narrow=False, hi_bronchi=False, chest_scale=1.0, bronchi=True):
    """Everything in the Chest group except the heart and flow (those stay in keyframes.chest)."""
    ex = 1 + 0.045 * insp * (1.5 if deep else 1)
    ls = 1 + 0.07 * insp * (1.4 if deep else 1)
    rng = random.Random(7)
    LR = lung("R", -1, HILUM_R, ls, hi_vessels, hi_bronchi, narrow, 11, bronchi)
    LL = lung("L", 1, HILUM_L, ls, hi_vessels, hi_bronchi, narrow, 23, bronchi)
    wall = path_d(MUSC_IN) + " " + path_d(CAVITY)
    o = [f'<g id="Chest" transform="translate({CX} {CY}) scale({chest_scale * ex:.3f}) translate({-CX} {-CY})">',
         f'<path id="Skin" d="{smooth(BODY)}" fill="{SKIN}" stroke="#4A4B4C" stroke-width="3"/>',
         f'<g id="Fat"><path d="{smooth(FAT_IN)}" fill="{FAT}"/></g>',
         f'<g id="Fat_lobules" fill="none" stroke="{FAT_LINE}" stroke-width="1.2" clip-path="url(#fatring)">{fat_lobules(rng)}</g>',
         f'<g id="Muscles"><path d="{smooth(FAT_IN)}" fill="{MUSCLE}" stroke="#3A3B3F" stroke-width="1.5"/>'
         f'<g id="Muscles/Fibers" fill="none" stroke="{FIBER}" stroke-width="1.3" stroke-linecap="round">{muscle_fibers(rng)}</g>'
         f'<g id="Muscles/Septa" fill="none" stroke="{SEPTUM}" stroke-width="1.6">{septa()}</g></g>',
         f'<path id="Cavity" d="{smooth(CAVITY)}" fill="#1B1C1E"/>',
         f'<g id="Lungs" clip-path="url(#cavityclip)" opacity="{1.0 if (hi_vessels or hi_bronchi) else 0.4}">'
         f'{LR[0]}{LL[0]}</g>',
         f'<g id="Inflammation" clip-path="url(#cavityclip)">{LR[1]}{LL[1]}</g>' if narrow else '',
         # Mark 2026-10-25: the mediastinum is the heart's outline and the heart doesn't scale with the breath, so it is
         # counter-scaled here; otherwise inspiration (chest x1.045) opened a dark ring between the lungs and the heart
         f'<g id="Mediastinum" transform="translate({CX} {CY}) scale({1 / (chest_scale * ex):.4f}) translate({-CX} {-CY})"><path id="Mediastinal_fat" d="{smooth(MEDIA)}" fill="{MEDIA_FILL}" stroke="#6A6B70" stroke-width="2"/>'
         f'<g fill="none" stroke="#26272A" stroke-width="1.2" clip-path="url(#mediaclip)">{media_lobules(rng)}</g></g>',
         f'<g id="Wall"><path d="{wall}" fill="{MUSCLE}" fill-rule="evenodd"/>'
         f'<path id="Pleura" d="{smooth(CAVITY)}" fill="none" stroke="#6A6B70" stroke-width="1.6"/></g>',
         f'<g id="Ribs">{ribs()}</g>',
         sternum_and_cartilage(),
         spine(),
         f'<g id="Esophagus"><ellipse cx="736" cy="712" rx="17" ry="12" fill="#2E2F33" stroke="#5A5B60" stroke-width="1.5"/>'
         f'<path d="M727 712 l5 -3 l4 4 l4 -4 l5 3 l-5 3 l-4 -4 l-4 4 Z" fill="{CAV}"/></g>',
         f'<g id="Descending_aorta"><circle cx="812" cy="706" r="19" fill="#3A3B40" stroke="#7A7B80" stroke-width="1.8"/><circle cx="812" cy="706" r="11" fill="#2A2B2F"/></g>',
         "</g>"]
    defs = (f'<defs><filter id="slimeblur" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3.5"/></filter><clipPath id="cavityclip"><path d="{smooth(CAVITY)}"/></clipPath><clipPath id="mediaclip"><path d="{smooth(MEDIA)}"/></clipPath>'
            f'<clipPath id="fatring"><path d="{path_d(BODY)} {path_d(FAT_IN)}" clip-rule="evenodd"/></clipPath></defs>')
    return defs + "".join(o)
