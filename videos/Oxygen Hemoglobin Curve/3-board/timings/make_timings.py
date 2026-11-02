"""Pass 1 timings for this video. Inputs: scribe_words.json (Scribe words per beat, IPA tokens folded back to script spelling),
the production doc read as XML (scene tables: Beat | Narration | Intent | Sync on | Hold), ../audio/vo_log.json (start_in_full_s).
Writes word_timings.csv and sync_points.csv. Cues in ";"-separated quotes; "(2nd)" picks an occurrence."""
import re,json,csv,html,os
s=open(__import__('sys').argv[1]).read()
V="/home/claude/motion-graphics/videos/Oxygen Hemoglobin Curve/3-board"
stt=json.load(open(V+'/timings/scribe_words.json'))
log=json.load(open(V+"/audio/vo_log.json"))
start={b['beat']:b['start_in_full_s'] for b in log['beats']}
def txt(x): return html.unescape(re.sub(r'<[^>]+>','',x)).strip()
rows=[]
for r in re.findall(r"<row [^>]*>(.*?)</row>",s,re.S):
    cells=[txt(c) for c in re.findall(r"<cell [^>]*>(.*?)</cell>",r,re.S)]
    if len(cells)==5 and re.fullmatch(r"\d+[A-D]",cells[0]): rows.append(cells)
print(len(rows))
norm=lambda t: re.sub(r"[^a-z0-9]","",t.lower())
os.makedirs(V+"/timings",exist_ok=True)
with open(V+"/timings/word_timings.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["beat","index","word","start_in_beat_s","end_in_beat_s","start_in_full_s","end_in_full_s"])
    for b in log['beats']:
        for i,x in enumerate(stt[b['beat']]['words']):
            w.writerow([b['beat'],i+1,x['text'],x['start'],x['end'],round(start[b['beat']]+x['start'],3),round(start[b['beat']]+x['end'],3)])
out=[];flags=[]
for beat,narr,intent,sync,hold in rows:
    W=stt[beat]['words']; wn=[norm(x['text']) for x in W]
    narrn=[norm(t) for t in re.sub(r"\[S\d+\]","",narr).split()]
    for cue in [c.strip() for c in sync.split(';') if c.strip() and c.strip()!='—']:
        m=re.match(r'"([^"]+)"\s*(?:\((\d)(?:st|nd|rd|th)\))?',cue)
        if not m: out.append([beat,cue,"","","","not a quoted word"]); flags.append((beat,cue,"not a quoted word")); continue
        ph,occ=m.group(1),m.group(2); toks=[norm(t) for t in ph.split() if norm(t)]
        hits=[i for i in range(len(wn)) if all(i+k<len(wn) and wn[i+k]==t for k,t in enumerate(toks))]
        verb=any(all(i+k<len(narrn) and narrn[i+k]==t for k,t in enumerate(toks)) for i in range(len(narrn)))
        note=[]
        if not verb: note.append("not verbatim in narration")
        if not hits:
            hits=[i for i in range(len(wn)) if toks[0] in wn[i]]; note.append("timed on partial match")
        if not hits: out.append([beat,cue,"","","","NOT FOUND"]); flags.append((beat,cue,"not found")); continue
        if len(hits)>1 and not occ: note.append(f"occurs {len(hits)}x ({', '.join(str(W[i]['start']) for i in hits)} s); took 1st")
        i=hits[int(occ)-1] if occ else hits[0]
        t=W[i]['start']
        out.append([beat,cue,W[i]['text'],t,round(start[beat]+t,3),"; ".join(note)])
        if note: flags.append((beat,cue,"; ".join(note)))
with open(V+"/timings/sync_points.csv","w",newline="") as f:
    w=csv.writer(f); w.writerow(["beat","sync_on","word_heard","start_in_beat_s","start_in_full_s","flag"]); w.writerows(out)
print(len(out),"cues"); 
for x in flags: print("FLAG",x)
