// stills.mjs: check stills. node stills.mjs <outDir> <seconds...>   (half size, review overlay on)
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';
const [,, outDir, ...times] = process.argv;
const PW = '/opt/pw-browsers';
const shell = fs.readdirSync(PW).filter((d) => d.startsWith('chromium_headless_shell-')).sort().pop();
const browserExecutable = path.join(PW, shell, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const inputProps = {review: true, label: 'check'};
const composition = await selectComposition({serveUrl, id: 'Short', browserExecutable, inputProps});
fs.mkdirSync(outDir, {recursive: true});
for (const s of times) {
  const frame = Math.round(parseFloat(s) * composition.fps);
  await renderStill({composition, serveUrl, browserExecutable, inputProps, frame, scale: 0.4, output: path.join(outDir, `t${String(s).padStart(5, '0')}.png`)});
}
console.log('done');
