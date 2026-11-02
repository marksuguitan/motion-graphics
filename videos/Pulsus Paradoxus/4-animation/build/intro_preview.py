"""Medzcool logo intro preview: logo chopped into a square grid; tiles land in batches on each S1 of
'Normal S1 S2 (Apex).mp3' (S1 times measured from the file). Renders PNG frames for a quick MP4 check."""
import json, math, random
from PIL import Image, ImageDraw, ImageChops
W,H,FPS,DUR = 1920,1080,30,3.3
BG,ACC = (21,21,21),(255,64,87)
POLYS=[[13.98,28.07,4.31,28.07,0,35.85,18.54,35.85,23.46,27.04,34.59,44.72,38.86,36.91,23.06,11.81,13.98,28.07],
       [61.63,19.81,50.85,1.86,41.25,18.59,29.55,0,25.33,7.9,41.56,33.67,51,17.22,57.23,27.59,65.77,27.59,69.66,19.81,61.63,19.81]]
LW=760; S=LW/69.66; LH=44.72*S
OX,OY=W/2-LW/2, H/2-LH/2
TILE=40; GAP=3
O=json.load(open("/tmp/claude-0/intro/fast_onsets.json"))   # v3: heartbeat sped up 1.6x (atempo, ~120 bpm); S1/S2 peaks measured from hb_fast.wav
S1=O["S1"]; S2=O["S2"]
BUILD=[t-0.02 for t in S1[:4]]; FINAL=S1[4]   # v3: one batch per lub (4 lubs), logo closes on the 5th lub
SS=2
logo=Image.new("L",(int(LW*SS),int(LH*SS)),0); d=ImageDraw.Draw(logo)
for p in POLYS: d.polygon([(p[i]*S*SS,p[i+1]*S*SS) for i in range(0,len(p),2)],fill=255)
logo_s=logo.resize((int(LW),int(LH)),Image.LANCZOS)
cols=math.ceil(LW/TILE); rows=math.ceil(LH/TILE)
tiles=[]
for r in range(rows):
    for c in range(cols):
        box=(c*TILE,r*TILE,min((c+1)*TILE,int(LW)),min((r+1)*TILE,int(LH)))
        m=logo_s.crop(box)
        cov=sum(m.get_flattened_data())/255/(TILE*TILE)
        if cov>0.02: tiles.append(dict(c=c,r=r,box=box,mask=m))
random.seed(7); random.shuffle(tiles)
frac=[0.16,0.22,0.28,0.34]; n=len(tiles); idx=0
for b,f in enumerate(frac):
    k=round(n*f) if b<3 else n-idx
    for t in tiles[idx:idx+k]: t["t0"]=BUILD[b]+random.uniform(0,0.04)
    idx+=k
def ease_back(x,s=2.2):
    x=min(max(x,0),1); x-=1; return x*x*((s+1)*x+s)+1
def pulse(t):
    v=0
    for i,s in enumerate(S1[1:5]):
        a=0.05 if s==FINAL else 0.022
        if t>=s: v+=a*math.exp(-(t-s)/0.12)*min(1,(t-s)/0.04)
    for s in S2[0:4]:
        if t>=s: v+=0.008*math.exp(-(t-s)/0.1)*min(1,(t-s)/0.04)
    return 1+v
def gap(t):  # seams close on the final beat
    if t<FINAL: return GAP
    return GAP*max(0,1-(t-FINAL)/0.15)
print("tiles",n,"grid",cols,rows)
def logo_at(P):
    w,h=round(LW*P),round(LH*P)
    im=Image.new("L",(W,H),0); im.paste(logo_s.resize((w,h),Image.LANCZOS),(round(W/2-w/2),round(H/2-h/2)))
    return im
for fi in range(int(DUR*FPS)):
    t=fi/FPS
    P=pulse(t); g=gap(t); full=logo_at(P)
    if t>=FINAL+0.15:
        layer=full
    else:
        rects=Image.new("L",(W,H),0); dr=ImageDraw.Draw(rects); pop=Image.new("L",(W,H),0)
        for tl in tiles:
            if t<tl["t0"]: continue
            x=(t-tl["t0"])/0.18; sc=ease_back(x); op=min(1,(t-tl["t0"])/0.06)
            x0,y0,x1,y1=tl["box"]
            cx=W/2+(OX+(x0+x1)/2-W/2)*P; cy=H/2+(OY+(y0+y1)/2-H/2)*P
            if x>=1:
                hw=(x1-x0)*P/2-g/2; hh=(y1-y0)*P/2-g/2
                dr.rectangle([cx-hw,cy-hh,cx+hw-1,cy+hh-1],fill=255)
            else:
                tw=(x1-x0)*sc*P-g*sc; th=(y1-y0)*sc*P-g*sc
                if tw<1 or th<1: continue
                m=tl["mask"].resize((max(1,round(tw)),max(1,round(th))),Image.BILINEAR)
                if op<1: m=m.point(lambda v:int(v*op))
                tmp=Image.new("L",(W,H),0); tmp.paste(m,(round(cx-tw/2),round(cy-th/2)))
                pop=ImageChops.lighter(pop,tmp)
        layer=ImageChops.lighter(ImageChops.multiply(full,rects),pop)
    fr=Image.new("RGB",(W,H),BG); fr.paste(Image.new("RGB",(W,H),ACC),(0,0),layer)
    fr.save(f"/tmp/claude-0/intro/fr/{fi:04d}.png")
json.dump({"S1":S1,"S2":S2,"tiles":n},open("/tmp/claude-0/intro/timing.json","w"))
