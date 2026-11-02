// Root.tsx: the compositions. "Video" is the whole explainer on full.mp3; "Thumbnail" is a still.
import React from 'react';
import {Composition} from 'remotion';
import {Video} from './Video';
import {Thumbnail} from './Thumbnail';
import {VIDEO} from './lib/timing';
import {FPS, H, W} from './style/theme';
import {loadFonts} from './lib/Fonts';

loadFonts();

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Video"
      component={Video}
      durationInFrames={Math.ceil((VIDEO.lead + VIDEO.trackDur + VIDEO.tail) * FPS)}
      fps={FPS}
      width={W}
      height={H}
      defaultProps={{review: false, label: ''}}
    />
    <Composition id="Thumbnail" component={Thumbnail} durationInFrames={1} fps={FPS} width={1280} height={720} />
  </>
);
