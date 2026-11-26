#!/usr/bin/env python3
"""prep_art.py: turns Mark's heart (art/heart-exterior.svg, copied from the design repo's assets/anatomy/heart/)
into src/data/heartArt.ts for the short. The drawing is used as it is, minus the two vessels that leave through
the bottom of the frame (the descending aorta stump and the inferior vena cava below the right atrium), because
the heart swings from its great vessels inside the sac and nothing should hang below it. Re-run if the art changes."""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, 'art/heart-exterior.svg')).read()
i, j = src.index('<g id="Layer_85">'), src.index('<g id="Layer_89">')
seg = src[i:j]
paths = re.findall(r'<path[^>]*?/>', seg, flags=re.S)
assert len(paths) == 23, len(paths)
for n in (6, 9, 20):  # the descending aorta stump: two fills and its dark opening
    seg = seg.replace(paths[n], '')
src = src[:i] + seg + src[j:]
# the vena cava is one shape from top to bottom; keep only the part above the lower edge of the right atrium
src = src.replace('<g id="Layer_89">', '<clipPath id="cavaClip"><rect x="0" y="-20" width="1000" height="675"/></clipPath><g id="Layer_89" clip-path="url(#cavaClip)">')
inner = src[src.index('<g id="heart">'):src.rindex('</svg>')]
inner = re.sub(r'\s+', ' ', inner)
out = os.path.join(HERE, 'src/data/heartArt.ts')
open(out, 'w').write('// Written by prep_art.py from art/heart-exterior.svg (viewBox 64 -10 866 1032). Do not edit by hand.\nexport const HEART_ART = ' + json.dumps(inner) + ';\n')
print('wrote', out, len(inner))
