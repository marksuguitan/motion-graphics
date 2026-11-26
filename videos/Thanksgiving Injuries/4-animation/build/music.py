#!/usr/bin/env python3
"""music.py: the music bed for Thanksgiving Injuries, synthesized, so nothing is downloaded or licensed.

Mark asked (Nov 25, 2026) for low-volume background music with the feel of a laid-back, downtempo lounge
breakbeat. This is an original piece in that feel: swung break, round bass, electric-piano chords (ii-V-iii-VI in C)
and a small vibraphone figure. It is written to the picture: the first chord lands with the plate, the beat comes
in on the knife chop, it thins out under the rhythm strip so the monitor beeps read, and it fades under the end screen.

Reads 4-animation/remotion/src/data/timeline.json, writes 4-animation/remotion/public/sfx/music.wav (48 kHz stereo,
peak -3 dBFS). Its level in the mix is MUSIC_GAIN in src/Video.tsx. Re-run after any timeline change:  python3 music.py
"""
import json
import os
import wave

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RM = os.path.join(os.path.dirname(HERE), 'remotion')
TL = json.load(open(os.path.join(RM, 'src/data/timeline.json')))
EV = TL['ev']
SR = 48000
DUR = TL['total']
N = int(SR * (DUR + 0.5))
rng = np.random.default_rng(11)

# Tempo from the picture: 8 beats from the plate landing to the knife chop (100 bpm with the v2 timeline).
T0 = EV['s1']['land']
BEAT = (EV['s2']['chop'] - T0) / 8
if not 0.52 <= BEAT <= 0.72:
    BEAT = 0.6
BAR = 4 * BEAT
STEP = BAR / 16
SWING = 0.17  # the off 16ths sit late
ES = TL['endScreen']['start']

dry = np.zeros((2, N))
send = np.zeros((2, N))  # reverb send
stems = {}  # mono sums per voice, only to report the balance


def db(x):
    return 10 ** (x / 20)


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def put(sig, t, gain_db, pan=0.0, rev=-14.0, stem=''):
    """sig mono or (2, n). pan -1..1. rev = send level in dB relative to the dry signal."""
    i = int(round(t * SR))
    if i < 0 or i >= N:
        return
    if sig.ndim == 1:
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        sig = np.stack([sig * l, sig * r]) * np.sqrt(2) / 1.0
    n = min(sig.shape[1], N - i)
    g = db(gain_db)
    dry[:, i:i + n] += sig[:, :n] * g
    send[:, i:i + n] += sig[:, :n] * g * db(rev)
    stems.setdefault(stem, np.zeros(N, dtype=np.float32))[i:i + n] += sig[:, :n].mean(0) * g


def step_t(bar, step):
    return T0 + bar * BAR + step * STEP + (SWING * STEP if step % 2 else 0)


def band(n, lo, hi, r=rng):
    X = np.fft.rfft(r.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    X[(fr < lo) | (fr > hi)] = 0
    x = np.fft.irfft(X, n)
    return x / (np.max(np.abs(x)) + 1e-9)


# ---------- voices ----------
def keys_note(m, dur, vel=1.0):
    """Electric piano: a two-operator FM tine, slightly detuned left and right."""
    n = int((dur + 0.25) * SR)
    t = np.arange(n) / SR
    out = []
    for cents in (-4, 4):
        f = hz(m) * 2 ** (cents / 1200)
        idx = (1.8 * vel) * np.exp(-t / 0.22) + 0.22
        body = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
        tine = 0.10 * vel * np.sin(2 * np.pi * f * 7.02 * t) * np.exp(-t / 0.05)
        out.append(body + tine)
    a = np.clip(t / 0.004, 0, 1) * np.exp(-t / 1.5)
    rel = np.clip((dur + 0.25 - t) / 0.25, 0, 1)
    trem = 0.18 * np.sin(2 * np.pi * 4.6 * t)  # slow auto-pan
    return np.stack([out[0] * (1 - trem), out[1] * (1 + trem)]) * a * rel * vel


def bass_note(m, dur, vel=1.0):
    n = int((dur + 0.08) * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) * np.exp(-t / 0.25) + 0.12 * np.sin(6 * np.pi * f * t) * np.exp(-t / 0.12)
    s = np.tanh(1.4 * s) / np.tanh(1.4)
    a = np.clip(t / 0.008, 0, 1) * np.exp(-t / 0.9) * np.clip((dur + 0.08 - t) / 0.08, 0, 1)
    return s * a * vel


def vibe_note(m, dur=0.9, vel=1.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    s = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * 4 * f * t) * np.exp(-t / 0.06)
    return s * np.clip(t / 0.003, 0, 1) * np.exp(-t / 0.28) * (1 + 0.25 * np.sin(2 * np.pi * 5.5 * t)) * vel


def kick(vel=1.0):
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    f = 46 + 90 * np.exp(-t / 0.03)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.11)
    return (s + 0.25 * band(n, 600, 3000) * np.exp(-t / 0.004)) * vel


def snare(vel=1.0):
    n = int(0.22 * SR)
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(185 + 60 * np.exp(-t / 0.02)) / SR) * np.exp(-t / 0.06)
    return (0.55 * body + band(n, 700, 5500) * np.exp(-t / (0.05 + 0.03 * vel))) * vel


def hat(vel=1.0, opened=False):
    n = int((0.22 if opened else 0.06) * SR)
    t = np.arange(n) / SR
    return band(n, 4500, 8500) * np.exp(-t / (0.07 if opened else 0.014)) * vel


# ---------- the tune: ii-V-iii-VI in C, one bar each ----------
CHORDS = [
    {'bass': 38, 'fifth': 45, 'keys': [53, 57, 60, 64]},  # Dm9
    {'bass': 43, 'fifth': 38, 'keys': [53, 57, 59, 64]},  # G13
    {'bass': 40, 'fifth': 47, 'keys': [55, 59, 62, 64]},  # Em7
    {'bass': 45, 'fifth': 40, 'keys': [55, 61, 65, 69]},  # A7(b13)
]
COMP = [[(0, 5, 1.0), (6, 1.2, 0.7), (11, 1.2, 0.55)], [(0, 6, 1.0), (7, 1.2, 0.6), (10, 2.5, 0.7)]]  # (step, length in steps, velocity)
# (step, which note, length, velocity). 'app' = a half step under the next bar's root.
BASSLINE = [[(0, 'root', 2.6, 1.0), (3, 'root', 0.9, 0.6), (6, 'oct', 1.2, 0.75), (10, 'fifth', 1.6, 0.8), (14, 'app', 1.6, 0.75)],
            [(0, 'root', 2.6, 1.0), (4, 'oct', 0.9, 0.55), (7, 'root', 1.4, 0.75), (10, 'fifth', 1.6, 0.8), (13, 'root', 0.9, 0.6), (15, 'app', 0.9, 0.7)]]
KICKS = [[(0, 1.0), (7, 0.6), (10, 0.9)], [(0, 1.0), (3, 0.5), (10, 0.9), (11, 0.55)]]
SNARES = [[(4, 1.0), (12, 1.0), (15, 0.3)], [(4, 1.0), (7, 0.28), (9, 0.3), (12, 1.0)]]
# vibraphone answer, two bars, over Dm9 and G13 (every second time round)
VIBE = [[(2, 69), (5, 72), (8, 74)], [(2, 76), (6, 74), (9, 72), (12, 69)]]

S6, S7 = EV['s6'], EV['s7']
nbars = int(np.ceil((DUR - T0) / BAR))
for b in range(nbars):
    tb = T0 + b * BAR
    ch, nxt = CHORDS[b % 4], CHORDS[(b + 1) % 4]
    intro = tb < EV['s2']['chop'] - 0.01
    outro = tb >= ES - BAR * 0.4
    thin = (not outro) and tb >= S6['line'] - 0.5 and tb + BAR <= S7['clear'] + 0.6  # under the rhythm strip
    hum = lambda: rng.uniform(-0.004, 0.004)

    # keys
    comp = [(0, 12, 0.9)] if intro or outro else COMP[b % 2]
    for st, ln, v in comp:
        for k, m in enumerate(ch['keys']):
            put(keys_note(m, ln * STEP, v * (0.9 if k else 1.0)), step_t(b, st) + hum() + 0.006 * k, -19, rev=-10, stem='keys')

    # bass (enters with the beat)
    if not intro:
        line = [(0, 'root', 6, 0.9), (10, 'fifth', 3, 0.7)] if (thin or outro) else BASSLINE[b % 2]
        for st, which, ln, v in line:
            m = {'root': ch['bass'], 'oct': ch['bass'] + 12, 'fifth': ch['fifth'], 'app': nxt['bass'] - 1}[which]
            put(bass_note(m, ln * STEP, v), step_t(b, st) + hum(), -18, rev=-40, stem='bass')

    # drums
    if not intro and not outro:
        if not thin:
            for st, v in KICKS[b % 2]:
                put(kick(v), step_t(b, st) + hum(), -16, rev=-40, stem='kick')
            for st, v in SNARES[b % 2]:
                put(snare(v), step_t(b, st) + hum() + 0.008, -19 if v > 0.5 else -23, pan=0.08, rev=-12, stem='snare')
        for st in range(16):
            v = (1.0 if st % 4 == 2 else 0.7 if st % 2 == 0 else 0.35) * rng.uniform(0.85, 1.0)
            if thin and st % 2:
                continue
            opened = st == 14 and b % 4 == 3 and not thin
            put(hat(v, opened), step_t(b, st) + hum(), -25, pan=0.3, rev=-16, stem='hat')
    elif intro and b == 1:
        for st, v in [(13, 0.3), (14, 0.45), (15, 0.6)]:  # pickup into the chop
            put(snare(v), step_t(b, st), -23, pan=0.08, rev=-12, stem='snare')

    # vibraphone answer with a dotted-eighth echo
    if not intro and not outro and b % 8 in (4, 5):
        for st, m in VIBE[b % 2]:
            for e, (g, pan) in enumerate([(0, -0.35), (-9, 0.4), (-16, -0.4)]):
                put(vibe_note(m, vel=0.9), step_t(b, st) + e * 3 * STEP, -22 + g, pan=pan, rev=-8, stem='vibe')

# ---------- room: a short, dark reverb (noise impulse response) ----------
nir = int(1.3 * SR)
tir = np.arange(nir) / SR
wet = np.zeros((2, N))
for c in range(2):
    ir = band(nir, 250, 4500, np.random.default_rng(100 + c)) * np.exp(-tir / 0.32)
    L = N + nir
    wet[c] = np.fft.irfft(np.fft.rfft(send[c], L) * np.fft.rfft(ir, L), L)[:N]
wet *= 0.5 / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(send))
mixd = dry + wet

# ---------- master: keep it soft and behind the effects (gentle top roll-off), fades, level ----------
X = np.fft.rfft(mixd, axis=1)
fr = np.fft.rfftfreq(N, 1 / SR)
X *= 1 / np.sqrt(1 + (fr / 6500) ** 4)  # low-pass around 6.5 kHz
X *= (fr / 32) ** 2 / np.sqrt(1 + (fr / 32) ** 4)  # high-pass around 32 Hz
mixd = np.fft.irfft(X, N, axis=1)
t = np.arange(N) / SR
fade = np.clip(t / 0.05, 0, 1) * np.clip((DUR - t) / 5.0, 0, 1) ** 1.5
mixd *= fade
mixd = np.tanh(mixd / (np.max(np.abs(mixd)) + 1e-9) * 1.25) / np.tanh(1.25)  # a touch of glue
mixd *= db(-3) / np.max(np.abs(mixd))

pcm = (mixd.T * 32767).astype(np.int16)
os.makedirs(os.path.join(RM, 'public/sfx'), exist_ok=True)
with wave.open(os.path.join(RM, 'public/sfx/music.wav'), 'wb') as w:
    w.setnchannels(2)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
body = mixd[:, int(8 * SR):int((ES - 1) * SR)]
print(f'music.wav {N / SR:.1f} s, {60 / BEAT:.1f} bpm, {nbars} bars, peak -3 dBFS, RMS {20 * np.log10(np.sqrt(np.mean(body ** 2))):.1f} dBFS (scenes)')
a, b_ = int(10.6 * SR), int(29.8 * SR)
print('stem RMS / peak over 10.6-29.8 s (pre-master): ' + ', '.join(f"{k} {20 * np.log10(np.sqrt(np.mean(v[a:b_] ** 2)) + 1e-9):.1f}/{20 * np.log10(np.max(np.abs(v[a:b_])) + 1e-9):.1f}" for k, v in stems.items()))
