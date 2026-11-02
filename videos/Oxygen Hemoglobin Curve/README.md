# Oxygen Hemoglobin Curve

Production doc: https://claude.ai/artifact/YAP5tHcbiA5QpoKKy3LpQb (the index to this folder).

Imported on Nov 2, 2026 from `~/Documents/Medzcool/Content/Oxygen Hemoglobin Curve/` on Mark's Mac. The original folder is untouched.

The video was first built in an earlier project, in a different pipeline: a Remotion (code-rendered) video with one full VO take. It was not built with per-beat SVGs, per-beat VO or After Effects. Here is how its files map:

- `2-script/Oxygen Hemoglobin Curve script v2 draft.md` was `oxyhemoglobin script-v2-draft.md`. It was written after the outside medical review and hasn't been voiced or accepted yet.
- `1-brief/reference/storyboard v1.2/` was `Oxygen Curve Storyboard/`: 20 key frames rendered from the Remotion build, plus `voiceover-timed.mp3` (take A of script v1, 3:10). It is reference only. The frames are not beat art, and the track doesn't contain beat files.

**Not in git, still only on the Mac:** `oxygen-dissociation-curve-v2.mp4` (render v2) and `logo-intro-preview-v7-sfx.mp4`.
- `1-brief/reference/remotion v2/` is the Remotion source Mark uploaded on Nov 2, 2026. It is reference for the After Effects rebuild: the curve math (`src/hill.ts`), the palette, the logo-to-cell morph and the dash physics. It also holds `vo/` (takes A and B of script v1 with word timings). `public/vo_timed.wav` and `public/vo.mp3` were left out; `prep_vo.py` regenerates the first, and the second is the same file as `vo/takeA.mp3`.

**Decision, Nov 2, 2026:** Mark chose to rebuild the video in After Effects under the production guide. The Remotion build won't be finished.
