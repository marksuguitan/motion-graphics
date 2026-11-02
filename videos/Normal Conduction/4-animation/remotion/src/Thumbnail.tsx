// Thumbnail.tsx: 1280x720 still, a frame of the walk-through with the title.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {M, FONT_HEAD} from './style/mono';

export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{background: M.bg, justifyContent: 'center', padding: 96}}>
    <div style={{fontFamily: FONT_HEAD, fontWeight: 600, fontSize: 104, color: M.ink}}>Normal conduction.</div>
  </AbsoluteFill>
);
