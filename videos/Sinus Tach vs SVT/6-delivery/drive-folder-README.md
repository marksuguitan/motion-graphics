# SVT vs Sinus Tach

A Medzcool motion-graphics explainer for medical students: **SVT vs Sinus Tachycardia: Is the Heart Answering or Looping?**

A fast, narrow, regular rhythm comes down to one question: is the heart answering a call, or stuck in a loop? Sinus tachycardia is the normal route running faster for a reason you can find. Most SVT is re-entry, a signal circling through or around the AV node, which is also why vagal maneuvers and adenosine can stop it. Sources: StatPearls (Supraventricular Tachycardia, AVNRT, AVRT).

| | |
| --- | --- |
| Final cut | **v9**, 3:28, 1920x1080, 30 fps (`svt-vs-sinus-tach-final-v9.mp4`) |
| What v9 adds | Two Kardiograph by Medzcool plugs cut into v8: a 9.3 s opener with no voice-over at 0:12, and a 21.5 s voiced end plug at 2:59 |
| Build | Remotion. Voice-over by markusguapo (ElevenLabs v4) |
| Shorts | Short 1, Answering or Looping, and Short 4, How Adenosine Stops SVT (9:16) |
| Status (Nov 14, 2026) | v9 done, not on YouTube yet. Before uploading, kardiograph.medzcool.com must serve the new Kardiograph app |

## Chapters (v9)

0:00 Answering or looping? · 0:21 The route every beat takes · 0:52 Sinus tachycardia · 1:26 SVT and re-entry · 2:00 Side by side · 2:20 Breaking the loop · 2:48 One question · 2:59 Kardiograph by Medzcool. The silent Subscribe card runs from 3:20.6 to the end, with room for YouTube end-screen elements.

## How it got here

1. Script v3, voiced as one take, then **storyboard v1** (25 key frames) and the Remotion **draft v5** (2:50).
2. **v8** (2:58), the final draft: new opening sound and logo, and the Subscribe card at the end. Packaged for YouTube with titles, description, chapters, thumbnails and two shorts.
3. **v9** (3:28, Nov 14, 2026): the Kardiograph plugs, built in Remotion and spliced into v8 without visible cuts. Every chapter after 0:12 moves 9.3 s later.

## Folder structure

```
SVT vs Sinus Tach/
├── README.md                                   this file
├── svt-vs-sinus-tach-youtube-package/          everything that goes to YouTube
│   ├── full-video/
│   │   ├── svt-vs-sinus-tach-final-v9.mp4      v9, the final cut, with the Kardiograph plugs (3:28)
│   │   ├── title-and-description-v9.md         v9 title, description, chapters and tags
│   │   ├── svt-vs-sinus-tach-final-draft.mp4   v8, without the plugs (2:58)
│   │   ├── title-and-description.md            v8 title, description, chapters and tags
│   │   ├── thumbnail-A-ecg-strips-recommended.png
│   │   └── thumbnail-B-conduction-heart-alternate.png
│   └── shorts/
│       ├── short-1-answering-or-looping.mp4
│       ├── short-1-answering-or-looping-cover.png
│       ├── short-4-how-adenosine-stops-svt.mp4
│       ├── short-4-how-adenosine-stops-svt-cover.png
│       └── shorts-titles-and-descriptions.md
├── svt-vs-sinus-tach-youtube-package.zip       the v8 package as one zip (Nov 2)
├── SVT Kardiograph Plugs Storyboard.zip        storyboard of the two plugs, frames from v9
├── SVT vs Sinus Tach Storyboard.zip            storyboard v1, the whole video (25 frames)
├── kardiograph-plug-graphics-svg/  (+ .zip)    the plugs' graphics as SVG, with a README
├── svt-circuit-graphics-svg/  (+ .zip)         AVNRT and AVRT circuit graphics as SVG, with a README
├── 3E_heart-backdrop_for-illustrator.svg       the heart backdrop named for scene 3E, prepared for Illustrator
├── script-v3.md                                script v3, the narration of the drafts
├── source-remotion-v5.tar.gz                   Remotion source of draft v5
└── svt-vs-sinus-tach-draft-v5.mp4              draft v5 (2:50)
```

## The files

**YouTube package.** `full-video/` holds the cut to upload and its copy. Upload **v9** with `title-and-description-v9.md`; v8 and its copy stay for reference. Thumbnail A is recommended, B is the alternate. `shorts/` holds the two 9:16 shorts with their covers and copy.

**Storyboards.** Each zip holds an `index.html` page to open in a browser, its frames in `f/`, and audio.
- `SVT Kardiograph Plugs Storyboard.zip`: 15 frames pulled from v9 at the plugs' key beats, each with its v9 timecode, narration or sounds, and a build note, plus the opener's sound and the end plug's audio.
- `SVT vs Sinus Tach Storyboard.zip`: storyboard v1 of the whole video, 25 frames with timecodes, narration and build notes, and the timed voice-over.

**Graphics.**
- `kardiograph-plug-graphics-svg/`: the Kardiograph mark and lockups, the link and Try it free pills, six true-scale lead II strips from Kardiograph's engine (sinus, SVT, atrial fibrillation, atrial flutter, 1st-degree AV block, Mobitz I), the calipers strip, the practice card, answer chips and score, the cursor, the end plug's tiles and rhythm grid, and icons. Text is outlined. Its README lists every file.
- `svt-circuit-graphics-svg/`: the AVNRT and AVRT circuits drawn on Mark's conduction-system heart, full heart, zoomed and overlay-only. Its README lists every file.
- `3E_heart-backdrop_for-illustrator.svg`: a heart backdrop prepared for Illustrator.

**Script and source.** `script-v3.md` is script v3, the narration of the drafts. `source-remotion-v5.tar.gz` and `svt-vs-sinus-tach-draft-v5.mp4` are the v5 draft and its source.

## Where the working files are

The production files are in the motion-graphics GitHub repo, under `videos/Sinus Tach vs SVT/`:
- `3-board/kardiograph-plug/`: plug key frames, the SVG and storyboard exports, and the engine strip export.
- `3-board/audio/`: the end plug's voice-over takes and log.
- `4-animation/remotion/`: the plugs' Remotion source (`src/plugs/`), their sounds, and `scripts/splice.sh`, which rebuilds v9 from v8 and the two plug renders.
- `6-delivery/youtube.md`: the v9 YouTube copy.
