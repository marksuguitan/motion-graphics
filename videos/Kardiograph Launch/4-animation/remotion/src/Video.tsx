// Video.tsx: Kardiograph Launch (no VO). One scene.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {KardiographLaunch} from './scenes/KardiographLaunch';
import {M} from './style/mono';

export const Video: React.FC<{review: boolean; label: string}> = ({review, label}) => (
  <AbsoluteFill style={{background: M.bg}}>
    <KardiographLaunch />
    {review ? <ReviewOverlay label={label} /> : null}
  </AbsoluteFill>
);
