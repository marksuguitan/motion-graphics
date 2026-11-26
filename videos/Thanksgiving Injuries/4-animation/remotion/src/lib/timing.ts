// timing.ts: measured VO timings for the build. Never estimate a sync point: every time comes from
// src/data/*.json, which `npm run prep` writes from the video's 3-board/timings/ and 3-board/audio/.
import {useCurrentFrame, useVideoConfig} from 'remotion';
import beatsJson from '../data/beats.json';
import syncJson from '../data/sync.json';
import wordsJson from '../data/words.json';
import videoJson from '../data/video.json';

export type Beat = {id: string; start: number; dur: number; end: number};
export type SyncPoint = {beat: string; sync_on: string; word: string; t_beat: number; t: number; flag: string};
export type Word = {beat: string; index: number; word: string; t_beat: number; t: number; end: number};

export const VIDEO = videoJson as {title: string; lead: number; tail: number; trackDur: number; fps: number};
export const BEATS = beatsJson as Beat[];
export const SYNC = syncJson as SyncPoint[];
export const WORDS = wordsJson as Word[];

/** Track time in seconds: 0 is the first sample of 3-board/audio/full.mp3 (the video starts `lead` seconds earlier). */
export function useTime(): number {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps - VIDEO.lead;
}

/** Frame number in the video for a track time, e.g. for `npx remotion still --frame`. */
export const toFrame = (t: number, fps = VIDEO.fps) => Math.round((t + VIDEO.lead) * fps);

export function beat(id: string): Beat {
  const b = BEATS.find((x) => x.id === id);
  if (!b) throw new Error(`Beat ${id} is not in src/data/beats.json. Run npm run prep.`);
  return b;
}
export const beatStart = (id: string) => beat(id).start;
export const beatEnd = (id: string) => beat(id).end;

const norm = (s: string) => s.toLowerCase().replace(/^["'“”]+|["'“”.,;:!?]+$/g, '');

/**
 * Track time of a Sync on word, from sync_points.csv (or, if the scene table doesn't list it, from word_timings.csv).
 * `nth` picks a word that appears more than once in the beat (1 = first). Throws rather than guessing.
 */
export function sync(beatId: string, word: string, nth = 1): number {
  const w = norm(word);
  const fromSync = SYNC.filter((s) => s.beat === beatId && (norm(s.sync_on) === w || norm(s.word) === w));
  if (fromSync.length >= nth) return fromSync[nth - 1].t;
  const fromWords = WORDS.filter((x) => x.beat === beatId && norm(x.word) === w);
  if (fromWords.length >= nth) return fromWords[nth - 1].t;
  throw new Error(`No measured time for "${word}" (${nth}) in beat ${beatId}. Measure it before keyframing.`);
}

/** Track time of the end of a word (for moves that should land as the word finishes). */
export function wordEnd(beatId: string, word: string, nth = 1): number {
  const w = norm(word);
  const hits = WORDS.filter((x) => x.beat === beatId && norm(x.word) === w);
  if (hits.length >= nth) return hits[nth - 1].end;
  throw new Error(`No measured time for "${word}" (${nth}) in beat ${beatId}.`);
}

/** The beat playing at track time t (the last beat that has started). */
export function beatAt(t: number): Beat | undefined {
  let cur: Beat | undefined;
  for (const b of BEATS) if (b.start <= t) cur = b;
  return cur;
}
