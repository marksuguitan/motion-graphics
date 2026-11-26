// Reel.tsx: the 9:16 Instagram reel cut (1080x1920) of the same piece: same timeline, art, words and sound.
// The art is drawn in the wide frame's coordinates and framed by a camera: centred on the plate for the open and
// the close, and on the art band (x 0-1080 of the wide frame) for scenes 2-6, with the cards underneath. The camera
// moves with the plate's own moves (into the knife, back to the plate), so nothing cuts. No YouTube end screen:
// the reel holds on "Happy Thanksgiving" and the music fades out.
import React from 'react';
import {AbsoluteFill, Audio, interpolate, staticFile, useVideoConfig} from 'remotion';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {useTime} from './lib/timing';
import {ArtLayer} from './scenes/Art';
import {Texts} from './scenes/Text';
import {C} from './style/theme';
import {progress} from './style/comma';
import {EV, CARD} from './lib/tl';
import {LayoutCtx, REEL} from './lib/layout';

export const RW = 1080;
export const RH = 1920;
/** The reel holds on the closing card from here (just before it would roll out for the end screen). */
export const REEL_FREEZE = CARD('7A').off - 1 / 30;
export const REEL_HOLD = 1.7;
export const REEL_DUR = REEL_FREEZE + REEL_HOLD;
const MUSIC_GAIN = 0.3; // as in Video.tsx
const FADE = 2.2;

type Cam = {k: number; tx: number; ty: number};
const CENTRED: Cam = {k: 1, tx: 540 - 960, ty: 760 - 420}; // plate (960, 420) -> (540, 760)
const BAND: Cam = {k: 0.95, tx: 27, ty: 150}; // wide x 0-1080, y 0-1080 -> top band
const mixCam = (a: Cam, b: Cam, u: number): Cam => ({k: a.k + (b.k - a.k) * u, tx: a.tx + (b.tx - a.tx) * u, ty: a.ty + (b.ty - a.ty) * u});
export const camAt = (t: number): Cam => {
  if (t < EV.s7.clear) return mixCam(CENTRED, BAND, progress(t, EV.s2.anti, EV.s2.move + 0.75 - EV.s2.anti, 'cross'));
  return mixCam(BAND, CENTRED, progress(t, EV.s7.clear, EV.s7.grow + 0.7 - EV.s7.clear, 'cross'));
};

export const ReelFrame: React.FC<{t: number}> = ({t}) => {
  const c = camAt(t);
  return (
    <LayoutCtx.Provider value={REEL}>
      <svg width={RW} height={RH} viewBox={`0 0 ${RW} ${RH}`} style={{position: 'absolute', inset: 0}}>
        <g transform={`translate(${c.tx} ${c.ty}) scale(${c.k})`}>
          <ArtLayer t={t} />
        </g>
      </svg>
      <Texts t={t} />
    </LayoutCtx.Provider>
  );
};

export const Reel: React.FC<{review: boolean; label: string}> = ({review, label}) => {
  const t = useTime();
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <ReelFrame t={Math.min(t, REEL_FREEZE)} />
      <Audio src={staticFile('sfx/sfx.wav')} />
      <Audio
        src={staticFile('sfx/music.wav')}
        volume={(f) => MUSIC_GAIN * interpolate(f / fps, [REEL_DUR - FADE, REEL_DUR], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}
      />
      {review ? <ReviewOverlay label={label} /> : null}
    </AbsoluteFill>
  );
};

/** Reel cover (1080x1920 still): the closing plate with its five hazards and the title. */
export const ReelCover: React.FC = () => (
  <AbsoluteFill style={{background: C.bg}}>
    <svg width={RW} height={RH} viewBox={`0 0 ${RW} ${RH}`} style={{position: 'absolute', inset: 0}}>
      <g transform={`translate(${CENTRED.tx} ${CENTRED.ty})`}>
        <ArtLayer t={EV.s7.icons + 1.2} />
      </g>
    </svg>
    <div style={{position: 'absolute', left: 70, top: 1000, width: 940, textAlign: 'center'}}>
      <div style={{fontFamily: 'Manrope, system-ui, sans-serif', fontWeight: 700, fontSize: 23, letterSpacing: 3, color: C.ink2, lineHeight: '34px', marginBottom: 14}}>THANKSGIVING</div>
      <div style={{fontFamily: 'Manrope, system-ui, sans-serif', fontWeight: 600, fontSize: 80, lineHeight: '96px', color: C.ink, letterSpacing: -0.5}}>
        Five ways the feast ends in the <span style={{color: C.focus}}>ER</span>
      </div>
    </div>
  </AbsoluteFill>
);
