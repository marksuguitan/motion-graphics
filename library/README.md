# Library

Scripts shared by every video. Copy the ones a video needs into its `4-animation/build/` (or run them from here) rather than editing them per video; improvements come back here.

| Folder | Scripts |
| --- | --- |
| `scripts/word-timings/` | `align_words.py` (carries word times from a reference take onto a file by sound, MFCC + DTW), `sync_points.py` (looks up each Sync on word), `qc.py` (pause check) |
| `scripts/adobe/` | `build_ai.jsx` (SVG → layered `.ai`), `ae_engine.jsx` + `ae_geom.js` (After Effects comp builder), `flatten.py` |

These are the Pulsus Paradoxus versions, the most recent. Some still have that video's paths written in (for example `qc.py`); pass the video's own paths when reusing them.
