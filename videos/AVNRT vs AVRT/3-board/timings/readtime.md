# AVNRT vs AVRT: reading-time check (Gate 3)

Measured Nov 2, 2026 against the final VO timing (`vo-redo-handoff/vo/stitch.json`, total 4:59.64).

**Rule:** each on-screen text item needs at least max(2.5 s, 1 s + 1 s per 3 words). It is assumed to land 0.5 s after its beat starts and to leave when the next beat starts (beat VO plus its Hold).

**Result:** 188 text items checked. 181 pass. The 7 short items are all in 3G (on screen 2.2 s): the six diagram labels carry over from 3F, so they are already read; the new caption "The loop is now self-sustaining" needs 2.7 s.

**Proposed fix:** raise the Hold after 3G from 0.5 s to 1.0 s. That gives the caption 2.7 s and makes the video 0.5 s longer (5:00.14). No wording change.

| Beat | Text | Words | Lands | Leaves | On screen | Minimum | OK |
|---|---|---|---|---|---|---|---|
| 1A | Patient 1 | 2 | 0:00.5 | 0:11.1 | 10.6 s | 2.5 s | yes |
| 1A | Lead II · 180 /min | 5 | 0:00.5 | 0:11.1 | 10.6 s | 2.7 s | yes |
| 1A | Patient 2 | 2 | 0:00.5 | 0:11.1 | 10.6 s | 2.5 s | yes |
| 1A | Lead II · 180 /min | 5 | 0:00.5 | 0:11.1 | 10.6 s | 2.7 s | yes |
| 1B | Small loop | 2 | 0:11.6 | 0:16.8 | 5.2 s | 2.5 s | yes |
| 1B | In and around the AV node A structure about 5 mm long | 12 | 0:11.6 | 0:16.8 | 5.2 s | 5.0 s | yes |
| 1C | Big loop | 2 | 0:17.3 | 0:22.5 | 5.2 s | 2.5 s | yes |
| 1C | Through the atria, the ventricles, and back | 7 | 0:17.3 | 0:22.5 | 5.2 s | 3.3 s | yes |
| 1D | AVNRT vs AVRT | 3 | 0:23.0 | 0:25.5 | 2.5 s | 2.5 s | yes |
| 1D | Small loop, big loop | 4 | 0:23.0 | 0:25.5 | 2.5 s | 2.5 s | yes |
| 2A | Atria and ventricles are kept apart | 6 | 0:26.0 | 0:32.7 | 6.6 s | 3.0 s | yes |
| 2A | Fibrous rings | 2 | 0:26.0 | 0:32.7 | 6.6 s | 2.5 s | yes |
| 2A | INSULATION | 1 | 0:26.0 | 0:32.7 | 6.6 s | 2.5 s | yes |
| 2B | ONE GATE | 2 | 0:33.2 | 0:37.3 | 4.2 s | 2.5 s | yes |
| 2B | The only normal connection | 4 | 0:33.2 | 0:37.3 | 4.2 s | 2.5 s | yes |
| 2B | AV node → His bundle | 5 | 0:33.2 | 0:37.3 | 4.2 s | 2.7 s | yes |
| 2C | Atria | 1 | 0:37.8 | 0:43.0 | 5.1 s | 2.5 s | yes |
| 2C | Slow | 1 | 0:37.8 | 0:43.0 | 5.1 s | 2.5 s | yes |
| 2C | Fast | 1 | 0:37.8 | 0:43.0 | 5.1 s | 2.5 s | yes |
| 2C | WHAT A LOOP NEEDS | 4 | 0:37.8 | 0:43.0 | 5.1 s | 2.5 s | yes |
| 2C | Two pathways, joined at both ends | 6 | 0:37.8 | 0:43.0 | 5.1 s | 3.0 s | yes |
| 2D | Slow | 1 | 0:43.5 | 0:49.9 | 6.4 s | 2.5 s | yes |
| 2D | Fast | 1 | 0:43.5 | 0:49.9 | 6.4 s | 2.5 s | yes |
| 2D | Two pathways that behave differently | 5 | 0:43.5 | 0:49.9 | 6.4 s | 2.7 s | yes |
| 2D | Fast · conducts quickly | 4 | 0:43.5 | 0:49.9 | 6.4 s | 2.5 s | yes |
| 2D | Slow · conducts slowly | 4 | 0:43.5 | 0:49.9 | 6.4 s | 2.5 s | yes |
| 2D | They recover at different speeds | 5 | 0:43.5 | 0:49.9 | 6.4 s | 2.7 s | yes |
| 2E | Slow | 1 | 0:50.4 | 0:55.6 | 5.3 s | 2.5 s | yes |
| 2E | Fast | 1 | 0:50.4 | 0:55.6 | 5.3 s | 2.5 s | yes |
| 2E | THEN A TRIGGER | 3 | 0:50.4 | 0:55.6 | 5.3 s | 2.5 s | yes |
| 2E | A premature beat | 3 | 0:50.4 | 0:55.6 | 5.3 s | 2.5 s | yes |
| 2E | Early beat | 2 | 0:50.4 | 0:55.6 | 5.3 s | 2.5 s | yes |
| 3A | AV node | 2 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | His bundle | 2 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | Ventricles | 1 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | Slow | 1 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | Fast | 1 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | Typical AVNRT | 2 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3A | The small loop Slow-fast | 4 | 0:56.1 | 1:01.1 | 5.0 s | 2.5 s | yes |
| 3B | AV node | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | His bundle | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | Ventricles | 1 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | Slow | 1 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | conducts slowly | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | recovers quickly | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | Fast | 1 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | conducts quickly | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3B | recovers slowly | 2 | 1:01.6 | 1:09.5 | 7.9 s | 2.5 s | yes |
| 3C | AV node | 2 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | His bundle | 2 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | Ventricles | 1 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | Slow | 1 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | Fast | 1 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | Sinus beat | 2 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3C | Down the fast pathway | 4 | 1:10.0 | 1:12.6 | 2.6 s | 2.5 s | yes |
| 3D | AV node | 2 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | His bundle | 2 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | Ventricles | 1 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | Slow | 1 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | Fast | 1 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | recovering | 1 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | Premature beat | 2 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3D | Down the slow pathway | 4 | 1:13.1 | 1:20.1 | 7.0 s | 2.5 s | yes |
| 3E | AV node | 2 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | His bundle | 2 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | Ventricles | 1 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | Slow | 1 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | Fast | 1 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | Recovered | 1 | 1:20.6 | 1:24.3 | 3.7 s | 2.5 s | yes |
| 3E | The fast pathway is ready again | 6 | 1:20.6 | 1:24.3 | 3.7 s | 3.0 s | yes |
| 3F | AV node | 2 | 1:24.8 | 1:29.5 | 4.7 s | 2.5 s | yes |
| 3F | His bundle | 2 | 1:24.8 | 1:29.5 | 4.7 s | 2.5 s | yes |
| 3F | Ventricles | 1 | 1:24.8 | 1:29.5 | 4.7 s | 2.5 s | yes |
| 3F | Slow | 1 | 1:24.8 | 1:29.5 | 4.7 s | 2.5 s | yes |
| 3F | Fast | 1 | 1:24.8 | 1:29.5 | 4.7 s | 2.5 s | yes |
| 3F | Back up the fast pathway | 5 | 1:24.8 | 1:29.5 | 4.7 s | 2.7 s | yes |
| 3G | AV node | 2 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | His bundle | 2 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | Ventricles | 1 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | Slow | 1 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | Fast | 1 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | Re-entry loop | 2 | 1:30.0 | 1:32.2 | 2.2 s | 2.5 s | **short** |
| 3G | The loop is now self-sustaining | 5 | 1:30.0 | 1:32.2 | 2.2 s | 2.7 s | **short** |
| 3H | AVNRT · THE SMALL LOOP Atria and ventricles fire together | 10 | 1:32.7 | 1:41.4 | 8.7 s | 4.3 s | yes |
| 3H | AV node | 2 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | His bundle | 2 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | Ventricles | 1 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | Up to the atria | 4 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | Down to the ventricles | 4 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | Lead II | 2 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3H | P wave hides here | 4 | 1:32.7 | 1:41.4 | 8.7 s | 2.5 s | yes |
| 3I | AVNRT ON THE ECG Where the P wave hides | 9 | 1:41.9 | 1:49.3 | 7.4 s | 4.0 s | yes |
| 3I | Lead II (also III, aVF) | 5 | 1:41.9 | 1:49.3 | 7.4 s | 2.7 s | yes |
| 3I | Pseudo S | 2 | 1:41.9 | 1:49.3 | 7.4 s | 2.5 s | yes |
| 3I | V1 | 1 | 1:41.9 | 1:49.3 | 7.4 s | 2.5 s | yes |
| 3I | Pseudo R′ | 2 | 1:41.9 | 1:49.3 | 7.4 s | 2.5 s | yes |
| 3J | AVNRT The most common paroxysmal SVT in adults | 8 | 1:49.8 | 2:00.8 | 11.0 s | 3.7 s | yes |
| 3J | 50–60% | 1 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 3J | of SVT cases | 3 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 3J | Young | 1 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 3J | adults, most often | 3 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 3J | ~2 in 3 | 3 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 3J | patients are women | 3 | 1:49.8 | 2:00.8 | 11.0 s | 2.5 s | yes |
| 4A | AVRT | 1 | 2:01.3 | 2:08.5 | 7.2 s | 2.5 s | yes |
| 4A | The big loop A strand of muscle that crosses the ring | 11 | 2:01.3 | 2:08.5 | 7.2 s | 4.7 s | yes |
| 4A | Accessory pathway | 2 | 2:01.3 | 2:08.5 | 7.2 s | 2.5 s | yes |
| 4A | Fibrous ring | 2 | 2:01.3 | 2:08.5 | 7.2 s | 2.5 s | yes |
| 4B | Orthodromic AVRT | 2 | 2:09.0 | 2:17.7 | 8.7 s | 2.5 s | yes |
| 4B | Down the AV node | 4 | 2:09.0 | 2:17.7 | 8.7 s | 2.5 s | yes |
| 4B | AV node → His-Purkinje | 4 | 2:09.0 | 2:17.7 | 8.7 s | 2.5 s | yes |
| 4B | Usually narrow QRS | 3 | 2:09.0 | 2:17.7 | 8.7 s | 2.5 s | yes |
| 4C | Orthodromic AVRT | 2 | 2:18.2 | 2:25.7 | 7.4 s | 2.5 s | yes |
| 4C | Back up the pathway | 4 | 2:18.2 | 2:25.7 | 7.4 s | 2.5 s | yes |
| 4C | Up the accessory pathway → atria | 6 | 2:18.2 | 2:25.7 | 7.4 s | 3.0 s | yes |
| 4C | The large majority of AVRT | 5 | 2:18.2 | 2:25.7 | 7.4 s | 2.7 s | yes |
| 4D | AVRT ON THE ECG The P wave trails the QRS | 10 | 2:26.2 | 2:42.2 | 16.0 s | 4.3 s | yes |
| 4D | Lead II · 180 /min | 5 | 2:26.2 | 2:42.2 | 16.0 s | 2.7 s | yes |
| 4D | RP: QRS onset → P onset | 6 | 2:26.2 | 2:42.2 | 16.0 s | 3.0 s | yes |
| 4D | In the ST segment, not inside the QRS | 8 | 2:26.2 | 2:42.2 | 16.0 s | 3.7 s | yes |
| 4D | Longer RP than typical AVNRT · often > 70 ms | 10 | 2:26.2 | 2:42.2 | 16.0 s | 4.3 s | yes |
| 4E | Antidromic AVRT | 2 | 2:42.7 | 2:57.8 | 15.1 s | 2.5 s | yes |
| 4E | Down the pathway, up the node Ventricles activated muscle to muscle | 11 | 2:42.7 | 2:57.8 | 15.1 s | 4.7 s | yes |
| 4E | Lead II · wide QRS | 5 | 2:42.7 | 2:57.8 | 15.1 s | 2.7 s | yes |
| 4E | Less common | 2 | 2:42.7 | 2:57.8 | 15.1 s | 2.5 s | yes |
| 4F | AVNRT | 1 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | Most common paroxysmal | 3 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | SVT in adults | 3 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | AVRT | 1 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | Most common SVT | 3 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | in children | 2 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 4F | especially younger children | 3 | 2:58.3 | 3:03.8 | 5.5 s | 2.5 s | yes |
| 5A | BETWEEN EPISODES The resting ECG can carry a clue | 9 | 3:04.3 | 3:22.8 | 18.6 s | 4.0 s | yes |
| 5A | Lead II · sinus rhythm · Wolff-Parkinson-White pattern | 8 | 3:04.3 | 3:22.8 | 18.6 s | 3.7 s | yes |
| 5A | Delta wave | 2 | 3:04.3 | 3:22.8 | 18.6 s | 2.5 s | yes |
| 5A | Short PR | 2 | 3:04.3 | 3:22.8 | 18.6 s | 2.5 s | yes |
| 5A | Wide QRS | 2 | 3:04.3 | 3:22.8 | 18.6 s | 2.5 s | yes |
| 5B | Manifest: conducts forward too | 4 | 3:23.3 | 3:34.8 | 11.5 s | 2.5 s | yes |
| 5B | Concealed: conducts backward only · no pre-excitation | 7 | 3:23.3 | 3:34.8 | 11.5 s | 3.3 s | yes |
| 5B | A normal resting ECG does not rule out AVRT | 9 | 3:23.3 | 3:34.8 | 11.5 s | 4.0 s | yes |
| 6A | AV node in both circuits | 5 | 3:35.3 | 3:43.2 | 7.9 s | 2.7 s | yes |
| 6A | AVNRT | 1 | 3:35.3 | 3:43.2 | 7.9 s | 2.5 s | yes |
| 6A | AVRT | 1 | 3:35.3 | 3:43.2 | 7.9 s | 2.5 s | yes |
| 6B | Stable · regular · narrow | 5 | 3:43.7 | 3:59.3 | 15.6 s | 2.7 s | yes |
| 6B | 1 Vagal maneuver (Valsalva) | 4 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6B | 2 Adenosine, unless contraindicated | 4 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6B | AVNRT | 1 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6B | AVRT | 1 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6B | AV node blocked | 3 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6B | AV node blocked | 3 | 3:43.7 | 3:59.3 | 15.6 s | 2.5 s | yes |
| 6C | REGULAR, NARROW-COMPLEX TACHYCARDIA First steps, same for both loops | 9 | 3:59.8 | 4:04.7 | 4.9 s | 4.0 s | yes |
| 6C | STABLE | 1 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | UNSTABLE | 1 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | 1 Vagal maneuver | 3 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | 2 Adenosine, unless contraindicated | 4 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | Synchronized cardioversion | 2 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | when the tachycardia causes the instability | 6 | 3:59.8 | 4:04.7 | 4.9 s | 3.0 s | yes |
| 6C | Lead II | 2 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6C | Loop broken | 2 | 3:59.8 | 4:04.7 | 4.9 s | 2.5 s | yes |
| 6D | Caution · wide complex | 4 | 4:05.2 | 4:14.3 | 9.1 s | 2.5 s | yes |
| 6D | Antidromic AVRT | 2 | 4:05.2 | 4:14.3 | 9.1 s | 2.5 s | yes |
| 6D | Avoid AV nodal blockers | 4 | 4:05.2 | 4:14.3 | 9.1 s | 2.5 s | yes |
| 6D | Procainamide is an alternative | 4 | 4:05.2 | 4:14.3 | 9.1 s | 2.5 s | yes |
| 6D | Lead II · regular, wide QRS · 180 /min | 9 | 4:05.2 | 4:14.3 | 9.1 s | 4.0 s | yes |
| 6E | Danger | 1 | 4:14.8 | 4:33.9 | 19.1 s | 2.5 s | yes |
| 6E | A SEPARATE ARRHYTHMIA | 3 | 4:14.8 | 4:33.9 | 19.1 s | 2.5 s | yes |
| 6E | Pre-excited atrial fibrillation | 3 | 4:14.8 | 4:33.9 | 19.1 s | 2.5 s | yes |
| 6E | Very fast · irregular · wide, in a patient with an accessory pathway | 13 | 4:14.8 | 4:33.9 | 19.1 s | 5.3 s | yes |
| 6E | Avoid AV nodal blockers, including adenosine | 6 | 4:14.8 | 4:33.9 | 19.1 s | 3.0 s | yes |
| 6E | Stable: procainamide | 2 | 4:14.8 | 4:33.9 | 19.1 s | 2.5 s | yes |
| 6E | Unstable: electrical cardioversion | 3 | 4:14.8 | 4:33.9 | 19.1 s | 2.5 s | yes |
| 6E | Lead II · irregularly irregular, wide | 6 | 4:14.8 | 4:33.9 | 19.1 s | 3.0 s | yes |
| 6F | AV node | 2 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | His bundle | 2 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | Ventricles | 1 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | Slow | 1 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | Fast | 1 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | AVNRT | 1 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | Ablate the slow pathway | 4 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6F | Success above 95% | 3 | 4:34.4 | 4:43.4 | 9.0 s | 2.5 s | yes |
| 6G | AVRT | 1 | 4:43.9 | 4:47.4 | 3.5 s | 2.5 s | yes |
| 6G | Ablate the accessory pathway | 4 | 4:43.9 | 4:47.4 | 3.5 s | 2.5 s | yes |
| 7A | Small loop | 2 | 4:47.9 | 4:59.6 | 11.8 s | 2.5 s | yes |
| 7A | Typical AVNRT: P usually hidden in the QRS | 8 | 4:47.9 | 4:59.6 | 11.8 s | 3.7 s | yes |
| 7A | Lead II · 180 /min | 5 | 4:47.9 | 4:59.6 | 11.8 s | 2.7 s | yes |
| 7A | Big loop | 2 | 4:47.9 | 4:59.6 | 11.8 s | 2.5 s | yes |
| 7A | Orthodromic AVRT: P usually trails the QRS | 7 | 4:47.9 | 4:59.6 | 11.8 s | 3.3 s | yes |
| 7A | Lead II · 180 /min | 5 | 4:47.9 | 4:59.6 | 11.8 s | 2.7 s | yes |
| 7A | A clue, not a rule | 5 | 4:47.9 | 4:59.6 | 11.8 s | 2.7 s | yes |
