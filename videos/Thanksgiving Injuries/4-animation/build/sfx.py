#!/usr/bin/env python3
"""sfx.py: the sound-effects track for Thanksgiving Injuries (no VO), synthesized, so nothing is downloaded.

Reads 4-animation/remotion/src/data/timeline.json (the same times the picture uses) and writes
4-animation/remotion/public/sfx/sfx.wav (48 kHz mono). Comma Clinical: soft and sparse, a hit on a landing or an
event, a whoosh only under a big move. Nothing under the end screen. Re-run after any timeline change:  python3 sfx.py
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RM = os.path.join(os.path.dirname(HERE), 'remotion')
TL = json.load(open(os.path.join(RM, 'src/data/timeline.json')))
EV, CARDS = TL['ev'], TL['cards']
SR = 48000
DUR = TL['total']
out = np.zeros(int(SR * (DUR + 0.5)))
rng = np.random.default_rng(7)


def db(x):
    return 10 ** (x / 20)


def place(sig, t, gain_db):
    i = int(round(t * SR))
    if i >= len(out) or t >= TL['endScreen']['start']:
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


def band(n, lo, hi):
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(X, n)
    return x / (np.max(np.abs(x)) + 1e-9)


def noise(dur, lo, hi, attack, decay):
    n = int(dur * SR)
    return band(n, lo, hi) * env(n, attack, decay)


def swell(dur, lo, hi, rise=True):
    n = int(dur * SR)
    x = band(n, lo, hi)
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


def bell(partials, dur, decay):
    """Inharmonic struck object (ceramic, glass, metal): partials as (freq, amp, decay scale)."""
    return mix(*[a * tone(f, f * 0.998, dur, decay * d) for f, a, d in partials])


clink = lambda: mix(bell([(2150, 1, 1), (3420, 0.6, 0.7), (5230, 0.35, 0.5), (1210, 0.3, 1.3)], 0.6, 0.18), 0.25 * noise(0.02, 2000, 9000, 0.0005, 0.004))
clink_low = lambda: mix(bell([(1480, 1, 1), (2410, 0.55, 0.7), (3720, 0.3, 0.5)], 0.6, 0.16), 0.3 * tone(180, 120, 0.15, 0.04))
glass = lambda: bell([(3180, 1, 1), (4690, 0.6, 0.8), (6950, 0.3, 0.6)], 0.9, 0.3)
tonk = lambda: mix(bell([(610, 1, 1), (1370, 0.5, 0.6), (2240, 0.25, 0.4)], 0.6, 0.14), 0.3 * noise(0.03, 300, 3000, 0.001, 0.01))
pop = lambda: tone(520, 260, 0.18, 0.05)
tick = lambda: mix(0.6 * tone(2400, 2200, 0.03, 0.006), 0.4 * noise(0.02, 2000, 7000, 0.0005, 0.004))
blip = lambda f=1320: tone(f, f * 1.02, 0.12, 0.035)
thud = lambda: mix(tone(110, 55, 0.35, 0.09), 0.3 * noise(0.05, 80, 400, 0.001, 0.02))
knock = lambda: mix(tone(230, 170, 0.2, 0.05), 0.5 * noise(0.05, 300, 1800, 0.001, 0.015))
chop = lambda: mix(tone(170, 90, 0.25, 0.06), 0.7 * noise(0.06, 250, 2500, 0.0005, 0.018), 0.15 * tone(3100, 3000, 0.1, 0.02))
huff = lambda: mix(noise(0.22, 180, 1400, 0.01, 0.06), 0.5 * tone(120, 80, 0.15, 0.04))
beep = lambda: tone(960, 960, 0.1, 0.06, attack=0.004)
whoosh = lambda d=0.6: swell(d, 250, 2200)
swish = lambda: swell(0.28, 1200, 6000)


def crackle(dur, rate, lo=2500, hi=9000):
    """Hot-oil sizzle: a bed of hiss with random crackles (a running process)."""
    n = int(dur * SR)
    bed = band(n, 3000, 10000) * 0.18
    clicks = np.zeros(n)
    k = int(dur * rate)
    for i in rng.integers(0, n - 400, k):
        c = noise(0.006, lo, hi, 0.0002, 0.0015)
        clicks[i:i + len(c)] += c * rng.uniform(0.3, 1.0)
    fade = np.minimum(1, np.arange(n) / (0.25 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.2 * SR))
    return (bed + clicks) * fade


def water(dur):
    n = int(dur * SR)
    x = band(n, 300, 3500)
    am = 0.75 + 0.25 * np.convolve(rng.standard_normal(n), np.ones(600) / 600, mode='same') * 8
    fade = np.minimum(1, np.arange(n) / (0.15 * SR)) * np.minimum(1, (n - np.arange(n)) / (0.2 * SR))
    return x * np.clip(am, 0.2, 1.3) * fade


STRIP = json.load(open(os.path.join(RM, 'src/data/strip.json')))


def count_ticks(t0, dur=0.9, gain=-36):
    """A number counting up: ticks that slow down as it settles."""
    k = 0
    while True:
        tt = dur * (1 - (1 - k / 12) ** 2) if k < 12 else None
        if tt is None:
            break
        place(tick(), t0 + tt * 0.8, gain)
        k += 1


# ---- scene 1: the plate grows, hops, lands; the title types on, then is erased as the plate leaves
s = EV['s1']
place(tone(300, 600, 0.25, 0.08), s['grow'], -28)
place(clink(), s['land'], -17)
for i, ch in enumerate(s['title']):
    if ch != ' ':
        place(tick(), s['type'] + i * s['charDur'], -31 + rng.uniform(-2, 1))
n_ch = len(s['title'])
for i in range(0, n_ch, 2):  # erased from the end, speeding up
    place(tick(), s['erase'] + (s['erased'] - s['erase']) * (i / n_ch) ** (1 / 1.5), -34)
place(swell(s['erased'] - s['erase'], 1500, 7000), s['erase'], -36)
# ---- scene 2: the plate becomes the knife; board; swing and chop
s = EV['s2']
place(whoosh(0.7), s['move'] - 0.05, -30)
place(knock(), s['board'] + 0.25, -24)
place(swish(), s['swish'] + 0.2, -28)
place(chop(), s['chop'], -13)
count_ticks(CARDS['2A']['on'] + 0.05)
# ---- scene 3: pot, sizzle, the pop of oil, running water
s = EV['s3']
place(whoosh(0.5), s['morph'] - 0.05, -32)
place(tonk(), s['morph'] + 0.45, -22)
place(crackle(EV['s4']['clear'] - s['bubbles'], 22), s['bubbles'], -30)
place(mix(noise(0.03, 1500, 8000, 0.0003, 0.008), 0.6 * tone(900, 500, 0.08, 0.02)), s['pop'], -16)
place(crackle(0.6, 60, 3000, 10000), s['drop'], -24)
place(water(EV['s4']['clear'] - s['water'] + 0.1), s['water'], -27)
count_ticks(CARDS['3B']['on'] + 0.1, 0.8)
# ---- scene 4: choking, abdominal thrusts, food stuck in the esophagus
s = EV['s4']
place(swell(0.45, 400, 3000, rise=False), s['clear'], -32)
place(clink_low(), s['clear'] + 0.6, -24)
place(swell(0.5, 200, 1500), s['card'], -34)
place(pop(), s['bite'] + 0.1, -28)
place(swish(), s['toss'], -32)
place(thud(), s['biteLand'], -18)
place(blip(660), s['biteLand'] + 0.05, -28)
count_ticks(CARDS['4A']['on'] + 0.05)
for tp in (s['thrust1'], s['thrust2']):
    place(huff(), tp, -20)
place(pop(), s['expel'] + 0.05, -20)
place(blip(1320), s['out'], -28)
place(tick(), s['back'], -26)
place(pop(), s['back'], -30)
place(swish(), s['toss2'], -34)
place(thud(), s['lodge'], -15)
count_ticks(CARDS['4C']['on'] + 0.35, 0.8, -38)
# ---- scene 5: C. perfringens
s = EV['s5']
place(swell(0.45, 400, 3000, rise=False), s['clear'], -32)
place(whoosh(0.6), s['dish'] - 0.05, -32)
place(clink_low(), s['dish'] + 0.65, -22)
place(glass(), s['lid'] + 0.1, -30)
for i in range(5):
    place(tick(), s['spores'] + i * 2 / 30 + 0.1, -32)
place(pop(), s['shield'] + 0.15, -26)
place(pop(), s['clock'] + 0.15, -26)
# clock ticks follow the hand: denser while it spins fast
t0 = s['clock'] + 0.2
for k in range(1, 26):
    tt = t0 + 2.6 * (1 - (1 - k / 26) ** 0.5)
    place(tick(), tt, -34)
for i, tg in enumerate(s['gens']):
    place(blip([880, 990, 1110, 1320][i]), tg + 0.05, -26)
for i in range(12):
    place(tick(), s['months'] + i * 2 / 30 + 0.12, -36)
place(pop(), s['peak'] + 0.1, -22)
place(blip(1320), s['peak'] + 0.18, -28)
# ---- scene 6: holiday heart. One monitor beep per QRS of the Kardiograph strip (R peak ~40 ms after onset)
s = EV['s6']
place(swell(0.45, 400, 3000, rise=False), s['clear'], -32)
place(glass(), s['glass'] + 0.3, -24)
place(swell(0.5, 600, 4000), s['line'] - 0.05, -32)
for q in STRIP['qrs']:
    tq = s['write'] + q['t'] + 0.04
    if tq < EV['s7']['clear']:
        place(beep(), tq, -26)
count_ticks(CARDS['6B']['on'] + 0.05, 0.8, -38)
for i in range(2):
    place(pop(), s['chips'] + i * 2 / 30 + 0.15, -26)
# ---- scene 7: back to the plate
s = EV['s7']
place(swell(0.35, 500, 4000, rise=False), s['clear'], -32)
place(tone(300, 600, 0.3, 0.09), s['grow'], -28)
place(clink(), s['land'], -17)
for i in range(5):
    place(tick(), s['icons'] + i * 2 / 30 + 0.12, -30)

# normalize to -1 dBFS peak and write
peak = np.max(np.abs(out))
out *= 0.89 / peak
pcm = (out * 32767).astype(np.int16)
os.makedirs(os.path.join(RM, 'public/sfx'), exist_ok=True)
with wave.open(os.path.join(RM, 'public/sfx/sfx.wav'), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f'sfx.wav {len(out) / SR:.1f} s, raw peak {20 * np.log10(max(peak, 1e-9)):.1f} dBFS, normalized to -1 dBFS')
