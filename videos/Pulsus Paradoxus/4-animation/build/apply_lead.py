"""Silent lead-ins before a beat's VO (Mark 2026-10-25: 3A labels the anatomy before "Now let's fill ...").
Reads timeline.json + cues/markers.json, writes timeline_now.json (+ "lead") and cues/markers_now.json with every beat from
the lead-in beat onward, and Cue B, shifted later by the lead. The scene before keeps its end; the extra time opens the beat."""
import json, sys
D = "/tmp/claude-0/anim"
LEAD = {"3A": 1.5}
tl = json.load(open(f"{D}/timeline.json")); mk = json.load(open(f"{D}/cues/markers.json"))
shift = 0.0; at = {}
for b in tl["beats"]:
    shift += LEAD.get(b["id"], 0.0); at[b["id"]] = shift
    b["start"] = round(b["start"] + shift, 3); b["end"] = round(b["end"] + shift, 3)
tl["total"] = round(tl["total"] + shift, 3); tl["lead"] = LEAD
s5 = at["5B"]
cb = mk["cueB"]; cb["starts_at_video_s"] = round(cb["starts_at_video_s"] + s5, 3)
for k, v in cb.items():
    if isinstance(v, dict) and "video_s" in v: v["video_s"] = round(v["video_s"] + s5, 3)
json.dump(tl, open(f"{D}/timeline_now.json", "w"), indent=1); json.dump(mk, open(f"{D}/cues/markers_now.json", "w"), indent=1)
print("total", tl["total"], "3A VO", [b["start"] for b in tl["beats"] if b["id"] == "3A"], "cueB", cb["starts_at_video_s"])
