import React from 'react';
import {Composition} from 'remotion';
import {Main} from './Main';
import {Intro, INTRO} from './Intro';
import {AbsoluteFill, Sequence} from 'remotion';
import {T} from './theme';
import {ThumbA, ThumbB} from './Thumb';
import {Short, shortFrames} from './Short';
const Video: React.FC = () => (
  <AbsoluteFill style={{background: T.bg}}>
    <Sequence from={Math.round(INTRO * FPS)}><Main /></Sequence>
    <Intro />
  </AbsoluteFill>
);
import {FPS, TOTAL} from './theme';
const IntroHi: React.FC = () => (<AbsoluteFill style={{background: T.bg}}><Intro /></AbsoluteFill>);
export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="SVT" component={Video} durationInFrames={TOTAL + Math.round(INTRO * FPS)} fps={FPS} width={1920} height={1080} />
    <Composition id="IntroHi" component={IntroHi} durationInFrames={Math.round(INTRO * 480)} fps={480} width={1920} height={1080} />
    <Composition id="ThumbA" component={ThumbA} durationInFrames={1} fps={30} width={1280} height={720} />
    <Composition id="ThumbB" component={ThumbB} durationInFrames={1} fps={30} width={1280} height={720} />
    <Composition id="ShortAnswering" component={Short} defaultProps={{id: 'answering' as const}} durationInFrames={shortFrames('answering')} fps={30} width={1080} height={1920} />
    <Composition id="ShortAnsweringHi" component={Short} defaultProps={{id: 'answering' as const}} durationInFrames={shortFrames('answering') * 16} fps={480} width={1080} height={1920} />
    <Composition id="ShortAdenosineHi" component={Short} defaultProps={{id: 'adenosine' as const}} durationInFrames={shortFrames('adenosine') * 16} fps={480} width={1080} height={1920} />
    <Composition id="ShortAdenosine" component={Short} defaultProps={{id: 'adenosine' as const}} durationInFrames={shortFrames('adenosine')} fps={30} width={1080} height={1920} />
  </>
);
