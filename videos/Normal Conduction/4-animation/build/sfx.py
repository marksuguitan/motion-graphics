#!/usr/bin/env python3
"""sfx.py: the sound-effects track for Normal Conduction (no VO), synthesized, so nothing is downloaded.

Reads 4-animation/remotion/src/data/timeline.json and conduction.json (the same times the picture uses) and
writes 4-animation/remotion/public/sfx/sfx.wav (48 kHz mono). Soft and sparse, per Comma Clinical: a hit on a
landing or an event, never on the start of a move. Re-run after any timeline change:  python3 sfx.py
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RM = os.path.join(os.path.dirname(HERE), 'remotion')
TL = json.load(open(os.path.join(RM, 'src/data/timeline.json')))
CD = json.load(open(os.path.join(RM, 'src/data/conduction.json')))
SR = 48000
DUR = TL['end']
out = np.zeros(int(SR * (DUR + 0.5)))
rng = np.random.default_rng(7)


def db(x):
    return 10 ** (x / 20)


def place(sig, t, gain_db):
    i = int(round(t * SR))
    if i >= len(out):
        return
    n = min(len(sig), len(out) - i)
    out[i:i + n] += sig[:n] * db(gain_db)


def env(n, attack=0.002, decay=0.08):
    tt = np.arange(n) / SR
    a = np.clip(tt / attack, 0, 1)
    return a * np.exp(-tt / decay)


def tone(f0, f1, dur, decay, attack=0.002, harm=0.0):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (tt / dur)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) + harm * np.sin(2 * ph)
    return s * env(n, attack, decay)


def noise(dur, lo, hi, attack, decay):
    n = int(dur * SR)
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(X, n)
    x /= np.max(np.abs(x)) + 1e-9
    return x * env(n, attack, decay)


def swell(dur, lo, hi, rise=True):
    n = int(dur * SR)
    x = noise(dur, lo, hi, 0.001, 10)
    shape = np.sin(np.linspace(0, np.pi, n)) ** 2
    if not rise:
        shape = shape[::-1] * np.linspace(1, 0, n) ** 0.3
    return x * shape


def mix(*parts):
    n = max(len(p) for p in parts)
    y = np.zeros(n)
    for p in parts:
        y[:len(p)] += p
    return y


tick = lambda: mix(0.6 * tone(2400, 2200, 0.03, 0.006), 0.4 * noise(0.02, 2000, 7000, 0.0005, 0.004))
pop = lambda: tone(520, 260, 0.18, 0.05)
thud = lambda: mix(tone(110, 55, 0.35, 0.09), 0.3 * noise(0.05, 80, 400, 0.001, 0.02))
blip = lambda f=1320: tone(f, f * 1.02, 0.12, 0.035)
lub = lambda: mix(tone(70, 45, 0.3, 0.07), 0.35 * tone(140, 90, 0.2, 0.05))
beep = lambda: tone(960, 960, 0.1, 0.06, attack=0.004)


def warp(x, k):
    if x <= k[0][0]:
        return k[0][1]
    for i in range(1, len(k)):
        if x <= k[i][0]:
            (x0, y0), (x1, y1) = k[i - 1], k[i]
            return y1 if x1 == x0 else y0 + (x - x0) / (x1 - x0) * (y1 - y0)
    return k[-1][1]


def time_of(tau, k):
    for i in range(1, len(k)):
        if tau <= k[i][1] and k[i][1] > k[i - 1][1]:
            (x0, y0), (x1, y1) = k[i - 1], k[i]
            return x0 + (tau - y0) / (y1 - y0) * (x1 - x0)
    return k[-1][0]


T = TL['title']
n_chars = len(T['text'])
# title: the dot pops in, keys tick as it types, deletes, retypes
place(pop(), 0.02, -24)
for i in range(1, n_chars + 1):
    place(tick(), T['typeOn'] + i * 2 / 30, -30)
    place(tick(), T['retype'] + i * 2 / 30, -30)
f, gap = 0, 4
for i in range(n_chars):
    f += gap
    gap = max(1, gap - 1)
    place(tick(), T['typeOff'] + f / 30, -32)
# the dot grows, hops and lands on the SA node; the heart unfolds from it
place(tone(300, 600, 0.25, 0.08), TL['dot']['grow'], -26)
place(thud(), TL['dot']['land'], -16)
place(pop(), TL['dot']['land'], -24)
place(swell(0.7, 300, 2500), TL['heart']['grow'] - 0.05, -32)
# walk-through
W = TL['walk']
for tp in W['pings']:
    place(blip(1320), tp, -22)
place(tone(420, 380, 0.2, 0.06), W['warp'][2][0], -22)  # into the AV node
place(blip(990), W['warp'][3][0], -24)  # out of it
t_bif = CD['routes']['toBif'][-1][2]
t_split = time_of(t_bif, W['warp'])
place(blip(1180), t_split, -24)
place(blip(1480), t_split + 0.07, -26)
place(lub(), W['squeeze'], -14)
# reset and ECG
place(swell(0.5, 400, 3000, rise=False), TL['reset']['t'], -32)
place(pop(), TL['reset']['orb'], -24)
E = TL['ecg']
place(beep(), time_of(0.192, E['slowWarp']), -24)
place(lub(), time_of(0.2, E['slowWarp']), -16)
for k in range(E['realBeats']):
    tb = E['realStart'] + k * CD['beat']
    place(beep(), tb + 0.192, -24)
    place(lub(), tb + 0.2, -17)
# outro: the heart folds into the dot
place(swell(0.35, 500, 4000), TL['heart']['shrink'] - 0.05, -30)
place(pop(), TL['heart']['shrink'] + 0.3, -24)

# soft limiter and write
peak = np.max(np.abs(out))
if peak > 0.89:
    out *= 0.89 / peak
pcm = (out * 32767).astype(np.int16)
os.makedirs(os.path.join(RM, 'public/sfx'), exist_ok=True)
with wave.open(os.path.join(RM, 'public/sfx/sfx.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'sfx.wav {len(out) / SR:.1f} s, peak {20 * np.log10(max(peak, 1e-9)):.1f} dBFS')
