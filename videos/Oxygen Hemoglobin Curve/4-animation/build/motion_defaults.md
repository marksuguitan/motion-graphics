# Motion defaults for the After Effects build

Copied on Nov 2, 2026 from the Motion Style Guide (project knowledge, "Motion" section), which stays the only source of truth. If the two disagree, the style guide wins.

**Feel (all scenes)**

- Easing: smooth ease-out for entrances, ease-in-out for moves across the frame; no linear moves except constant-rate processes (*starting value*: entrances 0.4–0.6 s).
- Transitions are continuous where possible: elements carry over and reshape between beats rather than cutting.

**Geometric choreography (signature language)**

- Abstract, mid-century-inspired shapes (circles, half-circles, capsules, rounded squares) with weight, momentum and physical interaction: they fall, roll, stack, bounce and settle.
- Used for introductions, transitions and conceptual explanations: a shape can stand in for an idea, then hand off to the anatomy.
- Anatomical and clinical scenes keep their visual specificity; shapes frame or lead into them, never replace the accurate drawing.
- Shapes use the palette's neutrals and accents, so the signature motion stays consistent from video to video.

**From the production guide, Part 3:** one focal move at a time; every move lands on its measured sync point (`3-board/timings/sync_points.csv`); holds per the scene tables.

## Playful override (Nov 2, 2026)

Mark asked for this video to be more playful. Motion only: art, VO and sync points stay locked, every move still starts on its measured sync point, and one focal move happens at a time. The numbers live in `MOTION` at the top of `plan.py`, so Mark can tune them there: change a value, run `plan.py`, then `build_ae.jsx`, and the next version picks it up. No bounce values are written into individual moves.

| Setting | Value | Used for |
| --- | --- | --- |
| Spring overshoot | 10 % | Entrances and moves: one visible overshoot, a small rebound (30 % of the overshoot), then rest |
| Spring settle | 0.6 s | From the start of the move to rest |
| Spring shape | peak at 55 %, rebound at 80 % of the settle, rebound 30 % of the overshoot | Sets the apparent frequency and damping of every spring |
| Stagger | 0.05 s, 0.3 s each | Siblings clearing together (the end of 1B) |
| Pop | 0 → 115 % → 100 % | O2 dots, markers, tetramers |
| Chip pop | 108 % | Chips with text (SO2 readouts): held back so the text stays steady |
| Text overshoot | 4 % max | Labels, titles, notes and footnotes fade and rise; never bounced |
| Card slide | 80 px from the right | Side cards entering (not cards that crossfade their text) |
| Chip drop | 24 px from above (60 px crossed the card heading, so it was held back) | Factor chips (8B, 9B), one per cue, landing with a 4 % squash from the chip's base (`chip_squash`) |
| Stretch / squash | 10 % / 8 % | Red cells travelling in 1B: stretch peaks at 40 % of the move, squash on arrival, settle in 0.25 s |
| Idle bob | ±4 px, 2 s period | A red cell at rest (1A, 1B); it fades in and out over 0.4 s and is off during any move |
| Emphasis | one ring ping, 0.4 s, to 180 % | The 4A and 4B points, the P50 dot (5A, 5B), the 6C "large" point; the art itself isn't scaled. The 8C "Bohr" chip pulses to 112 % (`pulse_scale`) |
| Exits | 0.25 s, ease in, to 96 % | Layers leaving at a cut |

Linear moves remain only for constant-rate processes.
