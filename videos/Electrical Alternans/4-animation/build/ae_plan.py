"""Stage 6 planner: turn the 22 layered beats + measured word times into an AE build plan (plan.json).

Per beat precomp, every layer gets one of:
  static   same art as the previous beat in the scene: on for the whole beat
  enter    new layer: fade (or fade + rise 20 px for text) on its sync word, else at the beat start
  move     same art, new place/size/opacity: the previous beat's copy animates to the new state, then hands over
  xfade    art changed: previous copy fades out while the new one fades in, on the sync word
  exit     layer gone: previous copy fades out at the beat start
plus overrides from the motion notes (needles, breath chip, flows, playhead, chest breath, bumps, readout snaps).
"""
import json, re, hashlib, sys
import xml.etree.ElementTree as ET

SRC = "/tmp/claude-0/ai/svg"
NS = "{http://www.w3.org/2000/svg}"
L = json.load(open(f"{SRC}/layers.json"))
G = json.load(open("/tmp/claude-0/ae/geom.json"))
TL = {b["id"]: b for b in json.load(open(sys.argv[1]))["beats"]}
SYNC = json.load(open(sys.argv[2]))
MK = json.load(open(sys.argv[3]))
BEATS = sorted(L)                          # "1A_cuff", ...
bid = lambda k: k.split("_")[0]
TEXTY = ("Label/", "Title/", "Card/", "Promise/", "Readout/", "Rule_", "Tag/")


def layer_sigs(key):
    root = ET.parse(f"{SRC}/{key}.svg").getroot()
    out = {}
    for spec in L[key]:
        g = root.find(f".//{NS}g[@id='{spec['id']}']")
        w = g
        while len(w) == 1 and w[0].tag == NS + "g" and not w[0].get("id"):
            w = w[0]
        inner = "".join(ET.tostring(c, encoding="unicode") for c in w)
        out[spec["name"]] = hashlib.md5(inner.encode()).hexdigest()[:10]
    return out


SIG = {k: layer_sigs(k) for k in BEATS}


def syncs(b, name):
    """measured sync times (s into beat) for this layer, from the motion notes."""
    ts = []
    for r in SYNC:
        if r["beat"] != b:
            continue
        pats = [p.strip() for p in r["layer"].split(",")]
        for p in pats:
            if p == name or (p.endswith("/*") and name.startswith(p[:-1])) or (p in ("Inflammation", "Lungs/Bronchi") and name.startswith(p.split("/")[0] + "/") and (p != "Lungs/Bronchi" or name.endswith("Bronchi"))) \
               or (p == "Lungs/Vessels" and name.startswith("Lungs/") and name.endswith("Vessels")):
                ts.append(r["start_in_beat_s"])
    return sorted(set(ts))


def alias(name):
    return name[len("Arm_scene/"):] if name.startswith("Arm_scene/Gauge/") else name


def bbox(key, name):
    g = G[key][name]
    return dict(cx=g["x"] + g["w"] / 2, cy=g["y"] + g["h"] / 2, w=g["w"], h=g["h"], op=g["wrapOpacity"])


plan = {"fps": 30, "w": 1920, "h": 1080, "scenes": []}
for sc in "12345":
    keys = [k for k in BEATS if k[0] == sc]
    first, last = TL[bid(keys[0])], TL[bid(keys[-1])]
    s_start = 0.0 if sc == "1" else first["start"] - 0.5     # half the inter-scene gap before, rest after
    nxt = [TL[b]["start"] for b in TL if b[0] == str(int(sc) + 1)]
    s_end = (min(nxt) - 0.5) if nxt else (last["end"] + 2.5)
    scene = {"name": f"Scene {sc}", "start": round(s_start, 3), "dur": round(s_end - s_start, 3), "beats": []}
    for i, key in enumerate(keys):
        b = bid(key)
        t0 = TL[b]["start"] - s_start if i else 0.0                 # precomp start inside the scene comp
        t_end = (TL[bid(keys[i + 1])]["start"] - s_start) if i + 1 < len(keys) else scene["dur"]
        dur = round(t_end - t0, 3)
        vo_off = round(TL[b]["start"] - s_start - t0, 3)           # VO start inside the precomp
        prev = keys[i - 1] if i else None
        cur_names = [x["name"] for x in L[key]]
        hidden = {x["name"] for x in L[key] if x.get("hidden")}
        prev_by_alias = {alias(x["name"]): x["name"] for x in L[prev]} if prev else {}
        acts = []
        for nm in cur_names:
            ts = [t + vo_off for t in syncs(b, nm)]
            a = {"layer": nm, "src": key}
            if nm in hidden:
                a["hidden"] = True
            pn = prev_by_alias.get(alias(nm)) if prev else None
            if nm in ("Background", "Grid"):
                a["do"] = "static"
            elif pn is None:
                a["do"] = "enter"; a["t"] = round(ts[0], 3) if ts else (0.0 if not prev else vo_off)
                a["rise"] = nm.startswith(TEXTY)
                if not prev and not ts:
                    a["t"] = 0.0
            elif SIG[prev][pn] == SIG[key][nm]:
                pb, cb = bbox(prev, pn), bbox(key, nm)
                same = abs(pb["cx"] - cb["cx"]) < 1 and abs(pb["cy"] - cb["cy"]) < 1 and abs(pb["w"] - cb["w"]) < 1 and abs(pb["op"] - cb["op"]) < 0.01
                if same:
                    a["do"] = "static"
                else:
                    a.update(do="move", prev=prev, prevLayer=pn, t=round(ts[0], 3) if ts else 0.0, d=0.6,
                             s=cb["w"] / pb["w"] if pb["w"] else 1, dx=cb["cx"] - pb["cx"], dy=cb["cy"] - pb["cy"], op0=pb["op"], op1=cb["op"])
            else:
                a.update(do="xfade", prev=prev, prevLayer=pn, t=round(ts[0], 3) if ts else 0.0, d=0.4)
            acts.append(a)
        if prev:
            cur_alias = {alias(n) for n in cur_names}
            gone = [x["name"] for x in L[prev] if alias(x["name"]) not in cur_alias]
            for nm in gone:
                acts.append({"layer": nm, "src": prev, "do": "exit", "t": 0.0, "d": 0.4, "z": "prev"})
        scene["beats"].append({"id": b, "key": key, "start": round(t0, 3), "dur": dur, "vo": f"{b}.mp3", "vo_at": vo_off, "acts": acts})
    plan["scenes"].append(scene)


# ---------------- overrides from the motion notes ----------------
def beat(b):
    for s in plan["scenes"]:
        for x in s["beats"]:
            if x["id"] == b:
                return s, x


def act(b, layer):
    s, x = beat(b)
    for a in x["acts"]:
        if a["layer"] == layer and a["do"] != "exit":
            return a


def W(b, word, n=1):
    """time of the n-th occurrence of a word in beat b, as precomp time."""
    s, x = beat(b)
    ws = [w for w in WORDS[b] if re.sub(r"[^a-z']", "", w["text"].lower()) == word]
    return round(ws[n - 1]["start"] + x["vo_at"], 3)


WORDS = json.load(open(sys.argv[4]))
DROP = 8.0  # deg per mmHg, drop gauge


def needle(b, key):
    n = G[key]["Gauge/Needle"]["needle"]; hubs = G[key]["__hubs"]
    import math
    tail, tip = n["tail"], n["tip"]
    def dist(p):  # hub closest to the needle line
        ax, ay = tip[0] - tail[0], tip[1] - tail[1]; L2 = ax * ax + ay * ay
        u = max(0, min(1, ((p[0] - tail[0]) * ax + (p[1] - tail[1]) * ay) / L2))
        return math.hypot(tail[0] + u * ax - p[0], tail[1] + u * ay - p[1])
    piv = min(hubs, key=dist)
    return piv, n["angle"]


# needles: rotate from the previous beat's angle on the sync word (drop gauges, Scenes 2-4; Scene 1 static)
for s in plan["scenes"]:
    for i, x in enumerate(s["beats"]):
        a = act(x["id"], "Gauge/Needle")
        if not a or x["id"][0] in "15":
            continue
        piv, ang = needle(x["id"], x["key"])
        if a["do"] in ("xfade", "move") or (i and a["do"] == "enter"):
            pang = needle(s["beats"][i - 1]["id"], s["beats"][i - 1]["key"])[1] if i else ang
            d = (ang - pang + 180) % 360 - 180
            a.clear(); a.update(layer="Gauge/Needle", src=x["key"], do="rotate", pivot=piv, keys=[[0, -d], [ (syncs(x["id"], "Gauge/Needle") or [0])[0] + x["vo_at"], -d], [(syncs(x["id"], "Gauge/Needle") or [0])[0] + x["vo_at"] + 0.4, 0]])
# 2D: needle dips 0 -> 8 mmHg on "dips", back to 0 on "back"
a = act("2D", "Gauge/Needle"); _, x = beat("2D"); piv, _ = needle("2D", x["key"])
a.clear(); a.update(layer="Gauge/Needle", src=x["key"], do="rotate", pivot=piv,
                    keys=[[0, 0], [W("2D", "dips"), 0], [W("2D", "dips") + 0.4, 8 * DROP], [W("2D", "back"), 8 * DROP], [W("2D", "back") + 0.4, 0]])

# Scene 5: one continuous deflation, needle by expression (notes): 144.5 mmHg at the 5B in-point, 2.0 mmHg/s, 1 deg per mmHg
cb = MK["cueB"]
art_val = {"5B": 142, "5C": 132, "5D": 116, "5E": 116}
for b, v in art_val.items():
    s, x = beat(b); a = act(b, "Gauge/Needle"); piv, _ = needle(b, x["key"])
    vt0 = s["start"] + x["start"]          # video time of the precomp start
    a.clear(); a.update(layer="Gauge/Needle", src=x["key"], do="expr", pivot=piv,
                        expr=f"var rate = {cb['rate_mmHg_s']}; var v0 = {cb['start_cuff_mmHg']}; var tVideo = time + {vt0:.3f}; "
                             f"(v0 - rate*(tVideo - {cb['starts_at_video_s']})) - {v};")
# Scene 5 playhead: constant speed, left edge at cue 0 s, right edge at the end of 5E
s5 = beat("5B")[0]
end5E = TL["5E"]["end"]
x_left, x_right = 160, 160 + 1600
rate = 1600 / (end5E - cb["starts_at_video_s"])
for b in ("5B", "5C", "5D"):
    s, x = beat(b); a = act(b, "Waveform/Playhead"); g = G[x["key"]]["Waveform/Playhead"]
    vt0 = s["start"] + x["start"]
    def px(tv): return x_left + (tv - cb["starts_at_video_s"]) * rate
    cx = g["x"] + g["w"] / 2
    a.clear(); a.update(layer="Waveform/Playhead", src=x["key"], do="slide",
                        keys=[[0, px(vt0) - cx], [x["dur"], px(vt0 + x["dur"]) - cx]])
PLAYHEAD = dict(left_edge_cue_s=0.0, right_edge_cue_s=round(end5E - cb["starts_at_video_s"], 2), px_per_s=round(rate, 1))

# breath chip: Scene 1 swaps on "in"/"out" (1A); Scene 5 on the cue B breath bands
CHIP = {"IN": "2A_inhale", "OUT": "1A_cuff"}
def chip(b, segs):
    """segs: [[t_from, t_to, 'IN'|'OUT'], ...] in precomp time."""
    s, x = beat(b)
    for a in list(x["acts"]):
        if a["layer"] in ("Breath/Other",) and a["do"] != "exit":
            x["acts"].remove(a)
    for st in ("IN", "OUT"):
        iv = [[max(0, f), min(x["dur"], t)] for f, t, ss in segs if ss == st and t > 0 and f < x["dur"]]
        if iv:
            x["acts"].append({"layer": "Breath/Other", "src": CHIP[st], "do": "intervals", "iv": iv, "as": f"Breath/Label_{st}"})
_, x = beat("1A")
chip("1A", [[0, W("1A", "in"), "OUT"], [W("1A", "in"), W("1A", "out"), "IN"], [W("1A", "out"), 99, "OUT"]])
bands = [[cb["breath_t0_cue_s"] - 2 + 5 * k, cb["breath_t0_cue_s"] + 5 * k] for k in range(-1, 7)]
BREATH5 = []
for b in ("5B", "5C", "5D", "5E"):
    s, x = beat(b); vt0 = s["start"] + x["start"]
    segs, t = [], -99
    marks = []
    for f, e in bands:
        marks += [(cb["starts_at_video_s"] + f - vt0, "IN"), (cb["starts_at_video_s"] + e - vt0, "OUT")]
    marks.sort(); stt = "OUT"; t = -99
    for m, st in marks:
        segs.append([t, m, stt]); t, stt = m, st
    segs.append([t, 99, stt])
    chip(b, segs)
BREATH5 = [[round(cb["starts_at_video_s"] + f, 2), round(cb["starts_at_video_s"] + e, 2)] for f, e in bands if cb["starts_at_video_s"] + e > cb["starts_at_video_s"] and f < 30]

# Scene 5 readouts snap on the measured taps
_, x = beat("5C"); a = act("5C", "Readout/Expiration_value")
a.update(do="enter", t=round(cb["first_tap_expiration"]["video_s"] - (beat("5C")[0]["start"] + x["start"]), 3), rise=False, bump=1.10)
whole = cb["starts_at_video_s"] + [e for f, e in bands if cb["starts_at_video_s"] + f <= cb["taps_every_beat_from"]["video_s"] <= cb["starts_at_video_s"] + e][0]
_, x = beat("5D"); a = act("5D", "Readout/Both_value")
a.update(do="enter", t=round(whole - (beat("5D")[0]["start"] + x["start"]), 3), rise=False, bump=1.10)
READ5 = dict(first_tap_s=cb["first_tap_expiration"]["video_s"], whole_breath_s=round(whole, 2))

# 1A trace draws left -> right across the beat (Cue A from 0 s)
a = act("1A", "Waveform/Trace"); a.update(do="reveal", t=0.0, d=round(beat("1A")[1]["dur"], 3), angle=270)
# flows draw on their sync word
for b, nm, d in (("2B", "Flow/Venous_dots", 0.8), ("2C", "Flow/Pulmonary_dots", 1.2), ("3B", "Flow/Venous_dots", 0.8), ("3C", "Flow/Aortic_dots", 0.8)):
    a = act(b, nm)
    if a and a["do"] in ("enter", "xfade"):
        a.update(do="reveal", d=d, angle=270)
# 1B gap bracket on "gap"; definition after the title lands; Rule bars wipe in (5F)
a = act("1B", "Waveform/Gap_bracket"); a.update(t=W("1B", "gap"))
a = act("1B", "Title/Definition"); a.update(t=round(act("1B", "Title/Pulsus_paradoxus")["t"] + 0.9, 3))
for r in ("Rule_1", "Rule_2", "Rule_3"):
    a = act("5F", r); a.update(do="reveal", d=0.6, angle=270)
# 3B RV free wall bump on "pinned"
a = act("3B", "Heart/RV_free_wall"); a["bump"] = [W("3B", "pinned"), 1.04]
# 2A: chest breathes in (scale 1/1.045 -> 1) on "breathe in", coronal lungs grow from the apex, diaphragm drops on "drops"
_, x = beat("2A")
axial = [a["layer"] for a in x["acts"] if a["layer"].split("/")[0] in ("Chest", "Lungs", "Hilum", "Pericardium", "Heart", "Inflammation")]
x["groups"] = [
    {"null": "Axial/Chest", "at": [560, 470], "layers": axial, "scale": [[0, 100 / 1.045], [W("2A", "breathe"), 100 / 1.045], [W("2A", "breathe") + 0.8, 100]]},
]
for nm in ("Coronal/Lungs/R", "Coronal/Lungs/L"):
    g = G[x["key"]][nm]
    act("2A", nm)["grow"] = {"anchor": [g["x"] + g["w"] / 2, g["y"]], "t": W("2A", "breathe"), "d": 1.2, "from": [100 / 1.06, 100 / 1.13]}
dd = 58 * 0.46
for nm in ("Coronal/Diaphragm", "Coronal/Abdomen"):
    act("2A", nm)["drop"] = {"t": W("2A", "drops"), "d": 0.8, "dy": dd}
act("2A", "Coronal/Diaphragm_arrows").update(t=W("2A", "drops"), rise=True)


# timing fixes from the notes: 2C lungs come up on "stretch"; 2D chest relaxes on "out"; 3B heart changes on "push"
for b, word, pref in (("2C", "stretch", ("Lungs/",)), ("2D", "out", ("Chest/", "Lungs/", "Hilum/", "Inflammation/")), ("3B", "pushing", ("Heart/", "Pericardium/"))):
    _, x = beat(b)
    for a in x["acts"]:
        if a["do"] in ("move", "xfade") and a["layer"].startswith(pref) and a["layer"] != "Heart/RV_free_wall":
            a["t"] = W(b, word)
act("3B", "Heart/LV")["t"] = W("3B", "left")
# 4A: Scene 3's effusion drains top -> bottom at the start (hidden layer switched on)
act("4A", "Pericardium/Fluid").update(do="drain", t=0.0, d=0.6)
# crossfades into Scenes 3 and 4 (notes): the outgoing scene runs 0.4 s longer, the new one fades up over it
for sc in plan["scenes"]:
    n = sc["name"][-1]
    sc["xfade_in"] = 0.4 if n in "34" else 0.0
for i, sc in enumerate(plan["scenes"][:-1]):
    if plan["scenes"][i + 1]["xfade_in"]:
        sc["dur"] = round(sc["dur"] + 0.4, 3); sc["beats"][-1]["dur"] = round(sc["beats"][-1]["dur"] + 0.4, 3)
plan["scenes"][-1]["fade_out"] = 0.6

json.dump(plan, open("/tmp/claude-0/ae/plan.json", "w"), indent=1)
json.dump(dict(playhead=PLAYHEAD, breath5=BREATH5, read5=READ5, cueA_bands=MK["cueA"]["breath_bands"]), open("/tmp/claude-0/ae/fill.json", "w"), indent=1)
# summary
from collections import Counter
c = Counter(a["do"] for s in plan["scenes"] for x in s["beats"] for a in x["acts"])
print(c)
for s in plan["scenes"]:
    print(s["name"], s["start"], s["dur"], [(x["id"], x["start"], x["dur"]) for x in s["beats"]])
