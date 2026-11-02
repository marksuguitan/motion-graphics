import json, subprocess, numpy as np, sys
SR=48000
raw=subprocess.run(['ffmpeg','-v','error','-i','vo/takeA.mp3','-ac','1','-ar',str(SR),'-f','f32le','-'],capture_output=True).stdout
a=np.frombuffer(raw,dtype=np.float32).copy()
W=[x for x in json.load(open('vo/words0.json')) if x.get('type','word')=='word']
LEAD=2.4; TAIL=4.0
GAPS={31:1.0,60:1.2,113:1.2,157:0.8,189:1.0,250:1.2,267:0.6,336:1.5,407:1.5}
cuts=sorted(GAPS)
segs=[];prev=0;shift={}
off=LEAD
pieces=[np.zeros(int(LEAD*SR),np.float32)]
bounds=[]
for c in cuts:
    t=(W[c-1]['end']+W[c]['start'])/2
    bounds.append((t,GAPS[c]))
pos=0.0
for t,g in bounds:
    pieces.append(a[int(pos*SR):int(t*SR)]); pieces.append(np.zeros(int(g*SR),np.float32)); pos=t
pieces.append(a[int(pos*SR):]); pieces.append(np.zeros(int(TAIL*SR),np.float32))
out=np.concatenate(pieces)
def m(t):
    o=LEAD
    for bt,g in bounds:
        if t>=bt: o+=g
    return t+o
cues=[{'w':x['text'],'s':round(m(x['start']),3),'e':round(m(x['end']),3)} for x in W]
total=len(out)/SR
json.dump({'total':total,'words':cues},open('src/cues.json','w'))
subprocess.run(['ffmpeg','-y','-v','error','-f','f32le','-ar',str(SR),'-ac','1','-i','-','-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar','48000','public/vo_timed.wav'],input=out.tobytes())
print('total',total)
