import {Composition} from 'remotion';
import {Main} from './Main';
import {TOTAL} from './cues';
import {FPS} from './util';
export const RemotionRoot = () => (<>
  <Composition id="Main" component={Main} durationInFrames={TOTAL} fps={FPS} width={1920} height={1080} />
  {/* 480 fps copy for motion-blurring the logo dash (frames are averaged down to 30 fps) */}
  <Composition id="MainHi" component={Main} durationInFrames={TOTAL * 16} fps={FPS * 16} width={1920} height={1080} />
</>);
