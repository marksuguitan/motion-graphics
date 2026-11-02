# YouTube end screen style frames, Oxygen Hemoglobin Curve (Comma Clinical look). Run: python3 make_endscreen.py <out_dir>
# Two layouts, each drawn at its end state. The dashed 16:9 plates and the circle are where Mark places the YouTube
# end-screen elements in YouTube Studio (YouTube draws the real thumbnails and subscribe button on top).
# Layer ids use Group/Sublayer (Illustrator reads "_x2F_" as "/").
import sys, os
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
C = dict(white="#FFFFFF", soft="#F7F7F5", div="#E6E4E0", ink="#222222", ink2="#6A6A6A", mute="#B9B5AE",
         coral="#F0645A", coralsoft="#FDE3E0", teal="#2E9C8F", tealsoft="#DDF0ED", red="#C94A44")
H = "font-family:Manrope"; B = "font-family:Inter"
# Medzcool mark: the two polygons from the approved Pulsus Paradoxus end card (endcard_gen.py), 69.66 x 44.72 units
POLYS = [[13.98, 28.07, 4.31, 28.07, 0, 35.85, 18.54, 35.85, 23.46, 27.04, 34.59, 44.72, 38.86, 36.91, 23.06, 11.81],
         [61.63, 19.81, 50.85, 1.86, 41.25, 18.59, 29.55, 0, 25.33, 7.9, 41.56, 33.67, 51, 17.22, 57.23, 27.59, 65.77, 27.59, 69.66, 19.81]]

def L(s): return s.replace("/", "_x2F_")
def group(name, *items): return f'<g id="{L(name)}">' + "\n".join(items) + '</g>'
def text(x, y, s, size=28, weight=400, fill=C["ink"], font=B, anchor="start", ls=None):
    st = f"{font};font-size:{size}px;font-weight:{weight}" + (f";letter-spacing:{ls}px" if ls else "")
    return f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" style="{st}" fill="{fill}">{s}</text>'
def card(x, y, w, h, fill=C["white"], r=24):
    return (f'<rect x="{x}" y="{y+8}" width="{w}" height="{h}" rx="{r}" fill="#222222" opacity="0.08" filter="url(#soft)"/>'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}"/>')
def logo(x, y, w, col=C["ink"]):
    k = w / 69.66
    pts = lambda p: " ".join(f"{x + p[i]*k:.1f},{y + p[i+1]*k:.1f}" for i in range(0, len(p), 2))
    return "".join(f'<polygon points="{pts(p)}" fill="{col}"/>' for p in POLYS)
def plate(name, x, y, w, label, sub):
    h = w * 9 / 16
    return group(name, f'<rect x="{x}" y="{y}" width="{w}" height="{h:.0f}" rx="16" fill="{C["soft"]}" stroke="{C["mute"]}" stroke-width="3" stroke-dasharray="14 10"/>',
                 text(x + w/2, y + h/2 - 6, label, 30, 600, C["ink2"], H, anchor="middle"),
                 text(x + w/2, y + h/2 + 34, sub, 22, 400, C["ink2"], anchor="middle"))
def sub_circle(cx, cy, r=100):
    return group("Slot/Subscribe", f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{C["soft"]}" stroke="{C["mute"]}" stroke-width="3" stroke-dasharray="14 10"/>',
                 text(cx, cy + 10, "Subscribe", 26, 600, C["ink2"], H, anchor="middle"))
def save(name, *parts):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">'
           '<defs><filter id="soft" x="-20%" y="-20%" width="140%" height="160%"><feGaussianBlur stdDeviation="12"/></filter></defs>\n'
           + group("Background/Fill", f'<rect width="1920" height="1080" fill="{C["soft"]}"/>') + "\n" + "\n".join(parts) + "\n</svg>")
    open(os.path.join(OUT, name), "w").write(svg)

# A: one big "Watch next" plate in the video's stage card, sign-off in the side card (continues the video's layout:
# the stage card and side card stay; the graph clears and the plate draws on in the stage card).
save("endscreen_A.svg",
     group("Header/Kicker", text(120, 96, "THE OXYHEMOGLOBIN DISSOCIATION CURVE", 23, 700, C["ink2"], H, ls=3)),
     group("Background/Stage", card(96, 150, 1080, 840)),
     group("Label/WatchNext", text(156, 236, "WATCH NEXT", 23, 700, C["ink2"], H, ls=3)),
     plate("Slot/Video", 156, 276, 960, "Next video", "YouTube end-screen element"),
     group("Panel/Card", card(1240, 150, 600, 840)),
     group("Logo/Mark", logo(1288, 214, 150)),
     group("Panel/Thanks", text(1288, 400, "Thanks for watching", 46, 600, C["ink"], H),
           text(1288, 452, "Right means release.", 28, 400, C["ink2"])),
     sub_circle(1540, 690))

# B: two plates side by side (YouTube "next video" + "best for viewer"), logo, sign-off and subscribe across the top
save("endscreen_B.svg",
     group("Logo/Mark", logo(120, 112, 120)),
     group("Panel/Thanks", text(280, 150, "Thanks for watching", 52, 600, C["ink"], H),
           text(282, 200, "Right means release.", 28, 400, C["ink2"])),
     sub_circle(1700, 160, 90),
     group("Label/WatchNext", text(120, 356, "WATCH NEXT", 23, 700, C["ink2"], H, ls=3), text(1000, 356, "RECOMMENDED", 23, 700, C["ink2"], H, ls=3)),
     plate("Slot/Video", 120, 390, 800, "Next video", "YouTube end-screen element"),
     plate("Slot/Best", 1000, 390, 800, "Best for viewer", "YouTube end-screen element"))
print("done")
