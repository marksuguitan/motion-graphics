#!/usr/bin/env python3
"""make_beeps.py: adds monitor beeps to the opening of Shorts 2, 3 and 5 (Mark, Nov 24, 2026: the start sounded silent).
Same beep as Shorts 1 and 4 (public/beep.wav, cut from short-adenosine.mp3), one per QRS of the strip the logo lands on,
from the first frame until the VO starts (3.7 s). Run after make_audio.sh; writes public/short9-<id>.mp3.
Beat k of a strip (rr = 60/bpm) peaks at short time 1.26 + k*rr: the strip's first R wave (strip time 0.28) printed
from the logo's landing (INTRO_STOP 1.58 s, PREPRINT 0.6 s); earlier beats are extrapolated at the same rate, as in Short 4."""
import os, subprocess, sys
import numpy as np
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'public'))
SR = 48000
def load(f):
    return np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, dtype=np.float32).copy()
beep = load('beep.wav')            # onset 0.02 s into the clip
VO_START = 3.7
SHORTS = {'narrow': 75, 'reason': 130, 'tells': 180}
for sid, bpm in SHORTS.items():
    vo = load(f'short9-{sid}.vo.mp3')             # written by make_audio.sh
    rr = 60 / bpm
    k0 = -int(1.26 // rr)
    times = [1.26 + k * rr for k in range(k0, 20)]
    times = [t for t in times if 0.15 <= t < VO_START - 0.02]
    out = vo.copy()
    for t in times:
        i = int(round((t - 0.02) * SR)); out[i:i + len(beep)] += beep[:len(out) - i]
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-b:a', '192k', f'short9-{sid}.mp3'], input=out.astype(np.float32).tobytes(), check=True)
    print(sid, ' '.join(f'{t:.2f}' for t in times))
