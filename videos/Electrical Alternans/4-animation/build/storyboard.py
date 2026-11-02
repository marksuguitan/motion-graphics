import os, re, html, sys
KF = sys.argv[1]; OUT = sys.argv[2]
SCENES = [
 ("1", "Cold open", [
  ("1A", "strip", "Look at this rhythm strip. Tall beat. Short beat. Tall. Short. The rhythm is regular, the rate is fast, and every other QRS changes height."),
  ("1B", "title", "This is electrical alternans. And in the right patient, it means the heart is swinging.")]),
 ("2", "What it is", [
  ("2A", "definition", "Electrical alternans is a beat-to-beat change in the QRS complex: its amplitude, its axis, or its shape, alternating every other beat."),
  ("2B", "total", "Sometimes the P wave and the T wave alternate too. When all three do, it's called total electrical alternans."),
  ("2C", "sign", "It's a sign, not a diagnosis. The job is to figure out why the complexes are alternating.")]),
 ("3", "What causes it", [
  ("3A", "two-buckets", "There are two kinds of reasons. Either the heart's electrical system is unstable, or the heart itself is moving."),
  ("3B", "electrical", "Electrical instability shows up in things like supraventricular tachycardia, ischemia, and T-wave alternans in long QT. Important, but uncommon, and mostly for the cardiologist."),
  ("3C", "effusion", "The one you need to know is motion. A large pericardial effusion lets the heart swing inside a bag of fluid."),
  ("3D", "swing", "Each swing takes two beats. So on one beat the heart points toward the electrode; on the next, away. Tall, short, tall, short."),
  ("3E", "drain", "Drain the fluid, and the swinging stops. So does the alternans.")]),
 ("4", "Recognizing it on the ECG", [
  ("4A", "every-other", "To find it, use the rhythm strip. Mark every other beat. If the odd beats match each other, and the even beats match each other, but the two sets don't match, that's alternans."),
  ("4B", "leads", "Look in every lead. On these tracings it's easiest to see in the chest leads and the long rhythm strip, where the complexes are tallest."),
  ("4C", "companions", "Then look for its two companions: sinus tachycardia and low voltage. Together, they point at a large effusion squeezing the heart."),
  ("4D", "numbers", "But know the numbers. In patients with tamponade, alternans is there only about one time in four: sensitivity, 23 percent. When it is there, it's almost always real: specificity, 98 percent."),
  ("4E", "rule", "So when you see it, believe it. When you don't see it, you've ruled out nothing."),
  ("4F", "bigeminy", "One trap. Bigeminy also gives you a tall-short pattern, but the beats come in uneven pairs. In alternans, the rhythm stays regular.")]),
 ("5", "Recognizing it at the bedside", [
  ("5A", "bedside", "Now go to the bedside. The ECG only told you the heart is swinging. The vitals tell you whether it's being squeezed."),
  ("5B", "beck", "The classic teaching is Beck's triad: low blood pressure, distended neck veins, and muffled heart sounds."),
  ("5C", "common", "But the full triad is uncommon. What's common is shortness of breath, in almost nine patients out of ten; a fast heart rate, in about eight; and raised neck veins, in about three out of four."),
  ("5D", "pulsus", "And one thing you can measure with a cuff: pulsus paradoxus. A drop in systolic pressure of more than 10 millimeters of mercury when the patient breathes in."),
  ("5E", "odds", "It's there in about eight out of ten patients with tamponade. More than 10 makes tamponade about three times more likely. Ten or less makes it very unlikely."),
  ("5F", "link", "How to measure it is its own video. We'll link it in the description below.")]),
 ("6", "Recap and outro", [
  ("6A", "recap-strip", "So: tall, short, tall, short, on a fast, regular rhythm. That's electrical alternans."),
  ("6B", "checklist", "Think swinging heart. Check the neck veins, check the pulsus, and get the echo, which finds almost every effusion that matters."),
  ("6C", "end", "The ECG tells you the heart is swinging. The bedside tells you whether it's being squeezed.")]),
]
head = '''<title>Electrical Alternans Key Frames</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: a storyboard; one row per beat, frame left and its locked narration right, stacking on phones */
:root{--bg:#F3F4F3;--fg:#17191A;--muted:#5C6260;--line:#DCDFDE;--accent:#C81E3A;--font:"Helvetica Neue",Helvetica,Arial,sans-serif;--mono:ui-monospace,Menlo,monospace}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#0F1011;--fg:#ECEEEC;--muted:#9AA09C;--line:#2A2D2F;--accent:#FF4057;color-scheme:dark}}
:root[data-theme="dark"]{--bg:#0F1011;--fg:#ECEEEC;--muted:#9AA09C;--line:#2A2D2F;--accent:#FF4057;color-scheme:dark}
body{background:var(--bg);color:var(--fg);font-family:var(--font);font-size:15px;line-height:1.5;padding-block:32px 56px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px))}
main{max-width:1180px;margin:0 auto;display:grid;gap:22px}
h1{font-weight:500;font-size:clamp(28px,4vw,40px);letter-spacing:-.01em;margin:0;text-wrap:balance}
.lead{margin:0;color:var(--muted);max-width:68ch}
.scene{font-weight:500;font-size:13px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:24px 0 0;padding-top:16px;border-top:1px solid var(--line)}
.kf{margin:0;display:grid;grid-template-columns:minmax(0,3fr) minmax(0,2fr);gap:20px;align-items:start}
@media (max-width:760px){.kf{grid-template-columns:1fr}}
.art{border:1px solid var(--line);border-radius:4px;overflow:hidden;line-height:0}
.art svg{width:100%;height:auto;display:block;max-width:100%}
figcaption{min-width:0;display:grid;gap:6px;align-content:start}
.id{font-weight:700;font-size:22px;color:var(--accent)}
figcaption code{font-family:var(--mono);font-size:12px;color:var(--muted);word-break:break-all}
figcaption p{margin:0;max-width:52ch}
footer{color:var(--muted);font-size:13px;border-top:1px solid var(--line);padding-top:16px}
</style>
<main>
<h1>Electrical Alternans: rough key frames</h1>
<p class="lead">Style C (spotlight), reused from Pulsus Paradoxus. One frame per beat, each drawn at the end state of its motion notes. These are rough: layout, hierarchy and color use are what to judge, not polish. Narration beside each frame is locked. ECG traces are drawn from a beat model patterned on your two reference ECGs, not traced from them yet.</p>
<h2 class="scene">Style</h2>
<p class="lead">Style C (spotlight) from Pulsus Paradoxus, chosen Oct 23, 2026: near-black ground with a faint 80&nbsp;px grid, one red accent for what the viewer should look at, effusion in blue, Helvetica. No new style frames.</p>
'''
out = [head]
n = 0
for num, name, beats in SCENES:
    out.append(f'<h2 class="scene">Scene {num} · {name}</h2>')
    for bid, slug, narr in beats:
        f = f"{bid}_{slug}.svg"
        s = open(os.path.join(KF, f)).read()
        s = s.replace("<svg ", f'<svg role="img" aria-label="Key frame {bid}" ', 1)
        out.append(f'<figure class="kf">\n  <div class="art">{s}</div>\n  <figcaption><span class="id">{bid}</span><code>{f}</code><p>{html.escape(narr, quote=False)}</p></figcaption>\n</figure>')
        n += 1
out.append(f'<footer>{n} SVGs at 1920×1080 in <code>~/Desktop/Electrical Alternans/assets/keyframes/</code>, generated by <code>build/keyframes_gen.py</code>.</footer>\n</main>\n')
open(OUT, "w").write("\n".join(out))
print(n, os.path.getsize(OUT))
