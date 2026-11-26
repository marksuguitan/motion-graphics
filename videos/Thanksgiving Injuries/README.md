# Thanksgiving Injuries

"Five Ways the Feast Ends in the ER": a no-narration motion piece (sound effects only, under 1:30) on common
Thanksgiving injuries and illnesses, for medical students. Requested by Mark on Nov 26, 2026.

| | |
| --- | --- |
| Status | Final v2 rendered Nov 26, 2026 (1:13.9 with the end screen), at Mark's review. v1 was 1:27.1. Mark waived the gates ("build this all in the cloud, use your discretion") |
| Production doc | Claude doc, the only copy: https://claude.ai/artifact/WD4yGKrwK7zGuhUimm2CeM |
| Style | Comma Clinical; one plate that morphs into each hazard and back |
| Sound | SFX only, no VO and no music. Timing comes from on-screen reading time and measured SFX hits instead of word timings |
| Build | Remotion (`4-animation/remotion/`). `build/timeline.py` sets every time from the reading-time rule and writes `src/data/timeline.json`; `build/kardiograph_strip.ts` synthesizes the scene 6 rhythm strip with the Kardiograph engine; `build/sfx.py` synthesizes the SFX track from the same times; then `npm run check` (stills, `TIMES=` list) and `npm run render:final` → `6-delivery/` |
| Script export | `2-script/Thanksgiving Injuries script v1.md` (for the outside medical review) |

Scenes: 1 cold open (plate) · 2 morning, carving cuts · 3 afternoon, hot oil · 4 dinner, choking and food bolus
impaction · 5 after dinner, C. perfringens · 6 late night, holiday heart · 7 close · house end screen.

Rebuild, in this order: `cd 4-animation/build && python3 timeline.py` (don't pipe it into `head`, it stops before
the last files are written), `node --experimental-strip-types kardiograph_strip.ts <path to a medzcool/kardiograph clone>`,
`python3 sfx.py`, then in `4-animation/remotion`: `npm ci && npm run render:final`. Only when the airway art changes:
`NODE_PATH=$(npm root -g) node airway_prep.cjs` (needs Playwright). Renders also go to the project files, `videos/Thanksgiving Injuries/delivery/`.

Changes from script v1 made while building (at my discretion, per Mark): 6A reads "after heavy drinking" instead of
"after a binge" (the glass makes it alcohol, "binge" alone could mean food); 4C adds the note "Adults · StatPearls".

## v2 (Nov 26, 2026), from Mark's notes on v1

- Title types on and is erased from the end; the erase overlaps the plate's move into the knife, so it is the
  transition (`Title` in `Text.tsx`).
- Numbers count up (`n()` in `Text.tsx`): 1,190, 20 minutes and 71% from 0, 85–90% from 60–65, 90% from 60.
- Tighter timing everywhere. Reading time is now `max(2.4, 0.8 + 0.3 x words)` counting only the words that are read
  (no kicker, no citation), 0.1 s after a scene's last card, and the next scene's shape starts moving while the last
  card rolls out. Cards with more to read keep more time. Total went from 1:27.1 to 1:13.9.
- Scene 4 uses Mark's airway vector (`3-board/art/airways original.svg`), cleaned and recoloured into the palette by
  `airway_prep.cjs`. The bite goes plate, mouth, top of the trachea; thrusts send it back to the plate; the second
  bite goes down the esophagus and lodges. The drawing's esophagus is hidden behind the lung, so it is continued
  downward in the same pink (`ESO_EXT` in `Art.tsx`).
- Scene 6 strip is lead II from the Kardiograph engine (`synthesizeCalibrated`): the `afib` preset, about 113/min,
  then the `normal` preset at 78/min, spliced on the baseline. Drawn at true scale (25 mm/s, 10 mm/mV) on scrolling
  ECG paper, with K+ and Mg2+ chips for "check potassium and magnesium".
