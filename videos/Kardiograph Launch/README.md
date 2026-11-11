# Kardiograph Launch

A short motion piece with no VO announcing the new Kardiograph app, made Nov 11, 2026 at Mark's request. It is
appended to **Normal Conduction** and opens on that video's last frame, pixel for pixel ("Normal conduction." with
the orb as its period).

| | |
| --- | --- |
| Style | Normal Conduction's monochrome Comma Clinical (`src/style/mono.ts`, `src/style/comma.ts`). Kardiograph amber #B97516 appears only on the app's mark. Manrope headings, Inter body |
| Build | Remotion, in the cloud (`4-animation/remotion/`), 1920×1080, 30 fps |
| Tracings | Every EKG is drawn by the Kardiograph engine (marksuguitan/medzcool-kardiograph `src/core`): `4-animation/build/engine_strips.ts` writes `src/data/engine.json` (lead II, 250 Hz). Nothing is hand-drawn |
| Sound | Synthesized SFX only (`4-animation/build/sfx.py`, same voices as Normal Conduction): ticks as the title deletes and the name types, a beep and soft thump on each QRS, detents on the slider, a blip per practice strip, pops on the card and the mark |
| Renders | Project files: `kardiograph/launch-video/` (the piece alone, 17.0 s, and joined to Normal Conduction, 52.3 s: the joined cut ends Normal Conduction at 35.3 s, after the title has finished typing, so its last 1.5 s of hold is dropped) |
| Copy | From the Kardiograph launch landing page: Basic only (course and practice); the editor (Pro) is not shown |

## Beat map

| ID | Time | What happens | On screen |
| --- | --- | --- | --- |
| 1 hand-off | 0:00–0:02.25 | The title deletes itself with the period as cursor; the period grows into the orb and hops onto the pen position | Normal conduction. |
| 2 paper | 0:02.25–0:05.8 | The orb is the pen: a normal sinus lead II scrolls out of it at 25 mm/s on true-scale paper, then slows to a stop | LEAD II / Now read it on the EKG. |
| 3 learn | 0:05.8–0:09.3 | The strip slides away; the orb opens into a lesson card; a QRS slider (the orb as its knob) widens one beat 90 → 150 ms, a bracket under the QRS | LEARN / Every figure is a tracing you can move. |
| 4 practice | 0:09.3–0:12.3 | Four practice strips sweep in, 0.75 s each: atrial fibrillation, Mobitz I, complete heart block, inferior STEMI | PRACTICE / A new tracing every time. |
| 5 end card | 0:12.3–0:17.0 | The card closes into the amber mark, the wave draws on, "Kardiograph" types on with the orb as its period | Kardiograph. / Learn to read the EKG. / Course and practice, part of Medzcool Basic / kardiograph.medzcool.com |

## Rebuild

```
cd 4-animation && KARDIOGRAPH=/path/to/medzcool-kardiograph node --experimental-strip-types build/engine_strips.ts && python3 build/sfx.py
cd remotion && npm install
TIMES=1.7,5.5,9.3,12.6,17.2 npm run check
npm run render:review -- 1
npm run render:final
```

## Change log

| Date | Change |
| --- | --- |
| Nov 11, 2026 | Storyboard v1 (stills from the Remotion build) for Mark's review |
| Nov 11, 2026 | Mark approved the storyboard. SFX added; v1 final rendered, alone and joined to Normal Conduction (ffmpeg concat, re-encoded at CRF 16) |
| Nov 11, 2026 | v2 (Mark's note: the hand-off was too long): the title starts deleting on the first frame (was 0.5 s in), 17.0 s total; the joined cut drops Normal Conduction's last 1.5 s of title hold. The Kardiograph motion now starts at 0:36.1 of the joined video (was 0:38.1) |
| Nov 11, 2026 | Vertical cut for Reels and Shorts: composition `Vertical` (1080×1920), same scene with a 9:16 layout (`setLayout` in the scene); the joined short is Normal Conduction's Vertical cut to 35.3 s, then this, 52.3 s, in project files `kardiograph/launch-video/` |
