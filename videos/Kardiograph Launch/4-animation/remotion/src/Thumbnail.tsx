// Thumbnail.tsx: 1280x720 still of the end card.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {KardiographLaunch} from './scenes/KardiographLaunch';

export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{transform: 'scale(0.6667)', transformOrigin: '0 0', width: 1920, height: 1080}}>
    <KardiographLaunch at={17} />
  </AbsoluteFill>
);
