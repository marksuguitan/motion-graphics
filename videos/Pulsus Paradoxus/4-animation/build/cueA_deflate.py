"""Cue A v2 (Mark 2026-10-24): Scene 1 cuff now DEFLATES, as in the Korotkoff Sounds video.
Cuff falls 2.0 mmHg/s (same rate as Cue B) from START so the first expiratory tap lands on
"first tap" (1A, 5.94 s); breathing as before (expiration 0-3 s, inspiration 3-5 s, 5 s cycle),
so taps vanish on inspiration 8-10 s ("breathes in", 8.20 s) and return on expiration
("breathe out", 10.92 s). The cue ends at 1A end + 0.6 s, before the cuff reaches 116 mmHg.
Usage: python3 cueA_deflate.py <dir with korotkoff_synth.py + pulsus_synth.py> <out dir>"""
import json, os, sys
sys.path.insert(0, sys.argv[1])
sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2], "x"]   # pulsus_synth reads argv[1] at import
import pulsus_synth as ps
out = sys.argv[2]
RATE = ps.RATE                      # 2.0 mmHg/s
T_END = 12.651 + 0.6                # 1A ends 12.651 s (animatic v4) + 0.6 s
T_CROSS = 5.80                      # cuff crosses 132 mmHg just before "first" (5.94 s)
START = ps.SBP_EXP + RATE * T_CROSS # 143.6 mmHg
cuff = lambda t: START - RATE * t
log = ps.render(T_END, cuff, 0.0, "cueA_1A", out)
aud = [b["time_s"] for b in log if b["audible"]]
info = dict(file="cueA_1A.wav", starts_at_s=0.0, start_cuff_mmHg=START, rate_mmHg_s=RATE, end_s=T_END,
            end_cuff_mmHg=round(cuff(T_END), 1), first_tap_s=aud[0], first_tap_cuff=round(cuff(aud[0]), 1),
            audible_taps_s=aud, breath_bands=[[3.0, 5.0], [8.0, 10.0]],
            beats=[b["time_s"] for b in log])
json.dump(info, open(os.path.join(out, "cueA_markers.json"), "w"), indent=1)
print(json.dumps({k: v for k, v in info.items() if k != "beats"}))
