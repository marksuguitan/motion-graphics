import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';
const [,, comp, outDir, ...frames] = process.argv;
const serveUrl = path.resolve(process.env.BUILD || 'build');
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell';
const composition = await selectComposition({serveUrl, id: comp, browserExecutable});
for (const f of frames) {
  await renderStill({composition, serveUrl, output: `${outDir}/${comp}_${String(f).padStart(4, '0')}.jpg`, frame: Number(f), browserExecutable, imageFormat: 'jpeg', jpegQuality: 85, scale: 0.5});
}
console.log('done', comp);
