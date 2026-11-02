# Normal Conduction

A 47.5 s motion piece with no VO, made Nov 2, 2026 at Mark's request: a small orb is the electrical impulse of one
normal beat, travelling SA node → atria → AV node → bundle of His → bundle branches → Purkinje fibers, to show what
normal conduction looks like. Mark waived the brief and script gates for this piece ("just show it to me when you are done").

| | |
| --- | --- |
| Style | Comma Clinical motion (`src/style/comma.ts`), **monochrome palette** (Mark's override): Comma's light grey ground, charcoal orb and type, gray heart. Palette in `src/style/mono.ts` |
| Build | Remotion, entirely in the cloud (`4-animation/remotion/`) |
| Art | Mark's gray conduction heart, `3-board/art/heart-conduction-gray.svg` (from marksuguitan/motion `assets/anatomy/heart/heart-conduction-gray.svg`) |
| Sound | Synthesized SFX only (`4-animation/build/sfx.py`): typing ticks, pops, blips at the SA node, AV node and the bundle split, soft thumps on ventricular contraction, a monitor beep on each QRS |
| Renders | Project files: `videos/Normal Conduction/renders/` (review, burned-in time) and `delivery/` (clean) |

## Beat map

| ID | Time | What happens | On screen |
| --- | --- | --- | --- |
| 1 title | 0:00–0:04.7 | A dot pops in and types "Normal conduction." as its own period, then deletes it | Title |
| 2 heart | 0:04.7–0:07.3 | The dot grows into the orb, hops, lands on the SA node; the heart unfolds from that point | — |
| 3A SA node | 0:07.3–0:10.0 | Orb pings twice (fires) | Step 1/5: SA node, "fires the impulse" |
| 3B atria | 0:10.0–0:12.6 | Orb runs the internodal tracts to the AV node; small fronts light both atria (Bachmann's bundle to the LA) | Step 2: Atria |
| 3C AV node | 0:12.6–0:15.6 | Orb squashes into the AV node and crawls through it (the delay); ring on the node | Step 3: AV node, "a brief delay" |
| 3D His + branches | 0:15.6–0:18.9 | Orb exits fast down the His bundle and splits into two at the top of the septum: right and left bundle branches | Step 4: Bundle of His |
| 3E Purkinje | 0:18.9–0:23.4 | Fronts spread through the Purkinje fibers up the ventricular walls; the heart squeezes | Step 5: Purkinje fibers |
| 4A ECG slowed | 0:23.4–0:36.2 | The path resets; one beat runs again in slow motion with its ECG drawing in sync; a bracket marks each part | P wave / Flat line (AV node delay) / QRS / T wave |
| 4B real speed | 0:36.2–0:41.4 | Six beats at real speed (75/min), the ECG scrolling, a squeeze and a beep per beat | Normal sinus rhythm |
| 5 outro | 0:41.4–0:47.5 | The ECG draws out, the heart folds back into the orb, which becomes the period of "Normal conduction." again | Title |

## How the impulse is timed

`4-animation/build/conduction_geo.py` traces the drawn pathway, then computes when the impulse reaches every point
(fastest path from the SA node, with an atrial speed, a slow AV-node speed and a fast His-Purkinje speed) so that within
one 0.8 s beat: the far left atrium is reached at 100 ms (end of the P wave), the impulse leaves the AV node at 125 ms,
and the farthest Purkinje fiber at 225 ms. The ECG uses PR 160 ms and QRS about 80 ms. These are modelled values for the
picture, inside the normal ranges below, and no number is shown on screen. The walk-through and the slowed beat stretch
time (`src/data/timeline.json`); the real-speed section does not.

## Sources

- StatPearls, Electrocardiogram (NCBI Bookshelf NBK549803): PR about 120–200 ms; QRS under 120 ms, usually 60–100 ms.
- StatPearls, Physiology, Sinoatrial Node (NBK459238): the SA node is the heart's pacemaker and starts each impulse.
- StatPearls, Atrioventricular Node (NBK557664): the AV node delays the impulse so the atria empty before the ventricles contract.
- StatPearls, Physiology, Bundle of His (NBK531498): the His bundle carries the impulse from the AV node into the ventricles, then the bundle branches and Purkinje system.

## Rebuild

```
cd "4-animation/build" && python3 conduction_geo.py && python3 sfx.py   # numpy, scipy, scikit-image, Pillow; node + playwright
cd ../remotion && npm install
TIMES=7.6,13.5,31.2 npm run check        # stills at any times (no VO, so no sync points)
npm run render:review -- 2               # -> 5-finish/renders/
npm run render:final                     # -> 6-delivery/
```

## Change log

| Date | Change |
| --- | --- |
| Nov 2, 2026 | v1 built and rendered (review v1 and final) |
