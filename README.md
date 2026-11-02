# Medzcool motion graphics

Every file for every Medzcool explainer video, one folder per video. The rules for how videos are made and how they look are in the Claude project (*Motion Graphics Production Guide* and *Motion Style Guide*); each video's production doc is the index to its folder.

```
library/
  scripts/
    word-timings/    align_words.py, sync_points.py, qc.py
    adobe/           Illustrator and After Effects build scripts
  remotion/          Remotion template, for the build path that needs no Mac
videos/
  _template/         copy this to start a video
  <Short title>/
    1-brief/         reference/ (papers, images, notes from Mark)
    2-script/        script exports for medical review, reviewer feedback
    3-board/
      style/         style frames
      art/           one SVG per beat: 1A_name.svg ...
      audio/         beat VO 1A.mp3 ..., full.mp3, vo_log.json, cues/, takes/
      timings/       word_timings.csv, sync_points.csv
    4-animation/
      build/         build scripts and plans (tracked); .aep and .ai (Mac only)
      remotion/      Remotion project, on the Remotion build path (tracked; node_modules and renders aren't)
    5-finish/        captions .srt; review renders (Mac only)
    6-delivery/      thumbnail, titles and descriptions; final .mp4 (Mac only)
```

You only need the stage number to find something: stage 3 lives in `3-board/`, and so on.

## What is tracked and what isn't

Git holds everything small and text-like: Markdown, SVG, VO (mp3 and wav), CSV and JSON, scripts, style frames, reference images. Stages 1–3 can therefore run entirely in the cloud, without the Mac.

The big binaries stay out of git (see `.gitignore`): After Effects projects and auto-saves, `.ai` files (regenerated from the SVGs), and every `.mp4`. On the Mac they sit inside the clone, in the same folders, so the layout is the same everywhere.

A video on the Remotion build path has no `.aep` or `.ai` at all; it is animated and rendered in the cloud, and its renders are kept in the Claude project's files instead of on the Mac (see the production guide, *Two build paths*).

## Working on the Mac

Clone once, then pull before each After Effects session and push after it:

```
git clone https://github.com/marksuguitan/motion-graphics.git
```

## Starting a video

Copy `videos/_template/` to `videos/<Short title>/` (a few words, e.g. `Korotkoff Sounds`).
