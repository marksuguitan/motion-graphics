// Video.tsx: Normal Conduction (no VO). One scene; the SFX track is made by 4-animation/build/sfx.py.
import React from 'react';
import {AbsoluteFill, Audio, staticFile} from 'remotion';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {NormalConduction} from './scenes/NormalConduction';
import {M} from './style/mono';

export const Video: React.FC<{review: boolean; label: string}> = ({review, label}) => (
  <AbsoluteFill style={{background: M.bg}}>
    <NormalConduction />
    <Audio src={staticFile('sfx/sfx.wav')} />
    {review ? <ReviewOverlay label={label} /> : null}
  </AbsoluteFill>
);
