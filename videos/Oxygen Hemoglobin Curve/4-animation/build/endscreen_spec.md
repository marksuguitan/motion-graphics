# YouTube end screen (layout B): build spec

Mark picked layout B on Nov 2, 2026. Style frame: `3-board/style/endscreen_B.svg`. Build art without placeholder words: `3-board/art/END_endscreen.svg` (regenerate both with `python3 3-board/style/make_endscreen.py 3-board/style`).

## Length and placement
- One comp, `End · YouTube`, 15.0 s, 1920×1080, 30 fps. It goes in the master right after Scene 10's last frame, with no overlap.
- There's no VO, no music and no landing sounds.
- YouTube end screens can run 5–20 s. Mark sets the end screen in YouTube Studio to start on this comp's first frame plus 1.0 s, once everything has landed.

## Layout (px, from the art)
| Layer | What | Position |
| --- | --- | --- |
| Background/Fill | soft ground #F7F7F5 | full frame |
| Logo/Mark | Medzcool mark, ink #222222 | x 120, top 112, 120 px wide |
| Panel/Thanks | "Thanks for watching", Manrope 600, 52 px, ink; "Right means release.", Inter 400, 28 px, ink2 #6A6A6A | baselines y 150 and 200, x 280 |
| Slot/Subscribe | dashed circle (mute #B9B5AE, 3 px, dash 14/10), fill soft | centre (1700,160), r 90 |
| Label/WatchNext | "WATCH NEXT" and "RECOMMENDED", Manrope 700, 23 px, tracking 3, ink2 | baselines y 356, x 120 and x 1000 |
| Slot/Video | dashed 16:9 plate, rx 16 | x 120–920, y 390–840 |
| Slot/Best | dashed 16:9 plate, rx 16 | x 1000–1800, y 390–840 |

For YouTube Studio: the "Video" element covers Slot/Video and the "Best for viewer" element covers Slot/Best (each 41.7% of the frame width, top at 36.1%). The "Subscribe" element sits on the circle.

## Motion (Comma Clinical; times from the comp's first frame)
- **0.00–0.45:** 10C clears. Do it in the last frames of 10C, or as a copy of 10C's end state at the start of this comp; either works.
  - The takeaway chip and footnote cut off.
  - The summary cards roll out of their card (cardswap exit), then the card shrinks into its centre.
  - The curves, grid and axes draw out in reverse, as in the 2B→3A change.
  - The stage card shrinks into its centre with accelerate.
  - The whole clear takes about 0.45 s with 2-frame staggers.
- **0.45:** the Medzcool mark grows from its centre with snap and settle and a 6% landing overshoot. It's a shape, so overshoot is allowed.
- **0.55:** "Thanks for watching" cuts on whole. "Right means release." cuts on 3 frames later.
- **0.60:** the subscribe circle grows from its centre (snap and settle, 0.5 s). Its dashed stroke traces on clockwise from 12 o'clock over 0.5 s.
- **0.75:** "WATCH NEXT" and "RECOMMENDED" cut on.
- **0.80:** both plates grow out of a point at their own centres to full size (snap and settle, 0.6 s), 3 frames apart (Video first). Each dashed outline traces on clockwise from its top-left over 0.6 s.
- **About 1.4 to 15.0:** hold. Everything has landed by about 1.4 s, so YouTube's elements, appearing at about 1.0 s, cover landed plates. There's no fade-out at the end.

## Checks
- No empty frames at the 10C→End join.
- Every plate and the circle are at the positions above on the last frame. Compare that frame with END_endscreen.svg.
- The master's runtime grows by 15.0 s. Report the new runtime.
