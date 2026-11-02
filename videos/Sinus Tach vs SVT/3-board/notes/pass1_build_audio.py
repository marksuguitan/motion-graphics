import json,os,subprocess,shutil,re
D=os.path.dirname(os.path.abspath(__file__))
A="/home/claude/motion-graphics/videos/Sinus Tach vs SVT/3-board/audio"
os.makedirs(A+"/takes",exist_ok=True)
meta=json.load(open(D+'/gens.json')); tts=json.load(open(D+'/tts.json'))
rows=json.load(open(D+'/scene_rows.json'))
hold={r[0]:(float(r[4].split()[0]) if r[4]!='—' else 0.5) for r in rows}
import wave
def dec(f):
    w=D+'/wav/'+os.path.basename(f)+'.wav'; os.makedirs(D+'/wav',exist_ok=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',f,'-ar','44100','-ac','1',w],check=True); return w
def dur(f):
    w=wave.open(dec(f)); return round(w.getnframes()/w.getframerate(),3)
order=[r[0] for r in rows]
runs={l.split()[0]:l.split()[1] for l in open(D+'/runs.txt')}
sess={}
for l in open(D+'/runs.txt'):
    p=l.split(); sess[p[2]]=p[0]; sess[p[3]]=p[0]
beats=[];t=0.0
# silent 1C
subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t','2.0','-c:a','libmp3lame','-b:a','128k',A+'/1C.mp3'],check=True)
for b in order:
    if b=='1C':
        d=dur(A+'/1C.mp3')
        beats.append(dict(beat='1C',node_id=None,takes=[],saved_take=None,saved_file='1C.mp3',tts_input=None,tts_input_respelling=[],transcript_generation_id=None,duration_s=d,start_in_full=round(t,3),hold_after=hold[b]))
        t+=d+hold[b]; continue
    g=sorted([(v['created'],k,v) for k,v in meta.items() if v['beat']==b])
    takes=[]
    for i,(c,gid,v) in enumerate(g,1):
        last=i==len(g)
        dst=A+(f'/{b}.mp3' if last else f'/takes/{b}_take{i}.mp3')
        shutil.copy(D+f'/raw/{gid}.mp3',dst)
        takes.append(dict(take=i,generation_id=gid,session_id=v['session'],duration_s=dur(dst),file=(f'{b}.mp3' if last else f'takes/{b}_take{i}.mp3')))
    d=takes[-1]['duration_s']
    beats.append(dict(beat=b,node_id=runs[b],takes=takes,saved_take=len(takes),saved_file=f'{b}.mp3',tts_input=tts[b][0],tts_input_respelling=tts[b][1],transcript_generation_id=None,duration_s=d,start_in_full=round(t,3),hold_after=hold[b]))
    t+=d+hold[b]
log=dict(video="Sinus Tach vs SVT",flow="Sinus Tach vs SVT — scratch VO",flow_id="MoNbJuiMddzcvgOYSSlX",voice="Markus Guapo (45wlHoJDsEn5ruTlzdZI)",model="eleven_v4",**{"pass":1},date="2026-11-02",
 notes="Saved take = last take generated (the active one on each speech node). Durations are decoded lengths (ffmpeg). Downloaded directly into the cloud workspace. 1C is a silent title card (2.0 s, agent's call) plus its 0.6 s hold. Holds from the production doc scene tables; 0.5 s where the table says —.",
 total_s=round(t,2),beats=beats)
json.dump(log,open(A+'/vo_log.json','w'),indent=1,ensure_ascii=False)
# stitch
lst=[]
os.makedirs(D+'/sil',exist_ok=True)
for x in beats:
    lst.append(D+'/wav/'+x['saved_file']+'.wav')
    s=D+f"/sil/{x['hold_after']}.wav"
    if not os.path.exists(s): subprocess.run(['ffmpeg','-y','-loglevel','error','-f','lavfi','-i','anullsrc=r=44100:cl=mono','-t',str(x['hold_after']),s],check=True)
    lst.append(s)
args=[];fl=''
for i,f in enumerate(lst): args+=['-i',f]; fl+=f'[{i}:a]aresample=44100,aformat=channel_layouts=mono[a{i}];'
fl+=''.join(f'[a{i}]' for i in range(len(lst)))+f'concat=n={len(lst)}:v=0:a=1[o]'
subprocess.run(['ffmpeg','-y','-loglevel','error',*args[:0]] if False else ['true']); W=wave.open(D+'/full.wav','wb'); W.setnchannels(1); W.setsampwidth(2); W.setframerate(44100)
for f in lst:
    r=wave.open(f); W.writeframes(r.readframes(r.getnframes()))
W.close()
subprocess.run(['ffmpeg','-y','-loglevel','error','-i',D+'/full.wav','-c:a','libmp3lame','-b:a','128k',A+'/full.mp3'],check=True)
if 0: subprocess.run(['x',*args,'-filter_complex',fl,'-map','[o]','-c:a','libmp3lame','-b:a','128k',A+'/full.mp3'],check=True)
print('full',dur(A+'/full.mp3'),'sum',round(t,2))
for x in beats: print(x['beat'],x['duration_s'],x['start_in_full'],[k['duration_s'] for k in x['takes']])
