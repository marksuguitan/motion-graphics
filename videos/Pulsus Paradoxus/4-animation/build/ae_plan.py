"""Stage 6 planner: turn the 22 layered beats + measured word times into an AE build plan (plan.json).

Per beat precomp, every layer gets one of:
  static   same art as the previous beat in the scene: on for the whole beat
  enter    new layer: fade (or fade + rise 20 px for text) on its sync word, else at the beat start
  move     same art, new place/size/opacity: the previous beat's copy animates to the new state, then hands over
  xfade    art changed: previous copy fades out while the new one fades in, on the sync word
  exit     layer gone: previous copy fades out at the beat start
plus overrides from the motion notes (needles, breath chip, flows, playhead, chest breath, bumps, readout snaps).
"""
import json, re, hashlib, sys, math
import xml.etree.ElementTree as ET

SRC = "/tmp/claude-0/ai/svg"
NS = "{http://www.w3.org/2000/svg}"
L = json.load(open(f"{SRC}/layers.json"))
G = json.load(open("/tmp/claude-0/ae/geom.json"))
TLJ = json.load(open(sys.argv[1])); TL = {b["id"]: b for b in TLJ["beats"]}
LEAD = TLJ.get("lead", {})        # silent lead-in before a scene's first VO (anim/apply_lead.py; 3A 1.5 s, Mark 2026-10-25)
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
    s_start = 0.0 if sc == "1" else first["start"] - 0.5 - LEAD.get(bid(keys[0]), 0)    # half the inter-scene gap before, rest after
    nxt = [TL[b]["start"] - LEAD.get(b, 0) for b in TL if b[0] == str(int(sc) + 1)]
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
# Scenes 2-4 drop bars (Mark 2026-10-24: the drop dial became a two-bar graph). The IN bar is scaled from its bottom edge
# and its accent outline (Bars/Drop) from the expiration line, on the words the needle used to move on.
BARV = {"2D": (0, 8, [8, 0]), "2E": (16, 16, [16]), "4C": (20, 20, [20])}   # Scene 3 has no graph (Mark 2026-10-25)   # art value, Drop art value, values on each sync
for b, (va, vd, vals) in BARV.items():
    s, x = beat(b); key = x["key"]
    ge, gi, gd = G[key]["Bars/Bar_expiration"], G[key]["Bars/Bar_inspiration"], G[key]["Bars/Drop"]
    H0 = ge["h"]; cxb = gi["x"] + gi["w"] / 2; k = H0 / 45.0      # the OUT bar spans 45 mmHg of the plot (px per mmHg)
    sy = lambda v: round(100 * (H0 - v * k) / (H0 - va * k), 3)
    sd = lambda v: round(100 * v / vd, 3)
    ts = [t + x["vo_at"] for t in syncs(b, "Gauge/Needle")]
    dur = 0.3 if b == "2E" else 0.4
    kb, kd, v = [[0, sy(0)]], [[0, sd(0)]], 0
    for t, nv in zip(ts, vals):
        kb += [[t, sy(v)], [t + dur, sy(nv)]]; kd += [[t, sd(v)], [t + dur, sd(nv)]]; v = nv
    for nm, kk, anc in (("Bars/Bar_inspiration", kb, [cxb, gi["y"] + gi["h"]]), ("Bars/Drop", kd, [cxb, gd["y"]])):
        a = act(b, nm)
        if not a:
            a = {}; x["acts"].append(a)
        a.clear(); a.update(layer=nm, src=key, do="bar", anchor=anc, keys=kk)
    if b == "2D":       # 2D shows -8 and takes it back: the two readouts swap
        t0, t1 = ts
        for nm, kk in (("Bars/Readout", [[0, 100], [t0, 100], [t0 + dur, 0], [t1, 0], [t1 + dur, 100]]),
                       ("Bars/Readout_dip", [[0, 0], [t0, 0], [t0 + dur, 100], [t1, 100], [t1 + dur, 0]])):
            a = act(b, nm)
            if not a:
                a = {}; x["acts"].append(a)
            a.clear(); a.update(layer=nm, src=key, do="opkeys", keys=kk)
    else:
        a = act(b, "Bars/Readout"); a["t"] = round(ts[0], 3)

# Scene 5: one continuous deflation, needle by expression (notes): 144.5 mmHg at the 5B in-point, 2.0 mmHg/s, 1 deg per mmHg
cb = MK["cueB"]
# Mark 2026-10-24: needle drawn at the cuff pressure at each beat's end; kicks on every audible tap of Cue B (as in Scene 1)
CB_BEATS = json.load(open(sys.argv[6]))
CB_TAPS = [round(cb["starts_at_video_s"] + q["time_s"], 3) for q in CB_BEATS if q["audible"]]
cuffB = lambda tv: max(cb["start_cuff_mmHg"] - cb["rate_mmHg_s"] * (tv - cb["starts_at_video_s"]), 100.0)
for b in ("5B", "5C", "5D", "5E"):
    s, x = beat(b); a = act(b, "Gauge/Needle"); piv, _ = needle(b, x["key"])
    vt0 = s["start"] + x["start"]          # video time of the precomp start
    v = round(cuffB(s["start"] + x["start"] + x["dur"]) if b != "5E" else cuffB(TL["5E"]["end"]))
    a.clear(); a.update(layer="Gauge/Needle", src=x["key"], do="expr", pivot=piv,
                        expr=(f"var tv = time + {vt0:.3f};\n"
                              f"var cuff = Math.max({cb['start_cuff_mmHg']} - {cb['rate_mmHg_s']} * (tv - {cb['starts_at_video_s']}), 100);\n"
                              f"var B = {json.dumps(CB_TAPS)}, lb = -1; for (var i = 0; i < B.length; i++) if (B[i] <= tv) lb = B[i];\n"
                              "var dt = lb < 0 ? 99 : tv - lb; var kick = dt < 0.7 ? 1.8 * (1 - Math.exp(-dt / 0.035)) * Math.exp(-dt / 0.16) : 0;\n"
                              f"(cuff + kick) - {v};"))
# 5B (Mark 2026-10-24): the needle scales up out of the rig with the dial as one object. The 5B needle rides a null
# that makes the same move as the dial (5A hub -> 5B hub, 1/s -> 100 %), and eases from the 5A art (160) onto the cuff.
s5b, x5b = beat("5B"); hub = act("5B", "Gauge/Hub")
pA = [hub_g["x"] + hub_g["w"] / 2 for hub_g in [G["5A_setup"]["Arm_scene/Gauge/Hub"]]] + [G["5A_setup"]["Arm_scene/Gauge/Hub"]["y"] + G["5A_setup"]["Arm_scene/Gauge/Hub"]["h"] / 2]
pB, _ = needle("5B", x5b["key"])
x5b["groups"] = [{"null": "Gauge/Rig", "at": pB, "layers": ["Gauge/Needle"],
                  "scale": [[hub["t"], 100 / hub["s"]], [hub["t"] + hub["d"], 100]],
                  "pos": [[hub["t"], pA], [hub["t"] + hub["d"], pB]]}]
na = act("5B", "Gauge/Needle"); V5A = 160
na["expr"] = na["expr"].replace("(cuff + kick)", f"(function () {{ var k = Math.min(1, Math.max(0, (time - {hub['t']}) / {hub['d']})); k = k * k * (3 - 2 * k); return {V5A} + (cuff + kick - {V5A}) * k; }})()")
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
# Scene 5 sound wave: the white copy is wiped on in step with Cue B across 5B-5E (completion keyed per precomp)
TB = end5E - cb["starts_at_video_s"]
fB = lambda tv: min(1.0, max(0.0, (tv - cb["starts_at_video_s"]) / TB))
for b in ("5B", "5C", "5D", "5E"):
    s, x = beat(b); a = act(b, "Waveform/Played"); vt0 = s["start"] + x["start"]
    sw = [[0, 100 * (1 - fB(vt0))], [x["dur"], 100 * (1 - fB(vt0 + x["dur"]))]]
    prev = a.get("prev"); pl = a.get("prevLayer")
    a.clear(); a.update(layer="Waveform/Played", src=x["key"], do="sweep", keys=sw)
    if b in ("5C", "5D", "5E") and prev:        # 5E: the wave dims to 40 %, so the brighter copy hands over
        a.update(prev=prev, prevLayer=pl, d=0.4)
PLAYHEAD = dict(left_edge_cue_s=0.0, right_edge_cue_s=round(end5E - cb["starts_at_video_s"], 2), px_per_s=round(rate, 1))

# breath chip: Scene 1 swaps on "in"/"out" (1A); Scene 5 on the cue B breath bands
CHIP = {"IN": "5B_deflate", "OUT": "5C_first-taps"}   # Mark 2026-10-25: no breath label in Scene 4     # old IN/OUT chip label sources (Scenes 1-2 now use the new label)   # OUT label source moved off 1A (Scene 1 now has the new two-chip label)
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
# Scene 1 (Mark 2026-10-24): chip follows Cue A v2's breathing (IN 3-5 s and 8-10 s); 1A precomp time = video time = cue time
CA = json.load(open(sys.argv[5]))
# Mark 2026-10-25: Scene 1 uses the new breath label: two stacked chips INSPIRATION / EXPIRATION (Breath/Inspiration, Breath/Expiration)
# that slide in from the left at the start of 1A, trade rows with a slide on each breath of Cue A (IN 3-5 s, 8-10 s), carry across
# the 1A -> 1B cut and fade out at master 0:14:14 (1.32 s into 1B). 1C has no breath label. A soft breath sound sits under each swap.
BR = dict(slide_dx=420, out_d=0.7, in_d=1.0, lag=0.45, first_d=1.0,   # Mark 2026-10-25: slower, and each arrival eases into a slow stop
          ease_in_start=15, ease_in_stop=90, ease_out_start=60, ease_out_end=15)
# Mark 2026-10-25: his own breath sounds, audio/Inspiration.wav (1.49 s, -11.3 LUFS) and audio/Expiration.wav (1.20 s, -12.5 LUFS),
# replace the synthesized ones; each is turned down to about -30 LUFS, 6 dB under the VO (-24 LUFS), so it sits under the narration
# Mark: barely audible at -18.7/-17.5 dB; raised 9 dB to about -21 LUFS, roughly level with the narration
SFX = {"IN": {"file": "Inspiration.wav", "dir": "audio/", "db": -9.7}, "OUT": {"file": "Expiration.wav", "dir": "audio/", "db": -8.5}}
def breath(b, segs, art_state, slide_in=None, out=None, sfx=True, extra_sfx=()):
    """segs: [[t_from, t_to, 'IN'|'OUT'], ...] in precomp time; art_state: which chip the key frame draws on the top row."""
    s, x = beat(b)
    for a in list(x["acts"]):
        if a["layer"].startswith("Breath/"): x["acts"].remove(a)
    rows = {"IN": [], "OUT": []}
    for f, t, st in segs:
        if t <= 0 or f >= x["dur"]: continue
        for k in ("IN", "OUT"):
            r = 1 if k == st else 2
            if not rows[k] or rows[k][-1][1] != r: rows[k].append([round(max(0, f), 3), r])
    for k, nm in (("IN", "Breath/Inspiration"), ("OUT", "Breath/Expiration")):
        a = {"layer": nm, "src": x["key"], "do": "breath", "row0": 1 if art_state == k else 2, "rows": rows[k]}
        a.update(BR)
        if slide_in is not None: a["slide_in"] = slide_in
        if out is not None: a["out"] = out
        x["acts"].append(a)
    if sfx:
        x["sfx"] = [dict(SFX[st], t=round(f, 3)) for f, t, st in segs if 0 < f < x["dur"]]
    for t_, st in extra_sfx:
        x.setdefault("sfx", []).append(dict(SFX[st], t=round(t_, 3)))
breath("1A", [[0, 3.0, "OUT"], [3.0, 5.0, "IN"], [5.0, 8.0, "OUT"], [8.0, 10.0, "IN"], [10.0, 99, "OUT"]], "OUT", slide_in=0.0)
_t_off = round((14 + 14 / 30) - beat("1B")[1]["start"], 3)      # 0:14:14 in the master = 1.316 s into 1B
breath("1B", [[0, 99, "OUT"]], "OUT", out=_t_off, sfx=False)
_, _x1c = beat("1C")
_x1c["acts"] = [a for a in _x1c["acts"] if not a["layer"].startswith("Breath/")]   # already faded out in 1B; no exit copy
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
# 1A sound wave: the white (played) copy is wiped on left to right in step with Cue A; the playhead rides the edge;
# the needle deflates with the cuff (2.0 mmHg/s from 143.6) and kicks on every audible tap, as in the Korotkoff video
a = act("1A", "Waveform/Played"); a.update(do="reveal", t=0.0, d=CA["end_s"], angle=270, feather=0)
_, x1a = beat("1A")
act("1A", "Waveform/Playhead").update(do="slide", enable=True, keys=[[0, 0], [CA["end_s"], 780]], off=CA["end_s"] + 0.3)
piv1, _ = needle("1A", x1a["key"])
a = act("1A", "Gauge/Needle"); a.clear()
a.update(layer="Gauge/Needle", src=x1a["key"], do="expr", pivot=piv1,
         expr=("var t = Math.min(Math.max(time, 0), %.3f);\n" % CA["end_s"]) +
              ("var B = %s, lb = -1; for (var i = 0; i < B.length; i++) if (B[i] <= t) lb = B[i];\n" % json.dumps(CA["audible_taps_s"])) +
              "var dt = lb < 0 ? 99 : t - lb; var kick = dt < 0.7 ? 1.8 * (1 - Math.exp(-dt / 0.035)) * Math.exp(-dt / 0.16) : 0;\n" +
              ("(%.1f - %.1f * t + kick) - %d;" % (CA["start_cuff_mmHg"], CA["rate_mmHg_s"], round(CA["start_cuff_mmHg"] - CA["rate_mmHg_s"] * CA["end_s"]))))
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
# Mark 2026-10-24: the diaphragm follows the base of the lungs. Same start, length and ease as the lung growth, and the
# drop equals how far the lung bases travel (lung height x (1 - 1/1.13)), so the bases ride on the diaphragm.
HL = max(G[x["key"]][nm]["h"] for nm in ("Coronal/Lungs/R", "Coronal/Lungs/L"))
dd = round(HL * (1 - 1 / 1.13), 2)
for nm in ("Coronal/Diaphragm", "Coronal/Abdomen"):
    act("2A", nm)["drop"] = {"t": W("2A", "breathe"), "d": 1.2, "dy": dd}
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

# 3A labels: see the 3A block further down (anatomy labels before the VO, Mark 2026-10-25)
act("3A", "Label/Pressure").update(t=W("3A", "climbs"))
# text whose sync sits on another layer's line in the notes
# Mark 2026-10-25: Scene 3 has no drop graph; in the last 0.8 s of 2E it slides out to the right, the 2 -> 3 transition
_, x2e = beat("2E")
bl2 = [a["layer"] for a in x2e["acts"] if a["layer"].startswith("Bars/")]
gb2 = [G[x2e["key"]][n] for n in bl2 if n in G[x2e["key"]]]
bx2 = min(g["x"] for g in gb2); bcx2 = (bx2 + max(g["x"] + g["w"] for g in gb2)) / 2; bcy2 = (min(g["y"] for g in gb2) + max(g["y"] + g["h"] for g in gb2)) / 2
off2 = round(1920 - bx2 + 40); e2 = x2e["dur"]
x2e["groups"] = (x2e.get("groups") or []) + [{"null": "Bars/Slide", "at": [bcx2, bcy2], "layers": bl2, "scale": [[0, 100]],
                                              "pos": [[e2 - 1.25, [bcx2, bcy2]], [e2 - 0.45, [bcx2 + off2, bcy2]]]}]   # done before Scene 3 starts (it overlaps the last 0.4 s)
# Mark 2026-10-25: 3A opens with no effusion (sac against the epicardium); on "fill ... with fluid" the pericardial cavity
# opens and fills: Sac, Serous_layer and Fluid become shape layers whose ring paths morph from the empty state to the drawn one
# (same angles in both states, so every point maps to its partner); the ripples fade in once it has filled.
sys.path.insert(0, "/tmp/claude-0/style")
from gen import heart as _heart
def _ring(f):
    d = _heart(960, 560, 1.32, bow=0, fluid=f)["sac"]       # 3A heart centred (Mark 2026-10-25)
    return [[float(v) for v in p.split(",")] for p in d.replace("M", "").replace("Z", "").split(" L")]
_, x3a = beat("3A")
f0 = W("3A", "fill"); f1 = round(max(W("3A", "fluid", 1) + 0.6, f0 + 1.4), 3)
hexrgb = lambda h: [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
for nm, spec in (("Pericardium/Fluid", dict(fill=hexrgb("#5E9BD6"), fill_op=30, a0=0, a1=58)),
                 ("Pericardium/Serous_layer", dict(color=hexrgb("#5A5B60"), w0=1.5, w1=1.5, a0=-1, a1=53)),
                 ("Pericardium/Sac", dict(color=hexrgb("#4A4B4C"), w0=6, w1=6, a0=4, a1=58))):
    a = act("3A", nm); a0, a1 = spec.pop("a0"), spec.pop("a1")
    a.clear(); a.update(layer=nm, src=x3a["key"], do="morph", t0=f0, t1=f1, **{"from": _ring(a0), "to": _ring(a1)}, in0=True, **spec)
act("3A", "Pericardium/Fluid_ripples").update(do="enter", t=f1, rise=False)
# Mark 2026-10-25: anatomy labels first, just after the heart fades in and before the VO (3A has a 1.5 s lead-in);
# they stay while the cavity fills and go on "so". PERICARDIAL EFFUSION (left) comes in as the fill completes.
# The pericardium and pericardial-cavity leaders are shape layers whose end (line + dot) follows the sac / band outward.
LD = json.load(open("/tmp/claude-0/style/leaders3a.json"))
t_out3 = W("3A", "so")
for i, nm in enumerate(("Label/Pericardium", "Label/Pericardial_cavity", "Label/Myocardium")):
    tin = round(0.6 + 0.3 * i, 3)
    act("3A", nm).update(do="flash", t=tin, t_out=t_out3, rise=False)
    ld = LD[nm]
    if not ld["full"]: continue
    circ = lambda c: [[c[0] + 5 * math.cos(math.radians(a)), c[1] + 5 * math.sin(math.radians(a))] for a in range(0, 360, 30)]
    x3a["acts"].append(dict(layer=nm + "_leader", src=x3a["key"], do="morph", t0=f0, t1=f1, **{"from": [ld["from"], ld["empty"]], "to": [ld["from"], ld["full"]]},
                            color=hexrgb("#6E6E6E"), w0=1.5, w1=1.5, fin=tin, off=t_out3, offd=0.3, in0=True))
    x3a["acts"].append(dict(layer=nm + "_dot", src=x3a["key"], do="morph", t0=f0, t1=f1, **{"from": circ(ld["empty"]), "to": circ(ld["full"])},
                            fill=hexrgb("#F2F2F2"), fill_op=100, fin=tin, off=t_out3, offd=0.3, in0=True))
act("3A", "Label/Effusion").update(t=round(W("3A", "fluid", 1) + 0.3, 3), rise=True)
act("2E", "Title/Threshold").update(t=W("2E", "ten"))   # Mark 2026-10-25: title in sooner, on "ten" (Scene 2 comp ~38:00), was "Paradoxus"
act("2E", "Title/Other").update(t=act("2E", "Title/Threshold")["t"])
# Mark 2026-10-25: the drop graph slides into 2D from the right (a null carries every Bars layer in from off-frame)
_, x2d = beat("2D")
bl = [a["layer"] for a in x2d["acts"] if a["layer"].startswith("Bars/")]
gb = [G[x2d["key"]][n] for n in bl if n in G[x2d["key"]]]
bx = min(g["x"] for g in gb); bcx = (bx + max(g["x"] + g["w"] for g in gb)) / 2; bcy = (min(g["y"] for g in gb) + max(g["y"] + g["h"] for g in gb)) / 2
off = round(1920 - bx + 40)
x2d.setdefault("groups", None)
x2d["groups"] = (x2d["groups"] or []) + [{"null": "Bars/Slide", "at": [bcx, bcy], "layers": bl, "scale": [[0, 100]],
                                         "pos": [[0.1, [bcx + off, bcy]], [0.9, [bcx, bcy]]]}]
for a in x2d["acts"]:
    if a["layer"] in bl and a["do"] == "enter": a.update(do="static")
act("3C", "Title/Mechanism").update(t=W("3C", "ventricular"))
act("4B", "Label/Pressure").update(t=W("4B", "forty"))
act("4C", "Label/Interdependence").update(t=W("4C", "fills"))

# exits: a layer that was hidden in the previous beat (3A anatomy labels) has nothing to fade out
for sc in plan["scenes"]:
    for x in sc["beats"]:
        x["acts"] = [a for a in x["acts"] if not (a["do"] == "exit" and any(l.get("hidden") and l["name"] == a["layer"] for l in L[a["src"]]))]
# 3B: the septum glow comes up with the septum on "pushing"
act("3B", "Heart/Septum_glow").update(t=W("3B", "pushing"))
# ---- Mark 2026-10-24, Scene 1 pass 3 ----
# (1) nothing pops on at 0:00: the needle, the playhead and the OUT label fade in with the rest of 1A
_, x = beat("1A"); x["fadein"] = ["Gauge/Needle", "Waveform/Playhead"]
for a in x["acts"]:
    if a.get("as") == "Breath/Label_OUT": a["fade0"] = True
# (2) 1C: "How to catch it" comes in on "how" (was "catch"); a red underline draws in under "Why" and under "How" on their words
s1c, x = beat("1C")
act("1C", "Promise/Catch").update(t=W("1C", "how"))
for nm, w in (("Promise/Why_underline", "why"), ("Promise/How_underline", "how")):
    a = act("1C", nm); a.clear(); a.update(layer=nm, src=x["key"], do="reveal", t=round(W("1C", w) + 0.15, 3), d=0.45, angle=270, feather=0)
# (3) Scene 1 -> 2: at the end of 1C everything but the "Why" underline fades away; at the cut the underline curls into
#     the 2A heart's epicardium (shape morph), the heart fills in behind it, then the chest, graph and coronal view come in on "chest"
T_OUT = round(x["dur"] - 0.6, 3)
x["outro"] = {"t": T_OUT, "d": 0.45, "keep": ["Background", "Grid", "Breath"]}   # the underline fades too: the morph layer above it takes over
EPI = json.load(open("/tmp/claude-0/ae/epi.json"))[0]
ep = EPI["pts"]
il = min(range(len(ep)), key=lambda i: ep[i][0]); ep = ep[il:] + ep[:il]
if ep[1][1] > ep[0][1]: ep = [ep[0]] + ep[1:][::-1]           # start at the leftmost point, go up (clockwise on screen)
CS, CC = 100 / 1.045 / 100, (560, 470)                          # 2A chest is at 1/1.045 until "breathe"
ep = [[round(CC[0] + (px - CC[0]) * CS, 2), round(CC[1] + (py - CC[1]) * CS, 2)] for px, py in ep]
g_ul = G["1C_promise"]["Promise/Why_underline"]
ux0, uw, uy = g_ul["x"], g_ul["w"], g_ul["y"] + g_ul["h"] / 2
NP = len(ep)
ul = [[round(ux0 + uw * (1 - math.cos(2 * math.pi * i / NP)) / 2, 2), round(uy, 2)] for i in range(NP)]
# Mark 2026-10-24 (pass 4): the morph straddles the cut. It lives in the master comp, starts in 1C as the text fades out
# and finishes in 2A, so the two scenes blend instead of meeting at the cut. Times are video seconds.
s2a, x2 = beat("2A")
CUT = round(s2a["start"] + x2["start"], 3)                     # Scene 1 -> 2 cut (27.917)
V0 = round(s1c["start"] + x["start"] + T_OUT, 3)               # 1C text starts fading (27.317)
V1 = round(CUT + 0.55, 3)                                      # outline lands on the heart 0.55 s into 2A
M1 = round(V1 - CUT, 3)                                        # same moment in 2A time
act("1C", "Promise/Why_underline")["cut_at"] = round(T_OUT + 0.04, 3)   # the morph layer, drawn on the same spot, takes over (no ghost)
plan["master_morphs"] = [{"layer": "Transition/Morph 1-2", "from": ul, "to": ep, "t0": V0, "t1": V1, "scenes": ["Scene 1", "Scene 2"],
                          "w0": round(g_ul["h"], 2), "w1": round(EPI["sw"], 2), "color": [1, 64 / 255, 87 / 255], "off": round(V1 + 0.05, 3), "offd": 0.3}]
for a in x2["acts"]:
    if a["do"] == "enter" and a.get("t", 0) < 0.05 and not a.get("hidden"):
        if a["layer"].startswith("Breath/"):
            a["do"] = "static"                                  # the chip carries straight across the cut
        else:                                                   # Mark 2026-10-24: heart, chest, coronal view and tags all fade in together,
            a["t"] = round(M1 - 0.1, 3); a["first"] = False       # just as the curling underline lands on the heart
# 2A lung arrows: pop out from the lungs toward the chest wall on "breathe in", gone when the chest has finished expanding
act("2A", "Lung_arrows").update(do="flash", t=W("2A", "breathe"), t_out=round(W("2A", "breathe") + 0.7, 3), pop=0.6)
# 2C: the "pulmonary vessels hold blood" label comes in as the vessels dilate on "stretch" (was "moment")
act("2C", "Label/Lungs").update(t=W("2C", "stretch"))
# Mark 2026-10-24: "RV filling" carries 2B into 2C unchanged (still red); it hands the accent to the new label on "stretch"
act("2C", "Label/RV").update(t=W("2C", "stretch"))
# ...and the vessels visibly widen on "stretch": they turn red drawn thin (Simple Choker +0.8 px) and swell to full width over 1 s
for nm in ("Lungs/R/Vessels", "Lungs/L/Vessels"):
    act("2C", nm)["dilate"] = {"t": W("2C", "stretch"), "d": 1.2, "from": 2.0}   # exaggerated: ~4 px -> 8.5 px main vessels
# Illustrator drops SVG masks: the coronal silhouette, rib cage and abdomen get their soft bottom edge back in AE
# soft bottom edge of the coronal view, comp px: native mask fades 706 -> 908 at the view's y offset and scale (2A 380/0.55, 4B 400/0.50)
COR_FADE = {"2A_inhale": [380 + 706 * 0.55, 380 + 908 * 0.55], "4B_suction": [400 + 706 * 0.50, 400 + 908 * 0.50]}
plan["fade_bottom"] = {k: {x["name"]: COR_FADE[k] for x in v if x.get("fade_bottom")} for k, v in L.items() if any(x.get("fade_bottom") for x in v)}

# Mark 2026-10-24 (found at the 4B->4C check): art that crossfades while the rest of the picture moves now rides that move
# (heart in 4C, bronchi/hilum/inflammation in 4B) instead of crossfading in its final place while the chest slides there.
# Each such xfade borrows the global transform (scale s, offset T) of the nearest moving layer: p -> s*p + T.
RIDE_GROUPS = ("Heart", "Pericardium", "Lungs", "Inflammation", "Hilum", "Chest", "Coronal")
def ctr(key, nm):
    g = G[key][nm]; return (g["x"] + g["w"] / 2, g["y"] + g["h"] / 2)
for s_ in plan["scenes"]:
    for x in s_["beats"]:
        mv = [a for a in x["acts"] if a["do"] == "move" and (abs(a["dx"]) > 3 or abs(a["dy"]) > 3 or abs(a["s"] - 1) > 0.01)]
        if not mv: continue
        for a in x["acts"]:
            # any xfade, also one delayed to a word (2B Heart/RV on "fills more"): the old copy rides the move, then waits there
            if a["do"] != "xfade" or a["layer"].split("/")[0] not in RIDE_GROUPS: continue
            if a["prevLayer"] not in G[a["prev"]]: continue
            # Mark 2026-10-25 (2C->2D RV tag jumped): a group that holds still in this beat (any of its layers static, e.g. the
            # heart while the chest wall breathes out in 2D) doesn't ride; a group that moves rides its own nearest mover
            grp = lambda n: "Heart" if (n.split("/")[0] in ("Heart", "Pericardium") or n == "Chest/Mediastinum") else n.split("/")[0]   # the mediastinum is the heart's outline
            if any(q["do"] == "static" and grp(q["layer"]) == grp(a["layer"]) for q in x["acts"]): continue
            pool = [q for q in mv if grp(q["layer"]) == grp(a["layer"])] or mv
            REF = "Heart/Epicardium_line"          # the heart rides its own outline's move (exact, whatever the chest does)
            if grp(a["layer"]) == "Heart" and REF in G[a["prev"]] and REF in G[a["src"]]:
                gp, gn = G[a["prev"]][REF], G[a["src"]][REF]
                sc = gn["w"] / gp["w"]; pc, nc = ctr(a["prev"], REF), ctr(a["src"], REF)
                T = [nc[0] - sc * pc[0], nc[1] - sc * pc[1]]
                if abs(sc - 1) < 0.01 and abs(nc[0] - pc[0]) < 3 and abs(nc[1] - pc[1]) < 3: continue
                m = min(pool, key=lambda q: abs(q["s"] - sc))
                a["ride"] = {"s": sc, "T": T, "d": m["d"], "t": m["t"], "via": REF}
                continue
            cp = ctr(a["prev"], a["prevLayer"])
            m = min(pool, key=lambda q: (ctr(q["prev"], q["prevLayer"])[0] - cp[0]) ** 2 + (ctr(q["prev"], q["prevLayer"])[1] - cp[1]) ** 2)
            mc = ctr(m["prev"], m["prevLayer"])
            T = [m["dx"] - (m["s"] - 1) * mc[0], m["dy"] - (m["s"] - 1) * mc[1]]
            a["ride"] = {"s": m["s"], "T": T, "d": m["d"], "t": m["t"], "via": m["layer"]}
# Mark 2026-10-25 (Scene 3 pass 2): the heart stays centred through 3A-3D (no move at 3B). At the start of 3E it scales from the
# centre (960, 560) x1.32 to the top left (380, 330) x0.55 over 0.8 s: the 3D copies of the heart and sac ride that move and
# hand over to 3E's own art when they arrive; layers 3E doesn't have (ripples, serous layer) shrink with it as they fade.
_, x3e = beat("3E")
s3 = 0.55 / 1.32
T3 = [round(380 - s3 * 960, 2), round(330 - s3 * 560, 2)]
for a in x3e["acts"]:
    if a["layer"].split("/")[0] not in ("Heart", "Pericardium"): continue
    if a["do"] == "xfade" and a.get("prev") == "3D_clinical":
        a.update(t=0.8, d=0.3, ride={"s": round(s3, 5), "T": T3, "d": 0.8, "t": 0.0, "via": "3D -> 3E heart to top left"})
    elif a["do"] == "exit":
        a.update(d=0.7, ride={"s": round(s3, 5), "T": T3, "d": 0.8, "t": 0.0})
# 3E graph: frame and labels fade in as the heart settles, the dashed guides draw in left to right, then the trace
for nm in ("Trace/Insp_band", "Trace/Other", "Trace/Other 2"):
    if act("3E", nm): act("3E", nm).update(do="enter", t=0.5, rise=False)
for nm in ("Trace/Systolic_line", "Trace/Diastolic_line"):
    act("3E", nm).update(do="reveal", t=0.9, d=1.0, angle=270)
act("3E", "Trace/Arterial").update(do="reveal", t=2.0, d=2.6, angle=270)
# 3C: the aortic arrow is labelled "↓ Stroke volume" (in on "stroke", just after the arrow starts to draw)
act("3C", "Label/Stroke_volume").update(do="enter", t=W("3C", "stroke"), rise=True)
# Mark 2026-10-25: 3A sounded cut at the start in AE although the file is whole. The new take now goes in as a WAV under its
# own name (audio/3A_v2.wav, decoded from audio/takes/3A_v2_take1.mp3), so no cached import of "3A.mp3" can stand in for it.
beat("3A")[1]["vo"] = "3A_v2.wav"
# Mark 2026-10-25 (Scene 5): ">10 mmHg = PULSUS PARADOXUS" fades in on "over" ("anything over ten", master 3:33:03), was "paradoxus";
# 5F recap rules wipe in sooner, at Mark's Scene 5 comp times 41:02, 44:05, 48:10 (5F starts at Scene 5 comp 40.0 s)
act("5E", "Readout/Threshold").update(t=W("5E", "over"))
_, x5f = beat("5F")
for r, tc in (("Rule_1", 41 + 2 / 30), ("Rule_2", 44 + 5 / 30), ("Rule_3", 48 + 10 / 30)):
    act("5F", r).update(t=round(tc - x5f["start"], 3))

# Mark 2026-10-25 (Scene 4): the drop graph first appears in 4C and slides in from the right (as in 2D); the line graph
# comes in late in 4C, drawing in over the ~2.5 s before "systolic" (frame and labels, then the guides, then the trace);
# the "pressure around LV" label (now white, right column) comes in with the ring.
_, x4c = beat("4C")
bl4 = [a["layer"] for a in x4c["acts"] if a["layer"].startswith("Bars/")]
gb4 = [G[x4c["key"]][n] for n in bl4 if n in G[x4c["key"]]]
bx4 = min(g["x"] for g in gb4); bcx4 = (bx4 + max(g["x"] + g["w"] for g in gb4)) / 2; bcy4 = (min(g["y"] for g in gb4) + max(g["y"] + g["h"] for g in gb4)) / 2
# Mark 2026-10-25 (pass 2): the graph is needed at Scene 4 comp 28:25 (4C 10.61 s), so it slides in over 8.1-8.9 s, before the drop on "falls"
tb4 = round((28 + 25 / 30) - x4c["start"] - 2.5, 3)
x4c["groups"] = (x4c.get("groups") or []) + [{"null": "Bars/Slide", "at": [bcx4, bcy4], "layers": bl4, "scale": [[0, 100]],
                                              "pos": [[tb4, [bcx4 + round(1920 - bx4 + 40), bcy4]], [tb4 + 0.8, [bcx4, bcy4]]]}]
for a in x4c["acts"]:
    if a["layer"] in bl4 and a["do"] == "enter": a.update(do="static")
# Mark 2026-10-25 (pass 2): the line graph draws in around Scene 4 comp 29:21 (4C 11.48 s): frame, guides, then the trace;
# the inspiratory diastolic drop is labelled on "fall" ("diastolic pressure tends to fall with it")
tg4 = round((29 + 21 / 30) - x4c["start"], 3)
tg4 = round(tg4 + 2.0, 3)   # Mark 2026-10-25: 2 s gap after "falls." for reading time; the line graph keeps its place before "But this time"
beat("4C")[1]["vo"] = "4C_v2.wav"
for nm in ("Trace/Insp_band", "Trace/Other", "Trace/Other 2"):
    if act("4C", nm): act("4C", nm).update(do="enter", t=round(tg4 - 0.2, 3), rise=False)
for nm in ("Trace/Systolic_line", "Trace/Diastolic_line"):
    act("4C", nm).update(do="reveal", t=round(tg4, 3), d=0.9, angle=270)
act("4C", "Trace/Arterial").update(do="reveal", t=round(tg4 + 0.9, 3), d=1.6, angle=270)
act("4C", "Label/Diastolic").update(do="enter", t=W("4C", "fall"), rise=True)
act("4C", "Label/LV_pressure").update(do="enter", t=act("4C", "Heart/LV_arrow")["t"], rise=True)
t4r = act("4C", "Bars/Readout")["t"]                          # the readout reads 0 until the IN bar drops, then -20
act("4C", "Bars/Readout").update(do="opkeys", keys=[[0, 0], [t4r, 0], [t4r + 0.4, 100]])
act("4C", "Bars/Readout_start").update(do="opkeys", keys=[[0, 100], [t4r, 100], [t4r + 0.4, 0]])
# Mark 2026-10-25, breath label Scene 2 (his Scene 2 comp times): INSPIRATION slides in at 3:03 with the inspiration sound
# ("breathe in"), holds through 2B-2C; at 24:21 ("with each breath in") the inspiration sound plays alone (label already
# INSPIRATION); at 34:01 ("when you breathe out") it swaps to EXPIRATION with the expiration sound and holds through 2E.
def s2t(tc, b):                                                  # Scene 2 comp timecode (s + frames/30) -> time in beat b
    return round(tc - beat(b)[1]["start"], 3)
_t_in2 = s2t(3 + 3 / 30, "2A")
breath("2A", [[0, 99, "IN"]], "IN", slide_in=_t_in2, sfx=False, extra_sfx=[(_t_in2, "IN")])
for _b in ("2B", "2C"):
    breath(_b, [[0, 99, "IN"]], "IN", sfx=False)
_t_out2 = s2t(34 + 1 / 30, "2D")
breath("2D", [[0, _t_out2, "IN"], [_t_out2, 99, "OUT"]], "OUT", extra_sfx=[(s2t(24 + 21 / 30, "2D"), "IN")])
breath("2E", [[0, 99, "OUT"]], "OUT", sfx=False)
# Mark 2026-10-25, breath label Scene 3 (Scene 3 comp times): INSPIRATION glides in at 15:02 with the inspiration sound
# (start of 3B, "When the patient breathes in"; 3B begins at 15.09 s, so it starts with the beat) and fades out at 27:09
# (0.56 s into 3C). No breath label in 3A, 3D or 3E.
def s3t(tc, b): return round(tc - beat(b)[1]["start"], 3)
breath("3B", [[0, 99, "IN"]], "IN", slide_in=max(0.0, s3t(15 + 2 / 30, "3B")), sfx=False, extra_sfx=[(max(0.0, s3t(15 + 2 / 30, "3B")), "IN")])
breath("3C", [[0, 99, "IN"]], "IN", out=s3t(27 + 9 / 30, "3C"), sfx=False)
_, _x3d = beat("3D")
_x3d["acts"] = [a for a in _x3d["acts"] if not a["layer"].startswith("Breath/")]   # already faded out in 3C; no exit copy
# Mark 2026-10-25: no breath label in Scene 4 (he removed the layers in AE himself); dropped from the build so a rebuild keeps
# it out. The art still carries the old chip, which Scene 5 uses as its IN/OUT label source until its own pass.
for _b in ("4A", "4B", "4C"):
    _, _x4 = beat(_b)
    _x4["acts"] = [a for a in _x4["acts"] if not a["layer"].startswith("Breath/")]
# Mark 2026-10-27: the Medzcool logo intro opens the video (comp built by build_intro.jsx, 3.3 s); the engine places it at
# 0:00 of the master and shifts every scene, the 1-2 morph and the check frames by its length.
plan["intro"] = {"comp": "Medzcool Intro", "dur": 3.3}
# Mark 2026-10-27: the Medzcool end card (call to action, 10 s, no VO) follows the last scene; the engine keeps it there.
plan["outro"] = {"comp": "Medzcool End Card", "dur": 10.0}
plan["layer_counts"] = {k: len(v) for k, v in L.items()}      # so the AE build can tell a stale import from a fresh one
json.dump(plan, open("/tmp/claude-0/ae/plan.json", "w"), indent=1)
json.dump(dict(playhead=PLAYHEAD, breath5=BREATH5, read5=READ5, cueA_bands=MK["cueA"]["breath_bands"]), open("/tmp/claude-0/ae/fill.json", "w"), indent=1)
# summary
from collections import Counter
c = Counter(a["do"] for s in plan["scenes"] for x in s["beats"] for a in x["acts"])
print(c)
for s in plan["scenes"]:
    print(s["name"], s["start"], s["dur"], [(x["id"], x["start"], x["dur"]) for x in s["beats"]])
