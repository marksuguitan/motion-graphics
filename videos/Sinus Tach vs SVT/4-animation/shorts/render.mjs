import {renderMedia, selectComposition} from '@remotion/renderer';
import path from 'node:path';
const [,, comp, out] = process.argv;
const serveUrl = path.resolve(process.env.BUILD || 'build');
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const composition = await selectComposition({serveUrl, id: comp, browserExecutable});
let last = -1;
await renderMedia({composition, serveUrl, browserExecutable, codec: 'h264', crf: 18, audioCodec: 'aac', audioBitrate: '192k', outputLocation: out, concurrency: 4,
  onProgress: ({progress}) => { const p = Math.floor(progress * 10); if (p !== last) { last = p; console.log(comp, p * 10 + '%'); } }});
console.log('done', out);
