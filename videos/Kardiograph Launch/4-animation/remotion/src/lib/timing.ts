// timing.ts: no VO in this piece, so time is plain video seconds. Beats (for the review overlay and
// `npm run check`) are in src/data/beats.json; every move's time is in scenes/KardiographLaunch.tsx (TL).
import {useCurrentFrame, useVideoConfig} from 'remotion';
import beatsJson from '../data/beats.json';
import videoJson from '../data/video.json';

export type Beat = {id: string; start: number; dur: number; end: number};
export const VIDEO = videoJson as {title: string; lead: number; tail: number; trackDur: number; fps: number};
export const BEATS = beatsJson as Beat[];

export function useTime(): number {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return frame / fps - VIDEO.lead;
}

export function beatAt(t: number): Beat | undefined {
  let cur: Beat | undefined;
  for (const b of BEATS) if (b.start <= t) cur = b;
  return cur;
}
