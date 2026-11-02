"""Pulsus Paradoxus Shorts (Mark approved 2026-10-27): three vertical 1080x1920 cut-downs of the finished master comp,
reusing its VO and animation. Hook title on top, the 16:9 master at full width in the middle, burned-in captions from
the measured word timings (words_now.json) below it. Writes shorts_plan.json and build_shorts.jsx."""
import json, re
P = json.load(open("/tmp/claude-0/ae/plan.json")); Wd = json.load(open("/tmp/claude-0/wt/words_now.json"))
OFF = P["intro"]["dur"]
beat = {}
for s in P["scenes"]:
    for b in s["beats"]:
        beat[b["id"]] = OFF + s["start"] + b["start"] + b.get("vo_at", 0.0)   # master time of the beat's VO t=0
# Mark 2026-10-27: each Short ends on a call to action to watch the full video on YouTube (3.5 s; the logo lands on one
# heartbeat from audio/cues/Heartbeat_endcard.wav, lub 0.40 s measured).
CTA_DUR = 3.5
CTA = dict(audio="audio/cues/Heartbeat_endcard.wav", lub=0.40, lines=["Watch the full video", "on YouTube"],
           sub="Pulsus paradoxus, explained in 4 minutes", pill="TAP THE LINK BELOW")
SHORTS = [
    dict(n=1, name="Short 1 - What is it", title=["Your pulse fades", "when you breathe in"],
         segs=[(4.0, 26.04, ["1A", "1B"]), (54.69, 67.86, ["2D"])]),
    dict(n=2, name="Short 2 - Why tamponade", title=["Why tamponade", "causes pulsus paradoxus"],
         segs=[(80.54, 132.78, ["3A", "3B", "3C", "3D"])]),
    dict(n=3, name="Short 3 - How to measure", title=["How to measure", "pulsus paradoxus"],
         segs=[(179.86, 219.66, ["5A", "5B", "5C", "5D", "5E"])]),
]
def phrases(words):
    """Greedy lines of <= 24 characters, broken at punctuation; a word that ends a clause may stretch a line to 30."""
    out, cur = [], []
    for w in words:
        txt = " ".join(x["text"] for x in cur + [w])
        ends = re.search(r"[.,:;?!]$", w["text"])
        if cur and len(txt) > (30 if ends else 24):
            out.append(cur); cur = []
        cur.append(w)
        if ends: out.append(cur); cur = []
    if cur: out.append(cur)
    return out
for S in SHORTS:
    t0, layers, caps = 0.0, [], []
    for a, b, ids in S["segs"]:
        layers.append(dict(start=round(t0 - a, 4), inp=round(t0, 4), out=round(t0 + b - a, 4), master_in=a, master_out=b))
        for bid in ids:
            for ph in phrases(Wd[bid]):
                ms = beat[bid] + ph[0]["start"]; me = beat[bid] + ph[-1]["end"]
                if ms < a - 0.05 or me > b + 0.05: continue
                caps.append(dict(t=round(t0 + ms - a, 3), end=round(t0 + me - a, 3), text=" ".join(x["text"] for x in ph)))
        t0 += b - a
    for i, c in enumerate(caps):          # hold each phrase until the next one starts (or 0.5 s past its last word)
        nxt = caps[i + 1]["t"] if i + 1 < len(caps) else c["end"] + 0.5
        c["off"] = round(min(nxt, c["end"] + 0.6), 3)
    S.update(dur=round(t0, 3), layers=layers, caps=caps)
    S["cta"] = round(t0, 3); S["total"] = round(t0 + CTA_DUR, 3)
    S["checks"] = [1.0, round(t0 * 0.5, 2), round(t0 - 0.5, 2), round(t0 + 0.5, 2), round(t0 + CTA_DUR - 0.3, 2)]
plan = dict(master="Pulsus Paradoxus", w=1080, h=1920, fps=30, bg="#151515", grid="#1F2021", acc="#FF4057", fg="#F2F2F2",
            video=dict(scale=56.25, pos=[540, 964]), cta=CTA, shorts=SHORTS)
json.dump(plan, open("/tmp/claude-0/shorts/shorts_plan.json", "w"), indent=1)
for S in SHORTS: print(S["name"], S["dur"], len(S["caps"]), [c["text"] for c in S["caps"][:6]])
JS = open("/tmp/claude-0/shorts/shorts_engine.jsx").read().replace("__PLAN__", json.dumps(plan, separators=(",", ":")))
open("/tmp/claude-0/shorts/build_shorts.jsx", "w").write(JS)
