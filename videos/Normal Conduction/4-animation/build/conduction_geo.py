#!/usr/bin/env python3
"""conduction_geo.py: turns Mark's gray conduction heart into animation data for the Remotion build.

Input:  3-board/art/heart-conduction-gray.svg  (from marksuguitan/motion, assets/anatomy/heart)
Output (into 4-animation/remotion/):
  src/data/heartArt.ts      the heart, highlight and conduction layers as SVG markup (monochrome)
  public/maps/act.png       activation-time map of the conduction system (R = time / ACT_MAX, 255 = never)
  src/data/conduction.json  ACT_MAX, key points, the main impulse routes and the branch fronts, each as
                            [x, y, t] in SVG units and seconds of one beat (t = 0 when the SA node fires)
  ../build/geo_check.png    a check image: the activation map with the routes drawn on

How the timing is made: a geodesic (fastest-path) distance from the SA node through the drawn pathway,
with one conduction speed for the atria, a slow one inside the AV node, and a fast one below it (His,
bundle branches, Purkinje). The three speeds are solved so that, within one 0.8 s beat:
  SA node fires at 0; the impulse reaches the far left atrium at T_ATRIA_END (end of the P wave); it leaves the AV node at T_AV_OUT;
  the farthest Purkinje fiber is reached at T_VENT_END.
Those targets sit inside StatPearls' normal ranges (PR 120-200 ms, QRS under 120 ms); they are
modelled values for the picture, not numbers shown on screen.

Run:  python3 conduction_geo.py   (needs numpy, scipy, scikit-image, Pillow, and node + playwright)
"""
import json
import os
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.graph import MCP_Geometric
from skimage.morphology import closing, disk, remove_small_objects, skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(VIDEO, '3-board/art/heart-conduction-gray.svg')
RM = os.path.join(VIDEO, '4-animation/remotion')
TMP = os.path.join(HERE, 'tmp_geo')
os.makedirs(TMP, exist_ok=True)

VB = (210, 108, 672, 887)  # the SVG's viewBox
S = 4  # analysis pixels per SVG unit
MAP_S = 2  # pixels per SVG unit in act.png

# Key points, in SVG units, read off the artwork (see geo_check.png)
SA = (350.75, 293.25)  # SA node: the thick knot where the SVC meets the right atrium, fibres fanning out
AV = (478.0, 488.0)  # AV node: the thick knot where the internodal tracts meet, above the tricuspid ring
AV_BOX = (440.0, 462.0, 512.0, 514.0)  # the slow AV-node zone: the whole knot (x0, y0, x1, y1)
BIF = (549.75, 538.0)  # His bundle divides into the right and left bundle branches, top of the septum
RBB_END = (512.0, 762.0)  # right bundle branch reaches the RV Purkinje network (moderator band region)
LBB_END = (783.75, 625.25)  # left bundle branch, around the apex and up the LV free wall
HIS_OUT = (521.0, 508.5)  # the His bundle, just past the AV-node knot
BACHMANN_GAP = [(534.75, 360.0), (551.25, 349.0)]  # the art breaks where the bundle passes the aorta; bridged

# Beat timing targets (seconds within one beat)
T_ATRIA_END = 0.10  # last of the left atrium (end of the P wave)
T_AV_OUT = 0.125
T_VENT_END = 0.225
BEAT = 0.8


def px(x, y):
    return (int(round((y - VB[1]) * S)), int(round((x - VB[0]) * S)))


def svg_units(r, c):
    return (c / S + VB[0], r / S + VB[1])


# ---------------------------------------------------------------- art layers (monochrome)
svg = open(SRC).read()
i_heart = svg.find('<g id="heart">')
i_cond = svg.find('<g id="conduction-system">')
i_high = svg.find('<g id="conduction-highlights">')
i_end = svg.rfind('</svg>')
heart = svg[i_heart:i_cond]
cond = svg[i_cond:i_high]
high = svg[i_high:i_end]
head = svg[:i_heart]


def inner(g):
    return g[g.find('>') + 1:g.rfind('</g>')]


cond_inner = inner(cond)
cond_paths = re.findall(r'd="([^"]+)"', cond_inner)
art_ts = os.path.join(RM, 'src/data/heartArt.ts')
with open(art_ts, 'w') as f:
    f.write('// Made by 4-animation/build/conduction_geo.py from 3-board/art/heart-conduction-gray.svg. Do not edit.\n')
    f.write(f'export const VIEWBOX = {json.dumps(list(VB))};\n')
    f.write(f'export const HEART = {json.dumps(inner(heart))};\n')
    f.write(f'export const HIGHLIGHTS = {json.dumps(inner(high))};\n')
    f.write(f'export const COND_PATHS: string[] = {json.dumps(cond_paths)};\n')

# ---------------------------------------------------------------- mask of the conduction layer
W, H = VB[2] * S, VB[3] * S
mask_svg = os.path.join(TMP, 'cond_mask.svg')
with open(mask_svg, 'w') as f:
    f.write(head.replace(f'width="{VB[2]}" height="{VB[3]}"', f'width="{W}" height="{H}"'))
    f.write(re.sub(r'fill:[^;"]+', 'fill:#000', cond))
    f.write('</svg>')
mask_png = os.path.join(TMP, 'cond_mask.png')
shot = os.path.join(TMP, 'shot.js')
with open(shot, 'w') as f:
    f.write("""const {chromium}=require('playwright');
(async()=>{const [src,out,w,h]=process.argv.slice(2);const b=await chromium.launch();
const p=await b.newPage({viewport:{width:+w,height:+h}});await p.goto('file://'+src);
await p.screenshot({path:out});await b.close();})();""")
env = dict(os.environ, NODE_PATH=subprocess.check_output(['npm', 'root', '-g']).decode().strip())
subprocess.check_call(['node', shot, mask_svg, mask_png, str(W), str(H)], env=env)
gray = np.array(Image.open(mask_png).convert('L'))
art_mask = gray < 128
m = closing(art_mask, disk(3))
m = remove_small_objects(m, max_size=500)
# bridge Bachmann's bundle across the aorta
walk = m.copy()
br = Image.fromarray(np.zeros_like(m, dtype=np.uint8))
ImageDraw.Draw(br).line([px(*BACHMANN_GAP[0])[::-1], px(*BACHMANN_GAP[1])[::-1]], fill=1, width=6 * S)
walk |= np.array(br).astype(bool)

# ---------------------------------------------------------------- regions and speeds
rr, cc = np.mgrid[0:H, 0:W]
X = cc / S + VB[0]
Y = rr / S + VB[1]
in_av = (X >= AV_BOX[0]) & (X <= AV_BOX[2]) & (Y >= AV_BOX[1]) & (Y <= AV_BOX[3])
vent = ((Y > AV_BOX[3]) | ((X > AV_BOX[2]) & (Y > AV_BOX[1] + 30))) & ~in_av
atr = ~in_av & ~vent


def solve(v_a, v_av, v_v):
    cost = np.full(m.shape, np.inf)
    cost[walk & atr] = 1.0 / v_a
    cost[walk & in_av] = 1.0 / v_av
    cost[walk & vent] = 1.0 / v_v
    mcp = MCP_Geometric(cost / S)  # per pixel: S pixels = 1 SVG unit
    t, _ = mcp.find_costs([px(*SA)])
    return t, mcp


def measure(t):
    tin = np.min(np.where(in_av & walk, t, np.inf))
    tout = t[px(*HIS_OUT)]
    tend = np.max(np.where(vent & walk & np.isfinite(t), t, -np.inf))
    tatr = np.max(np.where(atr & walk & np.isfinite(t), t, -np.inf))
    return tin, tout, tend, tatr


v = [1000.0, 1000.0, 1000.0]  # SVG units per second, solved below
for _ in range(8):
    t, mcp = solve(*v)
    tin, tout, tend, tatr = measure(t)
    print(v, tin, tout, tend)
    v[0] *= tatr / T_ATRIA_END
    t_av_in = tin * T_ATRIA_END / tatr  # where AV entry lands once the atrial speed is solved
    v[1] *= (tout - tin) / (T_AV_OUT - t_av_in)
    v[2] *= (tend - tout) / (T_VENT_END - T_AV_OUT)
t, mcp = solve(*v)
tin, tout, tend, tatr = measure(t)
print(f'speeds (units/s) atria {v[0]:.0f}, AV {v[1]:.0f}, ventricles {v[2]:.0f};'
      f' AV in {tin * 1000:.0f} ms, out {tout * 1000:.0f} ms, last Purkinje {tend * 1000:.0f} ms')
t_atr_max = np.max(np.where(atr & walk & np.isfinite(t), t, -np.inf))
print(f'last atrial tissue reached at {t_atr_max * 1000:.0f} ms')
ACT_MAX = float(np.max(t[np.isfinite(t) & walk]))

# ---------------------------------------------------------------- activation map png (dilated past the art's edge)
tt = np.where(walk & np.isfinite(t), t, np.nan)
known = ~np.isnan(tt)
dist, (ir, ic) = ndimage.distance_transform_edt(~known, return_indices=True)
filled = tt[ir, ic]
filled[dist > 4 * S] = np.nan
small = filled[::S // MAP_S, ::S // MAP_S]
enc = np.where(np.isnan(small), 255, np.clip(np.round(small / ACT_MAX * 250), 0, 250)).astype(np.uint8)
os.makedirs(os.path.join(RM, 'public/maps'), exist_ok=True)
Image.fromarray(enc, 'L').save(os.path.join(RM, 'public/maps/act.png'))


# ---------------------------------------------------------------- routes (the main impulse) and branch fronts
def route(end, step=2.0):
    r = mcp.traceback(px(*end))
    pts = []
    last = None
    for (a, b) in r:
        x, y = svg_units(a, b)
        if last is None or np.hypot(x - last[0], y - last[1]) >= step:
            pts.append([round(x, 1), round(y, 1), round(float(t[a, b]), 5)])
            last = (x, y)
    a, b = r[-1]
    x, y = svg_units(a, b)
    pts.append([round(x, 1), round(y, 1), round(float(t[a, b]), 5)])
    return pts


routes = {
    'toAV': route(AV),
    'toBif': route(BIF),
    'rbb': route(RBB_END),
    'lbb': route(LBB_END),
}
on_route = np.zeros_like(m)
for pts in routes.values():
    for x, y, _ in pts:
        r0, c0 = px(x, y)
        on_route[max(0, r0 - 10 * S):r0 + 10 * S, max(0, c0 - 10 * S):c0 + 10 * S] = True

# skeleton edges for the small fronts on the other branches
sk = skeletonize(m)
nb = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - 1
nb = np.where(sk, nb, 0)
junction = sk & (nb >= 3)
seg = sk & ~ndimage.binary_dilation(junction, iterations=1)
lab, n = ndimage.label(seg, structure=np.ones((3, 3)))
fronts = []
for k in range(1, n + 1):
    rs, cs = np.nonzero(lab == k)
    if len(rs) < 12 * S:  # shorter than 12 units: too small to carry a visible front
        continue
    if on_route[rs, cs].mean() > 0.5:
        continue
    ts = t[rs, cs]
    if not np.all(np.isfinite(ts)):
        continue
    order = np.argsort(ts)
    pts = []
    last = None
    for j in order:
        x, y = svg_units(rs[j], cs[j])
        if last is None or np.hypot(x - last[0], y - last[1]) >= 2.5:
            pts.append([round(x, 1), round(y, 1), round(float(ts[j]), 5)])
            last = (x, y)
    # keep fronts that travel (monotonic in space): drop branches where time and path disagree badly
    path_len = sum(np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    chord = len(rs) / S
    if path_len > 1.6 * chord:
        continue
    fronts.append(pts)
print(f'{len(fronts)} branch fronts')

data = {
    'note': 'Made by 4-animation/build/conduction_geo.py. SVG units; t in seconds after the SA node fires.',
    'viewBox': VB,
    'actMax': round(ACT_MAX, 5),
    'beat': BEAT,
    'speeds': {'atria': round(v[0]), 'avNode': round(v[1]), 'ventricles': round(v[2])},
    'times': {'avIn': round(float(tin), 4), 'avOut': round(float(tout), 4), 'ventEnd': round(float(tend), 4),
              'atriaEnd': round(float(t_atr_max), 4)},
    'points': {'SA': SA, 'AV': AV, 'BIF': BIF, 'RBB_END': RBB_END, 'LBB_END': LBB_END, 'HIS_OUT': HIS_OUT},
    'routes': routes,
    'fronts': fronts,
}
with open(os.path.join(RM, 'src/data/conduction.json'), 'w') as f:
    json.dump(data, f, separators=(',', ':'))

# ---------------------------------------------------------------- check image
vis = np.full((H // 2, W // 2, 3), 255, np.uint8)
tt2 = filled[::2, ::2]
ok = ~np.isnan(tt2) & art_mask[::2, ::2]
cm = (tt2[ok] / ACT_MAX)
vis[ok] = np.stack([255 * cm, 80 + 100 * (1 - cm), 255 * (1 - cm)], -1).astype(np.uint8)
im = Image.fromarray(vis)
d = ImageDraw.Draw(im)
q = lambda x, y: ((x - VB[0]) * S / 2, (y - VB[1]) * S / 2)
for name, pts in routes.items():
    d.line([q(x, y) for x, y, _ in pts], fill=(0, 0, 0), width=3)
for pts in fronts:
    d.line([q(x, y) for x, y, _ in pts], fill=(0, 160, 0), width=2)
for name, (x, y) in data['points'].items():
    X0, Y0 = q(x, y)
    d.ellipse([X0 - 8, Y0 - 8, X0 + 8, Y0 + 8], outline=(0, 0, 0), width=3)
    d.text((X0 + 10, Y0 - 10), name, fill=(0, 0, 0))
im.save(os.path.join(HERE, 'geo_check.png'))
print('ok', ACT_MAX)
