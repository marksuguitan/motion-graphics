"""AVNRT vs AVRT: the After Effects build plan (Stage 4, first build).

Reads the locked timings (vo stitch starts, 3-board/timings/word_timings.csv and sync_points.csv), the beat layers
(build/ai_src/layers.json from prep_ai.py) and the sampled paths (build/paths.json from paths.js), applies the
choreography below and writes build/ae_plan.json, which build_ae.jsx reads. Moves are keyed to words, never typed times:
  "start"            the beat's first frame          "end"            its last frame (next beat's start)
  "cue:fast"         the sync point named "fast"     "w:fast" / "w:fast#2"   start of the 1st / 2nd spoken "fast"
  any of them +/- seconds: "w:node+0.3"
Motion is Comma Clinical (Motion Style Guide): snap and settle, things grow out of what is on screen, text cuts on whole on
its word, no crossfades, conduction moves at a constant rate, a hold after every landing, reading time per the guide.

Layers the plan doesn't name follow the defaults (DEFAULTS below): held if unchanged; changed in place -> cut swap on the
beat's first cue; changed and moved -> carried (travels and resizes onto its new place); new -> enters by kind at ENTER;
gone -> text cuts off on the first frame, everything else shrinks into its centre over 0.25 s (accelerating).

Actions (do):
  hold | cut (text cuts on; t_off cuts it off) | grow (from its centre, or pivot "left"/"top"; over=overshoot) |
  unfold (card unfolds from its left edge) | wipe (dir ltr/rtl/ttb/btt, d, linear, stops=[[t, x], ...]) |
  draw (strokes draw on with Trim Paths; rev draws from the path's end; linear for conduction) |
  swap (the previous version cuts to this one at t) | carry (previous version travels/resizes onto this one) |
  out (previous beat's layer leaves at t: cut, shrink or "drawoff") | fade (small text only: opacity over <= 0.2 s) |
  opacity (keys [[t, %], ...]) | lap (a pulse dot laps a loop: path, period, until) |
  travel (the layer rides along a path: legs [[path, t0, t1], ...]) | stay (previous beat's layer stays until t)
Run: python3 plan.py
"""
import csv, json, math, pathlib, re

HERE = pathlib.Path(__file__).resolve().parent
VIDEO = HERE.parent.parent
BOARD = VIDEO / "3-board"
FPS, W, H = 30, 1920, 1080
TITLE = "AVNRT vs AVRT"
SCENES = {1: "Hook", 2: "What a loop needs", 3: "AVNRT", 4: "AVRT", 5: "Between episodes", 6: "Treatment", 7: "Close"}
# Beat starts in the full track (3-board/audio/full.mp3, 5:00.14, Holds included), from the VO stitch (timings.py)
STARTS = {"1A": 0.0, "1B": 11.14, "1C": 16.84, "1D": 22.54, "2A": 25.54, "2B": 32.68, "2C": 37.34, "2D": 42.96, "2E": 49.86,
          "3A": 55.64, "3B": 61.1, "3C": 69.52, "3D": 72.58, "3E": 80.12, "3F": 84.3, "3G": 89.52, "3H": 92.68, "3I": 101.9,
          "3J": 109.84, "4A": 121.32, "4B": 129.02, "4C": 138.24, "4D": 146.18, "4E": 162.68, "4F": 178.3, "5A": 184.26,
          "5B": 203.32, "6A": 215.28, "6B": 223.7, "6C": 239.8, "6D": 245.18, "6E": 254.8, "6F": 274.36, "6G": 283.9, "7A": 287.86}
TOTAL = 300.14
MOTION = {
    "snap_d": 0.6, "cross_d": 0.75, "accel_d": 0.25, "land_over": 0.06, "land_back": 0.2,
    "card_d": 0.6,            # a card unfolds from its left edge
    "grow_d": 0.6,            # anatomy and diagrams grow from their centre, no overshoot
    "ring_d": 0.3,            # emphasis rings draw on
    "print_d": 2.4,           # an ECG strip prints left to right at a constant rate
    "pulse_r": 12, "halo_r": 22,    # the travelling pulse on the diagram (same as the art's Diagram/Wave)
    "pulse_r_heart": 9, "halo_r_heart": 16,
    "lap_heart": 2.2,         # s per lap of the big loop on the heart card
    "lap_small": 0.9,         # s per lap of the small loop on the heart card
    "lap_diagram": 1.4,       # s per lap of the small loop on the diagram
    "stagger": 2 / 30,
}
ENTER = 0.3                    # unplanned new layers enter this long after the beat starts (after the old ones have cleared)
TEXT = re.compile(r"^(Header|Eyebrow|Title|Label/|Text/|Diagram/(Tags|PathLabels|AtriaLabel))")
CARRY = re.compile(r"^(Cards/|HeartBackdrop|Heart/(Base|Loop/|AccessoryPathway|FibrousRing|SmallLoop|AtrialWave)|Diagram/(Halo|Channels|AVNode|Tags|PathLabels|Slow|Fast|Stem|His))")
STROKE = re.compile(r"^(Heart/(Loop/(Down|Up|Across)|SmallLoop|HisActive|AccessoryPathway|FibrousRing|Gate)|Diagram/(Halo|Channels|Slow|Fast|Stem|His)|Bracket/|Focus/|Leader/|Marker/)")

# ---------------------------------------------------------------- paths (comp pixels) for laps and travels
P = json.load(open(HERE / "paths.json"))


def path(beat, *legs):
    """Concatenate stroked paths: legs are layer names, "-" prefix runs that path backwards; the first polyline of each."""
    pts = []
    for leg in legs:
        rev = leg.startswith("-"); name = leg.lstrip("-")
        q = P[beat][name][0]["pts"]
        q = q[::-1] if rev else q
        pts += q if not pts else q[1:]
    return [[round(x, 1), round(y, 1)] for x, y in pts]


def circle_path(beat, layer, start_deg=-90, ccw=True, idx=1):
    """A channel circle sampled from its top, counter-clockwise (down the left = slow side) or clockwise."""
    q = P[beat][layer][idx]["pts"]
    xs, ys = [p[0] for p in q], [p[1] for p in q]
    cx, cy, r = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (max(xs) - min(xs)) / 2
    out = []
    for i in range(121):
        a = math.radians(start_deg + (-1 if ccw else 1) * 360 * i / 120)
        out.append([round(cx + r * math.cos(a), 1), round(cy + r * math.sin(a), 1)])
    return out


ORTHO = ("Heart/Loop/Down", "Heart/Loop/Up", "Heart/AccessoryPathway", "Heart/Loop/Across")
ANTI = ("-Heart/Loop/Across", "-Heart/AccessoryPathway", "-Heart/Loop/Up", "-Heart/Loop/Down")
D = MOTION["snap_d"]

# ---------------------------------------------------------------- choreography, beat by beat (Intent column, scene tables)
PLAN = {
    "1A": [  # two lead II strips, one above the other, same rate; nothing says which is which
        {"layer": "Cards/Patient1", "do": "unfold", "at": "start+0.1"},
        {"layer": "Text/Patient1", "do": "cut", "at": "start+0.5"},
        {"layer": "ECG/Patient1/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.3"},
        {"layer": "ECG/Patient1/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.6", "d": 3.0},
        {"layer": "Cards/Patient2", "do": "unfold", "at": "w:both"},
        {"layer": "Text/Patient2", "do": "cut", "at": "w:both+0.4"},
        {"layer": "ECG/Patient2/Grid", "do": "wipe", "dir": "ltr", "at": "w:both+0.2"},
        {"layer": "ECG/Patient2/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "w:both+0.5", "d": 3.0},
    ],
    "1B": [  # strips leave; the conduction heart lands and a small loop circles the AV node, the pulse lapping it
        {"layer": "Cards/Heart", "do": "unfold", "at": "start+0.25"},
        {"layer": "Heart/Base", "do": "grow", "at": "start+0.4"},
        {"layer": "Header", "do": "cut", "at": "start+0.7"},
        {"layer": "Heart/SmallLoop", "do": "grow", "at": "cue:AV-0.2", "d": 0.5},
        {"do": "lap", "name": "Pulse/Small", "path": "small:1B", "at": "cue:AV+0.3", "until": "end", "period": "lap_small", "heart": True},
    ],
    "1C": [  # the big loop draws itself: across the atria, down to the ventricles, and back up the pathway
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Heart/SmallLoop", "do": "out", "how": "shrink", "at": "start"},
        {"layer": "Heart/Loop/Across", "do": "draw", "rev": False, "linear": True, "at": "cue:atria-0.3", "d": 0.8},
        {"layer": "Heart/Loop/Down", "do": "draw", "linear": True, "at": "w:ventricles-0.2", "d": 0.8},
        {"layer": "Heart/Loop/Up", "do": "draw", "linear": True, "at": "w:ventricles+0.6", "d": 0.6},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "linear": True, "at": "cue:back", "d": 0.3},
        {"layer": "Heart/Loop/Arrows", "do": "cut", "at": "cue:back+0.35"},
        {"do": "lap", "name": "Pulse/Big", "path": "ortho:1C", "at": "cue:back+0.35", "until": "end", "period": "lap_heart", "heart": True},
    ],
    "1D": [  # the title lands while both loops keep running
        {"layer": "Header", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Heart/SmallLoop", "do": "grow", "at": "start+0.75", "d": 0.5},     # after the heart has moved over for the title
        {"layer": "Title", "do": "cut", "at": "start+0.8"},
        {"do": "lap", "name": "Pulse/Big", "path": "ortho:1D", "at": "start+0.75", "until": "end", "period": "lap_heart", "heart": True},
        {"do": "lap", "name": "Pulse/Small", "path": "small:1D", "at": "start+1.25", "until": "end", "period": "lap_small", "heart": True},
    ],
    "2A": [  # mark the AV plane along the valve rings; the atrial wave spreads and stops at it
        {"layer": "Title", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Heart/SmallLoop", "do": "out", "how": "shrink", "at": "start"},
        *[{"layer": l, "do": "out", "how": "drawoff", "at": "start", "d": 0.3} for l in ("Heart/Loop/Down", "Heart/Loop/Up", "Heart/Loop/Across", "Heart/AccessoryPathway")],
        {"layer": "Heart/Loop/Arrows", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Eyebrow", "do": "cut", "at": "start+0.4"},
        {"layer": "Header", "do": "cut", "at": "start+0.4"},
        {"layer": "Heart/AtrialWave", "do": "grow", "pivot": "top", "at": "w:atria", "d": 1.6, "linear": True},
        {"layer": "Heart/FibrousRing", "do": "draw", "at": "cue:insulated", "d": 0.8},
        {"layer": "Leader/Header", "do": "fade", "at": "cue:rings-0.2"},
        {"layer": "Label/Fibrous rings", "do": "cut", "at": "cue:rings"},
    ],
    "2B": [  # open one gap in the ring; the wave passes only there
        {"layer": "Eyebrow", "do": "swap", "at": "start"},
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Leader/Header", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Label/Fibrous rings", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Heart/Gate", "do": "draw", "at": "cue:only", "d": 0.5},
        {"layer": "Heart/HisActive", "do": "draw", "linear": True, "at": "w:node-0.2", "d": 0.9},
        {"layer": "Label/AV node → His bundle", "do": "cut", "at": "cue:His"},
    ],
    "2C": [  # cut to the schematic: two channels that split and rejoin, all drawn open; the heart fades back behind it
        {"layer": "Cards/Diagram", "do": "unfold", "at": "start+0.25"},
        {"layer": "HeartBackdrop", "do": "grow", "at": "start+0.35"},
        {"layer": "HeartBackdrop", "do": "opacity", "keys": [["w:but", 100], ["w:but+0.6", 51.4]]},   # 35 % -> 18 % (Mark)
        {"layer": "Eyebrow", "do": "cut", "at": "start+0.5"},
        {"layer": "Header", "do": "cut", "at": "start+0.5"},
        {"layer": "Diagram/AtriaLabel", "do": "cut", "at": "start+0.6", "fade_off": "start+3.1"},   # fades once the schematic is drawn
        {"layer": "Diagram/Halo", "do": "draw", "at": "cue:two-0.3", "d": 0.9},
        {"layer": "Diagram/Channels", "do": "draw", "at": "cue:two-0.3", "d": 0.9},
        {"layer": "Diagram/PathLabels", "do": "cut", "at": "cue:joined+0.2"},
    ],
    "2D": [  # each side gets its properties as the words land
        {"layer": "Header", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Eyebrow", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Header", "do": "cut", "at": "start+0.2"},
        {"layer": "Label/Fast · conducts quic", "do": "cut", "at": "cue:fast-0.2"},
        {"layer": "Label/Slow · conducts slow", "do": "cut", "at": "cue:slowly-0.2"},
        {"layer": "Label/They recover at diff", "do": "cut", "at": "w:and"},     # reading time: lands on "And they take..."
    ],
    "2E": [  # an early beat prints on the strip and enters the top of the diagram
        {"layer": "Cards/Strip", "do": "unfold", "at": "start+0.25"},
        {"layer": "Eyebrow", "do": "cut", "at": "start+0.3"},
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "until_x": [["cue:premature", 1660]], "d": 2.4},
        {"layer": "Focus/EarlyBeat", "do": "draw", "at": "cue:premature", "d": 0.3},
        {"layer": "Label/Early beat", "do": "cut", "at": "cue:premature+0.3"},
        {"layer": "Diagram/Stem", "do": "draw", "linear": True, "at": "w:arrives", "d": 0.4},
        {"layer": "Diagram/Active/Rest", "do": "cut", "at": "w:arrives+0.4"},
        {"layer": "Diagram/Wave", "do": "grow", "at": "w:arrives+0.3", "d": 0.4, "over": True},
    ],
    "3A": [  # the same junction, now the typical AVNRT circuit, both pathways in and around the AV node
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Diagram/AVNode", "do": "grow", "at": "cue:node-0.4", "d": 0.5},
        {"layer": "Diagram/Tags", "do": "cut", "at": "cue:node+0.2"},
    ],
    "3B": [  # a property card on each side
        {"layer": "Cards/Fast", "do": "unfold", "at": "cue:fast-0.2"},
        {"layer": "Text/Fast", "do": "cut", "at": "cue:fast+0.25"},
        {"layer": "Cards/Slow", "do": "unfold", "at": "cue:slow-0.2"},
        {"layer": "Text/Slow", "do": "cut", "at": "cue:slow+0.25"},
    ],
    "3C": [  # a sinus beat runs down the fast side to the His bundle
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Diagram/PathLabels", "do": "cut", "at": "start+0.3"},
        {"layer": "Diagram/Stem", "do": "draw", "linear": True, "at": "w:travel", "d": 0.3},
        {"layer": "Diagram/Fast", "do": "draw", "rev": True, "linear": True, "at": "w:travel+0.3", "d": 0.6},
        {"layer": "Diagram/Active/Rest", "do": "cut", "at": "w:travel+0.6"},
        {"layer": "Diagram/His", "do": "draw", "linear": True, "at": "w:travel+0.9", "d": 0.4},
    ],
    "3D": [  # the fast side shades as recovering; the premature wave takes the slow side
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Diagram/His", "do": "out", "how": "drawoff", "at": "start", "d": 0.3},
        {"layer": "Diagram/Stem", "do": "draw", "linear": True, "at": "w:premature", "d": 0.3},
        {"layer": "Diagram/Fast", "do": "swap", "at": "cue:recovering-0.3"},
        {"layer": "Label/recovering", "do": "cut", "at": "cue:recovering"},
        {"layer": "Diagram/Slow", "do": "draw", "linear": True, "at": "w:travels", "d": 1.6},
        {"layer": "Diagram/Active/Rest", "do": "swap", "at": "w:travels+0.8"},
    ],
    "3E": [  # the wave reaches the node; the shading clears as it does
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Diagram/Fast", "do": "stay", "until": "cue:recovered"},
        {"layer": "Label/recovering", "do": "stay", "until": "cue:recovered"},
        {"layer": "Diagram/Wave", "do": "travel", "legs": [["slow:3E", "start", "w:bottom"]]},
    ],
    "3F": [  # the signal turns and races back up the fast side, then down the slow side again
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Diagram/Fast", "do": "draw", "linear": True, "at": "w:races", "d": 0.8},
        {"layer": "Diagram/Wave", "do": "travel", "legs": [["fast:3F", "w:races", "w:races+0.8"], ["slow:3F", "w:down", "w:down+1.0"],
                                                            ["fast:3F", "w:down+1.0", "w:down+1.8"]]},
    ],
    "3G": [  # the circuit closes; the pulse keeps lapping it
        {"layer": "Header", "do": "swap", "at": "start"},
        {"do": "lap", "name": "Pulse", "path": "ring:3G", "at": "start", "until": "end", "period": "lap_diagram"},
    ],
    "3H": [  # each lap sends one wave down and one up together; the strip zooms to the P wave at the end of the QRS
        {"layer": "Header", "do": "cut", "at": "start+0.5"},
        {"layer": "Cards/ECG", "do": "unfold", "at": "start+0.6"},
        {"do": "lap", "name": "Pulse", "path": "ring:3H", "at": "start+0.8", "until": "end", "period": "lap_diagram"},
        {"layer": "Diagram/Stem", "do": "draw", "linear": True, "at": "w:fires", "d": 0.3},
        {"layer": "Diagram/His", "do": "draw", "linear": True, "at": "w:fires", "d": 0.5},
        {"layer": "Label/Down to the ventricl", "do": "cut", "at": "w:ventricles"},
        {"layer": "Label/Up to the atria", "do": "cut", "at": "w:atria"},
        {"layer": "Text/Down to the ventricl", "do": "cut", "at": "start+0.9"},
        {"layer": "ECG/Strip/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+1.0", "d": 2.4},
        {"layer": "ECG/ZoomFrame", "do": "draw", "at": "w:so", "d": 0.4},
        {"layer": "Box/ZoomFrame", "do": "unfold", "at": "w:so+0.3"},
        {"layer": "ECG/Zoom/Grid", "do": "wipe", "dir": "ltr", "at": "w:so+0.5"},
        {"layer": "ECG/Zoom/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "w:so+0.6", "d": 1.2},
        {"layer": "Focus/PWave", "do": "draw", "at": "cue:inside", "d": 0.3},
        {"layer": "Label/P wave hides here", "do": "cut", "at": "cue:inside+0.3"},
    ],
    "3I": [  # two leads; circle the pseudo S in II, then the pseudo R prime in V1
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/Lead", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/Lead", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Lead/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Lead/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.6", "d": 2.4},
        {"layer": "Cards/V1", "do": "unfold", "at": "start+0.35"},
        {"layer": "Text/V1", "do": "cut", "at": "start+0.7"},
        {"layer": "ECG/V1/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.5"},
        {"layer": "ECG/V1/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 2.4},
        {"layer": "Focus/Pseudo S", "do": "draw", "at": "cue:pseudo", "d": 0.3},
        {"layer": "Label/Pseudo S", "do": "cut", "at": "cue:pseudo+0.3"},
        {"layer": "Focus/Pseudo R′", "do": "draw", "at": "w:pseudo#2", "d": 0.3},
        {"layer": "Label/Pseudo R′", "do": "cut", "at": "cue:prime"},
    ],
    "3J": [  # three stat cards build on the words
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/Stat1", "do": "unfold", "at": "cue:sixty-0.4"},
        {"layer": "Text/Stat1", "do": "cut", "at": "cue:sixty"},
        {"layer": "Cards/Stat2", "do": "unfold", "at": "cue:young-0.4"},
        {"layer": "Text/Stat2", "do": "cut", "at": "cue:young"},
        {"layer": "Cards/Stat3", "do": "unfold", "at": "w:and-0.3"},      # reading time: lands on "and about two thirds"
        {"layer": "Text/Stat3", "do": "cut", "at": "w:and+0.1"},
    ],
    "4A": [  # back to the heart; the accessory pathway appears in the lateral wall, crossing the mitral ring
        {"layer": "Cards/Heart", "do": "unfold", "at": "start+0.25"},
        {"layer": "Heart/Base", "do": "grow", "at": "start+0.35"},
        {"layer": "Header", "do": "cut", "at": "start+0.5"},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "at": "cue:accessory", "d": 0.5},
        {"layer": "Leader/Header", "do": "fade", "at": "cue:accessory+0.4"},
        {"layer": "Label/Accessory pathway", "do": "cut", "at": "cue:accessory+0.5"},
        {"layer": "Heart/FibrousRing", "do": "draw", "at": "cue:crosses", "d": 0.8},
        {"layer": "Leader/Accessory pathway", "do": "fade", "at": "w:insulating"},
        {"layer": "Label/Fibrous ring", "do": "cut", "at": "w:insulating+0.1"},
    ],
    "4B": [  # orthodromic: the wavefront runs down the AV node, His bundle and branches
        {"layer": "Header", "do": "swap", "at": "cue:orthodromic"},
        {"layer": "Heart/AccessoryPathway", "do": "swap", "at": "start"},
        {"layer": "Heart/Loop/Down", "do": "draw", "linear": True, "at": "w:down", "d": 1.6},
        {"layer": "Heart/Rest", "do": "cut", "at": "w:down+1.6"},
        {"layer": "Label/AV node → His-Purkin", "do": "cut", "at": "w:his"},
        {"layer": "Label/Usually narrow QRS", "do": "cut", "at": "w:qrs"},
    ],
    "4C": [  # the wave climbs the pathway (it glows), crosses the atrium and returns to the node; the loop closes
        {"layer": "Header", "do": "swap", "at": "start"},
        {"layer": "Heart/Rest", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Label/AV node → His-Purkin", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Label/Usually narrow QRS", "do": "out", "how": "cut", "at": "start"},
        {"layer": "Heart/Loop/Up", "do": "draw", "linear": True, "at": "w:crosses", "d": 0.6},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "linear": True, "at": "w:crosses+0.6", "d": 0.5},
        {"layer": "Label/Up the accessory pat", "do": "cut", "at": "cue:up"},
        {"layer": "Heart/AtrialWave", "do": "grow", "pivot": "right", "at": "w:atria", "d": 1.4, "linear": True},
        {"layer": "Heart/Loop/Across", "do": "draw", "linear": True, "at": "w:atria", "d": 1.7},
        {"layer": "Heart/Loop/Arrows", "do": "cut", "at": "w:node"},
        {"do": "lap", "name": "Pulse/Big", "path": "ortho:4C", "at": "w:node", "until": "end", "period": "lap_heart", "heart": True},
        {"layer": "Label/The large majority o", "do": "cut", "at": "w:node"},     # reading time: on from "node", not "majority"
    ],
    "4D": [  # zoom one beat: the retrograde P in the ST segment, RP bracketed from QRS onset to P onset
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/ECG", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/ECG", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 3.0},
        {"layer": "Focus/RetroP", "do": "draw", "at": "cue:after", "d": 0.3},
        {"layer": "Label/In the ST segment, n", "do": "cut", "at": "w:st"},
        {"layer": "Bracket/RP", "do": "draw", "at": "w:rp", "d": 0.5},
        {"layer": "Label/RP: QRS onset → P on", "do": "cut", "at": "w:rp+0.4"},
        {"layer": "Label/Longer RP than typic", "do": "cut", "at": "w:longer#2"},
    ],
    "4E": [  # the loop reverses: down the pathway, up the node; the ventricles light muscle to muscle; a wide strip beside it
        {"layer": "Cards/Heart", "do": "unfold", "at": "start+0.25"},
        {"layer": "Heart/Base", "do": "grow", "at": "start+0.35"},
        {"layer": "Heart/FibrousRing", "do": "draw", "at": "start+0.6", "d": 0.6},
        {"layer": "Label/Less common", "do": "cut", "at": "start+0.5"},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "rev": True, "linear": True, "at": "w:down", "d": 0.5},
        {"layer": "Heart/Loop/Up", "do": "draw", "rev": True, "linear": True, "at": "w:down+0.5", "d": 0.7},
        {"layer": "Heart/VentGlow", "do": "grow", "at": "w:down+0.6", "d": 1.2, "linear": True},
        {"layer": "Heart/Loop/Down", "do": "draw", "rev": True, "linear": True, "at": "w:back", "d": 0.7},
        {"layer": "Heart/Loop/Across", "do": "draw", "rev": True, "linear": True, "at": "w:back+0.7", "d": 0.7},
        {"layer": "Heart/Loop/Arrows", "do": "cut", "at": "w:back+1.4"},
        {"layer": "Header", "do": "cut", "at": "cue:antidromic"},
        {"do": "lap", "name": "Pulse/Big", "path": "anti:4E", "at": "w:back+1.4", "until": "end", "period": "lap_heart", "heart": True},
        {"layer": "Cards/Strip", "do": "unfold", "at": "w:because-0.3"},
        {"layer": "Text/Strip", "do": "cut", "at": "w:because+0.1"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "w:because"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "w:because+0.3", "d": 2.4},
    ],
    "4F": [  # a two-column card: the first side-by-side comparison of the loops
        {"layer": "Cards/AVNRT", "do": "unfold", "at": "start+0.25"},
        {"layer": "Label/AVNRT", "do": "cut", "at": "start+0.5"},
        {"layer": "Text/AVNRT", "do": "cut", "at": "start+0.5"},
        {"layer": "Cards/AVRT", "do": "unfold", "at": "start+0.35"},
        {"layer": "Label/AVRT", "do": "cut", "at": "start+0.6"},
        {"layer": "Text/AVRT", "do": "cut", "at": "start+0.6"},
    ],
    "5A": [  # a resting strip; short PR, delta wave and wide QRS marked as each is named
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/ECG", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/ECG", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 3.0},
        {"layer": "Bracket/PR", "do": "draw", "at": "cue:shortens", "d": 0.4},
        {"layer": "Label/Short PR", "do": "cut", "at": "cue:shortens+0.3"},
        {"layer": "Focus/Delta", "do": "draw", "at": "cue:delta", "d": 0.3},
        {"layer": "Label/Delta wave", "do": "cut", "at": "cue:delta+0.3"},
        {"layer": "Bracket/QRS", "do": "draw", "at": "cue:widens", "d": 0.4},
        {"layer": "Label/Wide QRS", "do": "cut", "at": "cue:widens+0.3"},
    ],
    "5B": [  # manifest (delta wave) over concealed (normal); the warning chip lands last
        {"layer": "Cards/Manifest", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/Manifest", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Manifest/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Manifest/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 2.4},
        {"layer": "Cards/Concealed", "do": "unfold", "at": "cue:concealed-0.5"},
        {"layer": "Text/Concealed", "do": "cut", "at": "cue:concealed"},
        {"layer": "ECG/Concealed/Grid", "do": "wipe", "dir": "ltr", "at": "cue:concealed-0.3"},
        {"layer": "ECG/Concealed/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "cue:concealed", "d": 2.4},
        {"layer": "Label/A normal resting ECG", "do": "cut", "at": "w:so"},   # reading time: 8 words need 3.7 s
    ],
    "6A": [  # both loops side by side, each AV node ringed
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/AVNRT", "do": "unfold", "at": "start+0.25"},
        {"layer": "Cards/AVRT", "do": "unfold", "at": "start+0.35"},
        {"layer": "Label/AVNRT", "do": "cut", "at": "w:avnrt"},
        {"layer": "Label/AVRT", "do": "cut", "at": "w:avrt"},
        {"layer": "HeartBackdrop", "do": "grow", "at": "start+0.5"},
        {"layer": "Diagram/Halo", "do": "draw", "at": "start+0.7", "d": 0.7},
        {"layer": "Diagram/Channels", "do": "draw", "at": "start+0.7", "d": 0.7},
        {"layer": "Diagram/Slow", "do": "draw", "linear": True, "at": "w:avnrt-0.3", "d": 0.6},
        {"layer": "Diagram/Fast", "do": "draw", "linear": True, "at": "w:avnrt+0.3", "d": 0.6},
        {"layer": "Diagram/Active/Rest", "do": "cut", "at": "w:avnrt+0.9"},
        {"layer": "Diagram/AVNode", "do": "grow", "at": "start+0.9", "d": 0.5},
        {"do": "lap", "name": "Pulse/AVNRT", "path": "ring:6A", "at": "w:avnrt+0.9", "until": "end", "period": "lap_diagram"},
        {"layer": "Heart/Base", "do": "grow", "at": "start+0.6"},
        {"layer": "Heart/Loop/Down", "do": "draw", "linear": True, "at": "w:avrt-0.4", "d": 0.5},
        {"layer": "Heart/Loop/Up", "do": "draw", "linear": True, "at": "w:avrt+0.1", "d": 0.4},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "linear": True, "at": "w:avrt+0.5", "d": 0.2},
        {"layer": "Heart/Loop/Across", "do": "draw", "linear": True, "at": "w:avrt+0.7", "d": 0.4},
        {"layer": "Heart/Loop/Arrows", "do": "cut", "at": "w:avrt+1.1"},
        {"do": "lap", "name": "Pulse/AVRT", "path": "ortho:6A", "at": "w:avrt+1.1", "until": "end", "period": "lap_heart", "heart": True},
        {"layer": "Focus/NodeRing", "do": "draw", "at": "cue:node-0.2", "d": 0.3},
        {"layer": "Focus/NodeRing 2", "do": "draw", "at": "cue:node", "d": 0.3},
    ],
    "6B": [  # build the steps; the AV node blocks briefly in both views and each loop falls quiet
        {"layer": "Header", "do": "swap", "at": "start"},
        *[{"layer": l, "do": "stay", "until": "w:blocking+0.6", "how": "drawoff"} for l in
          ("Diagram/Slow", "Diagram/Fast", "Heart/Loop/Down", "Heart/Loop/Up", "Heart/Loop/Across")],
        *[{"layer": l, "do": "stay", "until": "w:blocking+0.6"} for l in ("Diagram/Active/Rest", "Heart/Loop/Arrows", "Focus/NodeRing", "Focus/NodeRing 2")],
        {"layer": "Heart/AccessoryPathway", "do": "swap", "at": "w:blocking+0.6"},
        {"do": "lap", "name": "Pulse/AVNRT", "path": "ring:6A", "at": "start", "until": "w:node", "period": "lap_diagram", "phase": "6A"},
        {"do": "lap", "name": "Pulse/AVRT", "path": "ortho:6A", "at": "start", "until": "w:node", "period": "lap_heart", "heart": True, "phase": "6A"},
        {"layer": "Diagram/AVNode", "do": "swap", "at": "w:node"},
        {"layer": "Heart/AVNodeBlocked", "do": "grow", "at": "w:node", "d": 0.4},
        {"layer": "Label/AV node blocked", "do": "cut", "at": "w:node+0.3"},
        {"layer": "Label/AV node blocked 2", "do": "cut", "at": "w:node+0.3"},
    ],
    "6C": [  # the unstable row; the strip converts to sinus beneath
        {"layer": "Header", "do": "cut", "at": "start+0.3"},
        {"layer": "Cards/Steps", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/Steps", "do": "cut", "at": "start+0.5"},
        {"layer": "Label/1 Vagal maneuver", "do": "cut", "at": "start+0.5"},
        {"layer": "Label/2 Adenosine, unless ", "do": "cut", "at": "start+0.5"},
        {"layer": "Cards/Strip", "do": "unfold", "at": "start+0.35"},
        {"layer": "Text/Strip", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.45"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "until_x": [["w:use-0.2", 1198]], "d": 3.4},
        {"layer": "Label/Synchronized cardiov", "do": "cut", "at": "w:use-0.2"},     # reading time: on from "use", not "cardioversion"
        {"layer": "Text/Synchronized cardiov", "do": "cut", "at": "w:use-0.2"},
        {"layer": "Marker/Shock", "do": "draw", "at": "w:use-0.2", "d": 0.3},
        {"layer": "Label/Loop broken", "do": "cut", "at": "w:use-0.1"},
    ],
    "6D": [  # caution card with the regular wide-complex strip
        {"layer": "Cards/Caution", "do": "unfold", "at": "start+0.25"},
        {"layer": "Label/Caution · wide compl", "do": "cut", "at": "cue:caution-0.4"},
        {"layer": "Text/Caution · wide compl", "do": "cut", "at": "w:antidromic"},
        {"layer": "Label/Avoid AV nodal block", "do": "cut", "at": "cue:avoid"},
        {"layer": "Text/Avoid AV nodal block", "do": "cut", "at": "cue:Procainamide"},
        {"layer": "Cards/Strip", "do": "unfold", "at": "start+0.35"},
        {"layer": "Text/Strip", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.45"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 2.4},
    ],
    "6E": [  # its own card: the strip prints fast, irregular and wide; the cautions build on the words
        {"layer": "Cards/Danger", "do": "unfold", "at": "start+0.25"},
        {"layer": "Label/Danger", "do": "cut", "at": "cue:pre-excited-0.3"},
        {"layer": "Text/Danger", "do": "cut", "at": "cue:pre-excited"},
        {"layer": "Cards/Strip", "do": "unfold", "at": "w:very-0.4"},
        {"layer": "Text/Strip", "do": "cut", "at": "w:very"},
        {"layer": "ECG/Grid", "do": "wipe", "dir": "ltr", "at": "w:very-0.2"},
        {"layer": "ECG/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "w:very", "d": 3.0},
        {"layer": "Label/Avoid AV nodal block", "do": "cut", "at": "w:av"},
        {"layer": "Label/Stable: procainamide", "do": "cut", "at": "cue:procainamide"},
        {"layer": "Label/Unstable: electrical", "do": "cut", "at": "w:unstable"},
    ],
    "6F": [  # an ablation mark lands on the slow side; the loop can't close
        {"layer": "Cards/Diagram", "do": "unfold", "at": "start+0.25"},
        {"layer": "HeartBackdrop", "do": "grow", "at": "start+0.35"},
        {"layer": "Header", "do": "cut", "at": "start+0.4"},
        {"layer": "Diagram/Halo", "do": "draw", "at": "start+0.5", "d": 0.7},
        {"layer": "Diagram/Channels", "do": "draw", "at": "start+0.5", "d": 0.7},
        {"layer": "Diagram/Fast", "do": "draw", "rev": True, "linear": True, "at": "start+1.2", "d": 0.5},
        {"layer": "Diagram/AVNode", "do": "grow", "at": "start+0.9", "d": 0.5},
        {"layer": "Diagram/Tags", "do": "cut", "at": "start+1.2"},
        {"layer": "Diagram/PathLabels", "do": "cut", "at": "start+1.2"},
        {"layer": "Ablation", "do": "grow", "over": True, "at": "cue:slow-0.2", "d": 0.5},
        {"layer": "Label/Success above 95%", "do": "cut", "at": "w:with"},       # reading time: on from "with success"
    ],
    "6G": [  # close on the lateral wall; an ablation mark lands on the pathway
        {"layer": "Cards/Heart", "do": "unfold", "at": "start+0.25"},
        {"layer": "Heart/Base", "do": "grow", "at": "start+0.35"},
        {"layer": "Header", "do": "cut", "at": "start+0.4"},
        {"layer": "Heart/FibrousRing", "do": "draw", "at": "start+0.6", "d": 0.5},
        {"layer": "Heart/AccessoryPathway", "do": "draw", "at": "start+0.8", "d": 0.4},
        {"layer": "Ablation", "do": "grow", "over": True, "at": "cue:accessory", "d": 0.5},
    ],
    "7A": [  # the opening strips return, now labelled, each beside its loop
        {"layer": "Cards/Smallloop", "do": "unfold", "at": "start+0.25"},
        {"layer": "Text/Small loop", "do": "cut", "at": "start+0.6"},
        {"layer": "ECG/Smallloop/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.4"},
        {"layer": "ECG/Smallloop/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 3.0},
        {"layer": "Cards/Bigloop", "do": "unfold", "at": "start+0.35"},
        {"layer": "Text/Big loop", "do": "cut", "at": "start+0.7"},
        {"layer": "ECG/Bigloop/Grid", "do": "wipe", "dir": "ltr", "at": "start+0.5"},
        {"layer": "ECG/Bigloop/Trace", "do": "wipe", "dir": "ltr", "linear": True, "at": "start+0.7", "d": 3.0},
        {"layer": "Label/Small loop", "do": "cut", "at": "cue:small"},
        {"layer": "Dots/Smallloop", "do": "grow", "over": True, "at": "cue:small+0.2", "d": 0.4},
        {"layer": "Label/Big loop", "do": "cut", "at": "cue:big"},
        {"layer": "Dots/Bigloop", "do": "grow", "over": True, "at": "cue:big+0.2", "d": 0.4},
        {"layer": "Label/A clue, not a rule", "do": "cut", "at": "w:it's"},       # reading time: on from "It's a clue"
    ],
}

# ---------------------------------------------------------------- timings
IPA = {"/ˌkjuːɑːrˈɛs/": "qrs", "/ˌeɪviːɑːrˈtiː/": "avrt", "/ˌiːsiːˈdʒiː/": "ecg", "/ˌeɪˈviː/": "av", "hiss": "his",
       "pur-kin-jee": "purkinje", "pro-kane-uh-mide": "procainamide"}


def norm(w):
    w = w.strip().strip(".,:;!?\"'").lower()
    return IPA.get(w, re.sub(r"[^a-z0-9\-']", "", w))


def load_words():
    words = {}
    for r in csv.DictReader(open(BOARD / "timings" / "word_timings.csv")):
        words.setdefault(r["beat"], []).append((norm(r["word"]), float(r["start_in_beat"])))
    # letter-by-letter acronyms ("A V N R T") also answer to the joined word ("avnrt") at the first letter
    for b, ws in words.items():
        extra = []
        for i in range(len(ws)):
            for n in (5, 4, 2):
                if i + n <= len(ws) and all(len(x[0]) == 1 for x in ws[i:i + n]):
                    extra.append(("".join(x[0] for x in ws[i:i + n]), ws[i][1]))
        ws += sorted(extra, key=lambda x: x[1])
        ws.sort(key=lambda x: x[1])
    return words


def load_cues():
    cues = {}
    for r in csv.DictReader(open(BOARD / "timings" / "sync_points.csv")):
        if r["time_in_beat"]:
            cues.setdefault(r["beat"], {})[r["sync_word"]] = float(r["time_in_beat"])
    return cues


def main():
    snap = lambda t: round(t * FPS) / FPS
    order = list(STARTS)
    words, cues = load_words(), load_cues()
    layers = json.load(open(HERE / "ai_src" / "layers.json"))
    names = {b: [x["name"] for x in v["layers"]] for b, v in layers.items()}
    fx = {b: {x["name"]: x.get("fx") for x in v["layers"] if x.get("fx")} for b, v in layers.items()}
    out = {"title": TITLE, "fps": FPS, "w": W, "h": H, "total": snap(TOTAL), "motion": MOTION, "scenes": [], "markers": []}
    phases = {}
    prev = None
    for i, bid in enumerate(order):
        start = snap(STARTS[bid])
        end = snap(STARTS[order[i + 1]]) if i + 1 < len(order) else snap(TOTAL)
        dur = round(end - start, 4)

        def T(spec):
            m = re.fullmatch(r"(.+?)([+-]\d+(?:\.\d+)?)?", spec)
            base, off = m.group(1), float(m.group(2) or 0)
            if base == "start": t = 0.0
            elif base == "end": t = dur
            elif base.startswith("cue:"): t = cues[bid][base[4:]]
            elif base.startswith("w:"):
                w, _, n = base[2:].partition("#")
                hits = [x[1] for x in words[bid] if x[0] == w]
                if not hits: raise SystemExit(f"{bid}: no word {w!r} in {[x[0] for x in words[bid]]}")
                t = hits[int(n or 1) - 1]
            else: raise SystemExit(f"{bid}: bad time {spec}")
            return round(min(max(0.0, t + off), dur - 1 / FPS), 3)

        def PATH(spec):
            kind, b = spec.split(":")
            if kind == "small": return path(b, "Heart/SmallLoop")
            if kind == "ortho": return path(b, *ORTHO)
            if kind == "anti": return path(b, *ANTI)
            if kind == "ring": return circle_path(b, "Diagram/Channels")
            if kind == "slow": return path(b, "Diagram/Slow")
            if kind == "fast": return path(b, "Diagram/Fast")
            raise SystemExit(spec)

        cur, prv = names[bid], (names[prev] if prev else [])
        first = min(cues.get(bid, {"_": ENTER}).values())
        acts, named = [], {}
        for a in PLAN.get(bid, []):
            a = dict(a)
            for k in ("at", "until", "fade_off"):
                if k in a: a[{"at": "t", "until": "t_end", "fade_off": "t_off"}[k]] = T(a.pop(k))
            if "keys" in a: a["keys"] = [[T(k[0]), k[1]] for k in a["keys"]]
            if "legs" in a: a["legs"] = [[PATH(l[0]), T(l[1]), T(l[2])] for l in a["legs"]]
            if "until_x" in a: a["stops"] = [[T(s[0]), s[1]] for s in a.pop("until_x")]
            if a["do"] == "lap":
                a["pts"] = PATH(a.pop("path"))
                a["period"] = MOTION[a["period"]]
                ph = phases.get(a.pop("phase", None) or "", {}).get(a["name"])
                a["offset"] = ph if ph is not None else 0.0      # carries on from where the previous beat's pulse was
                phases.setdefault(bid, {})[a["name"]] = round((a["offset"] + (dur - a["t"]) / a["period"]) % 1.0, 4)
                acts.append(a); continue
            ln = a["layer"]
            if a["do"] in ("out", "stay") and ln not in prv: raise SystemExit(f"{bid}: {ln} is not in {prev}")
            if a["do"] not in ("out", "stay") and ln not in cur: raise SystemExit(f"{bid}: {ln} is not in this beat ({cur})")
            if a["do"] == "opacity":
                named.setdefault(ln, []); acts.append(a); continue
            named.setdefault(ln, []).append(a["do"])
            if ln in fx.get(bid, {}): a["fx"] = fx[bid][ln]
            acts.append(a)
        # defaults for everything the plan doesn't name
        for n in cur:
            if n in named and any(d not in ("out", "stay") for d in named[n]): continue
            f = fx.get(bid, {}).get(n)
            if n == "Background":
                acts.append({"layer": n, "do": "hold"})
            elif n not in prv:
                acts.append(enter(n, f))
            elif changed(prev, bid, n):
                mv = moved(prev, bid, n) and CARRY.match(n)
                acts.append({"layer": n, "do": "carry" if mv else "swap", "t": 0.0 if mv or moved(prev, bid, n) else round(first, 3),
                             "auto": True, **({"fx": f} if f else {})})
            else:
                acts.append({"layer": n, "do": "hold", **({"fx": f} if f else {})})
        for n in prv:
            if n not in cur and n not in named:
                acts.append({"layer": n, "do": "out", "how": "cut" if TEXT.match(n) or n.startswith("Leader/") else "shrink", "t": 0.0, "auto": True,
                             **({"fx": fx[prev][n]} if n in fx.get(prev, {}) else {})})
        for a in acts:                                   # carried-over layers keep their effects
            if a["do"] in ("out", "stay") and a["layer"] in fx.get(prev or "", {}): a["fx"] = fx[prev][a["layer"]]
        scene = int(bid[0])
        sc = next((s for s in out["scenes"] if s["n"] == scene), None)
        if not sc:
            sc = {"n": scene, "name": f"Scene {scene} · {SCENES[scene]}", "start": start, "beats": []}
            out["scenes"].append(sc)
        sc["beats"].append({"id": bid, "key": layers[bid]["file"][:-4], "ai": bid, "prev_ai": prev, "order": cur, "prev_order": prv,
                            "start": start, "dur": dur, "acts": acts})
        for c, t in cues.get(bid, {}).items():
            out["markers"].append({"t": round(start + t, 3), "beat": bid, "cue": c})
        prev = bid
    for k, sc in enumerate(out["scenes"]):
        sc["end"] = out["scenes"][k + 1]["start"] if k + 1 < len(out["scenes"]) else out["total"]
    (HERE / "ae_plan.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    for sc in out["scenes"]:
        print(sc["name"], sc["start"], "->", sc["end"])
        for b in sc["beats"]:
            print("  ", b["id"], b["start"], b["dur"], "; ".join(f"{a.get('layer', a.get('name'))}:{a['do']}@{a.get('t', '')}" for a in b["acts"] if a["do"] != "hold"))


def enter(n, f):
    a = {"layer": n, "t": ENTER, "auto": True}
    if f: a["fx"] = f
    if TEXT.match(n): a["do"] = "cut"
    elif n.startswith("Cards/") or n.startswith("Box/"): a["do"] = "unfold"; a["t"] = 0.25
    elif re.match(r"^ECG(/.*)?/Grid$", n): a["do"] = "wipe"; a["dir"] = "ltr"
    elif re.match(r"^ECG(/.*)?/Trace$", n): a["do"] = "wipe"; a["dir"] = "ltr"; a["linear"] = True; a["d"] = MOTION["print_d"]
    elif STROKE.match(n): a["do"] = "draw"; a["d"] = 0.6
    else: a["do"] = "grow"
    return a


_cache = {}
def _layers(b):
    import xml.etree.ElementTree as ET
    if b not in _cache:
        r = ET.parse(HERE / "ai_src" / f"{b}.svg").getroot()
        m = {x["id"]: x["name"] for x in json.load(open(HERE / "ai_src" / "layers.json"))[b]["layers"]}
        _cache[b] = {m[c.get("id")]: re.sub(rb"hb(Clip|Fade|Mask)\d+", b"hb", ET.tostring(c).replace(f'id="{c.get("id")}"'.encode(), b"")) for c in r if c.get("id") in m}
    return _cache[b]


def changed(b0, b1, name):
    return _layers(b0).get(name) != _layers(b1).get(name)


_bb = None
def moved(b0, b1, name):
    """Same layer, different place or size (from bboxes.json, written by paths.js): carry it rather than cut."""
    global _bb
    if _bb is None:
        f = HERE / "bboxes.json"
        _bb = json.load(open(f)) if f.exists() else {}
    a, b = _bb.get(b0, {}).get(name), _bb.get(b1, {}).get(name)
    if not a or not b: return False
    return max(abs(a[i] - b[i]) for i in range(4)) > 8


if __name__ == "__main__":
    main()
