# Mark's heart-conduction-system art (art.json, 8000x8000 units) split for the beat frames.
import json, re, math
SA = (2160, 2300); AV = (3320, 3400)

def flatten(d):
    """Return points of an SVG path (handles M L H V C S Q Z, absolute and relative)."""
    tok = re.findall(r"[MmLlHhVvCcSsQqZz]|-?(?:\d+\.?\d*|\.\d+)(?:e-?\d+)?", d)
    i, cmd, x, y, sx, sy, pts = 0, None, 0.0, 0.0, 0.0, 0.0, []
    def n():
        nonlocal i; i += 1; return float(tok[i-1])
    while i < len(tok):
        if re.match(r"[A-Za-z]", tok[i]): cmd = tok[i]; i += 1
        if cmd in "Zz": x, y = sx, sy; pts.append((x, y)); continue
        rel = cmd.islower(); c = cmd.upper()
        ox, oy = (x, y) if rel else (0, 0)
        if c == "M": x, y = ox + n(), oy + n(); sx, sy = x, y; pts.append((x, y)); cmd = "l" if rel else "L"
        elif c == "L": x, y = ox + n(), oy + n(); pts.append((x, y))
        elif c == "H": x = (x if rel else 0) + n(); pts.append((x, y))
        elif c == "V": y = (y if rel else 0) + n(); pts.append((x, y))
        elif c == "C": n(); n(); n(); n(); x, y = ox + n(), oy + n(); pts.append((x, y))
        elif c in "SQ": n(); n(); x, y = ox + n(), oy + n(); pts.append((x, y))
        else: i += 1
    return pts

def region(d):
    p = flatten(d)
    xs = [q[0] for q in p]; ys = [q[1] for q in p]
    cx, cy = (min(xs)+max(xs))/2, (min(ys)+max(ys))/2
    if math.hypot(cx-SA[0], cy-SA[1]) < 420: return "sa"
    if math.hypot(cx-AV[0], cy-AV[1]) < 300: return "av"
    if cy < 3300 or (cx < 3150 and cy < 4300): return "atria"
    return "his"

def load(path):
    A = json.load(open(path))
    heart = A["heart"]
    cond = {"sa": [], "av": [], "atria": [], "his": []}
    for d, _ in A["cond"]: cond[region(d)].append(d)
    return heart, cond
