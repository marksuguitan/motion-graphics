#!/usr/bin/env python3
"""conduction_geo.py: turns Mark's conduction heart into animation data for the Remotion build.

Input:  3-board/art/heart-conduction-natural.svg  (Mark's simplified heart, Nov 2, 2026; same as
        marksuguitan/motion assets/anatomy/heart/heart-conduction-natural.svg). Traced art: 570 paths, no layers;
        the conduction system is the orange paths (hue 18 deg or more, saturation above 45%).
Output (into 4-animation/remotion/):
  src/data/heartArt.ts      the conduction-system paths with their grey (before) and charcoal (after) fills
  public/maps/heart.png     the heart without its conduction system, in greys, with its soft shadow (drawn once)
  public/maps/act.png       activation-time map of the conduction system (R = time / ACT_MAX, 255 = never)
  src/data/conduction.json  ACT_MAX, layout, key points, the main impulse routes and the branch fronts, each as
                            [x, y, t] in SVG units and seconds of one beat (t = 0 when the SA node fires)
  ../build/geo_check.png    a check image: the activation map with the routes drawn on

Timing: a fastest-path time from the SA node through the drawn pathway, with one speed for the atria, a slow one
inside the AV node, and one each for the right and left ventricular conduction (bundle branch + Purkinje). The
speeds are solved so that, within one 0.8 s beat:
  the far left atrium is reached at T_ATRIA_END (end of the P wave); the impulse leaves the AV node at T_AV_OUT;
  the last right-ventricular fiber is reached at T_RV_END and the last left-ventricular fiber at T_LV_END
  (nearly together, the left a little later: Mark's note, Nov 2, 2026).
These are modelled values for the picture, inside StatPearls' normal ranges (PR 120-200 ms, QRS under 120 ms);
no number is shown on screen.

Run:  python3 conduction_geo.py   (needs numpy, scipy, scikit-image, Pillow, and node + playwright)
"""
import colorsys
import json
import os
import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from skimage.graph import MCP_Geometric
from skimage.morphology import closing, disk, remove_small_objects, skeletonize

HERE = os.path.dirname(os.path.abspath(__file__))
VIDEO = os.path.dirname(os.path.dirname(HERE))
SRC = os.path.join(VIDEO, '3-board/art/heart-conduction-natural.svg')
RM = os.path.join(VIDEO, '4-animation/remotion')
TMP = os.path.join(HERE, 'tmp_geo')
os.makedirs(TMP, exist_ok=True)

S = 0.5  # analysis pixels per SVG unit
MAP_DOWN = 2  # act.png is the analysis grid downsampled by this

# Key points, in SVG units, read off the artwork (see geo_check.png); snapped to the drawn pathway
SA = (2184.0, 2303.0)  # SA node: the round node high in the right atrium, by the SVC
AV_BOX = (3080.0, 3180.0, 3570.0, 3640.0)  # AV node: the round node above the septum (x0, y0, x1, y1), slow zone
AV = (3326.0, 3407.0)  # inside the AV node
HIS_OUT = (3624.0, 3385.0)  # the His bundle, just past the AV node
BIF = (4128.0, 3927.0)  # the His bundle divides into the right and left bundle branches
SEPTUM = [(4220.0, 3700.0), (5100.0, 7230.0)]  # a line down the septum: right ventricle to its left, left ventricle to its right

T_ATRIA_END = 0.10
T_AV_OUT = 0.125
T_RV_END = 0.215
T_LV_END = 0.225
BEAT = 0.8

# Monochrome mapping (lightness of the original -> grey)
HEART_GREY = (0x8E, 0xE6)  # darkest and lightest grey for the heart
PATH_GREY = (0xE6, 0xFF)  # the conduction system before the impulse
LIT_GREY = (0x16, 0x46)  # after the impulse

# ---------------------------------------------------------------- art: classify, recolour, keep paint order
svg = open(SRC).read()
VB = [float(v) for v in re.search(r'viewBox="([^"]+)"', svg).group(1).split()]
items = re.findall(r'<path style="([^"]*)" d="([^"]*)"\s*/>', svg)
art = []
lum = []
for style, d in items:
    hexc = re.search(r'fill:#([0-9A-Fa-f]{6})', style).group(1)
    r, g, b = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    is_cond = h * 360 >= 18 and s > 0.45
    art.append([d, is_cond, 0.2126 * r + 0.7152 * g + 0.0722 * b])
heart_l = [a[2] for a in art if not a[1]]
cond_l = [a[2] for a in art if a[1]]
lo_h, hi_h = np.percentile(heart_l, 3), np.percentile(heart_l, 97)
lo_c, hi_c = min(cond_l), max(cond_l)


def grey(v, lo, hi, rng):
    k = min(1, max(0, (v - lo) / (hi - lo + 1e-9)))
    return '#%02X%02X%02X' % ((round(rng[0] + k * (rng[1] - rng[0])),) * 3)


out = []
for d, is_cond, L in art:
    if is_cond:
        out.append([d, 1, grey(L, lo_c, hi_c, PATH_GREY), grey(L, lo_c, hi_c, LIT_GREY)])
    else:
        out.append([d, 0, grey(L, lo_h, hi_h, HEART_GREY), ''])
with open(os.path.join(RM, 'src/data/heartArt.ts'), 'w') as f:
    f.write('// Made by 4-animation/build/conduction_geo.py from 3-board/art/heart-conduction-natural.svg. Do not edit.\n')
    f.write('// Every path in paint order: [d, isConduction, fill, litFill].\n')
    f.write(f'export const VIEWBOX = {json.dumps(VB)};\n')
    f.write(f'export const COND_ART: [string, string, string][] = {json.dumps([[o[0], o[2], o[3]] for o in out if o[1]], separators=(",", ":"))};\n')
print(f'{len(out)} paths, {sum(o[1] for o in out)} conduction')

# The heart itself (everything but the conduction system) is drawn once to a PNG with its soft shadow, so each video
# frame only draws the conduction system as vectors. Conduction paths go on top of the heart: checked against the
# original paint order, fewer than 100 pixels at 804 px wide differ.
DISPLAY_H = 960  # px the heart is shown at (must match NormalConduction.tsx)
IMG_SCALE = 2 * DISPLAY_H / VB[3]  # PNG pixels per SVG unit (2x the display size)
MARGIN = 0.06 * VB[2]
HB = [VB[0] - MARGIN, VB[1] - MARGIN, VB[2] + 2 * MARGIN, VB[3] + 2 * MARGIN]
hw, hh = int(HB[2] * IMG_SCALE), int(HB[3] * IMG_SCALE)
k = DISPLAY_H / VB[3]
heart_svg = os.path.join(TMP, 'heart.svg')
with open(heart_svg, 'w') as f:
    f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{HB[0]} {HB[1]} {HB[2]} {HB[3]}" width="{hw}" height="{hh}">')
    f.write(f'<defs><filter id="s" x="-10%" y="-10%" width="120%" height="125%"><feDropShadow dx="0" dy="{10 / k}" '
            f'stdDeviation="{14 / k}" flood-color="#000" flood-opacity="0.12"/></filter></defs><g filter="url(#s)">')
    for d, is_cond, fill, _ in out:
        if not is_cond:
            f.write(f'<path d="{d}" fill="{fill}" stroke="{fill}" stroke-width="0.73"/>')
    f.write('</g></svg>')
HEART_IMG = {'x': HB[0], 'y': HB[1], 'w': HB[2], 'h': HB[3]}


# ---------------------------------------------------------------- mask of the conduction system
W, H = int(VB[2] * S), int(VB[3] * S)
head = svg[:svg.find('<path')]
mask_svg = os.path.join(TMP, 'cond_mask.svg')
with open(mask_svg, 'w') as f:
    f.write(re.sub(r'width="[^"]+" height="[^"]+"', f'width="{W}" height="{H}"', head, count=1))
    for d, is_cond, _ in art:
        c = '#000' if is_cond else '#fff'
        f.write(f'<path fill="{c}" stroke="{c}" stroke-width="0.73" d="{d}"/>')
    f.write('</svg>')
mask_png = os.path.join(TMP, 'cond_mask.png')
shot = os.path.join(TMP, 'shot.js')
with open(shot, 'w') as f:
    f.write("""const {chromium}=require('playwright');
(async()=>{const [src,out,w,h]=process.argv.slice(2,6);const b=await chromium.launch();
const p=await b.newPage({viewport:{width:+w,height:+h}});await p.goto('file://'+src);
await p.screenshot({path:out,omitBackground:process.argv[6]==='transparent'});await b.close();})();""")
env = dict(os.environ, NODE_PATH=subprocess.check_output(['npm', 'root', '-g']).decode().strip())
subprocess.check_call(['node', shot, mask_svg, mask_png, str(W), str(H)], env=env)
subprocess.check_call(['node', shot, heart_svg, os.path.join(RM, 'public/maps/heart.png'), str(hw), str(hh), 'transparent'], env=env)
art_mask = np.array(Image.open(mask_png).convert('L')) < 128
m = closing(art_mask, disk(3))
m = remove_small_objects(m, max_size=500)
walk = m


def px(x, y):
    return (int(round((y - VB[1]) * S)), int(round((x - VB[0]) * S)))


def svg_units(r, c):
    return (c / S + VB[0], r / S + VB[1])


# ---------------------------------------------------------------- regions and speeds
rr, cc = np.mgrid[0:H, 0:W]
X = cc / S + VB[0]
Y = rr / S + VB[1]
in_av = (X >= AV_BOX[0]) & (X <= AV_BOX[2]) & (Y >= AV_BOX[1]) & (Y <= AV_BOX[3])
# below the AV node is ventricular, except the atrial tract that runs down the right atrium's back wall (lower left)
vent = (((Y > AV_BOX[3]) & ~((X < AV_BOX[0]) & (Y < 4400))) | ((X > AV_BOX[2]) & (Y > AV_BOX[1]))) & ~in_av
(sx0, sy0), (sx1, sy1) = SEPTUM
side = (X - sx0) * (sy1 - sy0) - (Y - sy0) * (sx1 - sx0)  # > 0: right of the septum line on screen (left ventricle)
# the His bundle above the split belongs to neither side: it gets the right side's speed (one trunk)
trunk = (X < BIF[0] + 40) & (Y < BIF[1] + 40)
lv = vent & (side > 0) & ~trunk
rv = vent & ~lv
atr = ~in_av & ~vent


def solve(v):
    cost = np.full(m.shape, np.inf)
    cost[walk & atr] = 1.0 / v['atr']
    cost[walk & in_av] = 1.0 / v['av']
    cost[walk & rv] = 1.0 / v['rv']
    cost[walk & lv] = 1.0 / v['lv']
    mcp = MCP_Geometric(cost * 1.0 / S)
    t, _ = mcp.find_costs([px(*SA)])
    return t, mcp


def last(t, reg):
    tv = np.where(reg & walk & np.isfinite(t), t, -1.0)
    i = np.unravel_index(np.argmax(tv), tv.shape)
    return float(tv[i]), i


def measure(t):
    tin = float(np.min(np.where(in_av & walk, t, np.inf)))
    tout = float(t[px(*HIS_OUT)])
    return tin, tout, last(t, atr)[0], last(t, rv)[0], last(t, lv)[0]


v = {'atr': 5000.0, 'av': 600.0, 'rv': 8000.0, 'lv': 8000.0}
for it in range(10):
    t, mcp = solve(v)
    tin, tout, tatr, trv, tlv = measure(t)
    print(f'  iter {it}: AV in {tin * 1e3:.0f}, out {tout * 1e3:.0f}, atria {tatr * 1e3:.0f}, RV {trv * 1e3:.0f}, LV {tlv * 1e3:.0f} ms')
    v['atr'] *= tatr / T_ATRIA_END
    t_av_in = tin * T_ATRIA_END / tatr
    v['av'] *= (tout - tin) / (T_AV_OUT - t_av_in)
    v['rv'] *= (trv - tout) / (T_RV_END - T_AV_OUT)
    v['lv'] *= (tlv - tout) / (T_LV_END - T_AV_OUT)
t, mcp = solve(v)
tin, tout, tatr, trv, tlv = measure(t)
print('last atrial point', svg_units(*last(t, atr)[1]), 'RV end', svg_units(*last(t, rv)[1]), 'LV end', svg_units(*last(t, lv)[1]))
print('speeds (units/s):', {k: round(x) for k, x in v.items()})
print(f'AV in {tin * 1e3:.0f} ms, out {tout * 1e3:.0f} ms, atria end {tatr * 1e3:.0f} ms, RV end {trv * 1e3:.0f} ms, LV end {tlv * 1e3:.0f} ms')
ACT_MAX = float(np.max(t[np.isfinite(t) & walk]))
RV_END = svg_units(*last(t, rv)[1])
LV_END = svg_units(*last(t, lv)[1])

# ---------------------------------------------------------------- routes (the main impulse) and branch fronts
STEP = 8 / S  # sample every 8 analysis px


def route(end):
    r = mcp.traceback(px(*end))
    pts, lastp = [], None
    for (a, b) in r:
        x, y = svg_units(a, b)
        if lastp is None or np.hypot(x - lastp[0], y - lastp[1]) >= STEP:
            pts.append([round(x, 1), round(y, 1), round(float(t[a, b]), 5)])
            lastp = (x, y)
    a, b = r[-1]
    x, y = svg_units(a, b)
    pts.append([round(x, 1), round(y, 1), round(float(t[a, b]), 5)])
    return pts


routes = {'toAV': route(AV), 'toBif': route(BIF), 'rbb': route(RV_END), 'lbb': route(LV_END)}
# inside the AV node, each pixel lights with the nearest point of the impulse's route, so the node fills along the
# orb's crawl instead of a side lobe lighting late
rp = np.array([[px(x, y)[0], px(x, y)[1], tt_] for x, y, tt_ in routes['toBif']])
ar, ac = np.nonzero(in_av & walk)
nearest = np.argmin((ar[:, None] - rp[None, :, 0]) ** 2 + (ac[:, None] - rp[None, :, 1]) ** 2, axis=1)
t[ar, ac] = np.minimum(t[ar, ac], rp[nearest, 2])

# ---------------------------------------------------------------- activation map png (dilated past the art's edge)
tt = np.where(walk & np.isfinite(t), t, np.nan)
known = ~np.isnan(tt)
dist, (ir, ic) = ndimage.distance_transform_edt(~known, return_indices=True)
filled = tt[ir, ic]
# small separate conduction shapes (node highlights) take the time of the nearest pathway
filled[(dist > 10) & ~ndimage.binary_dilation(art_mask, iterations=3)] = np.nan
small = filled[::MAP_DOWN, ::MAP_DOWN]
enc = np.where(np.isnan(small), 255, np.clip(np.round(small / ACT_MAX * 250), 0, 250)).astype(np.uint8)
os.makedirs(os.path.join(RM, 'public/maps'), exist_ok=True)
Image.fromarray(enc, 'L').save(os.path.join(RM, 'public/maps/act.png'))

on_route = np.zeros_like(m)
for pts in routes.values():
    for x, y, _ in pts:
        r0, c0 = px(x, y)
        on_route[max(0, r0 - 40):r0 + 40, max(0, c0 - 40):c0 + 40] = True

sk = skeletonize(m)
nb = ndimage.convolve(sk.astype(int), np.ones((3, 3), int), mode='constant') - 1
nb = np.where(sk, nb, 0)
junction = sk & (nb >= 3)
seg = sk & ~ndimage.binary_dilation(junction, iterations=1)
lab, n = ndimage.label(seg, structure=np.ones((3, 3)))
fronts = []
for k in range(1, n + 1):
    rs, cs = np.nonzero(lab == k)
    if len(rs) < 48 or on_route[rs, cs].mean() > 0.5:
        continue
    ts = t[rs, cs]
    if not np.all(np.isfinite(ts)):
        continue
    pts, lastp = [], None
    for j in np.argsort(ts):
        x, y = svg_units(rs[j], cs[j])
        if lastp is None or np.hypot(x - lastp[0], y - lastp[1]) >= STEP * 1.25:
            pts.append([round(x, 1), round(y, 1), round(float(ts[j]), 5)])
            lastp = (x, y)
    plen = sum(np.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1))
    if plen > 1.6 * len(rs) / S:
        continue
    fronts.append(pts)
print(f'{len(fronts)} branch fronts')

# heart bounding box (for layout)
heart_mask = np.array(Image.open(mask_png).convert('RGB'))
data = {
    'note': 'Made by 4-animation/build/conduction_geo.py. SVG units; t in seconds after the SA node fires.',
    'viewBox': VB,
    'heartImage': HEART_IMG,
    'actMax': round(ACT_MAX, 5),
    'beat': BEAT,
    'speeds': {k: round(x) for k, x in v.items()},
    'times': {'avIn': round(tin, 4), 'avOut': round(tout, 4), 'atriaEnd': round(tatr, 4), 'rvEnd': round(trv, 4),
              'lvEnd': round(tlv, 4), 'ventEnd': round(max(trv, tlv), 4)},
    'points': {'SA': SA, 'AV': AV, 'HIS_OUT': HIS_OUT, 'BIF': BIF, 'RBB_END': [round(c, 1) for c in RV_END],
               'LBB_END': [round(c, 1) for c in LV_END]},
    'routes': routes,
    'fronts': fronts,
}
with open(os.path.join(RM, 'src/data/conduction.json'), 'w') as f:
    json.dump(data, f, separators=(',', ':'))

# ---------------------------------------------------------------- check image
D = 4
vis = np.full((H // D + 1, W // D + 1, 3), 255, np.uint8)[:filled[::D, ::D].shape[0], :filled[::D, ::D].shape[1]]
tt2 = filled[::D, ::D]
ok = ~np.isnan(tt2) & art_mask[::D, ::D]
cm = tt2[ok] / ACT_MAX
vis[ok] = np.stack([255 * cm, 80 + 100 * (1 - cm), 255 * (1 - cm)], -1).astype(np.uint8)
im = Image.fromarray(vis)
dr = ImageDraw.Draw(im)
q = lambda x, y: ((x - VB[0]) * S / D, (y - VB[1]) * S / D)
for pts in routes.values():
    dr.line([q(x, y) for x, y, _ in pts], fill=(0, 0, 0), width=2)
for pts in fronts:
    dr.line([q(x, y) for x, y, _ in pts], fill=(0, 160, 0), width=1)
dr.line([q(*SEPTUM[0]), q(*SEPTUM[1])], fill=(150, 150, 150), width=1)
for name, (x, y) in data['points'].items():
    X0, Y0 = q(x, y)
    dr.ellipse([X0 - 5, Y0 - 5, X0 + 5, Y0 + 5], outline=(0, 0, 0), width=2)
    dr.text((X0 + 7, Y0 - 7), name, fill=(0, 0, 0))
im.save(os.path.join(HERE, 'geo_check.png'))
print('ok', ACT_MAX)
