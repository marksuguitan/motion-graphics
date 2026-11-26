#!/usr/bin/env python3
"""sfx.py: the sound-effects track for the Electrical Alternans short (no VO). Synthesized, nothing downloaded.

Reads src/data/timeline.json (the same beat grid the picture uses) and writes public/sfx.wav (48 kHz mono).
A monitor beep on every beat: higher on tall beats, lower on short beats, so the alternans can be heard; once
the fluid is drained every beep is the same. Soft hits on landings, per Comma Clinical. Re-run after any
timeline change:  python3 sfx.py
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TL = json.load(open(os.path.join(HERE, 'src/data/timeline.json')))
SR = 48000
K = TL['k']
B = lambda k: TL['t0'] + k * TL['beat']
out = np.zeros(int(SR * TL['end']))
rng = np.random.default_rng(11)
db = lambda x: 10 ** (x / 20)


def place(sig, t, gain_db):
    i = int(round(t * SR))
    if i < 0 or i >= len(out):
        return
    n = min(len(sig), len(out) - i)
    out[i:i + n] += sig[:n] * db(gain_db)


def env(n, attack, decay):
    tt = np.arange(n) / SR
    return np.clip(tt / attack, 0, 1) * np.exp(-tt / decay)


def tone(f0, f1, dur, decay, attack=0.003, harm=0.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) + harm * np.sin(2 * ph)) * env(n, attack, decay)


def noise(dur, lo, hi):
    n = int(dur * SR)
    X = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(X, n)
    return x / (np.max(np.abs(x)) + 1e-9)


def swell(dur, lo, hi):
    n = int(dur * SR)
    return noise(dur, lo, hi) * np.sin(np.linspace(0, np.pi, n)) ** 2


def mix(*parts):
    y = np.zeros(max(len(p) for p in parts))
    for p in parts:
        y[:len(p)] += p
    return y


def beep(f):  # a soft monitor beep: a short sine with a rounded start and end
    n = int(0.11 * SR)
    tt = np.arange(n) / SR
    shape = np.clip(tt / 0.006, 0, 1) * np.clip((0.11 - tt) / 0.03, 0, 1)
    return (np.sin(2 * np.pi * f * tt) + 0.12 * np.sin(4 * np.pi * f * tt)) * shape


pop = lambda: tone(520, 300, 0.16, 0.045)
tick = lambda: mix(0.6 * tone(1900, 1700, 0.04, 0.008), 0.3 * noise(0.02, 2000, 7000) * env(int(0.02 * SR), 0.0005, 0.004))
thud = lambda: mix(tone(120, 60, 0.3, 0.08), 0.25 * noise(0.05, 80, 400) * env(int(0.05 * SR), 0.001, 0.02))
zip_in = lambda: tone(900, 220, 0.25, 0.4, attack=0.12) * np.linspace(0.2, 1, int(0.25 * SR)) ** 2  # shrink into the point

HI, LO = 880.0, 660.0  # tall beat, short beat (a fourth apart)

# the metronome: one beep per beat, alternating until the fluid is drained
for k in range(0, TL['lastBeep'] + 1):
    f = HI if (k >= K['steady'] or k % 2 == 0) else LO
    gain = -19 if f == HI else -22
    if K['title'] <= k < K['cause'] or k >= K['recapThink']:
        gain -= 3  # sit back under the title and the closing lines
    place(beep(f), B(k), gain)

# hook: each word lands with a soft thud under its beep; tall words land heavier
for i in range(4):
    place(thud(), B(K['hook'] + i), -21 if i % 2 == 0 else -27)
    place(thud(), B(K['recap'] + i), -20 if i % 2 == 0 else -26)

# scene changes: the old scene zips into the point, the next one pops out of it
for name in ('recap', 'logo'):
    place(zip_in(), B(K[name]) - 0.25, -27)
    place(pop(), B(K[name]), -21)
# the strip slides down, then the heart grows out of a point
place(swell(0.7, 300, 1500), B(K['cause']), -27)
place(pop(), B(K['cause']) + 0.4, -20)

# text that cuts on gets a small tick
for name in ('rowRegular', 'rowFast', 'rowHeading', 'title', 'titleSub', 'cause', 'causeSwings', 'causeReadout', 'drainStops', 'recapThink', 'recapEcho'):
    place(tick(), B(K[name]), -27)

# the swing: a soft whoosh on each pass through the middle (twice per swing), from the swing's start to the drain
t = B(K['swing']) + TL['beat'] / 2
i = 0
while t < B(K['drain']) + 1.0:
    ramp = min(1.0, (t - B(K['swing'])) / 1.5)
    fade = max(0.0, 1 - max(0.0, t - B(K['drain'])) / 1.0)
    lo, hi = (500, 2600) if i % 2 == 0 else (350, 1800)
    place(swell(0.34, lo, hi) * ramp * fade, t - 0.17, -27)
    t += TL['beat']
    i += 1

# the drain: a falling sweep with a little water noise while the ring closes in
n = int(1.0 * SR)
drain = mix(0.7 * tone(520, 150, 1.0, 0.5, attack=0.05), 0.5 * noise(1.0, 300, 1800) * np.linspace(1, 0, n) ** 1.5 * np.clip(np.arange(n) / (0.05 * SR), 0, 1))
place(drain, B(K['drain']), -21)

# the logo lands: a low thud and a soft two-note chime
place(thud(), B(K['logo']) + 0.3, -15)
place(mix(tone(660, 660, 1.4, 0.45, attack=0.005, harm=0.1), 0.7 * tone(990, 990, 1.4, 0.4, attack=0.005)), B(K['logo']) + 0.3, -22)

peak = np.max(np.abs(out))
print('peak before limit', round(float(peak), 3))
out = np.tanh(out * db(13)) * db(-1.5)  # master gain (the effects are the only sound), then a soft safety limit
os.makedirs(os.path.join(HERE, 'public'), exist_ok=True)
with wave.open(os.path.join(HERE, 'public/sfx.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((np.clip(out, -1, 1) * 32767).astype(np.int16).tobytes())
print('wrote public/sfx.wav', round(len(out) / SR, 2), 's')
