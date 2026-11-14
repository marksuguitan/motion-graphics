#!/usr/bin/env node
// render.mjs: renders the video in the cloud workspace (no Mac).
//   npm run render:review -- <N>   review render, pass N: beat ID and timecode burned in, lighter encode
//                                  -> ../../5-finish/renders/<Short title> review v<N>.mp4
//   npm run render:final           final render, nothing burned in, plus the thumbnail
//                                  -> ../../6-delivery/<Short title>.mp4 and <Short title> thumbnail.png
// Outside a video folder (the library template) both go to out/. Run `npm run prep` first.
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';
import {fileURLToPath} from 'url';

const HERE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const [mode, n = '1'] = process.argv.slice(2);
const video = JSON.parse(fs.readFileSync(path.join(HERE, 'src/data/video.json'), 'utf8'));
const inVideo = fs.existsSync(path.join(HERE, '../../3-board'));
const dir = (sub) => {
  const d = inVideo ? path.join(HERE, '../..', sub) : path.join(HERE, 'out');
  fs.mkdirSync(d, {recursive: true});
  return d;
};
const run = (...a) => execFileSync('npx', ['remotion', ...a, '--log=error'], {cwd: HERE, stdio: 'inherit'});

if (mode === 'review') {
  const out = path.join(dir('5-finish/renders'), `${video.title} review v${n}.mp4`);
  run('render', 'Video', out, `--props=${JSON.stringify({review: true, label: `v${n}`})}`, '--codec=h264', '--crf=23', '--audio-bitrate=128k');
  console.log(out);
} else if (mode === 'final') {
  const d = dir('6-delivery');
  const out = path.join(d, `${video.title}.mp4`);
  run('render', 'Video', out, '--props={"review":false,"label":""}', '--codec=h264', '--crf=16', '--audio-codec=aac', '--audio-bitrate=320k');
  run('still', 'Thumbnail', path.join(d, `${video.title} thumbnail.png`));
  console.log(out);
} else {
  console.error('usage: render.mjs review <N> | final');
  process.exit(1);
}
