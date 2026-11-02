"""Pass 1 timings for Sinus Tach vs SVT. Inputs (in this folder): scribe_full_words.json (Scribe on the stitched
../audio/full.mp3), scene_rows.json (scene-table rows Beat|Narration|Intent|Sync on|Hold from the production doc),
../audio/vo_log.json (start_in_full, duration_s). Words are assigned to the beat whose window holds their start.
Writes word_timings.csv and sync_points.csv. Usage: python3 -I make_timings.py"""
import json,csv,re,os
H=os.path.dirname(os.path.abspath(__file__))
W=[w for w in json.load(open(H+'/scribe_full_words.json'))['words'] if w.get('type','word')=='word']
log=json.load(open(H+'/../audio/vo_log.json')); rows=json.load(open(H+'/scene_rows.json'))
win={b['beat']:(b['start_in_full'],b['start_in_full']+b['duration_s']+b['hold_after']) for b in log['beats']}
per={b:[] for b in win}
for w in W:
    for b,(s,e) in win.items():
        if s-0.05<=w['start']<e: per[b].append(w); break
norm=lambda t: re.sub(r"[^a-z0-9]","",t.lower())
with open(H+'/word_timings.csv','w',newline='') as f:
    c=csv.writer(f); c.writerow(["beat","index","word","start_in_beat","end_in_beat","start_in_full","end_in_full"])
    for b in win:
        s0=win[b][0]
        for i,w in enumerate(per[b]): c.writerow([b,i,w['text'],round(w['start']-s0,3),round(w['end']-s0,3),w['start'],w['end']])
out=[];flags=[]
for beat,narr,intent,sync,hold in rows:
    ws=per[beat]; wn=[norm(w['text']) for w in ws]
    for cue in [x.strip() for x in sync.split(';') if x.strip() and x.strip()!='—']:
        ph=cue.strip('"'); toks=[norm(t) for t in ph.split()]
        hits=[i for i in range(len(wn)) if all(i+k<len(wn) and wn[i+k]==t for k,t in enumerate(toks))]
        note=[]
        if not hits:
            hits=[i for i in range(len(wn)) if toks[0] and toks[0] in wn[i]]
            if hits: note.append(f"matched inside '{ws[hits[0]]['text']}'")
        if not hits: out.append([beat,ph,"","","","NOT FOUND"]); flags.append((beat,ph,"not found")); continue
        if len(hits)>1: note.append(f"appears {len(hits)}x in beat; took 1st")
        w=ws[hits[0]]
        out.append([beat,ph,w['text'],round(w['start']-win[beat][0],3),w['start'],"; ".join(note)])
        if note: flags.append((beat,ph,"; ".join(note)))
with open(H+'/sync_points.csv','w',newline='') as f:
    c=csv.writer(f); c.writerow(["beat","sync_word","matched_spoken_word","time_in_beat","time_in_full","flag"]); c.writerows(out)
print(sum(len(v) for v in per.values()),"words of",len(W),";",len(out),"cues")
for x in flags: print("FLAG",x)
