#!/usr/bin/env node
// prep.mjs: brings a video's Stage 3 files into this Remotion project.
//   npm run prep                  (inside videos/<Short title>/4-animation/remotion/: uses ../../)
//   npm run prep -- <video dir>   (any video folder, or `demo` for the template's demo)
//   options: --lead 0.5 (s of silence before the VO), --tail 1.0 (s after it)
// It copies 3-board/art/*.svg -> public/art/ and 3-board/audio/*.mp3 -> public/audio/, measures every beat
// file with ffprobe, and writes src/data/{beats,sync,words,video}.json from 3-board/timings/.
// Re-run it whenever the art, VO or timings change. It never edits the video's own files.
import fs from 'fs';
import path from 'path';
import {execFileSync} from 'child_process';
import {fileURLToPath} from 'url';

const HERE = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  if (i < 0) return def;
  const v = Number(args[i + 1]);
  args.splice(i, 2);
  return v;
};
const lead = opt('lead', 0.5);
const tail = opt('tail', 1.0);
const videoDir = path.resolve(HERE, args[0] ?? '../..');
const board = path.join(videoDir, '3-board');
if (!fs.existsSync(board)) {
  console.error(`No 3-board/ in ${videoDir}`);
  process.exit(1);
}

// --- CSV (quoted fields, doubled quotes)
function csv(file) {
  if (!fs.existsSync(file)) return [];
  const text = fs.readFileSync(file, 'utf8').replace(/^﻿/, '');
  const rows = [];
  let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (q) {
      if (ch === '"' && text[i + 1] === '"') { cell += '"'; i++; }
      else if (ch === '"') q = false;
      else cell += ch;
    } else if (ch === '"') q = true;
    else if (ch === ',') { row.push(cell); cell = ''; }
    else if (ch === '\n' || ch === '\r') {
      if (ch === '\r' && text[i + 1] === '\n') i++;
      row.push(cell); cell = '';
      if (row.some((c) => c !== '')) rows.push(row);
      row = [];
    } else cell += ch;
  }
  if (cell !== '' || row.length) { row.push(cell); rows.push(row); }
  const [head, ...body] = rows;
  return body.map((r) => Object.fromEntries(head.map((h, i) => [h.trim(), (r[i] ?? '').trim()])));
}
const num = (v) => (v === '' || v === undefined ? NaN : Number(v));
const probe = (file) =>
  Number(execFileSync('ffprobe', ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', file]).toString().trim());

// --- copy art and audio
const copyDir = (from, to, ext) => {
  fs.rmSync(to, {recursive: true, force: true});
  fs.mkdirSync(to, {recursive: true});
  if (!fs.existsSync(from)) return [];
  const files = fs.readdirSync(from).filter((f) => f.toLowerCase().endsWith(ext));
  for (const f of files) fs.copyFileSync(path.join(from, f), path.join(to, f));
  return files;
};
const art = copyDir(path.join(board, 'art'), path.join(HERE, 'public/art'), '.svg');
const audio = copyDir(path.join(board, 'audio'), path.join(HERE, 'public/audio'), '.mp3');
if (!audio.includes('full.mp3')) {
  console.error('3-board/audio/full.mp3 is missing: stitch the full track first (production guide, Stage 3).');
  process.exit(1);
}

// --- words and sync points (times in the stitched track)
const words = csv(path.join(board, 'timings/word_timings.csv')).map((r) => ({
  beat: r.beat, index: num(r.index), word: r.word,
  t_beat: num(r.start_in_beat_s), t: num(r.start_in_full_s), end: num(r.end_in_full_s),
}));
const sync = csv(path.join(board, 'timings/sync_points.csv')).map((r) => ({
  beat: r.beat, sync_on: r.sync_on, word: r.word_heard,
  t_beat: num(r.start_in_beat_s), t: num(r.start_in_full_s), flag: r.flag ?? '',
}));

// --- beats: start in the full track from the word timings, duration measured from the beat file
const beatIds = audio.map((f) => f.replace(/\.mp3$/i, '')).filter((id) => /^\d+[A-Z]+$/.test(id));
const problems = [];
const beats = beatIds.map((id) => {
  const dur = probe(path.join(board, 'audio', `${id}.mp3`));
  const first = words.find((w) => w.beat === id && Number.isFinite(w.t) && Number.isFinite(w.t_beat));
  if (!first) problems.push(`${id}: no word timings, so its start in full.mp3 is unknown`);
  const start = first ? +(first.t - first.t_beat).toFixed(3) : NaN;
  return {id, start, dur: +dur.toFixed(3), end: +(start + dur).toFixed(3)};
});
beats.sort((a, b) => a.start - b.start);
for (const s of sync) if (s.flag) problems.push(`${s.beat} ${s.sync_on}: flagged (${s.flag})`);
for (const s of sync) if (!Number.isFinite(s.t)) problems.push(`${s.beat} ${s.sync_on}: no time`);

const trackDur = probe(path.join(board, 'audio', 'full.mp3'));
const title = path.basename(videoDir) === 'demo' ? 'Comma Clinical demo' : path.basename(videoDir);
const out = path.join(HERE, 'src/data');
fs.mkdirSync(out, {recursive: true});
const write = (name, data) => fs.writeFileSync(path.join(out, name), JSON.stringify(data, null, 1) + '\n');
write('beats.json', beats);
write('sync.json', sync);
write('words.json', words);
write('video.json', {title, lead, tail, trackDur: +trackDur.toFixed(3), fps: 30});

console.log(`${title}: ${beats.length} beats, ${sync.length} sync points, ${words.length} words, ${art.length} SVGs, full.mp3 ${trackDur.toFixed(2)} s`);
if (problems.length) {
  console.log('Check before keyframing:');
  for (const p of problems) console.log('  - ' + p);
}
