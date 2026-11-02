"""Mark, Oct 23: heart muscle greyer pink, with faint muscle striations through the LV wall and RV free wall."""
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "keyframes_gen.py")
s = open(p).read()
def rep(old, new, count=1):
    global s
    assert s.count(old) == count, (s.count(old), old[:70])
    s = s.replace(old, new)
rep('MYO, CAV, LINE = "#C9B6B9", "#141414", "#4A4B4C"   # MYO: light pink-grey myocardium (Mark 2026-10-23)\nMYO_LINE, FAT = "#9E8A8E", "#B3A0A4"',
    'MYO, CAV, LINE = "#A6979A", "#141414", "#4A4B4C"   # MYO: grey-pink myocardium (Mark 2026-10-23)\nMYO_LINE, FAT, FIBRE = "#7D6F72", "#958689", "#7A6B6E"')
rep('from style_frames_gen import heart, gauge, W, H, BG, FG, ACC, GREY, FONT',
    'from style_frames_gen import heart, radii, gauge, W, H, BG, FG, ACC, GREY, FONT')
rep('''def heart_in_sac(''', '''def striations(cx, cy, s):
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
    return f'<g id="Myocardium_striations" fill="none" stroke="{FIBRE}" stroke-width="{w:.1f}" stroke-linecap="round" stroke-opacity="0.55">{out}</g>'


def heart_in_sac(''')
rep('''f'<path id="RV" d="{h["rv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>\'''',
    '''+ striations(cx, cy, s) +
                      f'<path id="RV" d="{h["rv"]}" fill="{CAV}" stroke="{MYO_LINE}" stroke-width="2" stroke-linejoin="round"/>\'''')
open(p, "w").write(s)
print("patched", len(s))
