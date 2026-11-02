import json, sys, numpy as np
sys.path.insert(0,'.')
import align_words as aw
A="/mnt/user-data/uploads/Desktop/Pulsus Paradoxus/audio"; R=A+"/takes/word_timing_refs"
W=json.load(open(sys.argv[1]))
rows=[]
for b,words in W.items():
    if b.startswith('_'): continue
    x=aw.decode(f"{A}/{b}.mp3"); _,E=aw.features(x)
    thr=E.max()-35; q=E<thr
    # silent runs >= 150 ms inside the speech (not leading/trailing)
    on,off=aw.speech_bounds(E)
    gaps=[];i=0
    while i<len(q):
        if q[i]:
            j=i
            while j<len(q) and q[j]: j+=1
            s,e=i*aw.HOP/aw.SR,j*aw.HOP/aw.SR
            if e-s>=0.15 and s>on+0.05 and e<off-0.05: gaps.append((s,e))
            i=j
        else: i+=1
    bounds=[(a['end']+c['start'])/2 for a,c in zip(words,words[1:])]
    d=[]
    for s,e in gaps:
        m=(s+e)/2
        inside=[bb for bb in bounds if s-0.03<=bb<=e+0.03]
        d.append(0.0 if inside else min(abs(bb-m) for bb in bounds))
    rows.append((b,len(gaps),round(max(d),3) if d else None, sum(1 for v in d if v==0)))
for r in rows: print(*r)
