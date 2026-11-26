# Electrical Alternans short: "Tall. Short."

A 39 s vertical short (1080×1920, 30 fps) in Comma Clinical, made in Remotion. Type and sound effects only: no voice-over and no anatomy art (Mark, Nov 25, 2026: "simple motion graphics short for youtube, use comma clinical style, use sound effects and text only. be creative. use remotion"). v1 went to Mark for review on Nov 25, 2026.

## The idea

The type acts out the finding. Words and the letters "QRS" are set tall, then short, on a steady beat (one every 0.5 s, 120/min: regular and fast). A monitor beep sits on every beat, higher on tall beats and lower on short beats, so the alternans can be heard. The word "heart" swings in a ring of fluid, toward a chest electrode and away, one swing per two beats. When the fluid is drained the ring closes in, the swinging stops, every QRS is the same height and every beep is the same pitch.

## On-screen text and timing

Every line comes from the approved long-video script (Gate 2, Oct 23, 2026). Times are the short's own timecode.

| Time | On screen | Script beat |
| --- | --- | --- |
| 0:00 | Tall. / Short. / Tall. / Short. (one per beat) | 1A |
| 0:04 | QRS QRS QRS QRS (tall, short, tall, short) · Regular rhythm. · Fast rate. · Every other QRS changes height. | 1A |
| 0:10 | THIS IS · Electrical alternans (the title alternates in size) · A sign, not a diagnosis. | 1B, 2C |
| 0:14 | THE CAUSE TO KNOW · A large pericardial effusion · labels: electrode, fluid, heart | 3C |
| 0:17 | The heart swings in a bag of fluid. | 3C |
| 0:21 | Toward the electrode: tall. Away: short. (QRS readout under the ring) | 3D |
| 0:25 | Drain the fluid. | 3E |
| 0:28 | The swinging stops. So does the alternans. | 3E |
| 0:31 | Tall. Short. Tall. Short. · Think swinging heart. · Then get the echo. | 6A, 6B |
| 0:37 | Medzcool mark | |

Source for the script's facts: StatPearls, "Electrical Alternans" (NBK534229, PMID 30480962), Mark's reference for the long video. The StatPearls page could not be re-opened from the cloud workspace on Nov 25, 2026 (bot check), so the short adds no fact that is not in the approved script. The "swinging heart" with total electrical alternans in tamponade is also described in Verlaan D, et al. BMJ Case Rep. 2018 (doi:10.1136/bcr-2018-224771).

## Files

- `src/data/timeline.json`: the beat grid (first beat, beat length, the beat each thing lands on). The picture and the sound both read it.
- `src/Short.tsx`: the whole short. `src/style/comma.ts`, `theme.ts`, `src/lib/Fonts.tsx`, `public/fonts/` are copies from `library/remotion/`.
- `sfx.py`: synthesizes `public/sfx.wav` (nothing downloaded): beeps, soft landing hits, a whoosh on each swing, the drain, the logo chime.
- `stills.mjs`, `render.mjs`: check stills and renders, using the headless Chromium preinstalled in Claude cloud sessions.

## Rebuild

```sh
npm ci
python3 sfx.py                    # writes public/sfx.wav (not in git); re-run after any timeline change
node stills.mjs out/check 3.5 12 22.2 35.5
node render.mjs review 2          # timecode burned in -> out/
node render.mjs final             # clean -> out/
```

Renders are not in git. They live in the project files: `videos/Electrical Alternans/shorts/`.
