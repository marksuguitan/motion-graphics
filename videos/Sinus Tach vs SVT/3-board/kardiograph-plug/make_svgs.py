"""Exports the Kardiograph plug graphics as clean, standalone SVGs (svg/), for reuse in Illustrator, Figma or AE.

    pip install fonttools brotli uharfbuzz   # once
    python3 make_svgs.py

Each file matches what the Remotion plugs draw (4-animation/remotion/src/plugs/kit.tsx, Opener.tsx, EndPlug.tsx):
same sizes in px at 1920x1080, same colors. Text is converted to outlines (Manrope / Inter, shaped with HarfBuzz),
so the files look right without the fonts installed. Groups have readable ids, which Illustrator shows as layer names.
Every ECG strip is lead II from Kardiograph's own engine (strips.json), at true scale: 25 mm/s, 10 mm/mV, 9.6 px/mm.
"""
import io
import json
import pathlib

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

here = pathlib.Path(__file__).parent
OUT = here / 'svg'
FONTS = (here / '../../../../library/remotion/public/fonts').resolve()
S = json.load(open(here / 'strips.json'))

# Colors (theme.ts + kit.tsx)
CORAL, CORAL_SOFT = '#E0574F', '#FCEBEA'
INK, INK2, DIVIDER, SOFT, TEAL, TEAL_SOFT = '#222222', '#6A6A6A', '#E6E4E0', '#F7F7F5', '#2E9C8F', '#E7F4F2'
GRID_MINOR, GRID_MAJOR = '#F6DEDB', '#EDBDB7'
MM, H_MM = 9.6, 30
WAVE = 'M2 12h3l2-6 3 12 3-9 2 3h7'
ICON = {
    'book': ['M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z', 'M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z'],
    'clipboard': ['M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2', 'm9 14 2 2 4-4',
                  'M9 2h6a1 1 0 0 1 1 1v2a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1z'],
    'rotate': ['M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8', 'M3 3v5h5'],
    'check': ['M20 6 9 17l-5-5'],
}
NAMES = {'sinus': 'Normal sinus rhythm', 'afib': 'Atrial fibrillation', 'flutter': 'Atrial flutter',
         'avb1': '1st-degree AV block', 'mobitz1': 'Mobitz I', 'svt': 'SVT'}
SHADOW = ('<defs><filter id="soft-shadow" x="-20%" y="-20%" width="140%" height="160%">'
          '<feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="#222222" flood-opacity="{o}"/></filter></defs>')


class Font:
    """A static instance of a variable web font, for shaping text into SVG outlines."""

    def __init__(self, file, wght):
        tt = TTFont(FONTS / file)
        tt = instancer.instantiateVariableFont(tt, {'wght': wght})
        tt.flavor = None
        buf = io.BytesIO()
        tt.save(buf)
        data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upm = self.tt['head'].unitsPerEm
        os2 = self.tt['OS/2']
        self.asc, self.desc, self.gap = os2.sTypoAscender, -os2.sTypoDescender, os2.sTypoLineGap
        self.hb = hb.Font(hb.Face(data))

    def line(self, size, line_height=None):
        """CSS line box height and baseline offset from its top (line-height: normal unless given)."""
        content = (self.asc + self.desc) / self.upm * size
        lh = line_height if line_height is not None else (self.asc + self.desc + self.gap) / self.upm * size
        return lh, (lh - content) / 2 + self.asc / self.upm * size

    def run(self, text, size, tracking=0.0):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {'kern': True, 'liga': True})
        k = size / self.upm
        out, pen = [], 0.0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            out.append((self.order[info.codepoint], pen + pos.x_offset * k, pos.y_offset * k))
            pen += pos.x_advance * k + tracking * size
        return out, pen  # CSS letter-spacing also follows the last letter

    def width(self, text, size, tracking=0.0):
        return self.run(text, size, tracking)[1]

    def path(self, text, size, x, baseline, tracking=0.0):
        glyphs, _ = self.run(text, size, tracking)
        k = size / self.upm
        d = []
        for name, gx, gy in glyphs:
            pen = SVGPathPen(self.glyphs, ntos=lambda v: f'{v:.2f}'.rstrip('0').rstrip('.'))
            self.glyphs[name].draw(TransformPen(pen, (k, 0, 0, -k, x + gx, baseline - gy)))
            d.append(pen.getCommands())
        return ''.join(d)


MAN700, MAN600 = Font('manrope-latin-wght-normal.woff2', 700), Font('manrope-latin-wght-normal.woff2', 600)
INT400, INT500, INT600, INT700 = (Font('inter-latin-wght-normal.woff2', w) for w in (400, 500, 600, 700))


def text(id_, font, s, size, x, top, fill, tracking=0.0, line_height=None, anchor='start'):
    """Outlined text whose CSS line box starts at `top`. Returns (svg, width, line height)."""
    lh, base = font.line(size, line_height)
    w = font.width(s, size, tracking)
    if anchor == 'middle':
        x -= w / 2
    return f'<path id="{id_}" fill="{fill}" d="{font.path(s, size, x, top + base, tracking)}"/>', w, lh


def doc(title, x, y, w, h, body, shadow=None):
    defs = SHADOW.format(o=shadow) if shadow else ''
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="{x:.1f} {y:.1f} {w:.1f} {h:.1f}">\n'
            f'<title>{title}</title>{defs}\n{body}\n</svg>\n')


def write(name, svg):
    OUT.mkdir(exist_ok=True)
    (OUT / f'{name}.svg').write_text(svg)
    print(f'{name}.svg  {len(svg) / 1024:.0f} KB')


def icon(name, x, y, size, color, sw=2.0, id_=None):
    k = size / 24
    paths = ''.join(f'<path d="{p}"/>' for p in ICON[name])
    return (f'<g id="{id_ or "icon-" + name}" transform="translate({x:.1f} {y:.1f}) scale({k:.4f})" fill="none" stroke="{color}" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{paths}</g>')


def mark(x, y, size, id_='mark'):
    k = size * 0.62 / 24
    off = size * 0.19
    return (f'<g id="{id_}"><rect id="{id_}-tile" x="{x}" y="{y}" width="{size}" height="{size}" rx="{size * 0.25}" fill="{CORAL}"/>'
            f'<path id="{id_}-wave" transform="translate({x + off:.2f} {y + off:.2f}) scale({k:.4f})" d="{WAVE}" fill="none" '
            f'stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></g>')


def lockup(x, y):
    """Mark (132) + gap 36 + wordmark, as in the plugs. (x, y) is the mark's top left."""
    word, ww, wlh = text('wordmark-kardiograph', MAN700, 'Kardiograph', 104, x + 168, y - 12, INK, tracking=-0.02, line_height=104)
    by, bw, blh = text('wordmark-by-medzcool', INT500, 'by Medzcool', 34, x + 168, y - 12 + 104 + 12, INK2)
    return f'<g id="lockup">{mark(x, y, 132)}<g id="wordmark">{word}{by}</g></g>', 168 + ww, -12 + 104 + 12 + blh


def pill(id_, s, font, size, x, top, pad=(14, 30), fill='#fff', stroke=DIVIDER, color=INK, icon_name=None, icon_sw=2.2,
         radius=None, height=None):
    """A CSS pill: inline-flex, items centred, gap 14, border 2 (unless stroke is None). `height` = a flex row
    stretching it to the row's tallest item. Returns (svg, w, h)."""
    b = 2 if stroke else 0
    lh, base = font.line(size)
    ic = (30 + 14) if icon_name else 0
    tw = font.width(s, size)
    w = tw + ic + 2 * pad[1] + 2 * b
    h = height or lh + 2 * pad[0] + 2 * b
    r = h / 2 if radius is None else radius
    sa = f' stroke="{stroke}" stroke-width="2"' if stroke else ''
    shape = f'<rect x="{x + b / 2:.1f}" y="{top + b / 2:.1f}" width="{w - b:.1f}" height="{h - b:.1f}" rx="{r - b / 2:.1f}" fill="{fill}"{sa}/>'
    tx = x + b + pad[1]
    inner = ''
    if icon_name:
        inner = icon(icon_name, tx, top + (h - 30) / 2, 30, color, icon_sw)
        tx += ic
    inner += f'<path id="{id_}-label" fill="{color}" d="{font.path(s, size, tx, top + (h - lh) / 2 + base)}"/>'
    return f'<g id="{id_}">{shape}{inner}</g>', w, h


def strip_svg(name, seconds=6.0, start=0.0, ox=0.0, oy=0.0, id_='strip', calipers=None):
    """kit.tsx EcgStrip: white paper (radius 10), 1 mm and 5 mm grid, lead II trace, "II" label."""
    st = S[name]
    fs, mv = st['fs'], st['mv']
    w, h, base = seconds * 25 * MM, H_MM * MM, H_MM * 0.62
    i0, i1 = int(round(start * fs)), min(len(mv) - 1, int(round((start + seconds) * fs)))
    pts = ' '.join(f'{ox + (i / fs - start) * 25 * MM:.1f},{oy + (base - mv[i] * 10) * MM:.1f}' for i in range(i0, i1 + 1))
    cols = int(seconds * 25)
    minor = ''.join(f'M{ox + c * MM:.1f} {oy}V{oy + h:.1f}' for c in range(cols + 1) if c % 5) + \
        ''.join(f'M{ox} {oy + r * MM:.1f}H{ox + w:.1f}' for r in range(H_MM + 1) if r % 5)
    major = ''.join(f'M{ox + c * MM:.1f} {oy}V{oy + h:.1f}' for c in range(0, cols + 1, 5)) + \
        ''.join(f'M{ox} {oy + r * MM:.1f}H{ox + w:.1f}' for r in range(0, H_MM + 1, 5))
    cid = f'{id_}-clip'
    lead, _, _ = text(f'{id_}-lead-label', INT600, 'II', 24, ox + 22, oy + 40 - INT600.line(24)[1], INK)
    out = (f'<g id="{id_}"><clipPath id="{cid}"><rect x="{ox}" y="{oy}" width="{w:.1f}" height="{h:.1f}" rx="10"/></clipPath>'
           f'<g clip-path="url(#{cid})"><rect id="{id_}-paper" x="{ox}" y="{oy}" width="{w:.1f}" height="{h:.1f}" fill="#fff"/>'
           f'<path id="{id_}-grid-1mm" d="{minor}" stroke="{GRID_MINOR}" stroke-width="1" fill="none"/>'
           f'<path id="{id_}-grid-5mm" d="{major}" stroke="{GRID_MAJOR}" stroke-width="1.5" fill="none"/>'
           f'<polyline id="{id_}-trace" points="{pts}" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/></g>'
           f'{lead}')
    if calipers is not None:
        out += calipers_svg(name, calipers, ox, oy)[0]
    return out + '</g>', w, h


def r_peaks(name):
    st = S[name]
    mv, fs = st['mv'], st['fs']
    thr = 0.6 * max(mv)
    out = []
    for i in range(1, len(mv) - 1):
        if mv[i] >= thr and mv[i] >= mv[i - 1] and mv[i] > mv[i + 1] and (not out or i - out[-1] > 0.2 * fs):
            out.append(i)
    return out


def calipers_svg(name, n, ox, oy):
    """EndPlug.tsx Calipers, fully open: from R peak n to R peak n+1, with the interval and rate readout."""
    pk, fs = r_peaks(name), S[name]['fs']
    a, b = (ox + pk[n] / fs * 25 * MM), (ox + pk[n + 1] / fs * 25 * MM)
    top, bottom = oy + 2.2 * MM, oy + H_MM * MM - 2 * MM
    ms = (pk[n + 1] - pk[n]) / fs * 1000
    label = f'{ms:.0f} ms · {60000 / ms:.0f} bpm'
    cx, cy = (a + b) / 2, top - 2
    lh, base = INT600.line(28)
    txt = INT600.path(label, 28, cx - INT600.width(label, 28) / 2, cy + 10)
    return (f'<g id="calipers"><path id="calipers-legs" d="M{a:.1f} {top:.1f}V{bottom:.1f}M{b:.1f} {top:.1f}V{bottom:.1f}M{a:.1f} {top + 12:.1f}H{b:.1f}" '
            f'stroke="{CORAL}" stroke-width="3" fill="none"/>'
            f'<g id="calipers-readout"><rect x="{cx - 150:.1f}" y="{cy - 26:.1f}" width="300" height="52" rx="26" fill="{CORAL}"/>'
            f'<path fill="#fff" d="{txt}"/></g></g>'), ms


def row(items, gap, x0=0.0, top=0.0):
    """A flex row: items are callables (x, top, height) -> (svg, w, h), laid out left to right and stretched to the
    tallest one (align-items: stretch). Returns (svg, width, height)."""
    gaps = [0] + (gap if isinstance(gap, list) else [gap] * (len(items) - 1))
    hmax = max(it(0, 0, None)[2] for it in items)
    x, parts = x0, []
    for g, it in zip(gaps, items):
        x += g
        svg, w, _ = it(x, top, hmax)
        parts.append(svg)
        x += w
    return ''.join(parts), x - x0, hmax


# ---- 1. Brand ---------------------------------------------------------------------------------------------------
write('kardiograph-mark', doc('Kardiograph mark', 0, 0, 132, 132, mark(0, 0, 132)))

lk, lw, lb = lockup(0, 0)
write('kardiograph-lockup', doc('Kardiograph by Medzcool lockup', 0, -12, lw, lb + 12, lk))

kick_s, kick_size, kick_tr = 'THIS VIDEO IS BROUGHT TO YOU BY', 24, 0.14
kw = MAN700.width(kick_s, kick_size, kick_tr)
kick, _, klh = text('kicker-brought-to-you-by', MAN700, kick_s, kick_size, lw / 2, -160 + 66 - 0, INK2, tracking=kick_tr, anchor='middle')
x0 = min(0, lw / 2 - kw / 2)
write('kardiograph-lockup-brought-to-you-by',
      doc('This video is brought to you by Kardiograph by Medzcool', x0, -94, max(lw, kw), lb + 94, f'{kick}{lk}'))

# lockup + URL + Try it free (end plug layout: mark centre at y 480, the pills' row at y 640)
url = lambda x, t, h: pill('url-pill', 'kardiograph.medzcool.com', INT600, 46, x, t, pad=(20, 44), height=h)
free = lambda x, t, h: pill('try-it-free-pill', 'Try it free', INT600, 40, x, t, pad=(24, 44), fill=CORAL, stroke=None, color='#fff', height=h)
_, rw, _ = row([url, free], 24)
W2 = max(lw, rw)
lk2, _, _ = lockup((W2 - lw) / 2, 0)
cta_top = 640 - (480 - 66)
cta, _, rh = row([url, free], 24, x0=(W2 - rw) / 2, top=cta_top)
write('kardiograph-lockup-url-try-it-free', doc('Kardiograph lockup with kardiograph.medzcool.com and Try it free', 0, -12, W2,
                                               cta_top + rh + 12, f'{lk2}<g id="call-to-action">{cta}</g>'))

for label, slug in [('Kardiograph · Practice', 'practice'), ('Kardiograph · True scale', 'true-scale')]:
    s = label.upper()
    t, w, _ = text('corner-kicker', MAN700, s, 24, 64 + 20, 32 - 15, INK2, tracking=0.14)
    write(f'corner-label-{slug}', doc(f'Corner mark and kicker: {label}', 0, 0, 64 + 20 + w, 64, mark(0, 0, 64, 'corner-mark') + t))

# ---- 2. ECG strips (true scale) ---------------------------------------------------------------------------------
for name in ['sinus', 'svt', 'afib', 'flutter', 'avb1', 'mobitz1']:
    g, w, h = strip_svg(name)
    write(f'ecg-strip-{name}', doc(f'{NAMES[name]}, lead II, 6 s at 25 mm/s and 10 mm/mV (Kardiograph engine)', 0, 0, w, h, g))
g, w, h = strip_svg('sinus', calipers=2)
write('ecg-strip-sinus-calipers', doc('Normal sinus rhythm with calipers between two R waves', 0, -10, w, h + 10, g))

# ---- 3. Practice (opener) ----------------------------------------------------------------------------------------
chips = [lambda x, t, h: pill('chip-sinus', 'Sinus', INT500, 30, x, t, height=h),
         lambda x, t, h: pill('chip-atrial-flutter', 'Atrial flutter', INT500, 30, x, t, height=h),
         lambda x, t, h: pill('chip-svt-picked', 'SVT', INT600, 30, x, t, fill=CORAL, stroke=CORAL, color='#fff',
                              icon_name='check', icon_sw=3, height=h)]


def score(x, t, h=None):
    lh, base = INT500.line(30)
    w1 = INT700.width('100%', 30)
    w2 = INT500.width(' Rhythm: SVT', 30)
    w, h = w1 + w2 + 60, h or lh + 28
    ty = t + (h - lh) / 2 + base
    return (f'<g id="score-pill"><rect x="{x:.1f}" y="{t:.1f}" width="{w:.1f}" height="{h:.1f}" rx="16" fill="{TEAL_SOFT}"/>'
            f'<path id="score-percent" fill="{TEAL}" d="{INT700.path("100%", 30, x + 30, ty)}"/>'
            f'<path id="score-label" fill="{INK}" d="{INT500.path(" Rhythm: SVT", 30, x + 30 + w1, ty)}"/></g>'), w, h


b, w, h = row(chips + [score], [16, 16, 16 + 24])
write('practice-answers-scored', doc('Practice answers: SVT picked, scored 100%', 0, 0, w, h, f'<g id="practice-answers">{b}</g>'))
b, w, h = row(chips[:2] + [lambda x, t, h: pill('chip-svt', 'SVT', INT500, 30, x, t, height=h)], 16)
write('practice-answers', doc('Practice answers before a pick', 0, 0, w, h, f'<g id="practice-answers">{b}</g>'))

cursor = ('<path id="cursor" transform="translate(-1.5 -1.5) scale(2)" d="M1.5 1.5v22.5l6.2-5.6 4.1 9.4 4-1.8-4-9.2 8.4-.6z" '
          f'fill="{INK}" stroke="#fff" stroke-width="2" stroke-linejoin="round"/>')
write('cursor-arrow', doc('Cursor (tip at 0,0)', -4, -4, 50, 64, cursor))

# practice card: the SVT strip on its card, as in the opener
g, w, h = strip_svg('svt', ox=20, oy=20)
card = f'<rect id="card" x="0" y="0" width="{w + 40:.1f}" height="{h + 40:.1f}" rx="24" fill="#fff" filter="url(#soft-shadow)"/>'
write('practice-card-svt', doc('Practice card: SVT, lead II at true scale', -24, -16, w + 88, h + 88, f'{card}{g}', shadow=0.10))

# ---- 4. End plug pieces -----------------------------------------------------------------------------------------
def tile(id_, ic, title, sub):
    tlh, tb = MAN600.line(48)
    slh, sb = INT400.line(30)
    inner_h = max(88, tlh + 6 + slh)
    h = inner_h + 72
    ty = 36 + (inner_h - (tlh + 6 + slh)) / 2
    return (f'<g id="{id_}"><rect id="{id_}-card" width="520" height="{h:.1f}" rx="24" fill="#fff" filter="url(#soft-shadow)"/>'
            f'<rect id="{id_}-icon-tile" x="40" y="{36 + (inner_h - 88) / 2:.1f}" width="88" height="88" rx="22" fill="{CORAL_SOFT}"/>'
            f'{icon(ic, 40 + 20, 36 + (inner_h - 88) / 2 + 20, 48, CORAL)}'
            f'<path id="{id_}-title" fill="{INK}" d="{MAN600.path(title, 48, 40 + 88 + 28, ty + tb)}"/>'
            f'<path id="{id_}-sub" fill="{INK2}" d="{INT400.path(sub, 30, 40 + 88 + 28, ty + tlh + 6 + sb)}"/></g>'), h


tc, th = tile('tile-course', 'book', 'Course', '7 modules, 21 lessons')
tp, _ = tile('tile-practice', 'clipboard', 'Practice', '5 decks, scored')
write('tile-course', doc('Course tile', -24, -16, 568, th + 48, tc, shadow=0.08))
write('tile-practice', doc('Practice tile', -24, -16, 568, th + 48, tp, shadow=0.08))

p, w, h = pill('new-tracing-pill', 'New tracing', INT500, 30, 0, 0, icon_name='rotate')
write('new-tracing-pill', doc('New tracing pill', 0, 0, w, h, p))
p, w, h = pill('url-pill', 'kardiograph.medzcool.com', INT600, 46, 0, 0, pad=(20, 44))
write('url-pill', doc('kardiograph.medzcool.com pill', 0, 0, w, h, p))
p, w, h = pill('try-it-free-pill', 'Try it free', INT600, 40, 0, 0, pad=(24, 44), fill=CORAL, stroke=None, color='#fff')
write('try-it-free-pill', doc('Try it free pill', 0, 0, w, h, p))

# six-rhythm grid (end plug, "endless"): 3 s strips at 58%, on cards, with name chips
SC, COL, GAP = 0.58, 458, 36
cells, y_rows = [], [0, 0]
cw, chh = 720 * SC + 24, 288 * SC + 24
chip_lh = INT600.line(24)[0] + 12 + 4
cell_h = chh + 14 + chip_lh
for i, name in enumerate(['sinus', 'afib', 'flutter', 'avb1', 'mobitz1', 'svt']):
    cx = (i % 3) * (COL + GAP) + COL / 2
    cy = (i // 3) * (cell_h + GAP)
    sg, _, _ = strip_svg(name, seconds=3, start=1, id_=f'strip-{name}')
    chip_w = INT600.width(NAMES[name], 24) + 36 + 4
    chip, _, _ = pill(f'chip-{name}', NAMES[name], INT600, 24, cx - chip_w / 2, cy + chh + 14, pad=(6, 18))
    cells.append(f'<g id="cell-{name}"><rect x="{cx - cw / 2:.1f}" y="{cy:.1f}" width="{cw:.1f}" height="{chh:.1f}" rx="24" fill="#fff" filter="url(#soft-shadow)"/>'
                 f'<g transform="translate({cx - cw / 2 + 12:.1f} {cy + 12:.1f}) scale({SC})">{sg}</g>{chip}</g>')
GW = 3 * COL + 2 * GAP
write('rhythm-grid', doc('Six practice rhythms from the Kardiograph engine', -24, -16, GW + 48, 2 * cell_h + GAP + 48,
                         '<g id="rhythm-grid">' + ''.join(cells) + '</g>', shadow=0.10))

# ---- 5. Icons (one color: currentColor) -------------------------------------------------------------------------
for name in ['book', 'clipboard', 'rotate', 'check']:
    write(f'icon-{name}', doc(f'Icon: {name}', 0, 0, 24, 24, icon(name, 0, 0, 24, 'currentColor')))
