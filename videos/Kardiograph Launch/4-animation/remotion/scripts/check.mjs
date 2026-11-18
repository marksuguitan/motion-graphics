#!/usr/bin/env node
// check.mjs: the Remotion path's "scrub to every beat start and sync point" (production guide, Stage 4).
// Renders a still at every beat start and at every sync point plus 0.7 s (where a snap-and-settle move has landed),
// with the review overlay on, then tiles them into contact sheets in out/check/.
//   npm run check            all beats
//   npm run check -- 3A 3B   only these beats
// Look at every sheet before handing a pass back, and report what's on screen.
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';
import {fileURLToPath} from 'url';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';

const HERE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const only = process.argv.slice(2);
const read = (f) => JSON.parse(fs.readFileSync(path.join(HERE, 'src/data', f), 'utf8'));
const video = read('video.json');
const beats = read('beats.json').filter((b) => !only.length || only.includes(b.id));
const sync = read('sync.json').filter((s) => !only.length || only.includes(s.beat));

const marks = [];
for (const b of beats) marks.push({t: b.start + 0.03, what: `${b.id} start`});
for (const s of sync) marks.push({t: s.t + 0.7, what: `${s.beat} ${s.sync_on} +0.7 s`});
// This video has no VO: extra check times can be passed as TIMES=1.2,3.4 (seconds)
if (process.env.TIMES) {
  marks.length = 0;
  for (const x of process.env.TIMES.split(',')) marks.push({t: Number(x), what: `t ${x}`});
}
marks.sort((a, b) => a.t - b.t);

const outDir = path.join(HERE, 'out/check');
fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});

let browserExecutable = null;
const PW = '/opt/pw-browsers';
if (fs.existsSync(PW)) {
  const shell = fs.readdirSync(PW).filter((d) => d.startsWith('chromium_headless_shell-')).sort().pop();
  const exe = shell && path.join(PW, shell, 'chrome-headless-shell-linux64', 'chrome-headless-shell');
  if (exe && fs.existsSync(exe)) browserExecutable = exe;
}

const serveUrl = await bundle({entryPoint: path.join(HERE, 'src/index.ts'), publicDir: path.join(HERE, 'public')});
const inputProps = {review: true, label: 'check'};
const composition = await selectComposition({serveUrl, id: 'Video', inputProps, browserExecutable});
const lines = [];
for (let i = 0; i < marks.length; i++) {
  const frame = Math.min(composition.durationInFrames - 1, Math.round((marks[i].t + video.lead) * video.fps));
  const file = path.join(outDir, `f${String(i).padStart(3, '0')}.jpeg`);
  await renderStill({serveUrl, composition, frame, output: file, inputProps, imageFormat: 'jpeg', jpegQuality: 85, browserExecutable});
  lines.push(`${String(i).padStart(3, '0')}  f${frame}  ${marks[i].what}`);
}
fs.writeFileSync(path.join(outDir, 'index.txt'), lines.join('\n') + '\n');
execFileSync('ffmpeg', ['-loglevel', 'error', '-y', '-framerate', '1', '-i', path.join(outDir, 'f%03d.jpeg'),
  '-vf', 'scale=640:-1,tile=3x3:padding=8:color=white', path.join(outDir, 'sheet%02d.jpg')]);
console.log(`${marks.length} stills; sheets and index.txt in ${path.relative(process.cwd(), outDir)}/`);
