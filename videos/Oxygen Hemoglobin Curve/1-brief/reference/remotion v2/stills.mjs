import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'path';
const secs = process.argv.slice(2).map(Number);
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const comp = await selectComposition({serveUrl, id: 'Main', browserExecutable: '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell'});
for (const s of secs) {
  const frame = Math.round(s * 30);
  await renderStill({serveUrl, composition: comp, frame, output: process.env.OUT ? `${process.env.OUT}/s_${s}.png` : `out/s_${s}.png`, browserExecutable: '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell', chromiumOptions: {gl: 'angle'}});
  console.log('done', s);
}
