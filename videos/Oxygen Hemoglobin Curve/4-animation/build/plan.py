"""Oxygen Hemoglobin Curve: the After Effects build plan (first build, v1).

Reads the measured timings (3-board/audio/vo_log.json, 3-board/timings/sync_points.csv) and the beat layers
(build/ai_src/layers.json, from prep_ai.py), applies the choreography below, and writes build/ae_plan.json,
which build_ae.jsx reads. Every move is keyed to a sync point by name ("pH", "60+0.4"): times are never typed in.

Choreography, per beat, from the Intent column of the production doc scene tables and the motion defaults
(build/motion_defaults.md): entrances ease out (0.5 s), moves across the frame ease in-out, one focal move at a time.
Layers the plan doesn't name: unchanged from the previous beat -> held; new -> enter on the beat's first cue;
changed -> crossfade on the first cue; gone -> fade out at the beat start (0.4 s). Meta/BeatID never goes in.

Actions (do):
  in       fade up and rise 20 px (rise=0 for none)
  pop      scale 0 -> 108 -> 100 % from the layer's centre, fading up (geometric entrances only)
  wipe     reveal with an animated mask: dir ltr | rtl | ttb | btt; stops [[cue, edge px], ...] or one sweep of d;
           keep=True keeps the previous beat's version underneath (the layer grows out of what was there)
  xfade    previous version -> this one
  carry    previous layer (prev=name, default same) travels and resizes onto this layer while they crossfade;
           fit="w" scales by width only, uniform=False stretches to the new box, top=True rides above everything
  slidein  enters from an offset (dx, dy) while fading up; clip=[x0, y0, x1, y1] keeps it inside the graph
  nudge    held layer moves by keys [[cue, dx], ...] (clip as above)
  out      previous beat's layer fades out (t, d)
  draw     line art strokes on: the layer becomes shapes (Create Shapes from Vector Layer) with Trim Paths 0 -> 100 %, ease out
  leave    a layer of this beat clears before the cut (90 %, fade, ease in)
  gone     nothing to copy (left earlier, or a custom move takes its place)
  title1c  1B -> 1C transition (see build_ae.jsx)
  bump     held layer scales to 103 % and back on its cue
Run: python3 plan.py
"""
import csv, json, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
VIDEO = HERE.parent.parent
BOARD = VIDEO / "3-board"
FPS, W, H = 30, 1920, 1080
TITLE = "Oxygen Hemoglobin Curve"
SCENES = {1: "Hook", 2: "Axes", 3: "Cooperativity", 4: "Landmarks", 5: "P50", 6: "Shape", 7: "Shifts",
          8: "Right shift", 9: "Left shift", 10: "Summary"}
GX = lambda po2: 300 + po2 * 8.2           # graph: PO2 0..100 -> x 300..1120
GY = lambda so2: 810 - so2 * 6.0           # SO2 0..100 -> y 810..210
CLIP = [298, 150, 1176, 818]               # inside the graph card: hides anything pushed past the axes

# Comma Clinical (Mark 2026-11-02; replaces the v6 "playful" override). Motion only: art, VO and sync points stay locked.
# Source: Motion Style Guide, "Comma Clinical: Warm Clinical with Comma motion". The curves themselves (snap, cross, accel,
# anti) come from library/scripts/adobe/comma_easing.jsx; these are the durations and amounts. Tune here, then re-run.
MOTION = {
    "snap_d": 0.6,            # s: default snap and settle (first key 16 % at 6x average speed, last key 70 % at speed 0)
    "cross_d": 0.75,          # s: moves the eye tracks across the frame (cross curve, 0.6-0.9)
    "accel_d": 0.25,          # s: accelerating into a swap (forms collapsing before a cut)
    "land_over": 0.08,        # landings overshoot 8 % with one rebound ...
    "land_back": 0.2,         # ... settled in 0.2 s
    "squash": 0.25,           # squash on impact 75/125, recovering in 0.2 s (shapes only: the RBCs)
    "stretch": 0.10,          # RBCs stretch 10 % along a move
    "anticipation_px": 30,    # counter-move before a big move ...
    "anticipation_d": 0.2,    # ... over 0.2 s
    "stagger_frames": 2,      # frames between siblings ...
    "stagger_max": 0.38,      # ... and under 0.4 s in total
    "hold_min": 0.4,          # s held after a landing (checked, see the report)
    "bob_px": 2,              # idle bob of a resting RBC: ambient life, kept subtle
    "bob_period": 2.5,        # s
    "ping_d": 0.3,            # emphasis ring: a short snap ...
    "ring": 1.6,              # ... to 160 %
    "pulse_scale": 1.08,      # chip pulse (8C Bohr)
    "pulse_d": 0.3,
    "title_write": 0.6,       # 1C: the dot writes line 1 on "oxyhemoglobin" ...
    "title_line2": 0.12,      # ... and line 2 cuts on whole this much later
}
STAGGER = min(MOTION["stagger_frames"] / FPS, MOTION["stagger_max"] / 6)   # the 1B clear has 7 siblings
P50_DOT = (GX(27), GY(50))

PLAN = {
    "1A": [
        {"layer": "Background/Fill", "do": "hold"},
        {"layer": "Background/Stage", "do": "in", "at": "start", "rise": 0, "d": 0.4},
        {"layer": "Vessel/Capillary", "do": "in", "at": "start", "rise": 0, "d": 0.4},
        {"layer": "Cell/RBC", "do": "pop", "at": "red", "d": 0.6},
        {"layer": "Cell/RBC", "do": "bob", "at": "red+0.7", "until": "end"},
        {"layer": "Label/Title", "do": "in", "at": "red+0.5"},
    ],
    "1B": [
        # Mark 2026-11-02: line icons draw on (lungs on "Pick", arm on "go"); each zone and its label follows its icon
        {"layer": "Icon/Lungs", "do": "draw", "at": "Pick", "d": 0.6},
        {"layer": "Zone/Lungs", "do": "in", "at": "Pick+0.6", "rise": 0, "d": 0.5},
        {"layer": "Cell/Lungs", "do": "carry", "prev": "Cell/RBC", "at": "Pick", "squash": True, "anticipate": True},
        {"layer": "Cell/Lungs", "do": "bob", "at": "Pick+1.1", "until": "end"},
        {"layer": "Readout/SO2", "do": "in", "at": "Pick+0.8"},
        {"layer": "Label/Arrow", "do": "wipe", "dir": "ltr", "at": f"go-{MOTION['cross_d']}", "d": MOTION["cross_d"]},
        {"layer": "Cell/Tissues", "do": "slidein", "dx": -940, "dy": 0, "at": f"go-{MOTION['cross_d']}", "d": MOTION["cross_d"], "squash": True},
        {"layer": "Cell/Tissues", "do": "bob", "at": "go+0.3", "until": "end"},
        {"layer": "Icon/Tissues", "do": "draw", "at": "go", "d": 0.6},
        {"layer": "Zone/Tissues", "do": "in", "at": "go+0.6", "rise": 0, "d": 0.5},
        {"layer": "Cell/Released", "do": "in", "at": "go+0.3", "rise": 20},
    ] + [  # clear before the cut to 1C: 0.3 s each, 0.05 s apart, ending on the 1C start
        {"layer": l, "do": "leave", "at": f"end-{MOTION['accel_d'] + STAGGER * (6 - i):.3f}", "d": MOTION["accel_d"]} for i, l in enumerate(
            ["Readout/SO2", "Zone/Lungs", "Zone/Tissues", "Icon/Lungs", "Icon/Tissues", "Label/Arrow", "Cell/Released"])
    ],
    "1C": [
        # Mark 2026-11-02: a sleek transition into the title. From the 1C start the two cells merge at the centre (0.6 s), the
        # capillary grows into the card (from +0.4 s, 0.7 s), the cell shrinks to a dot at the start of line 1 (0.5 s) and waits;
        # on "oxyhemoglobin" the dot leads a wipe that writes line 1 (0.6 s) and line 2 rises in 0.12 s later.
        {"layer": "Title/Text", "do": "title1c", "at": "oxyhemoglobin", "merge": [0.0, MOTION["cross_d"]], "capsule": [MOTION["cross_d"] - 0.2, 0.7],
         "dot": [MOTION["cross_d"] + 0.5, MOTION["snap_d"]], "write": MOTION["title_write"], "line2": MOTION["title_line2"]},
        {"layer": "Title/Fact", "do": "in", "at": "oxyhemoglobin+0.9"},
    ] + [{"layer": l, "do": "gone"} for l in ["Vessel/Capillary", "Cell/Lungs", "Cell/Tissues", "Zone/Lungs", "Zone/Tissues", "Icon/Lungs",
                                             "Icon/Tissues", "Cell/Released", "Label/Arrow", "Readout/SO2"]],
    "2A": [
        {"layer": "Background/Stage", "do": "carry", "at": "start", "uniform": False},
        {"layer": "Header/Kicker", "do": "carry", "prev": "Title/Text", "at": "start", "fit": "w", "top": True, "anticipate": True},
        {"layer": "Title/Fact", "do": "out", "at": "start", "d": 0.3},
        {"layer": "Graph/Axes", "do": "wipe", "dir": "ltr", "at": "bottom", "d": 1.0},
        {"layer": "Note/X", "do": "in", "at": "dissolved"},
    ],
    "2B": [
        {"layer": "Graph/Axes", "do": "wipe", "dir": "btt", "keep": True, "at": "side", "d": 1.0},
        {"layer": "Note/X", "do": "xfade", "at": "side"},
        {"layer": "Note/Y", "do": "in", "at": "filled"},
        {"layer": "Graph/Grid", "do": "in", "at": "filled+0.6", "rise": 0, "d": 0.6},
    ],
    "3A": [
        {"layer": "Label/Header", "do": "in", "at": "start+0.4"},
        {"layer": "Hb/Tetramer", "do": "pop", "at": "four", "d": 0.6},
        {"layer": "Panel/Card", "do": "in", "at": "heme"},
    ],
    "3B": [
        {"layer": "Hb/Tetramer", "do": "xfade", "at": "first"},
        {"layer": "Panel/Card", "do": "xfade", "at": "shape"},
        {"layer": "Hb/Tetramer", "do": "bump", "at": "easily"},
    ],
    "3C": [
        {"layer": "Graph/Grid", "do": "in", "at": "start", "rise": 0},
        {"layer": "Graph/Axes", "do": "in", "at": "start", "rise": 0},
        {"layer": "Curves/Straight", "do": "wipe", "dir": "ltr", "at": "straight", "d": 0.8},
    ],
    "3D": [
        {"layer": "Curves/Straight", "do": "xfade", "at": "sigmoid"},
        {"layer": "Curves/Normal", "do": "wipe", "dir": "ltr", "at": "sigmoid", "d": 1.2},
        {"layer": "Label/Sigmoid", "do": "in", "at": "sigmoid+1.0"},
        {"layer": "Panel/Card", "do": "in", "at": "sigmoid+1.4"},
    ],
    "4A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},
        {"layer": "Point/Arterial", "do": "wipe", "dir": "rtl", "stops": [["100", GX(100) - 30, 0.5], ["97", 220, 0.8]]},
        {"layer": "Point/Arterial", "do": "ping", "at": "100+0.3", "c": [GX(100), GY(97)], "r": 14},
    ],
    "4B": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},
        {"layer": "Point/Arterial", "do": "xfade", "at": "40"},
        {"layer": "Point/Venous", "do": "wipe", "dir": "rtl", "stops": [["40", GX(40) - 30, 0.5], ["75", 220, 0.8]]},
        {"layer": "Point/Venous", "do": "ping", "at": "40+0.3", "c": [GX(40), GY(75)], "r": 14},
    ],
    "4C": [
        {"layer": "Point/Venous", "do": "xfade", "at": "quarter"},
        {"layer": "Band/Unloaded", "do": "in", "at": "quarter", "rise": 0, "d": 0.6},
        {"layer": "Panel/Card", "do": "xfade", "at": "quarter+0.4"},
    ],
    "5A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "Halfway"},
        {"layer": "Guide/Fifty", "do": "wipe", "dir": "ltr", "at": "50", "d": 0.8},
        {"layer": "Guide/Fifty", "do": "ping", "at": "50+0.8", "c": list(P50_DOT), "r": 14},
    ],
    "5B": [
        {"layer": "Guide/Fifty", "do": "wipe", "dir": "ttb", "keep": True, "at": "27", "d": 0.6},
        {"layer": "Guide/Fifty", "do": "ping", "at": "27", "c": list(P50_DOT), "r": 14},
        {"layer": "Panel/Card", "do": "xfade", "at": "27+0.3"},
    ],
    "6A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "flat"},
        # the marker leaves 100 and reaches 60 on "60"; the SO2 bar comes in on "90"
        {"layer": "Marker/Bars", "do": "wipe", "dir": "rtl", "stops": [["60-1.6", GX(60) - 14, 1.6], ["90", 270, 0.4]]},
    ],
    "6B": [
        {"layer": "Region/Plateau", "do": "in", "at": "plateau", "rise": 0},
        {"layer": "Panel/Card", "do": "xfade", "at": "plateau+0.4"},
        {"layer": "Region/Steep", "do": "in", "at": "steep", "rise": 0},
    ],
    "6C": [
        {"layer": "Panel/Card", "do": "xfade", "at": "small"},
        {"layer": "Marker/Bars", "do": "wipe", "dir": "rtl", "stops": [["small", GX(30) - 14, 0.8], ["large", 270, 0.5]]},
        {"layer": "Marker/Bars", "do": "ping", "at": "large", "c": [GX(30), 462], "r": 14},
    ],
    "7A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "shift"},
        {"layer": "Curves/Ghosts", "do": "in", "at": "shift", "rise": 0},
        {"layer": "Curves/Normal", "do": "nudge", "keys": [["shift", 0], ["shift+0.35", 40], ["shift+0.75", -40], ["P50", 0]], "clip": CLIP},
        {"layer": "Marker/P50", "do": "in", "at": "P50"},
    ],
    "8A": [
        {"layer": "Curves/Normal", "do": "xfade", "at": "right"},
        {"layer": "Curves/Shift", "do": "slidein", "dx": -(36 - 27) * 8.2, "dy": 0, "at": "right", "clip": CLIP},
        {"layer": "Panel/Card", "do": "xfade", "at": "right+0.4"},
        {"layer": "Footnote/Text", "do": "in", "at": "rises"},
    ],
    "8B": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start+0.3"},
        {"layer": "Factors/List", "do": "drop", "rows": [["pH", 430, 514], ["carbon", 514, 588], ["DPG", 588, 662], ["temperature", 662, 760]]},
    ],
    "8C": [
        {"layer": "Panel/Card", "do": "xfade", "at": "Bohr"},
        {"layer": "Factors/List", "do": "xfade", "at": "Bohr"},
        {"layer": "Factors/Bohr", "do": "in", "at": "Bohr", "rise": 0},
        {"layer": "Factors/Bohr", "do": "bump", "at": "Bohr+0.5", "pulse": True},
    ],
    "8D": [
        {"layer": "Curves/Normal", "do": "xfade", "at": "muscle"},
        {"layer": "Curves/Shift", "do": "xfade", "at": "muscle"},
        {"layer": "Panel/Card", "do": "xfade", "at": "muscle"},
        {"layer": "Marker/Extra", "do": "wipe", "dir": "ttb", "at": "released", "d": 0.8},
    ],
    "9A": [
        {"layer": "Curves/RightGhost", "do": "in", "at": "left", "rise": 0},
        {"layer": "Curves/Shift", "do": "out", "at": "left", "d": 0.6},
        {"layer": "Curves/Shift", "do": "slidein", "dx": (27 - 20) * 8.2, "dy": 0, "at": "left", "clip": [0] + CLIP[1:]},   # its label sits left of the y-axis
        {"layer": "Panel/Card", "do": "xfade", "at": "left+0.4"},
    ],
    "9B": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},
        {"layer": "Factors/List", "do": "drop", "rows": [["pH", 430, 514], ["carbon", 514, 588], ["DPG", 588, 662], ["temperature", 662, 760]]},
    ],
    "9C": [
        {"layer": "Curves/Shift", "do": "xfade", "at": "Fetal"},
        {"layer": "Panel/Card", "do": "xfade", "at": "Fetal"},
    ],
    "9D": [
        {"layer": "Curves/Shift", "do": "out", "at": "different", "d": 0.6},
        {"layer": "Panel/Card", "do": "xfade", "at": "different"},
        {"layer": "Hb/COTetramer", "do": "pop", "at": "occupies", "d": 0.6},
        {"layer": "Panel/Lines", "do": "wipe", "dir": "ttb", "stops": [["occupies+0.6", 716, 0.4], ["tightly", 770, 0.4]]},
        {"layer": "Footnote/Text", "do": "in", "at": "releases"},
    ],
    "10A": [
        {"layer": "Panel/Card", "do": "out", "at": "start", "d": 0.4},
        {"layer": "Curves/Right", "do": "slidein", "dx": -(36 - 27) * 8.2, "dy": 0, "at": "Right", "clip": CLIP},
        {"layer": "Panel/RightShift", "do": "in", "at": "Right"},
        {"layer": "Curves/Left", "do": "in", "at": "Right+1.0", "rise": 0, "d": 0.6},
        {"layer": "Panel/LeftShift", "do": "in", "at": "Right+1.0"},
    ],
    "10B": [
        {"layer": "Panel/RightShift", "do": "xfade", "at": "Left"},
        {"layer": "Panel/LeftShift", "do": "xfade", "at": "Left"},
    ],
    "10C": [
        {"layer": "Panel/LeftShift", "do": "xfade", "at": "start"},
        {"layer": "Takeaway/Text", "do": "pop", "at": "release", "d": 0.6, "from": 0.9},
        {"layer": "Footnote/Text", "do": "in", "at": "release+0.8"},
    ],
}


def main():
    vo = json.load(open(BOARD / "audio" / "vo_log.json"))
    full = vo.get("full_track", {})
    # Comps and layers live on whole frames: a beat or scene that starts between frames leaves an empty (black) frame
    # at the cut (Mark 2026-11-02: 0:00:13:22, 0:00:51:07). Starts snap to the nearest frame and each comp runs to the
    # next start; moves stay on the measured cue times, counted from the snapped start.
    snap = lambda t: round(t * FPS) / FPS
    beats = [(b["beat"], snap(b["start_in_full_s"])) for b in vo["beats"]]
    total = -(-round(207.88 * FPS * 1000) // 1000) / FPS          # full.mp3 (207.88 s), rounded up to a whole frame
    cues = {}
    for r in csv.DictReader(open(BOARD / "timings" / "sync_points.csv")):
        cues.setdefault(r["beat"], []).append((r["sync_on"].strip('"'), float(r["start_in_full_s"]), r["flag"]))
    layers = json.load(open(HERE / "ai_src" / "layers.json"))
    names = {b: [x["name"] for x in v["layers"] if x["name"] != "Meta/BeatID"] for b, v in layers.items()}

    out = {"title": TITLE, "fps": FPS, "w": W, "h": H, "total": total, "motion": MOTION, "scenes": [], "markers": []}
    prev_beat = None
    for i, (bid, start) in enumerate(beats):
        end = beats[i + 1][1] if i + 1 < len(beats) else total
        bc = {c: t - start for c, t, _ in cues[bid]}

        def T(spec):
            m = re.fullmatch(r"(.+?)([+-]\d+(?:\.\d+)?)?", spec)
            base, off = m.group(1), float(m.group(2) or 0)
            t = 0.0 if base == "start" else (round((end - start) * FPS) / FPS if base == "end" else bc[base])
            return round(max(0.0, t + off), 3)

        cur, prv = names[bid], names[prev_beat] if prev_beat else []
        acts, named = [], set()
        for a in PLAN.get(bid, []):
            a = dict(a)
            if "at" in a: a["t"] = T(a.pop("at"))
            if "stops" in a: a["stops"] = [[T(s[0]), s[1], s[2]] for s in a["stops"]]
            if "keys" in a: a["keys"] = [[T(k[0]), k[1]] for k in a["keys"]]
            if "rows" in a: a["rows"] = [[T(r[0]), r[1], r[2]] for r in a["rows"]]
            if "until" in a: a["t_end"] = T(a.pop("until"))
            acts.append(a)
            named.add((a["layer"], a["do"] in ("out", "gone")))
            if a["do"] == "carry":                       # the travelling copy replaces the previous layer's exit
                named.add((a.get("prev", a["layer"]), True))
        first = min(bc.values()) if bc else 0.0
        for n in cur:
            if (n, False) in named: continue
            if n not in prv:
                acts.append({"layer": n, "do": "in", "t": round(first, 3), "auto": True})
            elif changed(prev_beat, bid, n):
                acts.append({"layer": n, "do": "xfade", "t": round(first, 3), "auto": True})
            else:
                acts.append({"layer": n, "do": "hold"})
        for n in prv:
            if n not in cur and (n, True) not in named:
                acts.append({"layer": n, "do": "out", "t": 0.0, "d": 0.4, "auto": True})
        scene = int(re.match(r"\d+", bid).group())
        sc = next((s for s in out["scenes"] if s["n"] == scene), None)
        if not sc:
            sc = {"n": scene, "name": f"Scene {scene} · {SCENES[scene]}", "start": start, "beats": []}
            out["scenes"].append(sc)
        sc["beats"].append({"id": bid, "key": layers[bid]["file"][:-4], "ai": bid, "prev_ai": prev_beat,
                            "order": cur, "prev_order": prv, "start": start, "dur": round((end - start) * FPS) / FPS, "acts": acts})
        for c, t, flag in cues[bid]:
            out["markers"].append({"t": t, "beat": bid, "cue": c, "flag": flag})
        prev_beat = bid
    for k, sc in enumerate(out["scenes"]):
        sc["end"] = out["scenes"][k + 1]["start"] if k + 1 < len(out["scenes"]) else total
    (HERE / "ae_plan.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for sc in out["scenes"]:
        print(sc["name"], sc["start"], "->", sc["end"])
        for b in sc["beats"]:
            print("  ", b["id"], b["start"], b["dur"], "; ".join(f"{a['layer']}:{a['do']}@{a.get('t', '')}" for a in b["acts"] if a["do"] != "hold"))


_cache = {}
def changed(b0, b1, name):
    import xml.etree.ElementTree as ET
    def g(b):
        if b not in _cache:
            r = ET.parse(HERE / "ai_src" / f"{b}.svg").getroot()
            m = {x["id"]: x["name"] for x in json.load(open(HERE / "ai_src" / "layers.json"))[b]["layers"]}
            _cache[b] = {m[c.get("id")]: ET.tostring(c).replace(f'id="{c.get("id")}"'.encode(), b"") for c in r if c.get("id") in m}
        return _cache[b]
    return g(b0).get(name) != g(b1).get(name)


if __name__ == "__main__":
    main()
