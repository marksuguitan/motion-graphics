# Synthesizes the logo-dash sound effect from the same motion timeline as src/intromotion.ts.
# Layers: whoosh (filtered noise riding the speed curve, panned with x), a soft "bloop" at
# the morph (top speed), and a weighted thump + rubbery wobble on the sudden stop.
import numpy as np, subprocess
SR = 48000
hold, push, slide, friction, stop, recoilT = 1.2, 0.16, 0.3, 0.3, 0.05, 0.14
tPeak = hold + push; tStop = tPeak + slide; tStopEnd = tStop + stop
DUR = 3.0
t = np.arange(int(DUR * SR)) / SR
rng = np.random.default_rng(7)

def vunit(x):
    v = np.zeros_like(x)
    m = (x >= hold) & (x < tPeak); u = (x[m] - hold) / push; v[m] = 1 - (1 - u) ** 2
    m = (x >= tPeak) & (x < tStop); v[m] = 1 - friction * (x[m] - tPeak) / slide
    m = (x >= tStop) & (x < tStopEnd); u = (x[m] - tStop) / stop; v[m] = (1 - friction) * (1 - u) ** 2
    return v

# 1. whoosh: noise through a resonant band-pass whose centre rises with speed
spd = vunit(t)
env = np.convolve(spd, np.ones(int(0.012 * SR)) / int(0.012 * SR), 'same')  # soften edges
noise = rng.standard_normal(len(t))
fc = 300 + 2600 * env ** 1.3
q = 1.6
lp = bp = 0.0; wh = np.zeros(len(t))
i0, i1 = int((hold - 0.02) * SR), int((tStopEnd + 0.12) * SR)
for i in range(i0, i1):  # state-variable filter
    f = 2 * np.sin(np.pi * fc[i] / SR)
    hp = noise[i] - lp - bp / q
    bp += f * hp; lp += f * bp
    wh[i] = bp
tail = np.exp(-np.clip(t - tStopEnd, 0, None) / 0.035)  # quick air tail after the stop
wh *= (env ** 1.5) * np.where(t > tStopEnd, tail, 1.0)
wh /= np.abs(wh).max() + 1e-9
wh *= 0.55

# 2. morph bloop at top speed: short rising sine with a soft attack
k = t - (tPeak - 0.012)
m = k > 0
f0 = 420 + 760 * (1 - np.exp(-np.clip(k, 0, None) / 0.018))
ph = 2 * np.pi * np.cumsum(f0) / SR
bl = np.where(m, np.sin(ph) + 0.25 * np.sin(2 * ph), 0) * np.where(m, (1 - np.exp(-k / 0.003)) * np.exp(-k / 0.04), 0)
bl *= 0.42

# 3. stop: low thump with a pitch drop, a muffled click, and a rubbery wobble on the squash
k = t - tStop
m = k > 0
fT = 55 + 75 * np.exp(-np.clip(k, 0, None) / 0.03)
phT = 2 * np.pi * np.cumsum(np.where(m, fT, 0)) / SR
th = np.where(m, np.sin(phT) * (1 - np.exp(-k / 0.002)) * np.exp(-k / 0.11), 0) * 0.9
click = np.where(m, rng.standard_normal(len(t)) * np.exp(-k / 0.004), 0)
click = np.convolve(click, np.ones(24) / 24, 'same') * 0.6  # muffled
wob = np.where(m, np.sin(2 * np.pi * 150 * k) * np.exp(-k / 0.09) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * k)), 0) * 0.22
st = th + click + wob

# pan the whoosh with the cell's x (960 centre → 1380, slightly right)
xpos = 960 + 420 * np.clip(np.cumsum(spd) / max(np.cumsum(spd)[-1], 1e-9), 0, 1)
pan = (xpos - 960) / 960  # 0 .. ~0.44
L = wh * np.cos((pan + 1) * np.pi / 4) + (bl + st) * np.cos((pan[int(tStop * SR)] + 1) * np.pi / 4)
R = wh * np.sin((pan + 1) * np.pi / 4) + (bl + st) * np.sin((pan[int(tStop * SR)] + 1) * np.pi / 4)
mixd = np.stack([L, R], 1)
mixd *= 10 ** (-7 / 20) / np.abs(mixd).max()  # peak -7 dBFS
fade = np.clip((DUR - t) / 0.05, 0, 1)[:, None]
mixd *= fade
subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', '-', 'public/sfx_logo.wav'],
               input=mixd.astype(np.float32).tobytes(), check=True)
print('wrote public/sfx_logo.wav', 'peak', tPeak, 'stop', tStop)
