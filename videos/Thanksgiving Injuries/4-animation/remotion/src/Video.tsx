// Video.tsx: Thanksgiving Injuries (no VO, sound effects only). The SFX track is made by 4-animation/build/sfx.py
// from the same timeline.json the picture reads.
import React from 'react';
import {AbsoluteFill, Audio, staticFile} from 'remotion';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {useTime} from './lib/timing';
import {ArtLayer} from './scenes/Art';
import {Texts} from './scenes/Text';
import {EndScreen} from './scenes/EndScreen';
import {C, H, W} from './style/theme';

export const Video: React.FC<{review: boolean; label: string}> = ({review, label}) => {
  const t = useTime();
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{position: 'absolute', inset: 0}}>
        <ArtLayer t={t} />
      </svg>
      <Texts t={t} />
      <EndScreen t={t} />
      <Audio src={staticFile('sfx/sfx.wav')} />
      {review ? <ReviewOverlay label={label} /> : null}
    </AbsoluteFill>
  );
};
