"""Key frames for the Kardiograph plug (Sinus Tach vs SVT). Writes keyframes.html; render with shoot.cjs.

The SVT strip is lead II from Kardiograph's own engine (practice deck 'rhythm', seed 171,
183 bpm, QRS 96 ms), exported to svt-II.json at 250 Hz.
"""
import json
import pathlib

here = pathlib.Path(__file__).parent
d = json.load(open(here / 'svt-II.json'))
FONTS = (here / '../../../../library/remotion/public/fonts').resolve().as_uri()
CORAL = '#E0574F'   # Kardiograph's brand coral (kardiograph public/learn/learn.css)
MM = 9.6            # px per mm: a 6 s strip at 25 mm/s = 150 mm = 1440 px
W_MM, H_MM = 150, 30


def strip(seconds=6.0):
    n = int(seconds * d['fs'])
    mv = d['mv'][:n]
    base = H_MM * 0.62
    pts = ' '.join(f"{(i / d['fs']) * 25 * MM:.1f},{(base - v * 10) * MM:.1f}" for i, v in enumerate(mv))
    minor = ''.join(f'M{x*MM:.1f} 0V{H_MM*MM}' for x in range(W_MM + 1) if x % 5) + \
        ''.join(f'M0 {y*MM:.1f}H{W_MM*MM}' for y in range(H_MM + 1) if y % 5)
    major = ''.join(f'M{x*MM:.1f} 0V{H_MM*MM}' for x in range(0, W_MM + 1, 5)) + \
        ''.join(f'M0 {y*MM:.1f}H{W_MM*MM}' for y in range(0, H_MM + 1, 5))
    return f'''<svg width="{W_MM*MM}" height="{H_MM*MM}" viewBox="0 0 {W_MM*MM} {H_MM*MM}">
      <rect width="100%" height="100%" fill="#FFFFFF"/>
      <path d="{minor}" stroke="#F6DEDB" stroke-width="1" fill="none"/>
      <path d="{major}" stroke="#EDBDB7" stroke-width="1.5" fill="none"/>
      <polyline points="{pts}" fill="none" stroke="#222222" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/>
      <text x="22" y="40" font-family="Inter" font-weight="600" font-size="24" fill="#222">II</text>
    </svg>'''


WAVE = ('<svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.4" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M2 12h3l2-6 3 12 3-9 2 3h7"/></svg>')


def mark(size):
    return f'<div class="mark" style="width:{size}px;height:{size}px;border-radius:{size*0.25:.0f}px">{WAVE}</div>'


def lockup():
    return f'''<div class="lockup">{mark(132)}
      <div><div class="name">Kardiograph</div><div class="by">by Medzcool</div></div></div>'''


def chips(sel=None):
    out = []
    for c in ['Sinus', 'Atrial flutter', 'SVT']:
        on = c == sel
        out.append(f'<span class="chip{" on" if on else ""}">{"✓ " if on else ""}{c}</span>')
    return '<div class="chips">' + ''.join(out) + '</div>'


TOP = f'<div class="top">{mark(64)}<span class="kicker">Kardiograph · Practice</span></div>'
frames = [
    f'<div class="center"><div class="kicker">This video is brought to you by</div>{lockup()}</div>',
    f'{TOP}<div class="h">Read the tracing.</div><div class="card">{strip()}</div>{chips()}',
    f'''{TOP}<div class="h">Score your read.</div><div class="card">{strip()}</div>
        <div class="row">{chips("SVT")}<span class="score"><b>100%</b>&nbsp; Rhythm: SVT</span></div>''',
    f'<div class="center">{lockup()}<div class="url">kardiograph.medzcool.com</div></div>',
]
css = f'''
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
.top {{ position:absolute; top:84px; left:240px; display:flex; align-items:center; gap:20px; }}
.top .kicker {{ margin:0; }}
.h {{ font-family:Manrope; font-weight:600; font-size:64px; letter-spacing:-.01em; align-self:flex-start; margin:60px 0 36px 240px; }}
.card {{ padding:20px; background:#F7F7F5; border-radius:24px; box-shadow:0 8px 24px rgba(34,34,34,.10); }}
.card svg {{ display:block; border-radius:10px; }}
.chips {{ display:flex; gap:16px; }}
.f > .chips, .row {{ margin-top:44px; }}
.row {{ display:flex; gap:40px; align-items:center; }}
.chip {{ font-weight:500; font-size:30px; padding:14px 30px; border-radius:999px; border:2px solid #E6E4E0; background:#fff; }}
.chip.on {{ background:{CORAL}; border-color:{CORAL}; color:#fff; font-weight:600; }}
.score {{ font-size:30px; padding:14px 30px; border-radius:16px; background:#E7F4F2; }}
.score b {{ font-weight:700; color:#2E9C8F; }}
.url {{ margin-top:64px; font-weight:600; font-size:48px; padding:20px 44px; border-radius:999px; border:2px solid #E6E4E0; background:#F7F7F5; }}
'''
html = '<!doctype html><meta charset=utf-8><style>' + css + '</style>' + ''.join(f'<div class="f">{b}</div>' for b in frames)
(here / 'keyframes.html').write_text(html)
print('ok', len(frames))
