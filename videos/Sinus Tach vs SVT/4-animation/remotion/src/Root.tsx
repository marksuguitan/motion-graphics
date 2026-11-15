// Root.tsx: Sinus Tach vs SVT was finished as v8 in an earlier Remotion project (on Mark's Mac).
// This project only builds the two Kardiograph plugs that are cut into v8 (Nov 14, 2026):
//   Opener   after the title card, no VO
//   EndPlug  before the end card, with VO
import React from 'react';
import {Composition} from 'remotion';
import {FPS, H, W} from './style/theme';
import {loadFonts} from './lib/Fonts';
import {Opener, OPENER_FRAMES} from './plugs/Opener';
import {EndPlug, END_FRAMES} from './plugs/EndPlug';

loadFonts();

export const RemotionRoot: React.FC = () => (
  <>
    <Composition id="Opener" component={Opener} durationInFrames={OPENER_FRAMES} fps={FPS} width={W} height={H} />
    <Composition id="EndPlug" component={EndPlug} durationInFrames={END_FRAMES} fps={FPS} width={W} height={H} />
  </>
);
