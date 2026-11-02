# YouTube thumbnails, Oxygen Hemoglobin Curve (Comma Clinical look). Run: python3 make_thumbnails.py
# Writes thumb_A/B/C.html (temporary), then renders 1280x720 PNGs with headless Chrome (fonts: Manrope, Inter, installed on the Mac).
# Curves use the Hill equation S = P^n / (P^n + P50^n), n = 2.7; P50 27 (normal), 36 (right) and 20 (left) as in the video.
import subprocess, os
C = dict(bg="#F7F7F5", card="#FFFFFF", ink="#222222", ink2="#6A6A6A", grid="#E6E4E0", mute="#B9B5AE",
         coral="#F0645A", teal="#2E9C8F", red="#C94A44")
W, H = 1280, 720
def curve(x0, y0, w, h, p50, n=2.7, pmax=100):
    pts = []
    for i in range(201):
        p = pmax * i / 200
        s = p**n / (p**n + p50**n) if p > 0 else 0
        pts.append(f"{x0 + w * p / pmax:.1f},{y0 + h * (1 - s):.1f}")
    return " ".join(pts)
def S(p, p50, n=2.7): return p**n / (p**n + p50**n)
def graph(x, y, w, h, curves, extra=""):
    g = [f'<rect x="{x-40}" y="{y-40}" width="{w+80}" height="{h+90}" rx="28" fill="{C["card"]}" filter="url(#sh)"/>']
    for v in (25, 50, 75, 100):
        g.append(f'<line x1="{x}" x2="{x+w}" y1="{y + h*(1-v/100):.1f}" y2="{y + h*(1-v/100):.1f}" stroke="{C["grid"]}" stroke-width="2"/>')
    g.append(f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y+h}" stroke="{C["ink"]}" stroke-width="4" stroke-linecap="round"/>')
    g.append(f'<line x1="{x}" y1="{y+h}" x2="{x+w}" y2="{y+h}" stroke="{C["ink"]}" stroke-width="4" stroke-linecap="round"/>')
    for p50, col, sw in curves:
        g.append(f'<polyline points="{curve(x, y, w, h, p50)}" fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
    return "".join(g) + extra
def page(name, body):
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden;background:{C["bg"]}}}
.h{{font-family:Manrope;font-weight:800;fill:{C["ink"]}}} .s{{font-family:Inter;font-weight:500;fill:{C["ink2"]}}}
</style></head><body><svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs><filter id="sh" x="-20%" y="-20%" width="140%" height="150%"><feDropShadow dx="0" dy="10" stdDeviation="16" flood-color="#222" flood-opacity="0.10"/></filter></defs>
<rect width="{W}" height="{H}" fill="{C["bg"]}"/>{body}</svg></body></html>'''
    open(name + ".html", "w").write(html)
    subprocess.run(["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={W},{H}", "--force-device-scale-factor=1", "--virtual-time-budget=3000",
                    f"--screenshot={os.path.abspath(name + '.png')}", "file://" + os.path.abspath(name + ".html")], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# A: the curve itself, with its P50 landmark
gx, gy, gw, gh = 720, 150, 470, 430
px, py = gx + gw * 27 / 100, gy + gh * 0.5
A = graph(gx, gy, gw, gh, [(27, C["coral"], 9)],
          f'<line x1="{gx}" y1="{py}" x2="{px}" y2="{py}" stroke="{C["mute"]}" stroke-width="3" stroke-dasharray="8 8"/>'
          f'<line x1="{px}" y1="{py}" x2="{px}" y2="{gy+gh}" stroke="{C["mute"]}" stroke-width="3" stroke-dasharray="8 8"/>'
          f'<circle cx="{px}" cy="{py}" r="14" fill="{C["ink"]}"/>'
          f'<text x="{px+26}" y="{py+40}" class="h" font-size="40">P50</text>')
page("thumb_A", A + f'''<text x="80" y="290" class="h" font-size="104">Oxygen</text>
<text x="80" y="400" class="h" font-size="104" style="fill:{C["coral"]}">curve</text>
<text x="84" y="475" class="s" font-size="40">Why it's an S</text>''')

# B: right means release (normal curve grey, right shift coral, arrow between them high on the curve, where the gap is widest)
gx, gy, gw, gh = 640, 150, 560, 430
sv = 0.86; k = (sv / (1 - sv)) ** (1 / 2.7)
yy, x1, x2 = gy + gh * (1 - sv), gx + gw * 27 * k / 100, gx + gw * 36 * k / 100
B = graph(gx, gy, gw, gh, [(27, C["mute"], 7), (36, C["coral"], 9)],
          f'<line x1="{x1 + 22}" y1="{yy}" x2="{x2 - 46}" y2="{yy}" stroke="{C["ink"]}" stroke-width="7" stroke-linecap="round"/>'
          f'<polygon points="{x2 - 26},{yy} {x2 - 50},{yy-13} {x2 - 50},{yy+13}" fill="{C["ink"]}"/>')
page("thumb_B", B + f'''<text x="80" y="300" class="h" font-size="112" style="fill:{C["coral"]}">Right</text>
<text x="80" y="410" class="h" font-size="70">means release</text>
<text x="84" y="485" class="s" font-size="38">The O₂–hemoglobin curve</text>''')

# C: left or right? both shifts around the normal curve
gx, gy, gw, gh = 760, 150, 440, 430
Cc = graph(gx, gy, gw, gh, [(27, C["mute"], 7), (20, C["teal"], 9), (36, C["coral"], 9)],
           f'<text x="{gx + gw*0.08}" y="{gy + 60}" class="h" font-size="40" style="fill:{C["teal"]}">Left</text>'
           f'<text x="{gx + gw*0.62}" y="{gy + gh*0.86}" class="h" font-size="40" style="fill:{C["coral"]}">Right</text>')
page("thumb_C", Cc + f'''<text x="80" y="280" class="h" font-size="84">Which way</text>
<text x="80" y="370" class="h" font-size="84">does it <tspan style="fill:{C["coral"]}">shift?</tspan></text>
<text x="84" y="445" class="s" font-size="36">The O₂–hemoglobin curve</text>''')
print("ok")
