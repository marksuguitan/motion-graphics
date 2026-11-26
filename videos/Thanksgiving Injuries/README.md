# Thanksgiving Injuries

"Five Ways the Feast Ends in the ER": a no-narration motion piece (sound effects only, under 1:30) on common
Thanksgiving injuries and illnesses, for medical students. Requested by Mark on Nov 26, 2026.

| | |
| --- | --- |
| Status | Final v1 rendered Nov 26, 2026 (1:27.1 with the end screen), at Mark's review. Mark waived the gates ("build this all in the cloud, use your discretion") |
| Production doc | Claude doc, the only copy: https://claude.ai/artifact/WD4yGKrwK7zGuhUimm2CeM |
| Style | Comma Clinical; one plate that morphs into each hazard and back |
| Sound | SFX only, no VO and no music. Timing comes from on-screen reading time and measured SFX hits instead of word timings |
| Build | Remotion (`4-animation/remotion/`). `build/timeline.py` sets every time from the reading-time rule and writes `src/data/timeline.json`; `build/sfx.py` synthesizes the SFX track from the same file; then `npm run check` (stills, `TIMES=` list) and `npm run render:final` → `6-delivery/` |
| Script export | `2-script/Thanksgiving Injuries script v1.md` (for the outside medical review) |

Scenes: 1 cold open (plate) · 2 morning, carving cuts · 3 afternoon, hot oil · 4 dinner, choking and food bolus
impaction · 5 after dinner, C. perfringens · 6 late night, holiday heart · 7 close · house end screen.

Rebuild: `cd 4-animation/build && python3 timeline.py && python3 sfx.py`, then in `4-animation/remotion`:
`npm ci && npm run render:final`. Renders also go to the project files, `videos/Thanksgiving Injuries/delivery/`.

Changes from script v1 made while building (at my discretion, per Mark): 6A reads "after heavy drinking" instead of
"after a binge" (the glass makes it alcohol, "binge" alone could mean food); 4C adds the note "Adults · StatPearls".
