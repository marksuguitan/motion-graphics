# Oxyhemoglobin Dissociation Curve — Remotion project

Current state: v2 video plus the refined logo intro (study-based dash, motion blur, sound effect).
Script v1 narration (take A). Script v2 (peer-review changes) is drafted but not recorded yet.

## Setup
    npm install            # Remotion 4.0.539
    npx remotion studio    # live preview in the browser

## Render
    npx remotion render src/index.ts Main out/main.mp4 --concurrency=4 --crf=18 --audio-bitrate=192k
    ./splice.sh out/main.mp4 out/final.mp4   # swaps in the motion-blurred logo dash (480 fps comp "MainHi")

Use the `angle` GL renderer (set in remotion.config.ts). `swangle` paints stale copies of SVG content
in sequential renders (the stray x-axis line at 0:17 in v1). The config also points at a local
headless Chromium path; delete that line on your own machine.

## Files
- src/Main.tsx: all scenes. Animation times come from narration word indices (`w(i)` in src/cues.ts).
- src/intromotion.ts: logo dash physics (all timing knobs at the top).
- src/logo.tsx: Medzcool logo polygons and the logo-to-cell morph.
- src/tetramer.tsx: ribbon hemoglobin tetramer.
- src/hill.ts: Hill-equation curves (n = 2.7, P50 26.8; shifted 20 and 36 are illustrative).
- src/theme.ts, src/util.ts: palette, fonts, easing helpers.
- prep_vo.py: inserts section pauses into the voice-over and writes public/vo_timed.wav + src/cues.json.
- sfx_logo.py: synthesizes public/sfx_logo.wav from the same timeline as the dash.
- stills.mjs: `node stills.mjs 12 30.5 ...` renders stills at given seconds.
- vo/: original take A mp3 and the word timings it was cut from.
