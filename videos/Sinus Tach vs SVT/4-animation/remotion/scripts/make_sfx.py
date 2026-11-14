#!/usr/bin/env python3
"""Synthesizes the plugs' simple sounds into public/sfx/ (48 kHz, 16-bit, stereo WAV). Deterministic.

    python3 scripts/make_sfx.py

pop        soft landing hit (a short rounded thump), for a key landing
pop-soft   lighter, higher landing hit, for secondary landings
click      a mouse click (press, then release 75 ms later)
chime      two-note "correct" chime for the score

Levels are set against v8: its VO sits at -23 LUFS and its intro sounds peak near -15 dBFS, so these peak
between -14 (the click, which is very short) and -22 dBFS. Mark asked for sounds on the plugs (Nov 14, 2026).
"""
import pathlib
import wave

import numpy as np

SR = 48000
OUT = pathlib.Path(__file__).resolve().parent.parent / 'public' / 'sfx'
rng = np.random.default_rng(7)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def env(t, attack, tau):
    a = np.clip(t / attack, 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / tau)


def sweep(t, f0, f1, dur):
    f = f1 + (f0 - f1) * np.exp(-t / (dur / 3))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def lowpass(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def peak_to(x, dbfs):
    return x / np.max(np.abs(x)) * 10 ** (dbfs / 20)


def pop(f0, f1, dbfs, dur=0.25):
    t = t_axis(dur)
    body = sweep(t, f0, f1, 0.07) * env(t, 0.003, 0.035)
    over = sweep(t, 2 * f0, 2 * f1, 0.05) * env(t, 0.002, 0.015) * 0.2
    return peak_to(body + over, dbfs)


def click_part(t, pitch, amp):
    noise = rng.standard_normal(len(t))
    hp = np.diff(noise, prepend=0.0)  # high-passed noise: the plastic tick
    tick = lowpass(hp, 7000) * env(t, 0.0003, 0.0016)
    ping = np.sin(2 * np.pi * pitch * t) * env(t, 0.0003, 0.004) * 0.5
    body = np.sin(2 * np.pi * 900 * t) * env(t, 0.0005, 0.008) * 0.35
    return amp * (tick + ping + body)


def click(dbfs=-14):
    t = t_axis(0.2)
    x = click_part(t, 2800, 1.0)
    off = int(0.075 * SR)
    x[off:] += click_part(t[: len(t) - off], 3300, 0.6)
    return peak_to(x, dbfs)


def chime(dbfs=-20):
    t = t_axis(1.1)
    x = np.zeros_like(t)
    for f, start in [(1046.5, 0.0), (1568.0, 0.09)]:
        tt = np.maximum(t - start, 0)
        on = (t >= start).astype(float)
        x += on * (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(2 * np.pi * 2.0 * f * tt)) * env(tt, 0.004, 0.32)
    return peak_to(x, dbfs)


def write(name, x):
    OUT.mkdir(parents=True, exist_ok=True)
    fade = min(len(x), int(0.01 * SR))
    x = x.copy()
    x[-fade:] *= np.linspace(1, 0, fade)
    pcm = (np.clip(x, -1, 1) * 32767).astype('<i2')
    st = np.repeat(pcm[:, None], 2, axis=1)
    with wave.open(str(OUT / f'{name}.wav'), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(st.tobytes())
    print(name, f'{len(x) / SR:.2f} s')


write('pop', pop(520, 260, -18))
write('pop-soft', pop(640, 340, -22))
write('click', click())
write('chime', chime())
