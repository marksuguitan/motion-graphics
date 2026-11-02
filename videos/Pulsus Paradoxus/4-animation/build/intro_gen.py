"""Medzcool logo intro (approved preview v3, Mark 2026-10-27) -> build_intro.jsx for After Effects.

The Medzcool logo (Branding/Medzcool Logo.svg, two polygons) is cut into a 40 px square grid at 760 px wide,
centred in a 1920x1080 comp. Each grid cell that holds logo becomes one shape layer whose path is the logo clipped
to that cell (exact geometry, no masks). Tiles land in four batches on the first four lubs (S1) of the heartbeat,
which is 'Normal S1 S2 (Apex).mp3' sped up 1.6x with atempo (about 120 bpm, pitch kept). S1/S2 peak times were
measured from that file (fast_onsets.json); nothing here is estimated. On the 5th lub the 3 px seams close (tile
scale 92.5% -> 100%) and a single whole-logo layer takes over, so the finished logo has no seams or notches.
A null 'Pulse' parents everything and carries the heartbeat pulse as an expression.

Keyframes are sampled once per frame (linear), so the AE motion matches the preview frame for frame."""
import json, math, random, sys
from PIL import Image, ImageDraw

W, H, FPS, DUR = 1920, 1080, 30, 3.3
BG, ACC = "#151515", "#FF4057"
POLYS = [[13.98, 28.07, 4.31, 28.07, 0, 35.85, 18.54, 35.85, 23.46, 27.04, 34.59, 44.72, 38.86, 36.91, 23.06, 11.81, 13.98, 28.07],
         [61.63, 19.81, 50.85, 1.86, 41.25, 18.59, 29.55, 0, 25.33, 7.9, 41.56, 33.67, 51, 17.22, 57.23, 27.59, 65.77, 27.59, 69.66, 19.81, 61.63, 19.81]]
LW = 760; S = LW / 69.66; LH = 44.72 * S
OX, OY = W / 2 - LW / 2, H / 2 - LH / 2
TILE, GAP = 40, 3
O = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "/tmp/claude-0/intro/fast_onsets.json"))
S1, S2 = O["S1"], O["S2"]
BUILD = [t - 0.02 for t in S1[:4]]
FINAL = S1[4]
CLOSE = 0.15            # seams close over 0.15 s after the 5th lub
POP = 0.18              # tile pop duration
GAPSCALE = 100 * (1 - GAP / TILE)

# --- same tile selection and batch order as intro_preview.py (raster coverage > 2 %, seed 7) ---
SS = 2
logo = Image.new("L", (int(LW * SS), int(LH * SS)), 0); d = ImageDraw.Draw(logo)
for p in POLYS: d.polygon([(p[i] * S * SS, p[i + 1] * S * SS) for i in range(0, len(p), 2)], fill=255)
logo_s = logo.resize((int(LW), int(LH)), Image.LANCZOS)
cols, rows = math.ceil(LW / TILE), math.ceil(LH / TILE)
tiles = []
for r in range(rows):
    for c in range(cols):
        box = (c * TILE, r * TILE, min((c + 1) * TILE, int(LW)), min((r + 1) * TILE, int(LH)))
        m = logo_s.crop(box)
        if sum(m.get_flattened_data()) / 255 / (TILE * TILE) > 0.02: tiles.append(dict(c=c, r=r, box=box))
random.seed(7); random.shuffle(tiles)
frac = [0.16, 0.22, 0.28, 0.34]; n = len(tiles); idx = 0
for b, f in enumerate(frac):
    k = round(n * f) if b < 3 else n - idx
    for t in tiles[idx:idx + k]: t["t0"] = BUILD[b] + random.uniform(0, 0.04); t["batch"] = b + 1
    idx += k


def clip(poly, x0, y0, x1, y1):
    """Sutherland-Hodgman: subject polygon (comp px) against an axis-aligned rectangle."""
    def edge(pts, inside, inter):
        out = []
        for i in range(len(pts)):
            a, b = pts[i - 1], pts[i]
            ia, ib = inside(a), inside(b)
            if ib:
                if not ia: out.append(inter(a, b))
                out.append(b)
            elif ia: out.append(inter(a, b))
        return out
    def ix(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def iy(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    pts = poly
    for ins, it in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                    (lambda p: p[1] >= y0, iy(y0)), (lambda p: p[1] <= y1, iy(y1))):
        if not pts: break
        pts = edge(pts, ins, it)
    # drop repeated points
    o = []
    for p in pts:
        if not o or abs(p[0] - o[-1][0]) > 1e-6 or abs(p[1] - o[-1][1]) > 1e-6: o.append(p)
    if len(o) > 1 and abs(o[0][0] - o[-1][0]) < 1e-6 and abs(o[0][1] - o[-1][1]) < 1e-6: o.pop()
    return o if len(o) >= 3 else []


def area(p):
    return abs(sum(p[i - 1][0] * p[i][1] - p[i][0] * p[i - 1][1] for i in range(len(p)))) / 2


comp_polys = [[(OX + p[i] * S, OY + p[i + 1] * S) for i in range(0, len(p) - 2, 2)] for p in POLYS]   # last point repeats the first


def ease_back(x, s=2.2):
    x = min(max(x, 0), 1); x -= 1; return x * x * ((s + 1) * x + s) + 1


def fr(t):
    return round(t * FPS) / FPS


out_tiles = []
for tl in tiles:
    x0, y0, x1, y1 = tl["box"]
    cx, cy = OX + (x0 + x1) / 2, OY + (y0 + y1) / 2
    paths = []
    for cp in comp_polys:
        q = clip(cp, OX + x0, OY + y0, OX + x1, OY + y1)
        if q and area(q) > 0.5: paths.append([[round(px - cx, 3), round(py - cy, 3)] for px, py in q])
    if not paths: continue
    t0 = tl["t0"]
    sk, ok = [], []
    f0 = math.ceil(t0 * FPS)
    sk.append([round(t0, 4), 0]); ok.append([round(t0, 4), 0])
    f = f0
    while f / FPS <= t0 + POP + 1e-9:
        t = f / FPS
        if t > t0:
            sk.append([round(t, 4), round(GAPSCALE * ease_back((t - t0) / POP), 3)])
            ok.append([round(t, 4), round(100 * min(1, (t - t0) / 0.06), 2)])
        f += 1
    sk.append([round(t0 + POP, 4), GAPSCALE]); ok.append([round(t0 + 0.06, 4), 100])
    sk.append([round(FINAL, 4), GAPSCALE]); sk.append([round(FINAL + CLOSE, 4), 100])
    sk = sorted({k[0]: k for k in sk}.values()); ok = sorted({k[0]: k for k in ok}.values())
    out_tiles.append(dict(id=f"r{tl['r']:02d}c{tl['c']:02d}", batch=tl["batch"], pos=[round(cx, 3), round(cy, 3)],
                          paths=paths, t0=round(t0, 4), scale=sk, opacity=ok))
out_tiles.sort(key=lambda t: t["id"])

full = [[[round(x - W / 2, 3), round(y - H / 2, 3)] for x, y in cp] for cp in comp_polys]
plan = dict(name="Medzcool Intro", w=W, h=H, fps=FPS, dur=DUR, bg=BG, acc=ACC, S1=S1, S2=S2, final=FINAL,
            close=CLOSE, full_in=round(FINAL + CLOSE, 4), tile_out=round(FINAL + CLOSE + 1 / FPS, 4),
            audio="audio/cues/Heartbeat_intro_120bpm.wav", fade=[2.7, 3.3], tiles=out_tiles, full=full,
            checks=[0.3, 0.75, 1.0, 1.27, 1.5, 1.8, 2.3, 2.45, 3.2], master="Pulsus Paradoxus",
            # master frames after placing the intro: intro, the cut into Scene 1, the 1-2 morph, Scene 2/3/5 starts, the end
            master_checks=[1.0, 3.2, 3.4, DUR + 1.0, DUR + 27.6, DUR + 28.2, DUR + 75.9, DUR + 176.5, DUR + 231.5])
json.dump(plan, open("/tmp/claude-0/intro/intro_plan.json", "w"))
print("tiles", len(out_tiles), "batches", [sum(1 for t in out_tiles if t["batch"] == b) for b in (1, 2, 3, 4)],
      "multi-path tiles", sum(1 for t in out_tiles if len(t["paths"]) > 1))
