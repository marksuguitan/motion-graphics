# Normal Conduction

A 36.8 s motion piece with no VO, made Nov 2, 2026 at Mark's request: a small orb is the electrical impulse of one
normal beat, travelling SA node → atria → AV node → bundle of His → bundle branches → Purkinje fibers, to show what
normal conduction looks like. Mark waived the brief and script gates for this piece ("just show it to me when you are done").

| | |
| --- | --- |
| Style | Comma Clinical motion (`src/style/comma.ts`), **monochrome palette** (Mark's override): Comma's light grey ground, charcoal orb and type, grey heart. Palette in `src/style/mono.ts` |
| Build | Remotion, entirely in the cloud (`4-animation/remotion/`) |
| Art | Mark's simplified conduction heart, `3-board/art/heart-conduction-natural.svg` (same file as marksuguitan/motion `assets/anatomy/heart/heart-conduction-natural.svg`), recoloured to greys by lightness in `conduction_geo.py` (v1 used the gray heart) |
| Sound | Synthesized SFX only (`4-animation/build/sfx.py`): typing ticks, pops, blips at the SA node, AV node and the bundle split, soft thumps on ventricular contraction, a monitor beep on each QRS |
| Renders | Project files: `videos/Normal Conduction/renders/` (review, burned-in time) and `delivery/` (clean) |

## Beat map

| ID | Time | What happens | On screen |
| --- | --- | --- | --- |
| 1 title | 0:00–0:03.3 | A dot pops in and types "Normal conduction." as its own period, then deletes it | Title |
| 2 heart | 0:03.3–0:05.9 | The dot grows into the orb, hops, lands on the SA node; the heart unfolds from that point | — |
| 2B preview | 0:05.9–0:08.7 | Three full beats at real speed, a preview of the whole path, then the orb settles back on the SA node | — |
| 3A SA node | 0:08.7–0:09.3 | Orb pings twice (fires) | Step 1/5: SA node, "fires the impulse" |
| 3B atria | 0:09.3–0:10.1 | Orb runs the internodal tracts to the AV node; small fronts light both atria (Bachmann's bundle to the LA) | Step 2: Atria |
| 3C AV node | 0:10.1–0:11.1 | Orb squashes into the AV node and crawls through it (the delay); ring on the node | Step 3: AV node, "a brief delay" |
| 3D His + branches | 0:11.1–0:11.8 | Orb exits fast down the His bundle and splits into two at the top of the septum: right and left bundle branches, which reach the ends of their Purkinje networks nearly together (right 215 ms, left 225 ms) | Step 4: Bundle of His |
| 3E Purkinje | 0:11.8–0:12.7 | Fronts spread through the Purkinje fibers up the ventricular walls; the heart squeezes | Step 5: Purkinje fibers |
| 4A ECG slowed | 0:12.7–0:25.5 | The path resets; one beat runs again in slow motion with its ECG drawing in sync; a bracket marks each part | P wave / Flat line (AV node delay) / QRS / T wave |
| 4B real speed | 0:25.5–0:30.7 | Six beats at real speed (75/min), the ECG scrolling, a squeeze and a beep per beat | Normal sinus rhythm |
| 5 outro | 0:30.7–0:36.8 | The ECG draws out, the heart folds back into the orb, which becomes the period of "Normal conduction." again | Title |

## How the impulse is timed

`4-animation/build/conduction_geo.py` traces the drawn pathway, then computes when the impulse reaches every point
(fastest path from the SA node, with an atrial speed, a slow AV-node speed, and one speed each for the right and left
ventricular systems) so that within one 0.8 s beat: the far left atrium is reached at 100 ms (end of the P wave), the
impulse leaves the AV node at 125 ms, the last right-ventricular fiber at 215 ms and the last left-ventricular fiber at
225 ms (Mark: both sides finish nearly together, the left a little later). The ECG uses PR 160 ms and QRS about 80 ms. These are modelled values for the
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
| Nov 2, 2026 | v2 (Mark's notes): simplified natural heart in greys; right and left ventricular conduction end nearly together (215 / 225 ms); title hold 1.4 s shorter, so everything after it is 1.4 s earlier |
| Nov 2, 2026 | v3 (Mark's note): three real-speed beats as a preview at 0:05.9, before the step-by-step walk; everything after moves 2.8 s later |
| Nov 2, 2026 | v4 (Mark's note): no backflow in the lower atrial tract at 0:14. The two lower tracts touched just outside the AV node, so the impulse ran back up the longer one; that junction is now part of the node, the atrial pass runs with the node closed, and no front dot starts inside the node. Every atrial tract now runs SA node to AV node |
| Nov 2, 2026 | v5 (Mark's note): the labeled SA node → Purkinje pass is brisk, 0.9–1.4 s per label with no long holds (7.1 s, was 16.1 s); the slowed-down beat and everything after it are 9 s earlier; 39.9 s total |
| Nov 3, 2026 | v6 (Mark's note): the labeled SA node → Purkinje pass runs 4 s (0.6–1.0 s per label); everything after it is 3.1 s earlier; 36.8 s total |
| Nov 11, 2026 | v7 (Mark's note): in the slowed beat the QRS starts shortly after the impulse leaves the AV node. The AV delay still runs 16.9–18.7 s; the His bundle and bundle branches up to QRS onset (36 ms of beat time) now take 0.3 s instead of about 1.3 s, so the QRS label and the first deflection come at 19.0 s, not 19.5 s. Total length unchanged |
