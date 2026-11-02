import sys
from PIL import Image
fs=sys.argv[2:]; out=sys.argv[1]
W,H=960,540; cols=2; rows=(len(fs)+1)//2
s=Image.new('RGB',(W*cols,H*rows),'white')
for i,f in enumerate(fs): s.paste(Image.open(f).convert('RGB').resize((W,H)),((i%cols)*W,(i//cols)*H))
s.save(out,quality=80)
