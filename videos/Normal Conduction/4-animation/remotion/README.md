# Remotion template (the no-Mac build path)

Stage 4 for a video whose Build row says **Remotion** (production guide, *Two build paths* and *Stage 4: animation in Remotion*). The approved SVGs from `3-board/art/` are put on screen as they are and their `Group/Sublayer` layers are animated in code, on the measured sync points, with Comma Clinical easing. Everything, renders included, runs in the agent's cloud workspace.

## Start a video on this path

```
cp -r library/remotion "videos/<Short title>/4-animation/remotion"
cd "videos/<Short title>/4-animation/remotion"
rm -rf demo out node_modules            # the demo is only for the template
npm install
npm run prep                            # copies art + VO from ../../3-board, writes src/data/*.json
```

Then replace `src/scenes/Scene1.tsx` with the video's scenes (one component per scene) and list them in `src/Video.tsx`.

| Command | What it does |
| --- | --- |
| `npm run prep` | Copies `3-board/art/*.svg` and `3-board/audio/*.mp3` into `public/`, measures each beat file, writes beats, sync points and words into `src/data/`. Lists flagged sync points. Re-run after any art, VO or timing change. `-- <dir>` points it at another video folder; `--lead` / `--tail` set the silence before and after the VO (0.5 s / 1.0 s). |
| `npm run check` | A still at every beat start and every sync point + 0.7 s, review overlay on, tiled into `out/check/sheet*.jpg` with `index.txt`. `-- 3A 3B` for some beats only. |
| `npm run render:review -- N` | Whole video, beat ID + time into beat + timecode burned in, to `../../5-finish/renders/<Short title> review vN.mp4`. |
| `npm run render:final` | Final video (nothing burned in) and the 1280×720 thumbnail, to `../../6-delivery/`. |
| `npm run studio` | Remotion Studio, for previewing in a browser where one is available. Not needed. |
| `npm run typecheck` | TypeScript check. |

Renders are gitignored; copy them to the project files (`videos/<Short title>/renders/` or `delivery/`) and attach them in the chat.

## What's in `src/`

| File | |
| --- | --- |
| `style/comma.ts` | Comma Clinical easing: `ease`, `keys`, `overshoot`, `squash`, `anticipate`, `gravity`, `stagger`, `cut`, `swap`, `morph`, `typeOn` / `typeOff`, `fadeSmall`, plus Warm Clinical's `warmIn` / `warmMove`. The Remotion twin of `library/scripts/adobe/comma_easing.jsx`; the Motion Style Guide's *Remotion settings* table maps one to the other. If the guide changes, change both. |
| `style/theme.ts` | Warm Clinical colours, type styles, radii and shadow from the Motion Style Guide. |
| `lib/timing.ts` | `useTime()` (seconds on the full VO track), `sync(beat, word, nth)`, `wordEnd`, `beatStart`, `beatEnd`, `beatAt`, `toFrame`. `sync` throws if a word wasn't measured: never type a guessed time. |
| `lib/SvgArt.tsx` | Puts a beat SVG on screen inline and styles its layers by name (`visible`, `opacity`, `x`, `y`, `scale`, `sx`, `sy`, `rotate`, `origin`, `clip` wipes, `fill`, `stroke`), swaps path `d`s (morphs) and text. Finds Illustrator's `Group_x2F_Sublayer` ids too. Hides `Meta/BeatID`. |
| `lib/shapes.ts` | `roundRect` and `disc`: paths with matching commands, so a disc can morph into a card or a chip. |
| `lib/Fonts.tsx` | Manrope and Inter, vendored in `public/fonts/` (SIL OFL), so renders never fetch fonts. |
| `lib/ReviewOverlay.tsx` | The burn-in on review renders. |
| `scenes/Scene1.tsx` | The example scene: grow from a point, gravity hop and squash, text cut on its word, disc-to-card morph with a match cut to the SVG, overshoot chip. |

## Writing SVGs for this path

Same rules as the Motion Board (1920×1080, one per beat, `[ID]_[name].svg`), plus:

- Name every layer that moves with `<g id="Group/Sublayer">`. Anything not named can't be animated on its own.
- A layer that moves should be a `<g>` without its own `transform`; if it has one, `SvgArt` wraps it.
- Use `font-family="Manrope"` or `"Inter"` with numeric weights; no outlined text, so labels stay editable.
- No Illustrator: the agent draws and edits the SVG text directly, and previews it by rendering (`npm run check`, or a headless-browser screenshot).

## The demo

`demo/3-board/` is a two-beat stand-in video (silent VO, made-up word times) so the template renders as is: `npm run prep -- demo && npm run render:review -- 1` writes `out/Comma Clinical demo review v1.mp4`. Rendered in the cloud workspace on Nov 2, 2026 with Remotion 4.0.539 and the pre-installed headless Chromium (`remotion.config.ts` finds it); 7 s of 1080p took about 40 s.
