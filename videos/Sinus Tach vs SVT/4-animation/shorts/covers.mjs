import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
// cover images: one frame of each short, without captions, full size
const serveUrl = path.resolve(process.env.BUILD || 'build');
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const fr = (a, t) => Math.round((2.2 + 1.5 + (t - a)) * 30);
const C = [['Short2Narrow', 'narrow', fr(8.6, 25.6), 'short-2-why-the-qrs-is-narrow-cover.png'], ['Short3Reason', 'reason', fr(39.3, 62.0), 'short-3-fast-heart-find-the-reason-cover.png'], ['Short5Tells', 'tells', fr(95.15, 126.6), 'short-5-sinus-tach-or-svt-3-tells-cover.png']];
for (const [id, sid, frame, name] of C) {
  const inputProps = {id: sid, cover: true};
  const composition = await selectComposition({serveUrl, id, inputProps, browserExecutable});
  await renderStill({composition, serveUrl, inputProps, browserExecutable, output: `out/${name}`, frame, imageFormat: 'png'});
}
console.log('covers done');
