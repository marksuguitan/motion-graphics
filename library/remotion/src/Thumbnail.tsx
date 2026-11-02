// Thumbnail.tsx: the delivery thumbnail (1280x720), rendered with render:final as a still.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {C, TYPE} from './style/theme';
import {VIDEO} from './lib/timing';

export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{background: C.soft, justifyContent: 'center', padding: 96}}>
    <div style={{...TYPE.kicker, fontSize: 26}}>Medzcool</div>
    <div style={{...TYPE.title, fontSize: 96, marginTop: 16}}>{VIDEO.title}</div>
  </AbsoluteFill>
);
