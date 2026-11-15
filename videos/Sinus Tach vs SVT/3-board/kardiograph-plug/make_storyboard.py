"""Storyboard of the two Kardiograph plugs, pulled from the finished v9 render (same layout as storyboard v1).

    python3 make_storyboard.py <v9.mp4> <out dir>

Writes <out>/index.html, <out>/f/kNN.jpg (frames from v9 itself, so the stills match the final cut) and the plugs'
audio (opener-audio.mp3: sounds only; end-plug-audio.mp3: VO and sounds). Timecodes are v9 times.
v9 = v8 frames 0-370 + opener (278 frames) + v8 frames 371-5095 + end plug (645 frames) + v8 frames 5096-end.
"""
import html
import pathlib
import subprocess
import sys

V9, OUT = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
V1 = pathlib.Path(__file__).parent / '../../1-brief/reference/storyboard v1/index.html'
OPENER_AT, END_AT = 370, 5374  # v9 frames where each plug's frame 0 sits

# (v9 frame, scene, narration, build note)
OPENER = [
    (370, 'Title card (v8)', '(no narration; the pause after "or stuck in a loop?")',
     'The cut point. v8 holds its title card here, so the plug starts on this exact frame: the whole frame shrinks into the centre point on the accelerate curve (0.25 s).'),
    (436, 'Brought to you by', '(no narration) Sound: a soft pop as the mark lands, a lighter one as the wordmark finishes.',
     'The Kardiograph mark grows out of the point with a small overshoot, slides left, and the wordmark unfolds from its edge. "This video is brought to you by" cuts on. On screen about 2.4 s.'),
    (505, 'Read the tracing', '(no narration) Sound: a pop on the card, a soft pop on the chips.',
     'The mark tracks to the corner as the practice card grows from the centre. The strip is real SVT (183 bpm) from Kardiograph\'s engine, scrolling at 25 mm/s. Three answer chips land in a stagger, then the cursor grows from its tip and travels to SVT.'),
    (550, 'Score your read', '(no narration) Sound: a mouse click, then a two-note chime.',
     'Click: the SVT chip turns coral with a check and pings, a coral ring pushes out from the cursor, the heading cuts to "Score your read." and the 100% score grows on. The card holds about 1.8 s.'),
    (616, 'The link', '(no narration) Sound: a pop on the mark, a soft pop on the pills.',
     'The practice frame shrinks into the centre and the lockup grows back with kardiograph.medzcool.com and Try it free. On screen 1.6 s.'),
    (642, 'Back into the video', '(no narration)',
     'The lockup shrinks into the point and the title card grows back out of it, so v8 carries on from its next frame. Every chapter after this moves 9.3 s later than in v8.'),
]
END = [
    (5329, 'Last scene (v8)', '(v8)',
     'v8\'s last scene clears to blank paper (v8 frames 5091-5100). The end plug starts and ends on that same paper, so neither cut shows.'),
    (5491, 'Course and practice bench', 'Kardiograph is Medzcool\'s EKG course and practice bench.',
     'The mark grows on "Kardiograph" and the wordmark unfolds. The Course tile (7 modules, 21 lessons) lands on "course" and the Practice tile (5 decks, scored) on "practice".'),
    (5566, 'Drawn at true scale', 'Every tracing is drawn at true scale,',
     'On "Every" the lockup shrinks away and a sinus strip card grows; on "true" the heading and the paper speed cut on. Grid and trace are drawn at 25 mm/s and 10 mm/mV.'),
    (5638, 'Calipers', 'so you can measure it with calipers, like on the wards.',
     'On "calipers" the legs drop and open from one R wave to the next, then the readout grows on: 832 ms, 72 bpm.'),
    (5680, 'A new tracing every time', 'And every practice strip is procedurally generated,',
     'On "And" the heading cuts to "A new tracing every time." and the New tracing pill grows under the card.'),
    (5719, 'Montage', '(continues) ...procedurally generated,',
     'On "procedurally" the strip swaps every 0.3 s: atrial fibrillation, atrial flutter, 1st-degree AV block, Mobitz I, SVT, sinus. Each carries its name chip and a soft click, and the pill pings on every swap.'),
    (5860, 'Endless', 'so the variety of EKGs you\'ll see in Kardiograph\'s practice sessions is endless.',
     'On "variety" six rhythms grow into a grid in a stagger, each a 3 s strip with its name. The New tracing pill pings on "endless".'),
    (5959, 'Try it free', 'Try it free at kardiograph.medzcool.com.',
     'The lockup grows back on "Try", Try it free lands on "free" and the link on "Kardiograph". Holds 1 s after the last word, then shrinks into the centre and leaves blank paper.'),
    (6064, 'Subscribe card (v8)', '(no narration)',
     'v8\'s silent Subscribe card follows as before, now at 3:20.6 to 3:28.5, with room for YouTube end-screen elements.'),
]


def tc(frame):
    s = frame / 30
    return f'{int(s // 60)}:{s % 60:04.1f}'


def frames():
    allf = [f for f, *_ in OPENER + END]
    sel = '+'.join(f'eq(n\\,{f})' for f in allf)
    (OUT / 'f').mkdir(parents=True, exist_ok=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V9), '-vf', f"select='{sel}'", '-vsync', '0', '-q:v', '3',
                    str(OUT / 'f' / 'k%02d.jpg')], check=True)
    for a, b, name in [(OPENER_AT, OPENER_AT + 279, 'opener-audio.mp3'), (END_AT, END_AT + 645, 'end-plug-audio.mp3')]:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{a / 30:.3f}', '-to', f'{b / 30:.3f}', '-i', str(V9), '-vn',
                        '-c:a', 'libmp3lame', '-b:a', '160k', str(OUT / name)], check=True)


def figure(i, f, scene, vo, note):
    e = html.escape
    return f'''<figure class="frame">
<img src="f/k{i:02d}.jpg" alt="Storyboard frame k{i:02d} at {tc(f)}: {e(scene)}" loading="lazy" width="1920" height="1080">
<figcaption>
<div class="meta"><span class="tc">{tc(f)}</span><span class="scene">{e(scene)}</span></div>
<p class="vo">{e(vo)}</p>
<p class="note">{e(note)}</p>
</figcaption>
</figure>'''


def page():
    v1 = V1.read_text()
    head = v1[:v1.index('<main>')].replace('<title>SVT vs Sinus Tach Storyboard</title>', '<title>SVT Kardiograph Plugs Storyboard</title>')
    figs_o = '\n'.join(figure(i + 1, *row) for i, row in enumerate(OPENER))
    figs_e = '\n'.join(figure(len(OPENER) + i + 1, *row) for i, row in enumerate(END))
    return f'''{head}<main>
<header>
<div class="eyebrow">Storyboard · Kardiograph plugs · v9</div>
<h1>Sinus tach vs SVT <em>· brought to you by Kardiograph</em></h1>
<p class="lede">Two plugs for Kardiograph by Medzcool, cut into the finished v8. A quick opener with no voice-over right after the title card, and a voiced end plug before the Subscribe card. Both are Comma Clinical motion on v8's own warm paper, built in Remotion, and every strip is lead II from Kardiograph's own EKG engine. These frames are pulled from the v9 render itself, and timecodes are v9 times.</p>
<div class="facts"><span><b>Format</b> 16:9, 1920×1080, 30 fps</span><span><b>Video</b> 3:28 (v8 was 2:58)</span><span><b>Opener</b> 0:12.3 to 0:21.6, 9.3 s, sounds only</span><span><b>End plug</b> 2:59.1 to 3:20.6, 21.5 s, voiced</span><span><b>Voice</b> markusguapo, v4 (IPA for Medzcool and EKG)</span><span><b>Palette</b> v8 warm paper, charcoal, Kardiograph coral</span></div>
<div class="audio"><label for="op">Opener sound (no voice-over)</label><audio id="op" controls preload="none" src="opener-audio.mp3"></audio></div>
<div class="audio"><label for="ep">End plug, voice-over and sound</label><audio id="ep" controls preload="none" src="end-plug-audio.mp3"></audio></div>
</header>
<section class="sec"><h2>Opener · 0:12, no voice-over</h2><p class="lede">After the title card, the frame folds into a point and Kardiograph unfolds out of it: who brought you the video, one feature (practice: read a strip, pick an answer, get scored), and the link. Then the title card grows back and the video carries on.</p></section>
{figs_o}
<section class="sec"><h2>End plug · 2:59, voiced</h2><p class="lede">What Kardiograph is and why it helps a student: true-scale tracings you can measure, and practice strips that are generated fresh every time. Every move lands on a measured word.</p></section>
{figs_e}
<footer>Built from the Remotion project in videos/Sinus Tach vs SVT/4-animation/remotion (src/plugs/Opener.tsx, EndPlug.tsx) and 3-board/kardiograph-plug/make_storyboard.py in the motion-graphics repo.</footer>
</main>
</body></html>
'''


if __name__ == '__main__':
    frames()
    (OUT / 'index.html').write_text(page())
    print('wrote', OUT / 'index.html')
