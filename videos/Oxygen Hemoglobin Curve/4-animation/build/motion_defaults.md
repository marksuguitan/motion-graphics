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

## Comma Clinical (Nov 2, 2026)

Mark chose Comma Clinical for this video (production doc, Style row). It replaces the v6 "playful" override; the source is the Motion Style Guide, section "Comma Clinical: Warm Clinical with Comma motion", and its After Effects settings table. If this list and the guide disagree, the guide wins. The curves (snap, cross, accel, anti) come from `library/scripts/adobe/comma_easing.jsx`; the durations and amounts are the `MOTION` config at the top of `plan.py`. Change a value, run `plan.py`, then `build_ae.jsx`.

| Setting | Value | Used for |
| --- | --- | --- |
| Snap and settle | 0.6 s (first key 16 % at 6x average speed, last key 70 % at speed 0) | The default for every move, mask reveal and draw-on |
| Cross | 0.75 s | Moves the eye tracks across the frame: the 1B cell carry and travel, the 1C merge, the 2A stage and title-to-kicker carries |
| Accelerate | 0.25 s | Forms collapsing into a cut (the end of 1B) |
| Landing overshoot | 8 %, one rebound, settled in 0.2 s | Shapes growing from a point: the RBCs, tetramers, O2 dots, the P50 marker |
| Squash | off (was 75/125 on impact, stretch 10 % along a move) | Mark, Nov 2, 2026: no squish on the RBCs. `squash` and `stretch` in `MOTION` turn it back on |
| Anticipation | 30 px counter-move over 0.2 s | The 1B cell carry and the 2A title-to-kicker carry |
| Stagger | 2 frames, under 0.4 s in total | Siblings clearing together (the end of 1B) |
| Hold | at least 0.4 s after a landing | Set by the sync points; not changed by the build |
| Idle bob | ±2 px, 2.5 s period | A resting RBC (ambient life, kept subtle) |
| Emphasis | ring snap to 160 % over 0.3 s; chip pulse 108 % over 0.3 s | The 4A and 4B points, the P50 dot (5A, 5B), the 6C "large" point; the 8C "Bohr" chip |

Rules applied in the build:
- Text cuts on whole on its sync word: no fade and no rise. Secondary labels cut on just after the shape they name lands.
- No crossfades between ideas: a card whose text changes cuts on the cue; anything leaving cuts.
- Nothing slides in from off-screen: side cards unfold from their left edge, factor chips (8B, 9B) grow from their slot, shifted curves (8A, 9A, 10A) start on the normal curve and snap and settle into place with no spring.
- No overshoot or squash on the graph, axes, curves or anatomy.
- Landing sounds stay off.
- The 1B to 1C transition keeps its morph (capsule to card, cell to dot to title), retimed to these curves; the dot writes line 1 on "oxyhemoglobin" and line 2 cuts on 0.12 s later.

**Timing change, Nov 2, 2026 (v9-v14, Mark):** silence added before beats so cards and notes can be read (`GAPS` in `plan.py`): 1.0 s after 2B (1.5 s in v9), 1.0 s after 3D (2.0 s in v14-v15), 1.0 s after 4C and 1.0 s after 8C. Against `3-board/timings/sync_points.csv`, beats, markers and audio are +1.0 s from 3A, +2.0 s from 4A, +3.0 s from 5A and +4.0 s from 8D; the VO files and word timings are unchanged. The video is 211.90 s.
