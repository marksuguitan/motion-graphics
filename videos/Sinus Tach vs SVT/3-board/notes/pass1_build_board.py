import re,json,os,glob,html
V="/home/claude/motion-graphics/videos/Sinus Tach vs SVT/3-board"
OUT=os.path.dirname(os.path.abspath(__file__))+"/index.html"
log=json.load(open(V+"/audio/vo_log.json")); rows={r[0]:r for r in json.load(open(V+"/timings/scene_rows.json"))}
SYM=re.compile(r'<symbol id="(heart|cond-sa|cond-av|cond-atria|cond-his)".*?</symbol>',re.S)
shared=None; figs={}
for f in sorted(glob.glob(V+"/art/*.svg")):
    b=os.path.basename(f).split('_')[0]; s=open(f).read()
    syms=SYM.findall(s); full=[m.group(0) for m in SYM.finditer(s)]
    if shared is None: shared=full
    assert full==shared, f
    s=SYM.sub('',s)
    s=re.sub(r'<\?xml[^>]*\?>','',s)
    p=f"b{b}-"
    keep={'heart','cond-sa','cond-av','cond-atria','cond-his'}
    s=re.sub(r'\bid="([^"]+)"',lambda m:f'id="{p}{m.group(1)}"',s)
    s=re.sub(r'url\(#([^)]+)\)',lambda m:f'url(#{m.group(1) if m.group(1) in keep else p+m.group(1)})',s)
    s=re.sub(r'href="#([^"]+)"',lambda m:f'href="#{m.group(1) if m.group(1) in keep else p+m.group(1)}"',s)
    s=s.replace('<svg ',f'<svg role="img" aria-label="Beat {b}" ',1)
    figs[b]=(os.path.basename(f),s.strip())
scenes={"1":"Cold open: one strip, one question","2":"The normal route","3":"Sinus tach: the heart answering","4":"SVT: the heart in a loop","5":"What the mechanism predicts","6":"The AV node is the key","7":"Close"}
fmt=lambda t:f"{int(t//60)}:{int(t%60):02d}"
total=log['total_s']
parts=[]; last=None
for x in log['beats']:
    b=x['beat']
    if b[0]!=last: parts.append(f'<h2 class="scene">Scene {b[0]} · {scenes[b[0]]}</h2>'); last=b[0]
    name,svg=figs[b]; narr=re.sub(r'\s*\\?\[[^\]]*\\?\]','',rows[b][1]).replace('\\','').strip()
    narr="<em>No narration: title card, 2.0 s.</em>" if b=='1C' else html.escape(narr)
    parts.append(f'''<figure class="kf" id="beat-{b}" data-start="{x['start_in_full']}">
  <div class="art">{svg}</div>
  <figcaption>
    <span class="id">{b}</span>
    <code>{name} · {b}.mp3 · {x['duration_s']:.2f} s · hold {x['hold_after']} s</code>
    <audio controls preload="none" src="audio/{b}.mp3"></audio>
    <p>{narr}</p>
  </figcaption>
</figure>''')
T=open('/mnt/project-files/knowledge/motion-board-template.html').read()
script=T[T.index('<script>'):]
style=T[T.index('<style>'):T.index('</style>')+8]
style=style.replace('--accent:#4C7A10','--accent:#C2443B').replace('--accent:#D4FF3F','--accent:#F0645A')
style=style.replace('--font:"Helvetica Neue",Helvetica,Arial,sans-serif','--font:Inter,"Helvetica Neue",Arial,sans-serif;--display:Manrope,Inter,"Helvetica Neue",Arial,sans-serif')
style=style.replace('h1{font-weight:500','h1{font-family:var(--display);font-weight:600').replace('.scene{font-weight:500','.scene{font-family:var(--display);font-weight:700').replace('.id{font-weight:700','.id{font-family:var(--display);font-weight:700')
style=style.replace('/* Layout','.lead em{font-style:normal;color:var(--fg)}\n/* Layout')
page=f'''<meta charset="utf-8">
<title>Sinus Tach vs SVT Motion Board</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Manrope:wght@500;600;700;800&display=swap">
{style}
<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>{''.join(shared)}</defs></svg>
<main>
<h1>Sinus Tach vs SVT: Motion Board</h1>
<p class="lead">Style A, pass 1. Each frame is drawn at the end state of its beat; press a beat's player to hear its scratch VO (Markus Guapo), or Play all to hear the whole video ({fmt(total)}) with the frames following along. Comment on any beat: wording, artwork or read.</p>
<div class="player" aria-label="Play the whole video">
  <button type="button" id="playAll">Play all</button>
  <span class="now" id="now">{fmt(total)} · {len(log['beats'])} beats</span>
  <progress id="prog" value="0" max="1"></progress>
  <audio id="full" src="audio/full.mp3" preload="metadata"></audio>
</div>
{chr(10).join(parts)}
<footer>{len(figs)} SVGs in <code>videos/Sinus Tach vs SVT/3-board/art/</code> (drawn by <code>make_beats.py</code> from your conduction heart); beat audio, takes and <code>vo_log.json</code> in <code>3-board/audio/</code>; stitched track <code>audio/full.mp3</code>; word timings and sync points in <code>3-board/timings/</code>.</footer>
</main>
{script}'''
open(OUT,'w').write(page); print(len(page), len(figs))
