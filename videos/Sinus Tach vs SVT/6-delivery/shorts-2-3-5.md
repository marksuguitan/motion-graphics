# Shorts 2, 3 and 5: SVT vs Sinus Tachycardia

Made Nov 22, 2026 from the v9 narration, as three more 9:16 shorts next to Short 1 (Answering or looping?) and Short 4 (How adenosine stops SVT). Each short is numbered by the scene it comes from. The narration is the locked VO of the full video, unchanged; only on-screen text is new.

Shorts titles show about 40 characters in the feed, so the recommended titles are short. Each description links to the full video: paste its URL where it says [full video link], and set the full video as the Short's "Related video" on YouTube.

---

## Short 2: Why is the QRS narrow?

File: short-2-why-the-qrs-is-narrow.mp4 (0:41) · Cover: short-2-why-the-qrs-is-narrow-cover.png
Source: v9 0:21.7 to 0:49.6 (VO 8.6 to 36.85 s), scene 2, ending before "Both rhythms in this video start up here."

**Title (recommended):** Why Is the QRS Narrow?

Alternatives:
- The Fast Lane Behind a Narrow QRS
- Narrow QRS? The Problem Starts Up High

**Description:**

Every normal beat takes the same route: the SA node, across both atria, a hold of about a tenth of a second at the AV node, then down the fast His-Purkinje system into the ventricles. That fast lane is why the QRS is narrow, and why a narrow-complex tachycardia starts at or above the AV node.

Full video: [full video link]

For education only, not medical advice. Source: StatPearls.

#ECG #cardiology #shorts

---

## Short 3: Fast heart? Find the reason.

File: short-3-fast-heart-find-the-reason.mp4 (0:46) · Cover: short-3-fast-heart-find-the-reason-cover.png
Source: v9 0:52.5 to 1:26.0 (VO 39.3 to 73.35 s), all of scene 3.

**Title (recommended):** Fast Heart? Find the Reason

Alternatives:
- Sinus Tachycardia: Harmless or Serious?
- Sinus Tach Is the Heart Answering

**Description:**

In sinus tachycardia the route doesn't change: the SA node fires faster than 100 a minute because the body is asking for more output. Sometimes the reason is harmless, like exercise, stress, pain or anxiety. Sometimes it's serious, like low oxygen, blood loss, dehydration or sepsis. On the ECG it looks like a normal beat, only faster: an upright P wave in I, II and aVL before every QRS.

Full video: [full video link]

For education only, not medical advice. Source: StatPearls.

#ECG #tachycardia #shorts

---

## Short 5: Sinus tach or SVT? 3 tells

File: short-5-sinus-tach-or-svt-3-tells.mp4 (0:44) · Cover: short-5-sinus-tach-or-svt-3-tells-cover.png
Source: v9 1:48.4 to 2:19.6 (VO 95.15 to 126.95 s), the end of scene 4 and all of scene 5.

**Title (recommended):** Sinus Tach or SVT? 3 Tells

Alternatives:
- 3 Ways to Tell Sinus Tach From SVT
- SVT Is a Switch, Not a Dial

**Description:**

Three tells for a fast, narrow, regular rhythm. Trigger: sinus tach has a reason you can find, SVT often has none. Start and stop: sinus tach follows its reason, SVT switches on and off. P waves: sinus tach has an upright P before every QRS, and in AVNRT, the most common SVT, the P wave is often hidden inside the QRS.

Full video: [full video link]

For education only, not medical advice. Source: StatPearls.

#SVT #ECG #shorts

---

Tags (all three): SVT, sinus tachycardia, supraventricular tachycardia, narrow QRS, narrow complex tachycardia, AVNRT, re-entry, conduction system, AV node, ECG interpretation, ECG, EKG, cardiology, medical education, medical student

## Build notes

- Remotion, in `4-animation/shorts/` (the v5 source plus `src/ShortsV9.tsx`). Compositions `Short2Narrow`, `Short3Reason`, `Short5Tells`, 1080×1920, 30 fps.
- Same recipe as Shorts 1 and 4: the Medzcool logo lands on a strip, the strip prints under the hook title for 1.5 s, the VO stretch plays with word-synced captions, then a recap card, the strip rewinds into the logo and the "Full video on YouTube" card. The loop restarts cleanly.
- New on-screen text: the hook titles above; "1 · Trigger", "2 · Start and stop", "3 · P waves" and "in AVNRT, the most common SVT" in Short 5; the recap cards.
- Audio: the main VO (take B) cut to each stretch, about -23.7 LUFS like the full video and Shorts 1 and 4.
