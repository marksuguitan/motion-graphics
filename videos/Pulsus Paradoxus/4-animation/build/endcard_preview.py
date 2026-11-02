"""Medzcool end card (call to action), preview. 10 s, no VO. Logo lands on one heartbeat (lub at 0.40 s, taken from
the intro's 120 bpm heartbeat), then the CTA text and a 'Watch next' slot for a YouTube end-screen element."""
import math
from PIL import Image, ImageDraw, ImageFont
W,H,FPS,DUR=1920,1080,30,10.0
BG,FG,ACC,GREY,DIM,LINE=(21,21,21),(242,242,242),(255,64,87),(110,110,110),(189,189,189),(58,59,60)
B="/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"; R="/usr/share/fonts/truetype/freefont/FreeSans.ttf"
POLYS=[[13.98,28.07,4.31,28.07,0,35.85,18.54,35.85,23.46,27.04,34.59,44.72,38.86,36.91,23.06,11.81,13.98,28.07],
       [61.63,19.81,50.85,1.86,41.25,18.59,29.55,0,25.33,7.9,41.56,33.67,51,17.22,57.23,27.59,65.77,27.59,69.66,19.81,61.63,19.81]]
LX,LY,LWID=160,250,300; LS=LWID/69.66; LHGT=44.72*LS
LUB,DUB=0.40,0.60
def ob(x,s=2.0):
    x=min(max(x,0),1)-1; return x*x*((s+1)*x+s)+1
def oc(x):
    x=min(max(x,0),1); return 1-(1-x)**3
def spaced(d,xy,txt,font,fill,sp):
    x,y=xy
    for ch in txt:
        d.text((x,y),ch,font=font,fill=fill); x+=d.textlength(ch,font=font)+sp
    return x
fT=ImageFont.truetype(B,76); fS=ImageFont.truetype(R,36); fP=ImageFont.truetype(B,28); fL=ImageFont.truetype(B,24)
def mix(c,a): return tuple(int(BG[i]+(c[i]-BG[i])*a) for i in range(3))
def text_layer(t,t0,draw_fn):
    a=oc((t-t0)/0.5); dy=20*(1-a)
    return a,dy
for fi in range(int(DUR*FPS)):
    t=fi/FPS
    im=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(im)
    # logo: pop on the lub, small pulse on the dub
    if t>=LUB-0.02:
        sc=ob((t-(LUB-0.02))/0.3)
        if t>=DUB: sc*=1+0.012*math.exp(-(t-DUB)/0.1)*min(1,(t-DUB)/0.04)
        cx,cy=LX+LWID/2,LY+LHGT/2
        ss=4; lay=Image.new("L",(W*1,H*1),0)
        big=Image.new("L",(int(LWID*1.3*ss),int(LHGT*1.3*ss)),0); dd=ImageDraw.Draw(big)
        ox,oy=big.width/2,big.height/2
        for p in POLYS:
            dd.polygon([(ox+((p[i]*LS)-LWID/2)*sc*ss, oy+((p[i+1]*LS)-LHGT/2)*sc*ss) for i in range(0,len(p),2)],fill=255)
        sm=big.resize((big.width//ss,big.height//ss),Image.LANCZOS)
        op=min(1,(t-(LUB-0.02))/0.06)
        if op<1: sm=sm.point(lambda v:int(v*op))
        im.paste(Image.new("RGB",sm.size,ACC),(round(cx-sm.width/2),round(cy-sm.height/2)),sm)
    # text blocks: fade + rise 20 px, staggered
    for t0,fn in ((0.85,"title"),(1.05,"sub"),(1.25,"pill"),(1.45,"label")):
        if t<t0: continue
        a=oc((t-t0)/0.5); dy=20*(1-a)
        if fn=="title": d.text((LX-4,500+dy),"Thanks for watching",font=fT,fill=mix(FG,a))
        if fn=="sub": d.text((LX,600+dy),"Subscribe for more clinical explainers.",font=fS,fill=mix(DIM,a))
        if fn=="pill":
            d.rounded_rectangle([LX,690+dy,LX+300,762+dy],radius=8,fill=mix(ACC,a))
            w=sum(d.textlength(c,font=fP)+5 for c in "SUBSCRIBE")-5
            spaced(d,(LX+150-w/2,714+dy),"SUBSCRIBE",fP,mix((255,255,255),a),5)
        if fn=="label": spaced(d,(1000,290+dy),"WATCH NEXT",fL,mix(GREY,a),5)
    # slot outline traces clockwise from the top-left, 1.6-2.2 s
    if t>=1.6:
        x0,y0,x1,y1=1000,336,1760,764; per=2*(x1-x0)+2*(y1-y0); L=per*oc((t-1.6)/0.6)
        segs=[((x0,y0),(x1,y0)),((x1,y0),(x1,y1)),((x1,y1),(x0,y1)),((x0,y1),(x0,y0))]
        for (a0,a1) in segs:
            sl=math.dist(a0,a1)
            if L<=0: break
            f=min(1,L/sl); d.line([a0,(a0[0]+(a1[0]-a0[0])*f,a0[1]+(a1[1]-a0[1])*f)],fill=LINE,width=3); L-=sl
    # fade to black over the last 0.5 s
    if t>DUR-0.5:
        k=(t-(DUR-0.5))/0.5; im=Image.blend(im,Image.new("RGB",(W,H),(0,0,0)),k)
    im.save(f"/tmp/claude-0/outro/fr/{fi:04d}.png")
