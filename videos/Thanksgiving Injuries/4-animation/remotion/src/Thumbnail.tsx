// Thumbnail.tsx: 1280x720 still: the closing plate with its five hazards, and the title.
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {ArtLayer} from './scenes/Art';
import {C, FONT} from './style/theme';
import {TL} from './lib/tl';

export const Thumbnail: React.FC = () => (
  <AbsoluteFill style={{background: C.bg}}>
    <svg width={640} height={560} viewBox="610 70 700 612" style={{position: 'absolute', left: 20, top: 90}}>
      <ArtLayer t={TL.ev.s7.icons + 1.2} />
    </svg>
    <div style={{position: 'absolute', left: 690, top: 190, width: 540}}>
      <div style={{fontFamily: FONT.head, fontWeight: 700, fontSize: 24, letterSpacing: 3, color: C.ink2, textTransform: 'uppercase', marginBottom: 18}}>Thanksgiving</div>
      <div style={{fontFamily: FONT.head, fontWeight: 600, fontSize: 76, lineHeight: '88px', color: C.ink, letterSpacing: -0.5}}>
        Five ways the feast ends in the <span style={{color: C.focus}}>ER</span>
      </div>
    </div>
  </AbsoluteFill>
);
