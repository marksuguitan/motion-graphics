# YouTube thumbnail options (1280x720), Comma Clinical look. Run: python3 make_thumbs.py  -> thumb_A/B/C.svg (+ PNG via render.js)
import math, os
HERE = os.path.dirname(os.path.abspath(__file__))
C = dict(white="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A", mute="#B9B5AE",
         coral="#F0645A", red="#C94A44", deoxy="#8A3C6B", hb="#F1DCD6", alert="#E53935", teal="#2E9C8F")
H = "font-family:Manrope"; B = "font-family:Inter"
def sat(p, p50=27, n=2.7): return 100 * p**n / (p**n + p50**n)
def curve(x0, y0, w, h, p50=27, col=C["red"], sw=14, extra=""):
    pts = []
    for i in range(0, 101):
        p = i
        pts.append(f"{x0 + p / 100 * w:.1f},{y0 + h - sat(p, p50) / 100 * h:.1f}")
    return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round" {extra}/>'
def axes(x0, y0, w, h, sw=6):
    return (f'<path d="M{x0},{y0} V{y0+h} H{x0+w}" fill="none" stroke="{C["ink"]}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
def card(x, y, w, h, r=32, fill=C["white"]):
    return (f'<rect x="{x}" y="{y+10}" width="{w}" height="{h}" rx="{r}" fill="#222" opacity="0.10" filter="url(#soft)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
def t(x, y, s, size, weight=800, fill=C["ink"], font=H, anchor="start", ls=None):
    st = f"{font};font-size:{size}px;font-weight:{weight}" + (f";letter-spacing:{ls}px" if ls else "")
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" style="{st}" fill="{fill}">{s}</text>'
def svg(name, *parts):
    s = ('<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="720" viewBox="0 0 1280 720">'
         '<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="14"/></filter></defs>'
         f'<rect width="1280" height="720" fill="{C["soft"]}"/>' + "".join(parts) + '</svg>')
    open(os.path.join(HERE, name), "w").write(s)

# A: the curve itself, big; title left
gx, gy, gw, gh = 700, 150, 470, 420
P50x, P50y = gx + 27 / 100 * gw, gy + gh / 2
svg("thumb_A.svg",
    card(620, 80, 600, 560),
    axes(gx, gy, gw, gh),
    f'<line x1="{gx}" y1="{P50y}" x2="{P50x}" y2="{P50y}" stroke="{C["mute"]}" stroke-width="4" stroke-dasharray="12 10"/>',
    curve(gx, gy, gw, gh),
    f'<circle cx="{P50x}" cy="{P50y}" r="18" fill="{C["white"]}" stroke="{C["coral"]}" stroke-width="8"/>',
    t(P50x + 30, P50y + 12, "P50", 40, 800, C["coral"]),
    t(80, 250, "OXYHEMOGLOBIN", 36, 700, C["ink2"], ls=4),
    t(76, 360, "Oxygen", 120, 800),
    t(76, 480, "Curve", 120, 800),
    t(80, 570, "explained in 4 minutes", 40, 500, C["ink2"], B))

# B: right vs left shift, "Right means release"
gx, gy, gw, gh = 120, 150, 560, 440
svg("thumb_B.svg",
    card(60, 80, 680, 560),
    axes(gx, gy, gw, gh),
    curve(gx, gy, gw, gh, 20, C["mute"], 10),
    curve(gx, gy, gw, gh, 27, C["red"], 12, 'opacity="0.35"'),
    curve(gx, gy, gw, gh, 36, C["red"], 14),
    f'<path d="M{gx+0.22*gw:.0f},{gy+gh*0.5:.0f} h120 m-26,-22 l26,22 l-26,22" fill="none" stroke="{C["alert"]}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>',
    t(800, 270, "Right", 120, 800, C["red"]),
    t(800, 390, "means", 90, 700),
    t(800, 510, "release", 120, 800, C["red"]),
    t(804, 590, "The O₂ dissociation curve", 34, 600, C["ink2"], B))

# C: hemoglobin tetramer + one O2 binding, "Why S-shaped?"
cx, cy, r = 360, 380, 105
subs = [(cx - 115, cy - 105), (cx + 115, cy - 105), (cx - 115, cy + 105), (cx + 115, cy + 105)]
heme = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{C["hb"]}"/><circle cx="{x}" cy="{y}" r="24" fill="{C["red"]}"/>' for x, y in subs)
o2 = lambda x, y: (f'<circle cx="{x-17}" cy="{y}" r="24" fill="{C["coral"]}"/><circle cx="{x+17}" cy="{y}" r="24" fill="{C["coral"]}"/>'
                   + t(x, y + 12, "O₂", 30, 800, C["white"], anchor="middle"))
svg("thumb_C.svg",
    card(60, 80, 600, 560),
    heme,
    f'<circle cx="{subs[0][0]}" cy="{subs[0][1]}" r="{r+16}" fill="none" stroke="{C["alert"]}" stroke-width="8"/>',
    o2(subs[0][0], subs[0][1]),
    f'<path d="M545,170 q-60,-40 -120,-10" fill="none" stroke="{C["ink"]}" stroke-width="6" stroke-linecap="round" stroke-dasharray="2 14"/>',
    o2(585, 175),
    t(740, 230, "OXYGEN–HEMOGLOBIN CURVE", 26, 700, C["ink2"], ls=3),
    t(736, 360, "Why is it", 96, 800),
    t(736, 480, "S-shaped?", 96, 800, C["red"]),
    t(740, 560, "Cooperative binding, P50, shifts", 32, 500, C["ink2"], B))
print("ok")
