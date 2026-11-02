"""Look up the measured time of every 'on "word"' sync point in the motion notes.
Usage: python3 sync_points.py prod_doc.md words_all.json timeline.json out.json out.csv"""
import json,re,sys,csv
mdp,wp,tlp,outj,outc=sys.argv[1:6]; md=open(mdp).read()
W=json.load(open(wp)); TL={b['id']:b for b in json.load(open(tlp))['beats']}
norm=lambda t: re.sub(r"[^a-z0-9']","",t.lower().replace("’","'"))
rows=[]
# repeated words: which occurrence (1-based) the motion note means, read from its Intent line (agent's call, flagged)
OVR={("2B","Label/RV","more"):2, ("2D","Heart/LV","less"):1, ("2D","Label/LV","less"):1,
     ("3A","Pericardium/Fluid","fluid"):1, ("4C","Heart/LV_arrow","And"):2}
for blk in re.findall(r"```text\n(.*?)```",md,re.S):
    cur=None; layer=None
    for line in blk.split("\n"):
        m=re.match(r"^(\d[A-F])_[\w-]+\s+\"",line) or re.match(r"^(\d[A-F]) ",line)
        if m and m.group(1) in W: cur=m.group(1); layer="(beat)"
        lm=re.match(r"^  (\S[^ ]*(?: \S+)?)\s{2,}",line)
        if lm and not line.startswith("   ") and lm.group(1) not in ("Intent:","Hold:"): layer=lm.group(1)
        if not cur: continue
        for ph in re.findall(r'on (?:the word )?\\?"([^"\\]+)\\?"',line):
            toks=[norm(t) for t in ph.split() if norm(t)]
            wn=[norm(w['text']) for w in W[cur]]
            def find(pref):
                c=[i for i in range(len(wn)) if all(i+k<len(wn) and (wn[i+k].startswith(t) if pref else wn[i+k]==t) for k,t in enumerate(toks))]
                if not c: return None
                prev=max([r['start_in_beat_s'] for r in rows if r['beat']==cur] or [-1])
                after=[i for i in c if W[cur][i]['start']>=prev-0.01]
                find.others=[W[cur][i]['start'] for i in c]
                k=OVR.get((cur,layer,ph))
                if k: find.chosen="override"; return c[k-1]
                find.chosen="auto"
                return (after or c)[0]
            hit=find(False); note=""
            if hit is None: hit=find(True); note="partial word" if hit is not None else ""
            if hit is None:
                toks=toks[:1]; hit=find(False); note=f'phrase not verbatim in narration; timed on "{ph.split()[0]}"'
            w=W[cur][hit]
            if len(getattr(find,'others',[]))>1:
                note=(note+"; " if note else "")+"word occurs "+str(len(find.others))+"x in beat ("+", ".join(f"{t:.2f}" for t in find.others)+" s); "+("; occurrence chosen to match the Intent line, check at Stage 6" if find.chosen=="override" else "; took the first after the previous sync point, check at Stage 6")
            rows.append(dict(beat=cur,layer=layer,sync=ph,word=w['text'],start_in_beat_s=w['start'],animatic_s=round(TL[cur]['start']+w['start'],2),note=note))
for r in rows: r["note"]=r["note"].replace("; ;",";")
json.dump(rows,open(outj,"w"),indent=1)
with open(outc,"w",newline="") as f:
    wr=csv.DictWriter(f,fieldnames=list(rows[0])); wr.writeheader(); wr.writerows(rows)
for r in rows: print(r['beat'],r['layer'],'|',r['sync'],'→',r['word'],r['start_in_beat_s'],r['animatic_s'],r['note'])
