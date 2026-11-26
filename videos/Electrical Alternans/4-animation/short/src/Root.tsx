// Root.tsx: the Electrical Alternans short, 1080x1920 (text and sound effects only, no VO).
import React from 'react';
import {Composition} from 'remotion';
import {Short} from './Short';
import TL from './data/timeline.json';
import {loadFonts} from './lib/Fonts';

loadFonts();

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Short"
    component={Short}
    durationInFrames={Math.round(TL.end * TL.fps)}
    fps={TL.fps}
    width={1080}
    height={1920}
    defaultProps={{review: false, label: ''}}
  />
);
