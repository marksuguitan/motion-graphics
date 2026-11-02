// Scene1.tsx: the template's example scene (demo beats 1A and 1B). Copy its pattern, then replace it.
// It shows the Comma Clinical vocabulary on the Remotion path:
//   - every move starts on a measured word (sync), never a guessed time
//   - a disc grows from a point (overshoot), hops (gravity) and squashes on landing
//   - text cuts on with its word, no fades
//   - the disc morphs into the card (transform, don't enter), then hands off to the beat's SVG art,
//     whose card is drawn at exactly the morph's end shape (a match cut)
//   - the chip snaps in with an overshoot; group items stagger 2 frames
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {SvgArt} from '../lib/SvgArt';
import {beatEnd, beatStart, sync, useTime} from '../lib/timing';
import {anticipate, cut, ease, gravity, overshoot, squash, stagger} from '../style/comma';
import {disc, roundRect} from '../lib/shapes';
import {C} from '../style/theme';

const CX = 960, CY = 540; // centre of frame: one object, centred
const CARD = {w: 760, h: 420, r: 24}; // must match Card/Box in 1B_card.svg
const hex = (rgb: number[]) => `rgb(${rgb.map((v) => Math.round(v)).join(',')})`;
const CORAL = [240, 100, 90], WHITE = [255, 255, 255];

export const Scene1: React.FC = () => {
  const t = useTime();
  if (t > beatEnd('1B') + 2) return null;

  // 1A: the disc grows from a point on "One", hops on "shape", squashes as it lands
  const tGrow = sync('1A', 'One');
  const tHop = sync('1A', 'shape');
  const r = overshoot(t, tGrow, 0.6, 0, 90);
  const rise = 0.3, hang = 4 / 30, fall = 0.3;
  const hopY = gravity(t, tHop, 0, -160, rise, hang, fall);
  const sq = squash(t, tHop + rise + hang + fall, 'y');

  // 1B: anticipation (a small dip), then the disc morphs into the card on "Snap"
  const tMorph = sync('1B', 'Snap');
  const MORPH = 0.6;
  const dip = anticipate(t, tMorph, MORPH, 0, 1, 0.06); // -0.06 then 0 -> 1
  const k = Math.max(0, dip);
  const w = 180 + (CARD.w - 180) * k, h = 180 + (CARD.h - 180) * k, rad = 90 + (CARD.r - 90) * k;
  const squeeze = dip < 0 ? 1 + dip : 1; // the counter-move squashes the disc a touch
  const d0 = disc(CX, CY, r);
  const d1 = roundRect(CX, CY, w * squeeze, h / squeeze, rad);
  const d = t < tMorph - 0.2 ? d0 : d1; // same commands, so size and corner radius ease together
  // (for two arbitrary drawn paths, use morph() from comma.ts instead)
  const fill = hex(ease(t, tMorph, MORPH, CORAL, WHITE));
  const landed = t >= tMorph + MORPH; // match cut to the art on the frame the morph lands

  // 1B art: kicker on landing, heading cuts on with "settle", chip overshoots in on "softly"
  const tHead = sync('1B', 'settle');
  const tChip = sync('1B', 'softly');
  const chip = overshoot(t, tChip + stagger(0), 0.6, 0, 1);

  return (
    <AbsoluteFill style={{background: C.soft}}>
      {t >= beatStart('1A') - 1 && !landed ? (
        <svg width="100%" height="100%" viewBox="0 0 1920 1080" style={{position: 'absolute', inset: 0}}>
          <g style={{transform: `translate(0px, ${hopY}px) scale(${sq.sx}, ${sq.sy})`, transformOrigin: `${CX}px ${CY + 90}px`}}>
            <path d={d} fill={fill} style={{filter: `drop-shadow(0 8px 12px rgba(34,34,34,${0.1 * k}))`}} />
          </g>
          {cut(t, sync('1A', 'idea'), tMorph) ? (
            <text x={CX} y={CY + 170} textAnchor="middle" style={{font: '500 30px Inter', fill: C.ink}}>One idea</text>
          ) : null}
        </svg>
      ) : null}
      {landed ? (
        <SvgArt
          src="art/1B_card.svg"
          layers={{
            'Background/Fill': {visible: false},
            'Card/Heading': {visible: cut(t, tHead)},
            'Card/Chip': {visible: t >= tChip, scale: chip},
          }}
        />
      ) : null}
    </AbsoluteFill>
  );
};
