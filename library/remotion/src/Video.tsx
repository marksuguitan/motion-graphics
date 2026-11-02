// Video.tsx: the whole explainer. The stitched VO (3-board/audio/full.mp3) starts after VIDEO.lead seconds;
// every scene works in track time (useTime) and shows itself only during its beats.
// List one component per scene from the production doc's scene map.
import React from 'react';
import {AbsoluteFill, Audio, Sequence, staticFile, useVideoConfig} from 'remotion';
import {C} from './style/theme';
import {VIDEO} from './lib/timing';
import {ReviewOverlay} from './lib/ReviewOverlay';
import {Scene1} from './scenes/Scene1';

export const Video: React.FC<{review: boolean; label: string}> = ({review, label}) => {
  const {fps} = useVideoConfig();
  return (
    <AbsoluteFill style={{background: C.bg}}>
      <Scene1 />
      <Sequence from={Math.round(VIDEO.lead * fps)} layout="none">
        <Audio src={staticFile('audio/full.mp3')} />
      </Sequence>
      {review ? <ReviewOverlay label={label} /> : null}
    </AbsoluteFill>
  );
};
