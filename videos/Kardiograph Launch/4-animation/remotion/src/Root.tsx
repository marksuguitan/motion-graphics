// Root.tsx: "Video" is the Kardiograph launch piece (no VO), made to follow Normal Conduction.
import React from 'react';
import {Composition} from 'remotion';
import {Video} from './Video';
import {Thumbnail} from './Thumbnail';
import {VIDEO} from './lib/timing';
import {loadFonts} from './lib/Fonts';

loadFonts();

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Video"
      component={Video}
      durationInFrames={Math.ceil((VIDEO.lead + VIDEO.trackDur + VIDEO.tail) * VIDEO.fps)}
      fps={VIDEO.fps}
      width={1920}
      height={1080}
      defaultProps={{review: false, label: ''}}
    />
    <Composition id="Thumbnail" component={Thumbnail} durationInFrames={1} fps={VIDEO.fps} width={1280} height={720} />
  </>
);
