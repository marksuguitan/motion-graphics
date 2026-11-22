# Shorts 2, 3 and 5 (Remotion)

The Remotion source of draft v5 (`1-brief/reference/remotion v5/`, also `source-remotion-v5.tar.gz` in the project files) plus three more vertical shorts cut from the v9 narration (Nov 22, 2026). The new code is `src/ShortsV9.tsx`; `Short.tsx` and `Main.tsx` only gained `export`s, and `Root.tsx` registers the compositions `Short2Narrow`, `Short3Reason` and `Short5Tells`. Copy and timecodes: `6-delivery/shorts-2-3-5.md`.

## Set up

Two things are not in git because of their size. Take them from `source-remotion-v5.tar.gz`:

- `public/vo.mp3`, the main VO (take B, 1.5 s lead-in). Only `make_audio.sh` needs it.
- `public/maps/lit/` (222 PNGs, the lit conduction system). `tools-genlit.js` regenerates them.

```sh
npm ci
./make_audio.sh                                   # public/short9-*.mp3 (already committed)
npx remotion bundle src/index.ts --out-dir=build
node render.mjs Short2Narrow out/Short2Narrow.mp4  # also Short3Reason, Short5Tells
node stills.mjs Short5Tells check 30 90 600       # stills at frames, half size
```

`remotion.config.ts`, `render.mjs` and `stills.mjs` use the headless Chromium preinstalled in Claude cloud sessions.

## How a short is timed

Logo intro (2.2 s) → the strip prints under the hook title (1.5 s) → one stretch of the VO, `a`..`b` in VO seconds (`SHORTS9` in `src/ShortsV9.tsx`) → outro (8.6 s: recap, the strip rewinds into the logo, "Full video on YouTube"). Everything inside the stretch is timed in VO seconds like the main video, so it stays word-synced. v9 timecode = VO time + 12.94 s.
