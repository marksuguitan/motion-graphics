"""Electrical Alternans, Stage 4 planner (After Effects path).

Turns the 25 flattened beats (ai_src/layers.json, from library/scripts/adobe/flatten.py) and the measured word
times into an After Effects build plan (ae_plan.json) and the generated build script (build_ae.jsx).
Adapted on 2026-11-18 from the Pulsus Paradoxus planner. Inputs, all in this folder unless noted:

  ai_src/layers.json       layer list per beat (python3 ../../../../library/scripts/adobe/flatten.py refs.json ai_src ../../3-board/art/*.svg)
  geom.json                bbox, opacity and needle geometry per layer (node ae_geom.js ai_src geom.json, Playwright)
  timeline.json            beat starts in the stitched track (build_animatic.py timeline)
  ../../3-board/timings/sync_points.csv, word_timings.csv
  ../layer_map.json        sync layer names that differ from the SVG ids

Motion follows Comma Clinical (design.medzcool.com, Mark 2026-11-18: "let's tighten things up"): no crossfades or
dissolves anywhere. Per beat precomp, every layer gets one of:
  static   same art as the previous beat in the scene: on for the whole beat (a pulse if the notes sync it)
  enter    new layer on its sync word, else at the beat start: text cuts on whole; a wide form unfolds from its left
           edge; anything else grows from its centre (snap and settle, 0.6 s, no overshoot). Same-time entries stagger 2 frames.
  move     art that is the same form at a new place, size or tone: the previous beat's copy travels and scales about its
           centre (snap 0.6 s, or cross 0.75 s over 300 px), then hands over to this beat's art
  swap     changed text: the old cuts off and the new cuts on, on the word
  redraw   a trace that changes in place: it prints again from the left and the old one is erased by the same front
  exit     text cuts off; a form shrinks into the centre of its group (accelerate, 0.3 s), groups 2 frames apart
At the end of each scene everything collapses the same way (no scene crossfade), and the next scene builds from empty.
All beat and scene times sit on whole frames (v1 had a blank frame at 0:11:28 where two beats missed a frame).
Plus the overrides at the bottom (1A box, 1B strip carry, trace draw-ons, bar wipes, the swinging heart, the needle, the drain).

Run: python3 ae_plan.py   ->   ae_plan.json, ae_check_times.json, build_ae.jsx
"""
import csv, json, re, hashlib, pathlib
import xml.etree.ElementTree as ET

HERE = pathlib.Path(__file__).resolve().parent
VIDEO = HERE.parent.parent
LIB = VIDEO.parent.parent / "library" / "scripts" / "adobe"
SRC = HERE / "ai_src"
NS = "{http://www.w3.org/2000/svg}"
TITLE = "Electrical Alternans"
AUDIO_REL = "../3-board/audio/"            # relative to 4-animation/ (the engine's root)

L = json.load(open(SRC / "layers.json"))
G = json.load(open(HERE / "geom.json"))
TL = {b["id"]: b for b in json.load(open(HERE / "timeline.json"))["beats"]}
LMAP = json.load(open(VIDEO / "4-animation" / "layer_map.json"))
BEATS = sorted(L)
bid = lambda k: k.split("_")[0]
TEXTY = ("Title", "Caption", "Label", "Labels/", "Question", "Line_", "Card/Label", "Number/")
FPS = 30
fr = lambda x: round(x * FPS) / FPS                    # on a whole frame (full precision: 4 decimals left 1-frame gaps)
SHAPES = ("path", "line", "rect", "circle", "ellipse", "polygon", "polyline", "image", "use")


def is_text(key, name):
    """True when the layer is only type (cuts on and off instead of growing or shrinking)."""
    root = ET.parse(SRC / f"{key}.svg").getroot()
    spec = next(x for x in L[key] if x["name"] == name)
    g = root.find(f".//{NS}g[@id='{spec['id']}']")
    tags = {e.tag.replace(NS, "") for e in g.iter()}
    return "text" in tags and not (tags & set(SHAPES))


def has_text(key, name):
    root = ET.parse(SRC / f"{key}.svg").getroot()
    spec = next(x for x in L[key] if x["name"] == name)
    g = root.find(f".//{NS}g[@id='{spec['id']}']")
    return any(e.tag == NS + "text" for e in g.iter())

SYNC = []
for r in csv.DictReader(open(VIDEO / "3-board/timings/sync_points.csv", newline="")):
    lay = LMAP.get(r["beat"], {}).get(r["layer"], r["layer"])
    for x in lay.split("+"):
        SYNC.append({"beat": r["beat"], "layer": x, "t": float(r["start_in_beat_s"]), "word": r["sync"]})
WORDS = {}
for r in csv.DictReader(open(VIDEO / "3-board/timings/word_timings.csv", newline="")):
    WORDS.setdefault(r["beat"], []).append({"text": r["word"], "start": float(r["start_in_beat_s"]), "end": float(r["end_in_beat_s"])})


def layer_sigs(key):
    root = ET.parse(SRC / f"{key}.svg").getroot()
    out = {}
    for spec in L[key]:
        g = root.find(f".//{NS}g[@id='{spec['id']}']")
        inner = "".join(ET.tostring(c, encoding="unicode") for c in g)
        inner = re.sub(r'\sid="[^"]*"', "", inner)
        inner = re.sub(r'\sopacity="1(\.0)?"', "", inner)      # a no-op opacity is not a change (3E paper, 2026-11-18)
        out[spec["name"]] = hashlib.md5(inner.encode()).hexdigest()[:10]
    return out


SIG = {k: layer_sigs(k) for k in BEATS}


def match(sync_layer, name):
    return name == sync_layer or name.endswith("/" + sync_layer) or sync_layer.endswith("/" + name)


def syncs(b, name):
    return sorted({r["t"] for r in SYNC if r["beat"] == b and match(r["layer"], name)})


def bbox(key, name):
    g = G[key][name]
    return dict(cx=g["x"] + g["w"] / 2, cy=g["y"] + g["h"] / 2, w=g["w"], h=g["h"], op=g["wrapOpacity"])


GAP_SPLIT = 0.5                              # half of the 1.0 s scene gap before a scene, half after
plan = {"fps": FPS, "w": 1920, "h": 1080, "scenes": [], "layer_counts": {k: len(v) for k, v in L.items()}}
SCENES = sorted({k[0] for k in BEATS})
STAG = 2 / FPS
for sc in SCENES:
    keys = [k for k in BEATS if k[0] == sc]
    first, last = TL[bid(keys[0])], TL[bid(keys[-1])]
    s_start = 0.0 if sc == SCENES[0] else fr(first["start"] - GAP_SPLIT)
    nxt = [TL[b]["start"] for b in TL if b[0] == str(int(sc) + 1)]
    s_end = fr(min(nxt) - GAP_SPLIT) if nxt else fr(last["end"] + 3.0)
    scene = {"name": f"Scene {sc}", "start": s_start, "dur": fr(s_end - s_start), "beats": []}
    for i, key in enumerate(keys):
        b = bid(key)
        t0 = fr(TL[b]["start"] - s_start) if i else 0.0
        t_end = fr(TL[bid(keys[i + 1])]["start"] - s_start) if i + 1 < len(keys) else scene["dur"]
        dur = fr(t_end - t0)
        vo_off = round(TL[b]["start"] - s_start - t0, 3)
        prev = keys[i - 1] if i else None
        cur = [x["name"] for x in L[key]]
        hidden = {x["name"] for x in L[key] if x.get("hidden")}
        prev_names = {x["name"] for x in L[prev]} if prev else set()
        acts = []
        for nm in cur:
            ts = [t + vo_off for t in syncs(b, nm)]
            a = {"layer": nm, "src": key}
            if nm in hidden:
                a["hidden"] = True
            cb = bbox(key, nm)
            if nm in ("Background", "Grid"):
                a["do"] = "static"
            elif nm not in prev_names:
                a.update(do="enter", t=round(ts[0], 3) if ts else (0.0 if not prev else vo_off), synced=bool(ts), c=[cb["cx"], cb["cy"]])
                if is_text(key, nm):
                    a["how"] = "cut"
                elif cb["w"] > 700 or (cb["h"] > 0 and cb["w"] > 2.5 * cb["h"]) or cb["h"] < 1:
                    a.update(how="wipe", d=0.6)
                else:
                    a.update(how="grow", d=0.6)
            elif SIG[prev][nm] == SIG[key][nm] and bbox(prev, nm) == cb:
                a["do"] = "static"
                a["c"] = [cb["cx"], cb["cy"]]
                if ts:
                    a["bump"] = [round(ts[0], 3), 1.04]
            else:
                pb = bbox(prev, nm)
                t = round(ts[0], 3) if ts else 0.0
                sx = cb["w"] / pb["w"] if pb["w"] > 0.5 else 1.0
                sy = cb["h"] / pb["h"] if pb["h"] > 0.5 else 1.0
                dx, dy = cb["cx"] - pb["cx"], cb["cy"] - pb["cy"]
                same_box = abs(dx) < 1 and abs(dy) < 1 and abs(sx - 1) < 0.01 and abs(sy - 1) < 0.01
                tone_only = same_box and abs(pb["op"] - cb["op"]) >= 0.01
                if is_text(key, nm) and not tone_only and not (abs(sx - sy) < 0.04 * max(sx, sy) and not same_box):
                    a.update(do="swap", prev=prev, prevLayer=nm, t=t)
                elif same_box and abs(pb["op"] - cb["op"]) < 0.01:
                    a.update(do="redraw", prev=prev, prevLayer=nm, t=t, d=1.0)
                else:
                    if abs(sx - sy) < 0.04 * max(sx, sy):
                        sx = sy = (sx + sy) / 2
                    elif has_text(key, nm):
                        sx = sy = 1.0                # type inside: travel without squashing it (left edges aligned), the new art lands at the end
                        dx = (cb["cx"] - cb["w"] / 2) - (pb["cx"] - pb["w"] / 2)
                    far = (dx * dx + dy * dy) ** 0.5 > 300
                    d = 0.3 if same_box else (0.75 if far else 0.6)
                    a.update(do="move", prev=prev, prevLayer=nm, t=t, d=d, curve="cross" if far else "snap",
                             pc=[round(pb["cx"], 1), round(pb["cy"], 1)], dx=round(dx, 1), dy=round(dy, 1),
                             sx=round(sx, 4), sy=round(sy, 4), op0=pb["op"], op1=cb["op"])
            acts.append(a)
        if prev:
            gone = [x["name"] for x in L[prev] if x["name"] not in set(cur)]
            groups = []
            for nm in gone:
                g = nm.split("/")[0]
                if g not in groups:
                    groups.append(g)
            for nm in gone:
                if is_text(prev, nm):
                    acts.append({"layer": nm, "src": prev, "do": "exit", "how": "cut", "t": 0.0})
                    continue
                g = nm.split("/")[0]
                bs = [bbox(prev, x) for x in gone if x.split("/")[0] == g]
                x0 = min(q["cx"] - q["w"] / 2 for q in bs); x1 = max(q["cx"] + q["w"] / 2 for q in bs)
                y0 = min(q["cy"] - q["h"] / 2 for q in bs); y1 = max(q["cy"] + q["h"] / 2 for q in bs)
                acts.append({"layer": nm, "src": prev, "do": "exit", "how": "shrink", "t": 0.0, "d": 0.25,
                             "delay": round(min(groups.index(g) / FPS, 0.1), 3), "c": [round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)]})
        # forms that travel together share one curve: if any of them crosses the frame, they all use cross (4C leads, 5C figure)
        mv = [a for a in acts if a["do"] == "move" and not (abs(a["dx"]) < 1 and abs(a["dy"]) < 1 and a["sx"] == 1 and a["sy"] == 1)]
        if any(a["curve"] == "cross" for a in mv):
            for a in mv:
                a.update(curve="cross", d=0.75)
        scene["beats"].append({"id": b, "key": key, "start": t0, "dur": dur, "vo": AUDIO_REL + f"{b}.mp3", "vo_at": vo_off, "acts": acts})
    plan["scenes"].append(scene)


# ---------------- overrides ----------------
def beat(b):
    for s in plan["scenes"]:
        for x in s["beats"]:
            if x["id"] == b:
                return s, x
    raise KeyError(b)


def act(b, layer):
    _, x = beat(b)
    for a in x["acts"]:
        if a["layer"] == layer and a["do"] != "exit":
            return a
    raise KeyError(f"{b} {layer}")


def W(b, word, n=1):
    """precomp time of the n-th occurrence of a word in beat b."""
    _, x = beat(b)
    ws = [w for w in WORDS[b] if re.sub(r"[^a-z0-9']", "", w["text"].lower()) == word]
    return round(ws[n - 1]["start"] + x["vo_at"], 3)


def reveal(b, layer, t, d, angle=270, curve="linear"):
    a = act(b, layer)
    a.update(do="reveal", t=round(t, 3), d=d, angle=angle, curve=curve)
    a.pop("how", None)


# ---- Mark's notes on v1 (2026-11-18), scene 1 ----
# 1A: the caption cuts on at the second "Tall." (0:04:23), not at "every other QRS" (0:09:17)
act("1A", "Caption")["t"] = W("1A", "tall", 2)
# 1A: a box outlines the tall QRS on "Tall.", then snaps across to the short QRS on "Short.", and cuts off on "regular"
TALL_X, SHORT_X = 966, 1165                  # R peaks of the 5th and 6th beats of the 1A strip (keyframes_gen.ecg, V5, amp 150)
box = lambda x0, y0, x1, y1: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
_, b1a = beat("1A")
b1a["acts"].append({"layer": "Strip/Box", "do": "morph", "t0": W("1A", "short", 2), "t1": round(W("1A", "short", 2) + 0.5, 3),
                    "inAt": W("1A", "tall", 2), "cut_at": W("1A", "regular"), "curve": "snap",
                    "from": box(TALL_X - 32, 436, TALL_X + 32, 634), "to": box(SHORT_X - 32, 504, SHORT_X + 32, 626),
                    "color": [1.0, 0.251, 0.341], "w0": 4, "w1": 4})
# 1B: the strip already on screen carries on: it shrinks a little and slides down under the title (no new strip, no fade)
for nm in ("Strip/Paper", "Strip/Trace", "Strip/Marks_tall", "Strip/Marks_short"):
    a = act("1B", nm)
    a.clear()
    a.update(layer=nm, src="1A_strip", do="carry", t=0.0, d=0.75, curve="cross", pivot=[960, 540], to=[960, 770], s=0.82)


# ECG traces draw on left to right
reveal("1A", "Strip/Trace", W("1A", "look"), 2.0)
reveal("6A", "Strip/Trace", 0.0, 1.6)
reveal("4F", "Strips/Bigeminy/Strip", W("4F", "bigeminy"), 1.2)
reveal("4F", "Strips/Alternans", W("4F", "alternans"), 1.2)
reveal("5D", "Breath/Curve/Trace", W("5D", "drop"), 1.2)
# bars grow from their left end on their word; the rules wipe in
for b, nm, w in (("5C", "Bars/Dyspnea", "shortness"), ("5C", "Bars/Tachy", "fast"), ("5C", "Bars/JVP", "raised"), ("5E", "Bars/Pulsus", "eight")):
    reveal(b, nm, W(b, w), 0.6, curve="snap")
reveal("4E", "Rules/Rule_1", W("4E", "see"), 0.6, curve="snap")
reveal("4E", "Rules/Rule_2", W("4E", "don't"), 0.6, curve="snap")
# the numbers land with a small bump
for nm in ("Number/Sens", "Number/Spec"):
    act("4D", nm)["bump"] = 1.08

# the swinging heart: the heart travels to the ghost position and back, one swing every two beats
HEART = "Cross_section/Heart"
g3 = G["3D_swing"]
SW_DX = round(g3["Cross_section/Heart_ghost"]["x"] - g3[HEART]["x"], 1)
SW_DY = round(g3["Cross_section/Heart_ghost"]["y"] - g3[HEART]["y"], 1)
PERIOD = 1.2                                 # s per swing (two beats at 100/min)


def swing(b, layer, start, stop=None, dx=SW_DX, dy=SW_DY, video_t0=None, ramp=True):
    """position expression: k goes 0 -> 1 -> 0 each PERIOD, phase locked to video time so the swing runs on across beats.
    ramp=False when the heart is already swinging at the start of the beat (3D, 3E carry on from 3C)."""
    s, x = beat(b)
    a = act(b, layer)
    vt0 = s["start"] + x["start"]
    stop_expr = f"Math.max(0, 1 - (time - {stop:.3f}) / 0.8)" if stop is not None else "1"
    ramp_expr = f"Math.min(1, Math.max(0, (time - {start:.3f}) / 0.6))" if ramp else "1"
    a.update(exprpos=(f"var tv = time + {vt0:.3f}; var on = {ramp_expr} * "
                      f"(time < {stop if stop is not None else 1e9:.3f} ? 1 : {stop_expr}); "
                      f"var k = (1 - Math.cos(2 * Math.PI * tv / {PERIOD})) / 2 * on; value + [{dx} * k, {dy} * k];"))


swing("3C", HEART, W("3C", "swing"))
swing("3D", HEART, 0.0, ramp=False)
swing("3E", HEART, 0.0, stop=W("3E", "stops"), ramp=False)
# 3E: the needle drains the fluid on "fluid"
act("3E", "Cross_section/Sac/Fluid").update(do="drain", t=W("3E", "fluid"), d=1.6)
# 6B "think swinging heart": the mini heart swings to its ghost
g6 = G["6B_checklist"]
swing("6B", "Heart_mini/Heart", W("6B", "swinging"),
      dx=round(g6["Heart_mini/Heart_ghost"]["x"] - g6["Heart_mini/Heart"]["x"], 1),
      dy=round(g6["Heart_mini/Heart_ghost"]["y"] - g6["Heart_mini/Heart"]["y"], 1))

# 5D-5F gauge: the needle dips with each breath in (pulsus paradoxus), 4 s breaths, phase from video time
for b in ("5D", "5E", "5F"):
    s, x = beat(b)
    n = G[x["key"]]["Cuff/Gauge/Needle"]["needle"]
    vt0 = s["start"] + x["start"]
    a = act(b, "Cuff/Gauge/Needle")
    a.update(do="expr", pivot=n["tail"],
             expr=f"var tv = time + {vt0:.3f}; -14 * Math.max(0, Math.sin(2 * Math.PI * tv / 4.0)) + 1.5 * Math.sin(2 * Math.PI * tv / 0.6);")
    a.pop("t", None)

# a layer whose name only changed level between beats (3A "Cards/Electrics" -> 3B "Cards/Electrics/Other" + "/List") stays put:
# the old cuts and the new cuts on at the same frame
for s_ in plan["scenes"]:
    for x in s_["beats"]:
        ents = [a for a in x["acts"] if a["do"] == "enter"]
        for e_ in [a for a in x["acts"] if a["do"] == "exit"]:
            kids = [a for a in ents if a["layer"].startswith(e_["layer"] + "/") or e_["layer"].startswith(a["layer"] + "/")]
            same = [a for a in kids if not a.get("synced")]
            if kids:
                e_.update(how="cut", t=0.0)
                for a in same:
                    a.update(how="cut", t=0.0, keep=True)

# the end-screen placeholder stays out of the picture until the real end card is built
act("6C", "End_screen")["hidden"] = True

# entries wait for the exits of their beat to clear; entries at the same moment stagger 2 frames (under 0.4 s in all)
for s_ in plan["scenes"]:
    for x in s_["beats"]:
        ex = [a for a in x["acts"] if a["do"] == "exit" and a.get("how") == "shrink"]
        allex = [a for a in x["acts"] if a["do"] == "exit"]
        rest = [a for a in x["acts"] if a["do"] != "exit" and a["layer"] not in ("Background", "Grid") and not a.get("hidden")]
        if ex:
            # a word that lands while the old forms are still leaving: they all leave at once, faster
            if any(a["do"] in ("enter", "reveal") and a.get("t", 0) < 0.35 and (a.get("synced") or a["do"] == "reveal") for a in rest):
                for a in ex:
                    a.update(delay=0.0, d=0.2)
            clear = max(a["delay"] + a["d"] for a in ex)
            for a in x["acts"]:
                if a["do"] == "enter" and not a.get("synced") and not a.get("keep") and a["t"] < clear:
                    a["t"] = round(clear, 3)
        # nothing else on screen until a later word (4E): the old forms wait and leave just before it, so the frame is never empty
        if allex and rest and all(a["do"] in ("enter", "reveal", "morph") for a in rest):
            first = min(a.get("t", a.get("t0", 0)) for a in rest)
            if first > 0.5:
                for a in allex:
                    a["t"] = round(first - 0.3, 3)
        by_t = {}
        for a in x["acts"]:
            if a["do"] == "enter" and not a.get("hidden"):
                by_t.setdefault(round(a["t"], 2), []).append(a)
        by_t = {k: [a for a in v if not a.get("keep")] for k, v in by_t.items()}
        for t_, grp in by_t.items():
            if not grp:
                continue
            step = min(STAG, 0.4 / len(grp))
            for k, a in enumerate(grp):
                a["t"] = round(a["t"] + k * step, 3)

# 5D: the needle arrives once the gauge face has grown
act("5D", "Cuff/Gauge/Needle")["in_at"] = round(act("5D", "Cuff/Gauge/Face")["t"] + 0.3, 3)

# scene changes (no crossfade): the last beat of each scene collapses its forms into points and cuts its text, ending on the
# scene's last frame; the next scene builds from the empty frame
for s_ in plan["scenes"]:
    x = s_["beats"][-1]
    names = [a["layer"] for a in x["acts"] if a["do"] not in ("exit",) and a["layer"] not in ("Background", "Grid")]
    texts = [nm for nm in names if nm in {q["name"] for q in L[x["key"]]} and is_text(x["key"], nm)]
    gs, centers = [], {}
    for nm in names:
        g = nm.split("/")[0]
        if nm in texts or g in gs:
            continue
        gs.append(g)
    for g in gs:
        bs = [bbox(x["key"], q["name"]) for q in L[x["key"]] if q["name"].split("/")[0] == g]
        if not bs:
            centers[g] = [960, 540]
            continue
        x0 = min(q["cx"] - q["w"] / 2 for q in bs); x1 = max(q["cx"] + q["w"] / 2 for q in bs)
        y0 = min(q["cy"] - q["h"] / 2 for q in bs); y1 = max(q["cy"] + q["h"] / 2 for q in bs)
        centers[g] = [round((x0 + x1) / 2, 1), round((y0 + y1) / 2, 1)]
    delays = {g: round(min(k * STAG, 0.2), 3) for k, g in enumerate(gs)}
    d = 0.3
    t = fr(x["dur"] - d - max(delays.values() or [0]) - 1 / FPS)
    x["collapse"] = {"t": t, "d": d, "centers": centers, "delays": delays, "text": texts}
    s_["xfade_in"] = 0.0

# check frames: every beat start and 0.9 s after every sync point (where the move has landed), in video time
checks = []
for s in plan["scenes"]:
    for x in s["beats"]:
        vt0 = s["start"] + x["start"]
        checks.append({"t": round(vt0 + 0.3, 2), "file": f"{vt0 + 0.3:07.2f}_{x['id']}_start.png"})
        for r in SYNC:
            if r["beat"] == x["id"]:
                tv = vt0 + x["vo_at"] + r["t"] + 0.9
                checks.append({"t": round(tv, 2), "file": f"{tv:07.2f}_{x['id']}_{re.sub('[^A-Za-z0-9]+', '-', r['layer'])}.png"})
# v2 extras: the 1A box on the tall and the short QRS, the 1B strip mid-carry, and every scene change mid-collapse
_s1, _b1 = beat("1A")
for tv, nm in ((W("1A", "tall", 2) + 0.3, "1A_box-tall"), (W("1A", "short", 2) + 0.7, "1A_box-short"),
               (beat("1B")[1]["start"] + 0.35, "1B_strip-carry"), (beat("1B")[1]["start"] + 1.2, "1B_title")):
    checks.append({"t": round(tv, 2), "file": f"{tv:07.2f}_{nm}.png"})
for s in plan["scenes"]:
    x = s["beats"][-1]
    tv = s["start"] + x["start"] + x["collapse"]["t"] + 0.12
    checks.append({"t": round(tv, 2), "file": f"{tv:07.2f}_{x['id']}_collapse.png"})
    tv = s["start"] + 0.2
    checks.append({"t": round(tv, 2), "file": f"{tv:07.2f}_{s['beats'][0]['id']}_build.png"})
checks.sort(key=lambda c: c["t"])

json.dump(plan, open(HERE / "ae_plan.json", "w"), indent=1)
json.dump([[c["t"], c["file"]] for c in checks], open(HERE / "ae_check_times.json", "w"))

# ---------------- build_ae.jsx from the library engine ----------------
eng = (HERE / "ae_engine_comma.jsx").read_text(encoding="utf-8")      # the library engine with Comma Clinical motion
eng = eng.replace("Pulsus Paradoxus", TITLE)
eng = eng.replace('root + "/assets/" + key + ".ai"', 'root + "/ai/" + key + ".ai"')
eng = eng.replace('Folder(root + "/assets/_fresh/" + key + "_" + stamp)', 'Folder(root + "/ai/_fresh/" + key + "_" + stamp)')
eng = eng.replace('importAudio("audio/" + bt.vo)', "importAudio(bt.vo)")
eng = re.sub(r'\n\s*if \(s === 0\) \{ var ca = importAudio\("audio/cues/cueA_1A.wav"\);[^\n]*', "", eng)
eng = re.sub(r'\n\s*if \(S.name === "Scene 5"\) \{ var cbI[^\n]*', "", eng)
eng = eng.replace('aep = File(root + "/' + TITLE + '.aep")', 'aep = File(root + "/' + TITLE + '.aep")')
assert "__PLAN__" in eng and "__CHECKS__" in eng and "__ONLY__" in eng
jsx = eng.replace("__PLAN__", json.dumps(plan, separators=(",", ":"))).replace("__CHECKS__", json.dumps(checks, separators=(",", ":"))).replace("__ONLY__", "null")
(HERE / "build_ae.jsx").write_text(jsx, encoding="utf-8")

from collections import Counter
print(Counter(a["do"] for s in plan["scenes"] for x in s["beats"] for a in x["acts"]))
for s in plan["scenes"]:
    print(s["name"], s["start"], s["dur"], [(x["id"], x["start"], x["dur"]) for x in s["beats"]])
print("checks", len(checks))
