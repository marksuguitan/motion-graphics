"""Key frames for the two Kardiograph plugs in Sinus Tach vs SVT.

    python3 make_keyframes.py && node shoot.cjs

Writes keyframes.html (one 1920x1080 .f div per frame); shoot.cjs renders frames/<id>.png and the sheets.
Opener: K1-K4 (after the title card). End plug: E1-E4 (before the end card).
Every strip is lead II from Kardiograph's own engine (export_strips.ts -> strips.json, 250 Hz).
"""
import json
import pathlib

here = pathlib.Path(__file__).parent
S = json.load(open(here / 'strips.json'))
FONTS = (here / '../../../../library/remotion/public/fonts').resolve().as_uri()
CORAL = '#E0574F'   # Kardiograph's brand coral (kardiograph public/learn/learn.css)
MM = 9.6            # px per mm: a 6 s strip at 25 mm/s = 150 mm = 1440 px
H_MM = 30


def r_peaks(mv, fs):
    """Indices of R peaks: local maxima above 60% of the strip's max, at least 200 ms apart."""
    thr = 0.6 * max(mv)
    out = []
    for i in range(1, len(mv) - 1):
        if mv[i] >= thr and mv[i] >= mv[i - 1] and mv[i] > mv[i + 1]:
            if not out or i - out[-1] > 0.2 * fs:
                out.append(i)
    return out


def strip(name, seconds=6.0, mm=MM, calipers=None):
    st = S[name]
    fs, mv = st['fs'], st['mv'][:int(seconds * st['fs'])]
    w_mm = int(seconds * 25)
    base = H_MM * 0.62
    x = lambda i: (i / fs) * 25 * mm
    y = lambda v: (base - v * 10) * mm
    pts = ' '.join(f'{x(i):.1f},{y(v):.1f}' for i, v in enumerate(mv))
    minor = ''.join(f'M{i*mm:.1f} 0V{H_MM*mm}' for i in range(w_mm + 1) if i % 5) + \
        ''.join(f'M0 {j*mm:.1f}H{w_mm*mm}' for j in range(H_MM + 1) if j % 5)
    major = ''.join(f'M{i*mm:.1f} 0V{H_MM*mm}' for i in range(0, w_mm + 1, 5)) + \
        ''.join(f'M0 {j*mm:.1f}H{w_mm*mm}' for j in range(0, H_MM + 1, 5))
    extra = ''
    if calipers is not None:
        pk = r_peaks(mv, fs)
        a, b = pk[calipers], pk[calipers + 1]
        xa, xb, top = x(a), x(b), 2.2 * mm
        ms = (b - a) / fs * 1000
        extra = f'''<g stroke="{CORAL}" stroke-width="3" fill="none">
            <path d="M{xa:.1f} {top:.1f}V{H_MM*mm - 2*mm:.1f}M{xb:.1f} {top:.1f}V{H_MM*mm - 2*mm:.1f}M{xa:.1f} {top + 12:.1f}H{xb:.1f}"/></g>
          <g transform="translate({(xa + xb) / 2:.1f},{top - 2:.1f})"><rect x="-150" y="-26" width="300" height="52" rx="26" fill="{CORAL}"/>
            <text text-anchor="middle" y="10" font-family="Inter" font-weight="600" font-size="28" fill="#fff">{ms:.0f} ms · {60000 / ms:.0f} bpm</text></g>'''
    return f'''<svg width="{w_mm*mm:.0f}" height="{H_MM*mm:.0f}" viewBox="0 0 {w_mm*mm:.1f} {H_MM*mm:.1f}" overflow="visible">
      <rect width="100%" height="100%" fill="#FFFFFF"/>
      <path d="{minor}" stroke="#F6DEDB" stroke-width="1" fill="none"/>
      <path d="{major}" stroke="#EDBDB7" stroke-width="1.5" fill="none"/>
      <polyline points="{pts}" fill="none" stroke="#222222" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>
      <text x="22" y="40" font-family="Inter" font-weight="600" font-size="24" fill="#222">II</text>{extra}
    </svg>'''


def icon(paths, color='#fff', sw=2.2):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round" '
            f'stroke-linejoin="round">{paths}</svg>')


WAVE = '<path d="M2 12h3l2-6 3 12 3-9 2 3h7"/>'
BOOK = '<path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/>'
CLIP = ('<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6'
        'a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>')
ROTATE = '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>'


def mark(size):
    return f'<div class="mark" style="width:{size}px;height:{size}px;border-radius:{size*0.25:.0f}px">{icon(WAVE, sw=2.4)}</div>'


def lockup():
    return f'''<div class="lockup">{mark(132)}
      <div><div class="name">Kardiograph</div><div class="by">by Medzcool</div></div></div>'''


def chips(sel=None):
    out = []
    for c in ['Sinus', 'Atrial flutter', 'SVT']:
        on = c == sel
        out.append(f'<span class="chip{" on" if on else ""}">{"✓ " if on else ""}{c}</span>')
    return '<div class="chips">' + ''.join(out) + '</div>'


def top(kicker):
    return f'<div class="top">{mark(64)}<span class="kicker">{kicker}</span></div>'


def tile(ic, title, sub):
    return f'''<div class="tile"><div class="tile__ic">{icon(ic, CORAL, 2)}</div>
      <div><div class="tile__t">{title}</div><div class="tile__s">{sub}</div></div></div>'''


FRAMES = [
    # Opener, after the title card
    ('K1', f'<div class="center"><div class="kicker">This video is brought to you by</div>{lockup()}</div>'),
    ('K2', f'{top("Kardiograph · Practice")}<div class="h">Read the tracing.</div><div class="card">{strip("svt")}</div>{chips()}'),
    ('K3', f'''{top("Kardiograph · Practice")}<div class="h">Score your read.</div><div class="card">{strip("svt")}</div>
        <div class="row">{chips("SVT")}<span class="score"><b>100%</b>&nbsp; Rhythm: SVT</span></div>'''),
    ('K4', f'<div class="center">{lockup()}<div class="url">kardiograph.medzcool.com</div></div>'),
    # End plug, before the end card
    ('E1', f'''<div class="center"><div class="kicker">Kardiograph by Medzcool</div>
        <div class="title">Learn to read the EKG.</div>
        <div class="tiles">{tile(BOOK, "Course", "7 modules, 21 lessons")}{tile(CLIP, "Practice", "5 decks, scored")}</div></div>'''),
    ('E2', f'''{top("True scale")}<div class="h">Measure it with calipers.</div>
        <div class="card">{strip("sinus", calipers=2)}</div>
        <div class="cap">25 mm/s · 10 mm/mV</div>'''),
    ('E3', f'''{top("Kardiograph · Practice")}<div class="h">A new tracing every time.</div>
        <div class="stack"><div class="card ghost g2"></div><div class="card ghost g1"></div><div class="card">{strip("afib")}</div></div>
        <div class="row"><span class="pill">{icon(ROTATE, "#222", 2.2)} New tracing</span></div>'''),
    ('E4', f'''<div class="center">{lockup()}<div class="row" style="margin-top:64px">
        <div class="url" style="margin:0">kardiograph.medzcool.com</div><span class="cta">Start free</span></div></div>'''),
]

CSS = f'''
@font-face {{ font-family: Manrope; src: url("{FONTS}/manrope-latin-wght-normal.woff2"); font-weight: 200 800; }}
@font-face {{ font-family: Inter; src: url("{FONTS}/inter-latin-wght-normal.woff2"); font-weight: 100 900; }}
body {{ margin:0; background:#ddd; }}
.f {{ width:1920px; height:1080px; background:#FFFFFF; position:relative; overflow:hidden; font-family:Inter; color:#222;
      display:flex; flex-direction:column; align-items:center; justify-content:center; }}
.center {{ display:flex; flex-direction:column; align-items:center; }}
.kicker {{ font-family:Manrope; font-weight:700; font-size:24px; letter-spacing:.14em; text-transform:uppercase; color:#6A6A6A; margin-bottom:44px; }}
.lockup {{ display:flex; align-items:center; gap:36px; }}
.mark {{ background:{CORAL}; display:grid; place-items:center; }}
.mark svg {{ width:62%; height:62%; }}
.name {{ font-family:Manrope; font-weight:700; font-size:104px; letter-spacing:-.02em; line-height:1; }}
.by {{ font-weight:500; font-size:34px; color:#6A6A6A; margin-top:12px; }}
.title {{ font-family:Manrope; font-weight:600; font-size:88px; letter-spacing:-.015em; }}
.top {{ position:absolute; top:84px; left:240px; display:flex; align-items:center; gap:20px; }}
.top .kicker {{ margin:0; }}
.h {{ font-family:Manrope; font-weight:600; font-size:64px; letter-spacing:-.01em; align-self:flex-start; margin:60px 0 36px 240px; }}
.card {{ padding:20px; background:#F7F7F5; border-radius:24px; box-shadow:0 8px 24px rgba(34,34,34,.10); position:relative; }}
.card svg {{ display:block; border-radius:10px; }}
.stack {{ position:relative; }}
.ghost {{ position:absolute; inset:0; padding:0; }}
.g1 {{ transform:translate(18px,-18px) scale(.985); opacity:.9; }}
.g2 {{ transform:translate(36px,-36px) scale(.97); opacity:.8; }}
.chips {{ display:flex; gap:16px; }}
.f > .chips, .f > .row {{ margin-top:44px; }}
.row {{ display:flex; gap:40px; align-items:center; }}
.chip, .pill {{ font-weight:500; font-size:30px; padding:14px 30px; border-radius:999px; border:2px solid #E6E4E0; background:#fff; }}
.pill {{ display:flex; align-items:center; gap:14px; }}
.pill svg {{ width:30px; height:30px; }}
.chip.on {{ background:{CORAL}; border-color:{CORAL}; color:#fff; font-weight:600; }}
.score {{ font-size:30px; padding:14px 30px; border-radius:16px; background:#E7F4F2; }}
.score b {{ font-weight:700; color:#2E9C8F; }}
.url {{ margin-top:64px; font-weight:600; font-size:48px; padding:20px 44px; border-radius:999px; border:2px solid #E6E4E0; background:#F7F7F5; }}
.cta {{ font-weight:600; font-size:40px; padding:24px 44px; border-radius:999px; background:{CORAL}; color:#fff; }}
.cap {{ margin-top:28px; font-size:28px; color:#6A6A6A; }}
.tiles {{ display:flex; gap:36px; margin-top:72px; }}
.tile {{ display:flex; align-items:center; gap:28px; width:520px; padding:36px 40px; background:#F7F7F5; border-radius:24px; box-shadow:0 8px 24px rgba(34,34,34,.08); }}
.tile__ic {{ width:88px; height:88px; border-radius:22px; background:#FCEBEA; display:grid; place-items:center; }}
.tile__ic svg {{ width:48px; height:48px; }}
.tile__t {{ font-family:Manrope; font-weight:600; font-size:48px; }}
.tile__s {{ font-size:30px; color:#6A6A6A; margin-top:6px; }}
'''
html = '<!doctype html><meta charset=utf-8><style>' + CSS + '</style>' + \
    ''.join(f'<div class="f" id="{fid}">{body}</div>' for fid, body in FRAMES)
(here / 'keyframes.html').write_text(html)
print('ok', ', '.join(f for f, _ in FRAMES))
