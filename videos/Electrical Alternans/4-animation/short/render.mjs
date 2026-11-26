// render.mjs: renders the short in the cloud workspace (no Mac).
//   node render.mjs review <N>   timecode burned in  -> out/Electrical Alternans short review v<N>.mp4
//   node render.mjs final        nothing burned in   -> out/Electrical Alternans short.mp4
// Run python3 sfx.py first if the timeline changed.
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';
import fs from 'fs';
import path from 'path';
const [,, mode = 'review', n = '1'] = process.argv;
const PW = '/opt/pw-browsers';
const shell = fs.readdirSync(PW).filter((d) => d.startsWith('chromium_headless_shell-')).sort().pop();
const browserExecutable = path.join(PW, shell, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
const review = mode === 'review';
const inputProps = {review, label: review ? `v${n}` : ''};
const out = path.resolve('out', review ? `Electrical Alternans short review v${n}.mp4` : 'Electrical Alternans short.mp4');
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'Short', browserExecutable, inputProps});
await renderMedia({composition, serveUrl, browserExecutable, inputProps, codec: 'h264', crf: review ? 20 : 16, audioCodec: 'aac', audioBitrate: '192k', outputLocation: out, concurrency: 4, logLevel: 'error'});
console.log(out);
