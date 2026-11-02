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
import csv, json, math, pathlib, re

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
# A wipe stop that reveals a point stops inside the point's white rim (radius 11 + stroke 4 = 15 px), so the mask edge and its
# 4 px feather fall on the rim, never on the guide line behind it. Wider (30 px in v1-v11, 16 in a v12 draft) let the next
# piece leak in early: the end of the "Arterial" label (4A) and the venous horizontal guide (4B), Mark 2026-11-02
POINT_EDGE = 12
# Separate layers that sit inside the side card and leave with it at a card change on the next beat's first frame
CARD_CONTENT = {"2B": ["Note/XTerm", "Note/XDef", "Note/Y"], "8C": ["Factors/List", "Factors/Bohr"], "9B": ["Factors/List"]}

# Comma Clinical (Mark 2026-11-02; replaces the v6 "playful" override). Motion only: art, VO and sync points stay locked.
# Source: Motion Style Guide, "Comma Clinical: Warm Clinical with Comma motion". The curves themselves (snap, cross, accel,
# anti) come from library/scripts/adobe/comma_easing.jsx; these are the durations and amounts. Tune here, then re-run.
MOTION = {
    "snap_d": 0.6,            # s: default snap and settle (first key 16 % at 6x average speed, last key 70 % at speed 0)
    "cross_d": 0.75,          # s: moves the eye tracks across the frame (cross curve, 0.6-0.9)
    "accel_d": 0.25,          # s: accelerating into a swap (forms collapsing before a cut)
    "land_over": 0.08,        # landings overshoot 8 % with one rebound ...
    "land_back": 0.2,         # ... settled in 0.2 s
    "squash": 0,              # squash on impact (0.25 = 75/125). 0: Mark 2026-11-02 didn't like the RBCs squishing
    "stretch": 0,             # RBC stretch along a move (was 0.10). 0: same note
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
    "tick_d": 0.4,            # tick numbers sweep on (2 frames a tick, about)
    "card_rise": 40,          # side-card content change (Mark 2026-11-02: the hard cut was abrupt): rows roll up this far
    "card_out_d": 0.25,       # old rows clear in this long in all, ending on the cue (accelerate into the swap) ...
    "card_in_d": 0.3,         # ... new rows arrive from the cue, each in this long (snap and settle), clipped to the card
    "card_stagger": 1 / 30,   # rows 1 frame apart, from the top (Mark: the roll must not cost reading time)
    "draw_out": 0.09,         # s between graph pieces drawing themselves out (3A): about 0.7 s in all, inside the 1.0 s pause
    "ring_d": 0.3,            # heme circles draw on / off in this long ...
    "ring_hold": 0.4,         # ... and hold this long in between
    "first_o2_d": 0.8,        # s: the first O2's trip to α1 (cross curve)
    "next_o2_d": 0.35,        # s: each of the next O2s (accelerating): quicker and more direct, "more easily"
    "tr_swell": 1.08,         # T -> R (Mark: "just make the other subunits larger"): the empty subunits grow to 108 % ...
    "swell_d": 0.5,           # ... over this long (snap) ...
    "swell_back_d": 0.3,      # ... and settle back to 100 % this fast as their O2 lands
}
# Silence added before a beat, s (Mark 2026-11-02: more time to read the y note before Scene 3). Everything from that beat on
# (picture, audio, markers) moves later by the same amount; the VO files and their word timings are unchanged.
GAPS = {"3A": 1.0,                      # Mark 2026-11-02: was 1.5 s, "a little too long, make it shorter, like 1s"
        "4A": 1.0,                      # Mark 2026-11-02: time to read the 3D card before Scene 4 (2.0 s in v14-v15; "make scene 3 like 1 second shorter")
        "5A": 1.0,                      # Mark 2026-11-02 (v14): the 4C card was up under 2 s
        "8D": 1.0}                      # Mark 2026-11-02 (v14): the 8C card was up about 2 s
TETRAMER_C = [636, 590]
DRAW_OUT = MOTION["draw_out"]
# 3B: subunit centres, heme centres and bound-O2 spots of tetramer(636, 590)
SUB_C = {"α1": (506, 480), "β1": (766, 480), "β2": (506, 700), "α2": (766, 700)}
HEME = {"β1": [796, 460], "β2": [476, 720], "α2": [796, 720]}
BOUND = {"β1": [858, 460], "β2": [414, 720], "α2": [858, 720]}
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
    # Mark 2026-11-02 (v9): fill the 2A gap with the axis detail and the side card, bring the grid in sooner, give the y note
    # time to read, and grow Scene 3 out of Scene 2. "w:<word>" is a measured word time from word_timings.csv.
    "2A": [
        {"layer": "Background/Stage", "do": "carry", "at": "start", "uniform": False},
        {"layer": "Header/Kicker", "do": "carry", "prev": "Title/Text", "at": "start", "fit": "w", "top": True, "anticipate": True},
        {"layer": "Title/Fact", "do": "out", "at": "start", "d": 0.3},
        {"layer": "Graph/AxisX", "do": "wipe", "dir": "ltr", "at": "bottom", "d": MOTION["cross_d"]},
        {"layer": "Panel/Card", "do": "in", "at": "w:PO2"},
        {"layer": "Note/XTerm", "do": "in", "at": f"w:PO2+{MOTION['snap_d']}"},
        {"layer": "Graph/TicksX", "do": "wipe", "dir": "ltr", "at": "w:millimeters", "d": MOTION["tick_d"]},
        {"layer": "Graph/GridV", "do": "wipe", "dir": "btt", "at": "w:mercury", "d": MOTION["snap_d"]},
        {"layer": "Note/XDef", "do": "in", "at": "dissolved"},
    ],
    "2B": [
        {"layer": "Graph/AxisY", "do": "wipe", "dir": "btt", "at": "side", "d": MOTION["cross_d"]},
        {"layer": "Graph/TicksY", "do": "wipe", "dir": "btt", "at": "w:saturation", "d": MOTION["tick_d"]},
        {"layer": "Graph/GridH", "do": "wipe", "dir": "ltr", "at": "w:saturation", "d": MOTION["snap_d"]},
        {"layer": "Note/Y", "do": "in", "at": "w:percentage"},
    ],
    "3A": [
        # Mark 2026-11-02: the graph draws itself out, the reverse of how it drew in (last drawn, first gone)
        {"layer": "Graph/GridH", "do": "out", "at": "start", "retract": "rtl"},
        {"layer": "Graph/TicksY", "do": "out", "at": f"start+{1 * DRAW_OUT:.3f}", "retract": "ttb"},
        {"layer": "Graph/AxisY", "do": "out", "at": f"start+{2 * DRAW_OUT:.3f}", "retract": "ttb"},
        {"layer": "Graph/GridV", "do": "out", "at": f"start+{3 * DRAW_OUT:.3f}", "retract": "ttb"},
        {"layer": "Graph/TicksX", "do": "out", "at": f"start+{4 * DRAW_OUT:.3f}", "retract": "rtl"},
        {"layer": "Graph/AxisX", "do": "out", "at": f"start+{5 * DRAW_OUT:.3f}", "retract": "rtl"},
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},                 # the side card stays; its text cuts to STRUCTURE
        {"layer": "Label/Header", "do": "in", "at": f"start+{5 * DRAW_OUT + MOTION['accel_d']:.3f}"},   # once the graph has gone
        {"layer": "Hb/Tetramer", "do": "pop", "at": "four", "plain": True},   # a diagram: grows from its centre, no overshoot
        # "Each one holds a heme group": each circle draws on, holds, draws itself off (α1, β1, β2, α2)
    ] + [{"layer": f"Heme/Circle {n}", "do": "draw", "at": f"w:heme+{STAGGER * k:.3f}", "off_at": f"w:heme+{STAGGER * k + MOTION['ring_d'] + MOTION['ring_hold']:.3f}",
          "d": MOTION["ring_d"]} for k, n in enumerate(["α1", "β1", "β2", "α2"])] + [
        # the first O2 grows in on "bind" and travels to α1, landing as "oxygen molecule" ends; its label goes on landing
        {"layer": "O2/First", "do": "o2", "at": "w:bind", "go_at": f"we:molecule-{MOTION['first_o2_d']}", "d": MOTION["first_o2_d"],
         "mol": [1060, 590], "to": [414, 460], "label_y": 570, "kind": "cross"},
    ],
    "3B": [
        # v15: at the end the tetramer and its O2s shrink together into the centre, accelerating, before 3C draws the graph
        {"layer": "Hb/α1", "do": "gather", "post": True, "at": "end-0.3", "c": TETRAMER_C, "prefixes": ["Hb/", "O2/"], "d": 0.3},
        # until the shape change the 3A drawing holds (no rings yet); the four subunit layers take over on "changes"
        {"layer": "Hb/Tetramer", "do": "out", "at": "w:changes"},
        {"layer": "O2/First", "do": "out", "at": "w:changes", "shift": [414 - 1060, 460 - 590], "label_y": 570},
        {"layer": "Panel/Card", "do": "xfade", "at": "shape"},
        # Mark 2026-11-02: T -> R, simply: the three subunits without O2 grow (about their own centres); α1, with its O2, stays.
        # Each settles back as its O2 lands, so by "easily" all four are equal again
        {"layer": "Hb/α1", "do": "in", "at": "w:changes", "cut": True},
    ] + [{"layer": f"Hb/{n}", "do": "swell", "at": "w:changes", "c": list(SUB_C[n]), "s": MOTION["tr_swell"], "d": MOTION["swell_d"],
          "back_at": f"w:bind+{3 / FPS * k + MOTION['next_o2_d']:.3f}", "back_d": MOTION["swell_back_d"]} for k, n in enumerate(["β1", "β2", "α2"])] + [
        # the rings on the empty sites ping as they settle: these sites now fill more easily
    ] + [{"layer": f"Hb/{n}", "do": "ping", "at": f"w:changes+{MOTION['swell_d']:.3f}", "c": HEME[n], "r": 50} for n in ["β1", "β2", "α2"]] + [
        # the next O2s grow in on "next", then fly in fast on "bind", 3 frames apart; each site pings as its O2 lands
    ] + [{"layer": f"O2/Next {n}", "do": "o2", "at": "w:next", "go_at": f"w:bind+{3 / FPS * k:.3f}", "d": MOTION["next_o2_d"],
          "mol": [1060, y], "to": BOUND[n], "label_y": y - 20, "kind": "accel"} for k, (n, y) in enumerate([("β1", 470), ("β2", 590), ("α2", 710)])] + [
        {"layer": f"O2/Next {n}", "do": "ping", "at": f"w:bind+{3 / FPS * k + MOTION['next_o2_d']:.3f}", "c": HEME[n], "r": 50}
        for k, n in enumerate(["β1", "β2", "α2"])],
    "3C": [
        # Mark 2026-11-02 (v15): the graph draws itself on (as in 2A/2B) instead of cutting in, done before "curve";
        # the side card keeps 3B's content through 3C and rolls to 3D's on "sigmoid"
        {"layer": "Graph/Axes", "do": "axisdraw", "at": "start", "dx": 0.35, "dy": 0.3, "y_split": GY(0) - 20},
        {"layer": "Graph/Grid", "do": "wipe", "dir": "btt", "at": "start+0.45", "d": 0.4},
        {"layer": "Curves/Straight", "do": "wipe", "dir": "ltr", "at": "straight", "d": 0.8},
        {"layer": "Panel/Card", "do": "out", "at": "end"},
    ],
    "3D": [
        # Mark 2026-11-02: no time to read the card before Scene 4. It comes in with "sigmoid"; in the pause before 4A the
        # dashed line draws itself out and "S-shaped" clears, while the curve and the card stay
        {"layer": "Curves/Straight", "do": "xfade", "at": "sigmoid"},
        {"layer": "Curves/Straight", "do": "undraw", "dir": "rtl", "at": f"end-{MOTION['snap_d'] + MOTION['card_out_d']:.2f}"},
        {"layer": "Curves/Normal", "do": "wipe", "dir": "ltr", "at": "sigmoid", "d": 1.2},
        {"layer": "Label/Sigmoid", "do": "in", "at": "sigmoid+1.0", "out_at": f"end-{MOTION['snap_d'] + MOTION['card_out_d']:.2f}"},
        {"layer": "Panel/Card", "do": "cardswap", "phase": "both", "old_ai": "3B", "new_ai": "3D", "at": "sigmoid-0.25", "new_at": "sigmoid"},
    ],
    "4A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},
        {"layer": "Point/Arterial", "do": "wipe", "dir": "rtl", "stops": [["100", GX(100) - POINT_EDGE, 0.5], ["97", 220, 0.8]]},
        {"layer": "Point/Arterial", "do": "ping", "at": "100+0.3", "c": [GX(100), GY(97)], "r": 14},
    ],
    "4B": [
        {"layer": "Panel/Card", "do": "xfade", "at": "start"},
        {"layer": "Point/Arterial", "do": "xfade", "at": "40"},
        {"layer": "Point/Venous", "do": "wipe", "dir": "rtl", "stops": [["40", GX(40) - POINT_EDGE, 0.5], ["75", 220, 0.8]]},
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
        {"layer": "Marker/Bars", "do": "wipe", "dir": "rtl", "stops": [["60-1.6", GX(60) - POINT_EDGE, 1.6], ["90", 270, 0.4]]},
    ],
    "6B": [
        {"layer": "Region/Plateau", "do": "in", "at": "plateau", "rise": 0},
        {"layer": "Panel/Card", "do": "xfade", "at": "plateau+0.4"},
        {"layer": "Region/Steep", "do": "in", "at": "steep", "rise": 0},
    ],
    "6C": [
        {"layer": "Panel/Card", "do": "xfade", "at": "small"},
        {"layer": "Marker/Bars", "do": "wipe", "dir": "rtl", "stops": [["small", GX(30) - POINT_EDGE, 0.8], ["large", 270, 0.5]]},
        {"layer": "Marker/Bars", "do": "ping", "at": "large", "c": [GX(30), 462], "r": 14},
    ],
    "7A": [
        {"layer": "Panel/Card", "do": "xfade", "at": "shift"},
        {"layer": "Curves/Ghosts", "do": "in", "at": "shift", "rise": 0},
        {"layer": "Curves/Normal", "do": "nudge", "keys": [["shift", 0], ["shift+0.35", 40], ["shift+0.75", -40], ["P50", 0]], "clip": CLIP},
        # the P50 dot appears on "P50" and its arrows draw outward along the 50% line to the ghost curves' P50s (art b9e1fe7)
        {"layer": "Marker/P50", "do": "centrewipe", "at": "P50", "c": [519.8, 510], "half": 16},
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
        # Mark 2026-11-02 (marker at "tightly"): show hemoglobin holding its O2 tightly. The mini tetramer draws in and coral
        # rings snap in around its two bound O2s, and stay
        {"layer": "Hb/COTetramer", "do": "clamp", "at": "tightly", "s": 0.94, "pts": [[1662.1, 428.5], [1417.9, 571.5]], "r": 24,
         "locks": ["Lock/Grip 1", "Lock/Grip 2"], "badge": [[18, -20], [-18, -20]]},   # Mark: a small lock on each grip ring
        {"layer": "Lock/Grip 1", "do": "skip"}, {"layer": "Lock/Grip 2", "do": "skip"},
        {"layer": "Panel/Lines", "do": "wipe", "dir": "ttb", "stops": [["occupies+0.6", 716, 0.4], ["tightly", 770, 0.4]]},
        {"layer": "Footnote/Text", "do": "in", "at": "releases"},
    ],
    # Mark 2026-11-02: each shift appears on the graph when the VO speaks about it, and the other one greys out
    "10A": [
        {"layer": "Panel/Card", "do": "out", "at": "start", "d": 0.4},
        {"layer": "Curves/Right", "do": "slidein", "dx": -(36 - 27) * 8.2, "dy": 0, "at": "Right", "clip": CLIP},
        {"layer": "Panel/RightShift", "do": "in", "at": "Right"},
        {"layer": "Curves/Left", "do": "skip"},
        {"layer": "Panel/LeftShift", "do": "skip"},
    ],
    "10B": [
        {"layer": "Curves/Right", "do": "hold"},
        {"layer": "Curves/Right", "do": "grey", "at": "Left", "from": 0, "to": 100},
        {"layer": "Curves/Left", "do": "wipe", "dir": "ltr", "at": "Left", "d": MOTION["snap_d"]},
        {"layer": "Panel/RightShift", "do": "xfade", "at": "Left"},
        {"layer": "Panel/LeftShift", "do": "in", "at": "Left"},
    ],
    "10C": [
        # "right means release": the right shift returns to its colour and the left one greys
        {"layer": "Curves/Right", "do": "hold"},
        {"layer": "Curves/Right", "do": "grey", "at": "start", "from": 100, "to": 100, "d": 0.01},
        {"layer": "Curves/Right", "do": "grey", "at": "w:right", "from": 100, "to": 0},
        {"layer": "Curves/Left", "do": "hold"},
        {"layer": "Curves/Left", "do": "grey", "at": "w:right", "from": 0, "to": 100},
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
    shift, beats, shifts = 0.0, [], {}
    for b in vo["beats"]:
        shift += GAPS.get(b["beat"], 0.0)
        shifts[b["beat"]] = shift
        beats.append((b["beat"], snap(b["start_in_full_s"] + shift)))
    total = -(-round((207.88 + shift) * FPS * 1000) // 1000) / FPS          # full.mp3 (207.88 s) + gaps, up to a whole frame
    words, wends = {}, {}
    for r in csv.DictReader(open(BOARD / "timings" / "word_timings.csv")):
        w = re.sub(r"[^A-Za-z0-9]", "", r["word"])
        words.setdefault(r["beat"], {}).setdefault(w, float(r["start_in_full_s"]))
        wends.setdefault(r["beat"], {}).setdefault(w, float(r["end_in_full_s"]))
    cues = {}
    for r in csv.DictReader(open(BOARD / "timings" / "sync_points.csv")):
        cues.setdefault(r["beat"], []).append((r["sync_on"].strip('"'), float(r["start_in_full_s"]) + 0, r["flag"]))
    layers = json.load(open(HERE / "ai_src" / "layers.json"))
    names = {b: [x["name"] for x in v["layers"] if x["name"] != "Meta/BeatID"] for b, v in layers.items()}

    out = {"title": TITLE, "fps": FPS, "w": W, "h": H, "total": total, "motion": MOTION, "scenes": [], "markers": []}
    prev_beat = None
    for i, (bid, start) in enumerate(beats):
        end = beats[i + 1][1] if i + 1 < len(beats) else total
        sh = shifts[bid]
        bc = {c: t + sh - start for c, t, _ in cues[bid]}
        bw = {w: t + sh - start for w, t in words.get(bid, {}).items()}
        bwe = {w: t + sh - start for w, t in wends.get(bid, {}).items()}

        def T(spec):
            m = re.fullmatch(r"(.+?)([+-]\d+(?:\.\d+)?)?", spec)
            base, off = m.group(1), float(m.group(2) or 0)
            if base == "start": t = 0.0
            elif base == "end": t = round((end - start) * FPS) / FPS
            elif base.startswith("w:"): t = bw[base[2:]]
            elif base.startswith("we:"): t = bwe[base[3:]]
            else: t = bc[base]
            return round(max(0.0, t + off), 3)

        cur, prv = names[bid], names[prev_beat] if prev_beat else []
        acts, named, post = [], set(), []
        for a in PLAN.get(bid, []):
            a = dict(a)
            if "at" in a: a["t"] = T(a.pop("at"))
            if "stops" in a: a["stops"] = [[T(s[0]), s[1], s[2]] for s in a["stops"]]
            if "keys" in a: a["keys"] = [[T(k[0]), k[1]] for k in a["keys"]]
            if "rows" in a: a["rows"] = [[T(r[0]), r[1], r[2]] for r in a["rows"]]
            if "until" in a: a["t_end"] = T(a.pop("until"))
            for k in ("go", "off", "out", "back", "new"):
                if k + "_at" in a: a["t_" + k] = T(a.pop(k + "_at"))
            if a["do"] == "cardswap" and "old" not in a:    # a roll written into the plan by hand: fill in both cards' geometry
                a["old"], a["new"] = card_geom(a["old_ai"]), card_geom(a["new_ai"])
            if a.pop("post", False):
                post.append(a); continue
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
        # every side-card content change rolls instead of cutting, centred on its cue: the old rows clear in the last 0.25 s
        # before it, the new rows arrive just after. A change on (or just after) a beat's first frame splits across the cut
        for a in list(acts):
            if a["layer"] == "Panel/Card" and a["do"] == "xfade":
                acts.remove(a)
                if a["t"] >= MOTION["card_out_d"]:
                    acts.append(cardswap(prev_beat, bid, a["t"] - MOTION["card_out_d"], a["t"], "both"))
                    for g in acts:                           # card content that leaves in this beat rolls out with the old rows
                        if g["do"] == "out" and g["layer"] in CARD_CONTENT.get(prev_beat, []):
                            g["t"] = round(a["t"] - MOTION["card_out_d"], 3); g["roll"] = card_geom(prev_beat)["rect"]
                else:
                    pb = next(b for sc_ in out["scenes"] for b in sc_["beats"] if b["id"] == prev_beat)
                    pb["acts"].append(cardswap(prev_beat, bid, pb["dur"] - MOTION["card_out_d"] + a["t"], pb["dur"], "out"))
                    for ln in CARD_CONTENT.get(prev_beat, []):     # layers that live in the card roll out with it
                        pb["acts"].append({"layer": ln, "do": "rollout", "t": round(pb["dur"] - MOTION["card_out_d"] + a["t"], 3),
                                           "clip": card_geom(prev_beat)["rect"]})
                    acts.append(cardswap(prev_beat, bid, 0, a["t"], "in"))
        scene = int(re.match(r"\d+", bid).group())
        sc = next((s for s in out["scenes"] if s["n"] == scene), None)
        if not sc:
            sc = {"n": scene, "name": f"Scene {scene} · {SCENES[scene]}", "start": start, "audio_shift": sh, "beats": []}
            out["scenes"].append(sc)
        sc["beats"].append({"id": bid, "key": layers[bid]["file"][:-4], "ai": bid, "prev_ai": prev_beat,
                            "order": cur, "prev_order": prv, "start": start, "dur": round((end - start) * FPS) / FPS, "acts": acts, "post": post})
        for c, t, flag in cues[bid]:
            out["markers"].append({"t": round(t + sh, 3), "beat": bid, "cue": c, "flag": flag})
        prev_beat = bid
    for k, sc in enumerate(out["scenes"]):
        sc["end"] = out["scenes"][k + 1]["start"] if k + 1 < len(out["scenes"]) else total
        # the VO stops where the next scene's audio would begin, so an added gap is silence
        nxt = out["scenes"][k + 1] if k + 1 < len(out["scenes"]) else None
        sc["audio_end"] = (nxt["start"] - nxt["audio_shift"] + sc["audio_shift"]) if nxt else total
    (HERE / "ae_plan.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for sc in out["scenes"]:
        print(sc["name"], sc["start"], "->", sc["end"])
        for b in sc["beats"]:
            print("  ", b["id"], b["start"], b["dur"], "; ".join(f"{a['layer']}:{a['do']}@{a.get('t', '')}" for a in b["acts"] if a["do"] != "hold"))


def card_geom(beat, layer="Panel/Card"):
    """The side card's white rect and its content rows (top to bottom), from the beat's art."""
    import xml.etree.ElementTree as ET
    NS = "{http://www.w3.org/2000/svg}"
    m = {x["id"]: x["name"] for x in json.load(open(HERE / "ai_src" / "layers.json"))[beat]["layers"]}
    g = next(c for c in ET.parse(HERE / "ai_src" / f"{beat}.svg").getroot() if m.get(c.get("id")) == layer)
    rects = [[float(e.get(k)) for k in ("x", "y", "width", "height")] + [e.get("opacity")] for e in g.iter(NS + "rect")]
    card = next(r[:4] for r in rects if r[4] is None and r[2] >= 500)
    bands = []
    for e in g.iter(NS + "text"):
        y, size = float(e.get("y")), float(re.search(r"font-size:([\d.]+)", e.get("style")).group(1))
        bands.append([y - 0.8 * size - 6, y + 0.3 * size + 6])
    for r in rects:                                   # chips inside the card travel with their text
        if r[4] is None and r[:4] != card: bands.append([r[1] - 2, r[1] + r[3] + 2])
    bands.sort(); rows = []
    for b in bands:
        if rows and b[0] <= rows[-1][1]: rows[-1][1] = max(rows[-1][1], b[1])
        else: rows.append(list(b))
    return {"rect": card, "rows": [[round(a, 1), round(b, 1)] for a, b in rows]}


def cardswap(old, new, t_out, t_in, phase):
    """One side-card roll: old rows leave from t_out (out phase), new rows arrive from t_in (in phase); beat-local times."""
    return {"layer": "Panel/Card", "do": "cardswap", "phase": phase, "old_ai": old, "new_ai": new, "old": card_geom(old),
            "new": card_geom(new), "t": round(t_out, 3), "t_new": round(t_in, 3)}


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
