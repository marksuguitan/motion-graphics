// Vertical.tsx: Normal Conduction for Reels and Shorts (1080x1920). The 16:9 scene is shown through two windows
// instead of being redrawn: the heart above, the ECG and its labels below. The title moments use one centred
// window, and the camera moves between the two layouts with Comma Clinical's tracked move ('cross', 0.9 s).
// The last frame matches Kardiograph Launch's vertical cut (title baseline at y 988, centred).
import React from 'react';
import {AbsoluteFill, Audio, staticFile} from 'remotion';
import {NormalConduction} from './scenes/NormalConduction';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {useTime} from './lib/timing';
import {progress} from './style/comma';
import {M} from './style/mono';

type Rect = [number, number, number, number]; // x, y, w, h

// [source rect in the 16:9 frame, destination rect in the 9:16 frame]
const TITLE_SRC: Rect = [420, 0, 1080, 1080];
const TITLE_DST: Rect = [0, 420, 1080, 1080];
const HEART_SRC: Rect = [160, 40, 870, 1000];
const HEART_DST: Rect = [148, 60, 783, 900]; // heart at 0.9
const LOWER_SRC: Rect = [1010, 270, 900, 580];
const LOWER_DST: Rect = [90, 990, 900, 580]; // ECG and labels at 1.0

const PAN_IN = 3.55; // after the dot reaches the centre, before it hops into the heart
const PAN_OUT = 31.6; // as the heart folds back into the dot
const PAN = 0.9;

const mix = (a: Rect, b: Rect, k: number): Rect => a.map((v, i) => v + (b[i] - v) * k) as Rect;

const Window: React.FC<{src: Rect; dst: Rect}> = ({src, dst}) => {
  const s = dst[2] / src[2];
  return (
    <div style={{position: 'absolute', left: dst[0], top: dst[1], width: dst[2], height: dst[3], overflow: 'hidden'}}>
      <div style={{position: 'absolute', width: 1920, height: 1080, transformOrigin: '0 0', transform: `scale(${s}) translate(${-src[0]}px, ${-src[1]}px)`}}>
        <NormalConduction />
      </div>
    </div>
  );
};

export const Vertical: React.FC<{review: boolean; label: string}> = ({review, label}) => {
  const t = useTime();
  const k = t < PAN_OUT ? progress(t, PAN_IN, PAN, 'cross') : 1 - progress(t, PAN_OUT, PAN, 'cross');
  const top: [Rect, Rect] = [mix(TITLE_SRC, HEART_SRC, k), mix(TITLE_DST, HEART_DST, k)];
  const lower = t >= PAN_IN + PAN && t < PAN_OUT;
  return (
    <AbsoluteFill style={{background: M.bg}}>
      <Window src={top[0]} dst={top[1]} />
      {lower ? <Window src={LOWER_SRC} dst={LOWER_DST} /> : null}
      <Audio src={staticFile('sfx/sfx.wav')} />
      {review ? <ReviewOverlay label={label} /> : null}
    </AbsoluteFill>
  );
};
