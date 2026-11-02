import data from './cues.json';
import {FPS} from './util';
export const W = (data as any).words as {w: string; s: number; e: number}[];
export const w = (i: number) => W[i].s;
export const we = (i: number) => W[i].e;
export const TOTAL = Math.ceil((data as any).total * FPS);
// sentences for captions
export const SENT: {text: string; s: number; e: number}[] = [];
{
  let cur: string[] = [], s = -1;
  W.forEach((x, i) => {
    if (s < 0) s = x.s;
    cur.push(x.w);
    if (/[.]$/.test(x.w) || i === W.length - 1) { SENT.push({text: cur.join(' '), s, e: x.e}); cur = []; s = -1; }
  });
}
