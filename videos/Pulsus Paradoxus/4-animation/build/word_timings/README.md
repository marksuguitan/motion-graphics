# Word timings — Pulsus Paradoxus

Measured 2026-10-23 against the VO in `audio/` (2E and 3E are Mark's own files).

| File | What it is |
| --- | --- |
| `word_timings.csv` / `.json` | Every word of every beat: start and end in seconds from the start of its beat file, and its start in animatic v4 |
| `sync_points.csv` / `.json` | Every `on "word"` sync point in the motion notes, with the measured time. Rows flagged in `note` need a look at Stage 6 |
| `ref_transcripts.json` | ElevenLabs Scribe transcripts of the reference takes (input) |
| `align_words.py` | Carries word times from a reference take onto our file (MFCC + DTW) |
| `sync_points.py` | Reads the motion notes (production doc as markdown) and looks up each sync word |
| `qc.py` | Pause check: every silence of 150 ms or more in our file should fall on a word boundary |
| `all_beats.mp3`, `offsets.json` | All 22 beats joined with 1.5 s gaps, and where each beat starts (for a single transcription pass if uploads ever work) |

Reference audio: `audio/takes/word_timing_refs/REF_<beat>.mp3`. For 1A–5F these are the other ElevenLabs take of each beat; 2E and 3E are one-take references of the new wording.

**How it was measured:** the network blocks uploads to ElevenLabs, but ElevenLabs will transcribe audio already in the flow. Each reference take was transcribed there (Scribe, free), downloaded through the browser, and aligned to our file by sound.

**Accuracy:** on reference takes stretched by known amounts (tempo ±12 %, an inserted 0.2 s pause), 99 % of word starts landed within 1 frame (33 ms); median error 7 ms. On the real files, every measured pause falls on a word boundary except two word ends before a breath (3E "moves,", 5A "normally,"). Keyframes use word starts.

**Re-run** after any VO change: `python3 align_words.py <audio dir> <refs dir> ref_transcripts.json word_timings_raw.json`, then `sync_points.py`.
