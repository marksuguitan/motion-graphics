#!/usr/bin/env python3
"""timeline.py: the timing for Thanksgiving Injuries (no VO), written to remotion/src/data/timeline.json.

With no voice-over there are no word timings. Each card's time on screen comes from the production guide's
reading-time rule (at least 2.5 s, or 1 s plus 1 s per 3 words, whichever is longer) plus a small margin, and
every action and sound effect is placed relative to those times. The picture (src/) and the sound
(build/sfx.py) both read this one file, so they can't drift apart.  Run:  python3 timeline.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'remotion/src/data/timeline.json')

ROLL_IN = 0.3   # new rows roll into place (snap and settle)
ROLL_OUT = 0.25  # old rows roll out (accelerate)
HOLD = 0.1      # after the last card of a scene; its rows roll out while the next scene's first move starts
END_SCREEN = 15.0
TITLE = 'Five ways the feast ends in the ER'
TYPE_CHAR = 0.05  # s per typed character
TITLE_HOLD = 1.8  # fully typed, before it is erased
ERASE = 0.7       # erased right to left; the plate leaves for the knife scene while it goes


def read_min(words):
    """v2 (Mark, Nov 25, 2026: tighter, less dead time). Was max(2.5, 1 + words / 3)."""
    return max(2.4, 0.8 + 0.3 * words)


# (scene, pre-action before its first card, [(beat, words that are read (no kicker, no citation), pre-action before this
#  card, extra read time where the picture carries the point too)], hold)
SCENES = [
    ('s2', 1.2, [('2A', 10, 0, 0)], HOLD),
    ('s3', 1.0, [('3A', 7, 0, 0.4), ('3B', 10, 0, 0)], HOLD),
    ('s4', 1.55, [('4A', 9, 0, 0), ('4B', 9, 0, 0), ('4C', 12, 0.75, 0)], HOLD),
    ('s5', 0.95, [('5A', 6, 0, 0.4), ('5B', 10, 0, 0), ('5C', 7, 0, 0)], HOLD),
    ('s6', 1.3, [('6A', 7, 0, 0.3), ('6B', 13, 0, 0)], HOLD),
    ('s7', 0.9, [('7A', 3, 0, 0)], 0.5),
]

scenes, cards, table = {}, {}, []
# scene 1: the plate lands, the title types on, holds, and is erased; the erase is the way into scene 2
type_on = 1.0
typed = type_on + len(TITLE) * TYPE_CHAR
erase = typed + TITLE_HOLD
t = erase + 0.1
scenes['s1'] = {'start': 0.0, 'end': round(t, 3)}
cards['1A'] = {'on': type_on, 'landed': round(typed, 3), 'off': round(erase, 3), 'words': 8, 'min': TITLE_HOLD}
for name, pre, items, hold in SCENES:
    s0 = t
    t += pre
    for k, (beat, words, extra, more) in enumerate(items):
        t += extra
        on = t
        landed = on + (ROLL_IN if k else 0)
        need = round(read_min(words) + more, 2)
        off = landed + need  # rows start to leave here
        cards[beat] = {'on': round(on, 3), 'landed': round(landed, 3), 'off': round(off, 3), 'words': words, 'min': need}
        table.append((beat, words, need))
        t = off + (ROLL_OUT if k + 1 < len(items) else 0)
    t += hold
    scenes[name] = {'start': round(s0, 3), 'end': round(t, 3)}
    # the last card's rows leave at the scene end
    cards[items[-1][0]]['off'] = round(t, 3)

end_start = t
total = t + END_SCREEN
S = {k: v['start'] for k, v in scenes.items()}
C = cards

# --- events every scene and the SFX share (seconds of video time) ---
ev = {}
ev['s1'] = {'grow': 0.1, 'rise': 0.35, 'land': 1.0, 'type': type_on, 'typed': typed, 'erase': erase, 'erased': erase + ERASE,
            'title': TITLE, 'charDur': TYPE_CHAR}
ev['s2'] = {'anti': S['s2'], 'move': S['s2'] + 0.2, 'board': S['s2'] + 0.6, 'swish': S['s2'] + 0.75, 'chop': C['2A']['on']}
ev['s3'] = {'morph': S['s3'], 'skin': S['s3'] + 0.3, 'bubbles': S['s3'] + 0.45, 'pop': C['3A']['on'],
            'drop': C['3A']['on'] + 0.7, 'water': C['3B']['on'] + 0.1}
a, b4, c4 = C['4A']['on'], C['4B']['on'], C['4C']['on']
ev['s4'] = {'clear': S['s4'], 'card': S['s4'] + 0.3, 'bite': S['s4'] + 0.45, 'toss': a - 0.85, 'mouth': a - 0.45, 'biteLand': a,
            'thrust1': b4 + 0.4, 'thrust2': b4 + 0.95, 'expel': b4 + 1.03, 'out': b4 + 1.48, 'back': b4 + 1.9,
            'toss2': c4 - 1.0, 'mouth2': c4 - 0.6, 'lodge': c4}
ev['s5'] = {'clear': S['s5'], 'dish': S['s5'], 'cover': S['s5'] + 0.5, 'lid': C['5A']['on'] - 0.15, 'spores': C['5A']['on'] + 0.2,
            'shield': C['5A']['on'] + 0.7, 'clock': C['5B']['on'] + 0.05, 'gens': [C['5B']['on'] + 0.4 + 0.55 * i for i in range(4)],
            'months': C['5C']['on'] + 0.05, 'peak': C['5C']['on'] + 0.65}
ev['s6'] = {'clear': S['s6'], 'glass': S['s6'], 'line': S['s6'] + 0.85, 'write': S['s6'] + 1.2, 'convert': C['6B']['on'] + 1.5,
            'chips': C['6B']['on'] + 0.35, 'stripEnd': scenes['s6']['end'] + 0.5}
ev['s7'] = {'clear': S['s7'], 'grow': S['s7'] + 0.2, 'land': C['7A']['on'], 'icons': C['7A']['on'] + 0.1}
ev['end'] = {'start': end_start, 'mark': end_start + 0.45}
for k in ev:
    for kk, v in ev[k].items():
        if isinstance(v, float):
            ev[k][kk] = round(v, 3)
        elif isinstance(v, list):
            ev[k][kk] = [round(x, 3) for x in v]
# The rhythm strip itself (samples and QRS times) comes from Kardiograph's engine: build/kardiograph_strip.ts,
# run after this file, writes src/data/strip.json from ev.s6.write / convert / stripEnd.

doc = {
    'note': 'Generated by 4-animation/build/timeline.py. Seconds of video time. Card times follow the reading-time rule; actions and SFX are placed from them.',
    'fps': 30, 'total': round(total, 3), 'endScreen': {'start': round(end_start, 3), 'dur': END_SCREEN},
    'scenes': scenes, 'cards': cards, 'ev': ev,
}
json.dump(doc, open(OUT, 'w'), indent=1)
print(f'scenes end {end_start:.2f} s, total {total:.2f} s ({int(total // 60)}:{total % 60:05.2f})')
for name, v in scenes.items():
    print(f"  {name} {v['start']:6.2f} - {v['end']:6.2f}")
print('beat words read-time')
for row in table:
    print('  ', *row)

# beats.json / video.json / sync.json for the review overlay and check.mjs (lead 0: video time = track time)
D = os.path.dirname(OUT)
beats = []
order = ['1A'] + [b for _, _, items, _ in SCENES for b, _, _, _ in items]
for i, b in enumerate(order):
    st = cards[b]['on'] if i else 0.0
    # a scene's first beat starts with the scene (its pre-action belongs to it)
    for name, pre, items, hold in SCENES:
        if items[0][0] == b:
            st = scenes[name]['start']
    if b == '1A':
        st = 0.0
    beats.append({'id': b, 'start': round(st, 3)})
beats.append({'id': 'END', 'start': round(end_start, 3)})
for i, b in enumerate(beats):
    b['end'] = beats[i + 1]['start'] if i + 1 < len(beats) else round(total, 3)
    b['dur'] = round(b['end'] - b['start'], 3)
json.dump(beats, open(os.path.join(D, 'beats.json'), 'w'), indent=1)
json.dump([], open(os.path.join(D, 'sync.json'), 'w'))
json.dump([], open(os.path.join(D, 'words.json'), 'w'))
json.dump({'title': 'Thanksgiving Injuries', 'lead': 0, 'tail': 0, 'trackDur': round(total, 3), 'fps': 30}, open(os.path.join(D, 'video.json'), 'w'), indent=1)
