"""Applies Mark's Oct 23 key frame notes to keyframes_gen.py: level traces (1B, 2A), pink-grey myocardium,
sac/epicardium labels and chest-wall electrode (scene 3), patient from Mark's silhouette (scene 5)."""
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "keyframes_gen.py")
s = open(p).read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)
SIL = "M71 1000 L65 1000 L59 996 L48 985 L41 973 L27 960 L26 956 L27 945 L30 937 L29 922 L32 906 L32 890 L19 806 L18 785 L23 747 L17 717 L17 644 L6 594 L4 532 L2 529 L-3 530 L-5 532 L-4 567 L-16 648 L-17 679 L-27 722 L-25 754 L-27 807 L-32 854 L-37 884 L-37 900 L-34 919 L-36 943 L-34 950 L-35 958 L-47 971 L-54 987 L-67 998 L-74 998 L-82 995 L-93 995 L-103 993 L-109 990 L-112 983 L-112 977 L-108 970 L-99 959 L-83 945 L-73 927 L-73 906 L-88 814 L-90 779 L-89 748 L-84 721 L-86 700 L-85 673 L-96 623 L-104 569 L-103 509 L-96 462 L-81 404 L-79 378 L-78 358 L-81 337 L-88 314 L-90 312 L-93 314 L-98 332 L-96 354 L-99 391 L-117 445 L-126 466 L-133 491 L-133 495 L-123 507 L-114 522 L-109 540 L-109 554 L-112 560 L-118 560 L-121 554 L-122 544 L-125 545 L-129 561 L-130 588 L-132 594 L-138 597 L-142 603 L-145 603 L-149 597 L-154 595 L-156 589 L-162 582 L-165 549 L-163 501 L-164 450 L-163 424 L-152 364 L-142 338 L-138 320 L-137 236 L-132 203 L-126 190 L-112 176 L-89 164 L-59 156 L-45 147 L-38 140 L-35 134 L-35 122 L-41 112 L-45 100 L-52 92 L-55 80 L-56 67 L-49 62 L-51 49 L-50 32 L-45 20 L-35 10 L-22 3 L-7 -0 L14 2 L24 6 L35 15 L42 28 L45 44 L44 65 L52 68 L52 81 L48 92 L41 100 L37 113 L32 120 L33 127 L40 141 L46 147 L56 153 L102 167 L113 171 L125 183 L132 201 L134 224 L135 293 L140 328 L147 357 L148 458 L155 482 L155 500 L165 529 L165 548 L162 559 L157 570 L139 588 L131 591 L126 591 L123 585 L128 574 L131 564 L127 536 L124 533 L119 535 L120 552 L117 555 L113 554 L110 550 L107 539 L109 519 L121 490 L122 485 L116 461 L102 422 L96 399 L92 370 L92 331 L89 318 L86 329 L81 417 L96 464 L104 553 L93 627 L78 692 L78 723 L82 769 L76 834 L66 895 L65 931 L79 953 L99 976 L101 980 L101 986 L98 991 L89 998 L71 1000 Z"

rep('MYO, CAV, LINE = "#26272A", "#141414", "#4A4B4C"',
    'MYO, CAV, LINE = "#C9B6B9", "#141414", "#4A4B4C"   # MYO: light pink-grey myocardium (Mark 2026-10-23)\nMYO_LINE, FAT = "#9E8A8E", "#B3A0A4"')
rep('''f'<path id="Epicardial_fat" d="{h["fat"]}" fill="#2E2C29"/>'
                      f'<path id="Myocardium" d="{h["outline"]}" fill="{MYO}" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      f'<path id="RV" d="{h["rv"]}" fill="{CAV}" stroke="{LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      f'<path id="LV" d="{h["lv"]}" fill="{CAV}" stroke="{LINE}" stroke-width="2"/>\'''',
    '''f'<path id="Epicardial_fat" d="{h["fat"]}" fill="{FAT}"/>'
                      f'<path id="Myocardium" d="{h["outline"]}" fill="{MYO}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      f'<path id="RV" d="{h["rv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>'
                      f'<path id="LV" d="{h["lv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2"/>\'''')
rep('''stroke="{ACC}" stroke-width="3" stroke-opacity="0.55"/>\'''', '''stroke="{ACC}" stroke-width="3.5" stroke-opacity="0.95"/>\'''')

rep(''', extra=' transform="rotate(-2 960 790)"')''', ')')

rep('pair, r1, r2 = big_pair(260, 1040, base, amp, second_rot=15, notch=True)', 'pair, r1, r2 = big_pair(260, 1040, base, amp, notch=True)')
old_axis = s[s.index('              + G("Axis", '):s.index('              + G("Shape", ')]
new_axis = '''              + G("Axis", axis_dial("Vector_1", r1, base + 170, 60, FG) + axis_dial("Vector_2", r2, base + 170, 45, ACC, ghost=60)
                  + T(r2 + 110, base + 182, "AXIS", 30, ACC, 700, "start", 3))
'''
s = s.replace(old_axis, new_axis)
rep('''def big_pair(''', '''def axis_dial(gid, cx, cy, deg, col, ghost=None, r=70):
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


def big_pair(''')

rep('''def electrode(x, y, label="V5"):''', '''CW_R, CW_A0, CW_A1, EL_A = 560, -80, -12, -42      # chest wall arc around the heart (px, degrees); electrode angle


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


def electrode(x, y, label="V5"):''')

rep('''    hs, _, h0 = heart_in_sac(SC_CX, SC_CY, SC_S, fluid=120)
    fx, fy = h0["anchors"]["fluid"]
    lab = G("Labels", f'<line x1="1240" y1="430" x2="{fx:.0f}" y2="{fy:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                      f'<circle cx="{fx:.0f}" cy="{fy:.0f}" r="5" fill="{EFF}"/>' + T(1250, 440, "pericardial effusion", 34, EFF, 700))
    return G("Cross_section", hs) + electrode(1420, 190) + lab + T(80, 120, "a heart swinging in a bag of fluid", 30, DIM)''',
'''    fl = 120
    hs, _, h0 = heart_in_sac(SC_CX, SC_CY, SC_S, fluid=fl)
    P = lambda th, r: (SC_CX + r * SC_S * math.cos(math.radians(th)), SC_CY + r * SC_S * math.sin(math.radians(th)))
    sac_pt, epi_pt, flu_pt = P(-6, 236 + 12 + fl), P(14, 236 + 12), P(36, 236 + 12 + fl / 2)
    def leader(gid, pt, ly, text, col):
        return G(gid, f'<line x1="1240" y1="{ly - 9}" x2="{pt[0]:.0f}" y2="{pt[1]:.0f}" stroke="{GREY}" stroke-width="1.5"/>'
                      f'<circle cx="{pt[0]:.0f}" cy="{pt[1]:.0f}" r="6" fill="{col}"/>' + T(1250, ly, text, 34, col, 700))
    lab = G("Labels", leader("Sac_label", sac_pt, 430, "pericardial sac", FG) + leader("Epicardium_label", epi_pt, 530, "epicardium", ACC)
            + leader("Effusion_label", flu_pt, 630, "pericardial effusion", EFF))
    cw, _ = chest_wall(SC_CX, SC_CY)
    return G("Cross_section", hs) + cw + lab + T(80, 120, "a heart swinging in a bag of fluid", 30, DIM)''')

rep('''    ex, ey = 1420, 190
    hx, hy = rot(SC_CX, SC_CY, ang, px, py)''', '''    cw, (ex, ey) = chest_wall(SC_CX, SC_CY)
    hx, hy = rot(SC_CX, SC_CY, ang, px, py)''')
rep('''    return G("Cross_section", hs) + electrode(ex, ey) + vec + labels + s''', '''    return G("Cross_section", hs) + cw + vec + labels + s''')
rep('''    tipx, tipy = SC_CX + 230 * SC_S * 0.92, SC_CY - 236 * SC_S * 0.82
    needle = G("Needle", f'<line x1="1180" y1="110" x2="{tipx:.0f}" y2="{tipy:.0f}" stroke="{FG}" stroke-width="5" stroke-linecap="round"/>'
                         f'<rect x="1170" y="80" width="140" height="48" rx="6" fill="{CARD}" stroke="{FG}" stroke-width="2" transform="rotate(-35 1180 110)"/>')''',
'''    r_sac = (236 + 12 + 18) * SC_S
    tipx, tipy = SC_CX + r_sac * math.cos(math.radians(40)), SC_CY + r_sac * math.sin(math.radians(40))
    hx, hy = tipx + 300, tipy + 190
    needle = G("Needle", f'<line x1="{hx:.0f}" y1="{hy:.0f}" x2="{tipx:.0f}" y2="{tipy:.0f}" stroke="{FG}" stroke-width="5" stroke-linecap="round"/>'
                         f'<rect x="{hx - 10:.0f}" y="{hy - 24:.0f}" width="150" height="48" rx="6" fill="{CARD}" stroke="{FG}" stroke-width="2" transform="rotate(32 {hx:.0f} {hy:.0f})"/>')
    cw, _ = chest_wall(SC_CX, SC_CY)''')
rep('''    return G("Cross_section", hs) + electrode(1420, 190) + needle + s + T(1250, 470, "drained · swing stops", 34, DIM, 700)''',
    '''    return G("Cross_section", hs) + cw + needle + s + T(1250, 470, "drained · swing stops", 34, DIM, 700)''')

old_pat = s[s.index("def patient(cx=760, top=150, op=1.0):"):s.index("# ---------------- beats")]
new_pat = f'''SIL_PATH = "{SIL}"
SIL_K, SIL_TOP, PCX = 0.9, 110, 860          # silhouette path is 1000 units tall, x centred on 0


def ppt(x, y, cx=PCX):
    """Point on the patient, in silhouette units -> frame px."""
    return cx + x * SIL_K, SIL_TOP + y * SIL_K


def patient(cx=PCX, op=1.0):
    return G("Patient", f'<path d="{{SIL_PATH}}" transform="translate({{cx}} {{SIL_TOP}}) scale({{SIL_K}})" fill="#25262A" '
                        f'stroke="{{DIM}}" stroke-width="{{2.5 / SIL_K:.2f}}" stroke-linejoin="round"/>', f' opacity="{{op}}"')


'''
s = s.replace(old_pat, new_pat)

old_beck = s[s.index("def beck_icons(op=1.0, cx=760):"):s.index("@beat\ndef b_5A_bedside")]
new_beck = '''def beck_icons(op=1.0, cx=PCX):
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


'''
s = s.replace(old_beck, new_beck)
rep('''    triad = (patient() + beck_icons() + G("Title", T(760, 120, "BECK'S TRIAD", 56, FG, 700, "middle", 6))
             + G("Uncommon", f'<rect x="590" y="150" width="340" height="76" rx="6" fill="{BG}" stroke="{ACC}" stroke-width="4" transform="rotate(-6 760 188)"/>'
                 + T(760, 206, "UNCOMMON", 44, ACC, 700, "middle", 8, extra=' transform="rotate(-6 760 188)"')))''',
'''    triad = (patient() + beck_icons() + G("Title", T(PCX, 70, "BECK'S TRIAD", 56, FG, 700, "middle", 6))
             + G("Uncommon", f'<rect x="{PCX - 170}" y="96" width="340" height="76" rx="6" fill="{BG}" stroke="{ACC}" stroke-width="4" transform="rotate(-6 {PCX} 134)"/>'
                 + T(PCX, 152, "UNCOMMON", 44, ACC, 700, "middle", 8, extra=f' transform="rotate(-6 {PCX} 134)"')))''')
rep('''G("Beck", f'<g opacity="0.45">{triad}</g>', ' transform="translate(60 200) scale(0.6)"')''',
    '''G("Beck", f'<g opacity="0.45">{triad}</g>', ' transform="translate(20 300) scale(0.6)"')''')
rep('''patient() + T(1180, 300, "Is it being squeezed?", 52, FG, 300) + T(1180, 370, "the vitals", 32, DIM)''',
    '''patient() + T(1180, 420, "Is it being squeezed?", 52, FG, 300) + T(1180, 490, "the vitals", 32, DIM)''')
open(p, "w").write(s)
print("patched", len(s))
