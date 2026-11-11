#!/usr/bin/env python3
"""sfx.py: the sound-effects track for Kardiograph Launch (no VO), synthesized with the same voices as
Normal Conduction's sfx.py (ticks, pops, blips, a monitor beep and a soft thump per QRS), so the two join cleanly.

Reads 4-animation/remotion/src/data/timeline.json and engine.json (the times the picture uses) and writes
4-animation/remotion/public/sfx/sfx.wav (48 kHz mono). Re-run after any timeline change:  python3 sfx.py
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RM = os.path.join(os.path.dirname(HERE), 'remotion')
TL = json.load(open(os.path.join(RM, 'src/data/timeline.json')))
EN = json.load(open(os.path.join(RM, 'src/data/engine.json')))
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


T = TL
title = 'Normal conduction'
# the title deletes itself (same cadence as typeOff in comma.ts)
f, gap = 0, 4
for i in range(len(title)):
    f += gap
    gap = max(1, gap - 1)
    place(tick(), T['typeOff'] + f / 30, -32)
# the period grows, hops and lands on the pen
place(tone(300, 600, 0.25, 0.08), T['grow'], -26)
place(thud(), T['land'], -18)
place(pop(), T['land'], -24)
# the paper runs: a beep and a soft thump on every QRS drawn before the paper stops
for on in EN['strips']['normal']['onsets']:
    tq = T['land'] + on + 0.04
    if tq < T['paperStop'] + 0.1:
        place(beep(), tq, -24)
        place(lub(), tq + 0.01, -18)
# the strip slides away, the orb opens into the card
place(swell(0.35, 500, 4000), T['stripOut'] - 0.05, -32)
place(pop(), T['card'] + 0.3, -24)
# the slider: soft detents every 10 ms of QRS width (on the cross curve, as the knob moves)
bez = (0.33, 0, 0.15, 1)
def cubic(p1x, p1y, p2x, p2y, x):
    lo, hi = 0.0, 1.0
    for _ in range(40):
        u = (lo + hi) / 2
        bx = 3 * (1 - u) ** 2 * u * p1x + 3 * (1 - u) * u * u * p2x + u ** 3
        lo, hi = (u, hi) if bx < x else (lo, u)
    u = (lo + hi) / 2
    return 3 * (1 - u) ** 2 * u * p1y + 3 * (1 - u) * u * u * p2y + u ** 3
prev = 0
for i in range(1, 91):
    s = T['slider'] + 0.9 * i / 90
    k = cubic(*bez, i / 90)
    step = int(k * 6 + 1e-6)
    if step > prev:
        prev = step
        place(blip(1100 + 60 * step), s, -30)
# practice: each strip sweeps in with a blip
for i, td in enumerate(T['deal']):
    place(blip([990, 1180, 1320, 1480][i]), td, -25)
    place(swell(0.3, 1500, 6000), td, -36)
# the card closes into the mark; the wave draws; the name types; the period pops
place(swell(0.35, 500, 4000), T['mark'] - 0.05, -30)
place(thud(), T['mark'] + 0.3, -20)
place(pop(), T['mark'] + 0.3, -24)
place(tone(660, 990, 0.25, 0.08), T['icon'], -28)
place(pop(), T['word'] - 0.1, -24)
for i in range(1, len('Kardiograph') + 1):
    place(tick(), T['word'] + i * 2 / 30, -30)

peak = np.max(np.abs(out))
if peak > 0.89:
    out *= 0.89 / peak
pcm = (out[: int(SR * DUR)] * 32767).astype(np.int16)
os.makedirs(os.path.join(RM, 'public/sfx'), exist_ok=True)
with wave.open(os.path.join(RM, 'public/sfx/sfx.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'sfx.wav {len(pcm) / SR:.1f} s, peak {20 * np.log10(max(peak, 1e-9)):.1f} dBFS')
