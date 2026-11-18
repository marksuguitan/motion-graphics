// KardiographLaunch.tsx: the Kardiograph launch piece, made to follow Normal Conduction (no VO).
// It opens on Normal Conduction's last frame ("Normal conduction." with the orb as its period). The period
// leaves the title and becomes the pen of an EKG, then the card of a lesson figure, then a practice deck,
// then Kardiograph's mark. Every tracing is drawn by the Kardiograph engine (src/data/engine.json, written
// by 4-animation/build/engine_strips.ts); none is hand-made.
// Look: Normal Conduction's monochrome (src/style/mono.ts); Kardiograph amber only on the app's mark.
// Motion: Comma Clinical (src/style/comma.ts).
import React from 'react';
import {AbsoluteFill} from 'remotion';
import {useTime} from '../lib/timing';
import {roundRect} from '../lib/shapes';
import {cut, ease, fadeSmall, keys, overshoot, progress, squash, typeOff, typeOn} from '../style/comma';
import {M, FONT_HEAD, FONT_BODY} from '../style/mono';
import ENGINE from '../data/engine.json';
import TIMELINE from '../data/timeline.json';

type Strip = {id: string; name: string; II: number[]; onsets: number[]};
const E = ENGINE as unknown as {fs: number; strips: Record<string, Strip>; qrs: {qrsMs: number; II: number[]}[]};
const FS = E.fs;

// ------------------------------------------------------------------ palette additions
const KG_AMBER = '#B97516'; // Kardiograph's identity colour (design system, App colors): the mark only
const GRID_MINOR = '#E1E1DE';
const GRID_MAJOR = '#CFCFCC';
const CARD = '#FFFFFF';

// ------------------------------------------------------------------ the hand-off: Normal Conduction's last frame
const TITLE = 'Normal conduction';
const TITLE_SIZE = 80;
let TITLE_BASE = 568;
const DOT_R = 7;
const DOT_GAP = 5;
const ORB_R = 15;

// ------------------------------------------------------------------ timeline (seconds)
export const TL = TIMELINE as {
  typeOff: number; grow: number; jump: number; land: number; paperStop: number; stripOut: number; card: number;
  cardContent: number; slider: number; practice: number; deal: number[]; mark: number; icon: number; word: number;
  line1: number; line2: number; end: number;
};

// ------------------------------------------------------------------ layout
// Two layouts: 16:9 (1920x1080, the YouTube video) and 9:16 (1080x1920, Reels and Shorts). The vertical one
// matches Normal Conduction's vertical cut (src/Vertical.tsx there), whose title sits 420 px lower and 420 px left.
// setLayout() sets every value at the top of each render, so either layout can render after the other.
let VERT = false;
let FW = 1920; // frame
let FH = 1080;
let CX = 960; // centre
let CY = 540;
let PEN_X = 1560;
let BASE_Y = 590; // the strip's baseline
let STRIP_L = 140; // left edge of the paper
let PX_MM = 12; // paper at 12 px per mm: 25 mm/s = 300 px/s, 10 mm/mV = 120 px/mV
let PX_S = 25 * PX_MM;
let PX_MV = 10 * PX_MM;
let PAPER_TOP = BASE_Y - 216;
let PAPER_BOT = BASE_Y + 156;
let CARD_C: [number, number] = [960, 600];
let CARD_W = 1120;
let CARD_H = 600;
const CARD_R = 28;
let CAP_Y = 196; // caption kicker baseline
let SLIDER_HALF = 300;

let TILE = 168; // Kardiograph's mark at the end
let TILE_R = 40;
const WORD_SIZE = 112;
const WORD_FONT = `800 ${WORD_SIZE}px Manrope`;
let END_Y = 470; // centre line of the mark and wordmark (16:9); the wordmark's centre line (9:16)

function setLayout(vertical: boolean) {
  VERT = vertical;
  if (!vertical) {
    FW = 1920; FH = 1080; CX = 960; CY = 540;
    TITLE_BASE = 568;
    PEN_X = 1560; BASE_Y = 590; STRIP_L = 140;
    PX_MM = 12; PX_S = 25 * PX_MM; PX_MV = 10 * PX_MM;
    PAPER_TOP = BASE_Y - 216; PAPER_BOT = BASE_Y + 156;
    CARD_C = [960, 600]; CARD_W = 1120; CARD_H = 600;
    CAP_Y = 196; SLIDER_HALF = 300;
    TILE = 168; TILE_R = 40; END_Y = 470;
    return;
  }
  FW = 1080; FH = 1920; CX = 540; CY = 960;
  TITLE_BASE = 568 + 420;
  PEN_X = 900; BASE_Y = 1010; STRIP_L = 80;
  PX_MM = 10; PX_S = 25 * PX_MM; PX_MV = 10 * PX_MM;
  PAPER_TOP = BASE_Y - 180; PAPER_BOT = BASE_Y + 130;
  CARD_C = [540, 1090]; CARD_W = 980; CARD_H = 640;
  CAP_Y = 560; SLIDER_HALF = 250;
  TILE = 200; TILE_R = 48; END_Y = 1000;
}

// ------------------------------------------------------------------ helpers
let ctx: CanvasRenderingContext2D | null = null;
function textWidth(s: string, font: string): number {
  if (typeof document === 'undefined') return s.length * 40;
  if (!ctx) ctx = document.createElement('canvas').getContext('2d');
  ctx!.font = font;
  return ctx!.measureText(s).width;
}
const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, k: number) => a + (b - a) * k;

/** Path through samples [i0, i1) of a lead, sample i at x(i), mV v at y0 - v * pxMv. */
function tracePath(s: number[], i0: number, i1: number, x: (i: number) => number, y0: number, pxMv: number): string {
  const a = Math.max(0, Math.floor(i0));
  const b = Math.min(s.length, Math.ceil(i1));
  if (b - a < 2) return '';
  let d = '';
  for (let i = a; i < b; i++) d += `${i === a ? 'M' : 'L'}${x(i).toFixed(1)} ${(y0 - s[i] * pxMv).toFixed(1)}`;
  return d;
}

/** EKG paper: 1 mm and 5 mm lines over [x0, x1] x [y0, y1], lines anchored at paper position `ox`. */
const Grid: React.FC<{x0: number; x1: number; y0: number; y1: number; ox: number; oy: number; mm: number; opacity?: number}> = ({x0, x1, y0, y1, ox, oy, mm, opacity = 1}) => {
  if (x1 <= x0) return null;
  const lines: React.ReactNode[] = [];
  const kx0 = Math.ceil((x0 - ox) / mm);
  const kx1 = Math.floor((x1 - ox) / mm);
  for (let k = kx0; k <= kx1; k++) {
    const x = ox + k * mm;
    const major = ((k % 5) + 5) % 5 === 0;
    lines.push(<line key={`v${k}`} x1={x} x2={x} y1={y0} y2={y1} stroke={major ? GRID_MAJOR : GRID_MINOR} strokeWidth={major ? 1.6 : 1} />);
  }
  const ky0 = Math.ceil((y0 - oy) / mm);
  const ky1 = Math.floor((y1 - oy) / mm);
  for (let k = ky0; k <= ky1; k++) {
    const y = oy + k * mm;
    const major = ((k % 5) + 5) % 5 === 0;
    lines.push(<line key={`h${k}`} y1={y} y2={y} x1={x0} x2={x1} stroke={major ? GRID_MAJOR : GRID_MINOR} strokeWidth={major ? 1.6 : 1} />);
  }
  return <g opacity={opacity}>{lines}</g>;
};

/** Seconds of paper that have run under the pen: real speed, then a short slow-down to a stop. */
function paperTime(t: number): number {
  if (t < TL.land) return 0;
  if (t < TL.paperStop) return t - TL.land;
  const D = 0.4;
  const k = clamp((t - TL.paperStop) / D, 0, 1);
  return TL.paperStop - TL.land + D * (k - (k * k) / 2);
}

/** Lead II of one beat at a QRS width between 90 and 150 ms, blended between the engine's 10 ms steps. */
function qrsBeat(ms: number): number[] {
  const q = E.qrs;
  const f = clamp((ms - q[0].qrsMs) / (q[1].qrsMs - q[0].qrsMs), 0, q.length - 1);
  const i = Math.min(q.length - 2, Math.floor(f));
  const k = f - i;
  return q[i].II.map((v, j) => lerp(v, q[i + 1].II[j], k));
}

const PRACTICE: {id: string; label: string}[] = [
  {id: 'afib', label: 'Atrial fibrillation'},
  {id: 'mobitz1', label: 'Second-degree AV block, Mobitz I'},
  {id: 'chb', label: 'Complete heart block'},
  {id: 'stemiInf', label: 'Inferior STEMI'},
];

// The mark's wave (the app's "wave" icon, a 24-unit Lucide-style path, 2 px stroke)
const WAVE_D = 'M2 12h3l2-6 3 12 3-9 2 3h7';
const WAVE_LEN = 3 + Math.hypot(2, 6) + Math.hypot(3, 12) + Math.hypot(3, 9) + Math.hypot(2, 3) + 7;

// ------------------------------------------------------------------ the scene
export const KardiographLaunch: React.FC<{at?: number; vertical?: boolean}> = ({at, vertical}) => {
  setLayout(!!vertical);
  const tNow = useTime();
  const t = at ?? tNow;

  // ---- title (beat 1)
  const titleFont = `600 ${TITLE_SIZE}px Manrope`;
  const fullW = textWidth(TITLE, titleFont);
  const x0 = CX - (fullW + DOT_GAP + 2 * DOT_R) / 2;
  const typed = typeOff(TITLE, t, TL.typeOff, 30, 4);
  const dotAt = (s: string) => ({x: x0 + (s ? textWidth(s, titleFont) : 0) + DOT_GAP + DOT_R, y: TITLE_BASE - DOT_R});

  // ---- the orb: period -> pen -> card (beats 1-3)
  let orb: {x: number; y: number; r: number; sx: number; sy: number} | null = null;
  if (t < TL.land) {
    let p = dotAt(typed);
    let r = DOT_R;
    if (t >= TL.grow) {
      const p0 = dotAt('');
      const k = progress(t, TL.grow, 0.6, 'snap');
      p = {x: lerp(p0.x, CX, k), y: lerp(p0.y, CY, k)};
      r = lerp(DOT_R, ORB_R, k);
    }
    if (t >= TL.jump) {
      const tj = TL.jump;
      const dur = TL.land - tj - 0.15;
      const k = progress(t, tj + 0.15, dur, 'cross');
      const lift = Math.sin(Math.PI * clamp((t - tj - 0.15) / dur, 0, 1)) * 150;
      const dip = keys(t, [[tj, CY], [tj + 0.15, CY + 16]], 'snap');
      p = {x: lerp(CX, PEN_X, k), y: (t < tj + 0.15 ? dip : lerp(CY + 16, BASE_Y, k)) - lift};
    }
    orb = {...p, r, sx: 1, sy: 1};
  } else if (t < TL.card) {
    const tau = paperTime(t);
    const n = Math.floor(tau * FS);
    const v = E.strips.normal.II[Math.min(n, E.strips.normal.II.length - 1)] ?? 0;
    const sq = squash(t, TL.land, 'y', 0.25);
    let p = {x: PEN_X, y: BASE_Y - v * PX_MV};
    if (t >= TL.stripOut) {
      const k = progress(t, TL.stripOut, 0.55, 'cross');
      p = {x: lerp(PEN_X, CARD_C[0], k), y: lerp(p.y, CARD_C[1], k)};
    }
    orb = {...p, r: ORB_R, sx: sq.sx, sy: sq.sy};
  }

  // ---- the strip (beat 2)
  const tau = paperTime(t);
  const stripShift = t >= TL.stripOut ? ease(t, TL.stripOut, 0.35, 0, -760, 'accel') : 0;
  const showStrip = t >= TL.land && t < TL.stripOut + 0.35;
  const sN = E.strips.normal.II;
  const nNow = Math.min(sN.length, tau * FS + 1);
  const xOf = (i: number) => PEN_X - (tau - i / FS) * PX_S;
  const stripD = showStrip ? tracePath(sN, Math.max(0, (tau - (PEN_X - STRIP_L) / PX_S) * FS - 2), nNow, xOf, BASE_Y, PX_MV) : '';
  const paperLeft = Math.max(STRIP_L, PEN_X - tau * PX_S);
  const paperOx = PEN_X - tau * PX_S; // paper position 0 sits where the first sample was drawn

  // ---- the card: lesson figure (beat 3) and practice deck (beat 4), then the mark (beat 5)
  const showCard = t >= TL.card;
  const cOpen = progress(t, TL.card, 0.6, 'snap');
  const cClose = progress(t, TL.mark, 0.6, 'snap');
  const ws = textWidth('Kardiograph', WORD_FONT);
  const groupW = TILE + 48 + ws + DOT_GAP + 2 * 11;
  // 16:9: mark and wordmark side by side; 9:16: the mark above the wordmark
  const tileC: [number, number] = VERT ? [CX, END_Y - 210] : [CX - groupW / 2 + TILE / 2, END_Y];
  let cardD = '';
  let cardFill = CARD;
  if (showCard) {
    if (t < TL.mark) {
      cardD = roundRect(CARD_C[0], CARD_C[1], lerp(2 * ORB_R, CARD_W, cOpen), lerp(2 * ORB_R, CARD_H, cOpen), lerp(ORB_R, CARD_R, cOpen));
      cardFill = cOpen < 0.15 ? M.orb : CARD;
    } else {
      const s = overshoot(t, TL.mark, 0.6, 0, 1, 0.06);
      cardD = roundRect(lerp(CARD_C[0], tileC[0], s), lerp(CARD_C[1], tileC[1], s), lerp(CARD_W, TILE, s), lerp(CARD_H, TILE, s), lerp(CARD_R, TILE_R, s));
      const k = progress(t, TL.mark + 0.1, 0.4, 'snap');
      cardFill = mixHex(CARD, KG_AMBER, k);
    }
  }
  const cardShadow = showCard && t < TL.mark + 0.3;

  // lesson figure inside the card
  const inLesson = t >= TL.cardContent && t < TL.practice;
  const figL = CARD_C[0] - CARD_W / 2 + 64;
  const figR = CARD_C[0] + CARD_W / 2 - 64;
  const figTop = CARD_C[1] - CARD_H / 2 + 56;
  const figBase = figTop + 290;
  const figBot = figTop + 400;
  const F_MM = 26; // figure paper: 26 px per mm
  const sliderK = progress(t, TL.slider, 0.9, 'cross');
  const qrsMs = 90 + 60 * sliderK;
  const beatS = qrsBeat(qrsMs);
  const figX0 = CX - (beatS.length / FS) * 25 * F_MM / 2;
  const figX = (i: number) => figX0 + (i / FS) * 25 * F_MM;
  const figD = inLesson ? tracePath(beatS, 0, beatS.length, figX, figBase, 10 * F_MM) : '';
  const qOn = figX(0.3 * FS);
  const qOff = qOn + (qrsMs / 1000) * 25 * F_MM;

  // practice deck inside the card
  const inPractice = t >= TL.practice && t < TL.mark;
  let deal = -1;
  for (let i = 0; i < TL.deal.length; i++) if (t >= TL.deal[i]) deal = i;
  const P_MM = 8; // practice paper: 8 px per mm (a 4.8 s strip)
  const pL = CARD_C[0] - CARD_W / 2 + 64;
  const pR = CARD_C[0] + CARD_W / 2 - 64;
  const pBase = CARD_C[1] + 60;
  let practiceD = '';
  let sweepX = pL;
  if (inPractice && deal >= 0) {
    const s = E.strips[PRACTICE[deal].id].II;
    const sweep = progress(t, TL.deal[deal], 0.45, 'cross');
    const nShow = ((pR - pL) / (25 * P_MM)) * FS;
    sweepX = lerp(pL, pR, sweep);
    practiceD = tracePath(s, FS * 1, FS * 1 + nShow * sweep, (i) => pL + ((i - FS) / FS) * 25 * P_MM, pBase, 10 * P_MM);
  }

  // ---- captions
  const capA = cut(t, TL.land + 0.45, TL.stripOut); // beat 2
  const capB = cut(t, TL.card + 0.35, TL.practice); // beat 3
  const capC = cut(t, TL.practice, TL.mark); // beat 4
  const capY = CAP_Y;

  // ---- end card
  const wordTyped = typeOn('Kardiograph', t, TL.word, 30, 2);
  const wordX = VERT ? CX - (ws + DOT_GAP + 22) / 2 : tileC[0] + TILE / 2 + 48;
  const wordBase = END_Y + WORD_SIZE * 0.36;
  const lineY = VERT ? END_Y + 40 : END_Y;
  const periodPop = t >= TL.word ? overshoot(t, TL.word - 0.1, 0.3, 0, 1, 0.1) : 0;
  const periodX = wordX + (wordTyped ? textWidth(wordTyped, WORD_FONT) : 0) + DOT_GAP + 11;
  const iconK = progress(t, TL.icon, 0.55, 'snap');

  return (
    <AbsoluteFill style={{background: M.bg}}>
      <svg width={FW} height={FH} viewBox={`0 0 ${FW} ${FH}`}>
        <defs>
          <linearGradient id="fadeL" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0" stopColor="#fff" stopOpacity="0" />
            <stop offset="0.12" stopColor="#fff" stopOpacity="1" />
            <stop offset="1" stopColor="#fff" stopOpacity="1" />
          </linearGradient>
          <mask id="stripMask" maskUnits="userSpaceOnUse" x={0} y={0} width={FW} height={FH}>
            <rect x={STRIP_L} y={0} width={PEN_X - STRIP_L + 40} height={FH} fill="url(#fadeL)" />
          </mask>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="160%">
            <feDropShadow dx="0" dy="8" stdDeviation="12" floodColor="#222" floodOpacity="0.10" />
          </filter>
        </defs>

        {/* beat 1: the title, deleting itself */}
        {typed && t < TL.grow ? (
          <text x={x0} y={TITLE_BASE} fontFamily={FONT_HEAD} fontWeight={600} fontSize={TITLE_SIZE} fill={M.ink}>
            {typed}
          </text>
        ) : null}

        {/* beat 2: the paper and the trace, scrolling out of the pen */}
        {showStrip ? (
          <g transform={`translate(0 ${stripShift})`} mask="url(#stripMask)">
            <Grid x0={paperLeft} x1={PEN_X} y0={PAPER_TOP} y1={PAPER_BOT} ox={paperOx} oy={BASE_Y} mm={PX_MM} />
            <path d={stripD} fill="none" stroke={M.ink} strokeWidth={4} strokeLinejoin="round" strokeLinecap="round" />
          </g>
        ) : null}
        {capA ? <Caption y={capY + stripShift} kicker="Lead II" head="Now read it on the EKG." /> : null}

        {/* beats 3-5: the card */}
        {showCard ? <path d={cardD} fill={cardFill} filter={cardShadow ? 'url(#soft)' : undefined} /> : null}

        {inLesson ? (
          <g opacity={fadeSmall(t, TL.cardContent)}>
            <Grid x0={figL} x1={figR} y0={figTop} y1={figBot} ox={CX} oy={figBase} mm={F_MM} />
            <path d={figD} fill="none" stroke={M.ink} strokeWidth={5} strokeLinejoin="round" strokeLinecap="round" />
            {/* QRS bracket */}
            <g stroke={M.ink} strokeWidth={3} fill="none">
              <path d={`M${qOn} ${figBot + 26} V${figBot + 40} H${qOff} V${figBot + 26}`} />
            </g>
            <Slider t={t} k={sliderK} ms={qrsMs} y={CARD_C[1] + CARD_H / 2 - 70} />
          </g>
        ) : null}
        {capB ? <Caption y={capY} kicker="Learn" head={VERT ? 'Every figure is a tracing\nyou can move.' : 'Every figure is a tracing you can move.'} /> : null}

        {inPractice && deal >= 0 ? (
          <g>
            <Grid x0={pL} x1={pR} y0={pBase - 160} y1={pBase + 120} ox={pL} oy={pBase} mm={P_MM} />
            <path d={practiceD} fill="none" stroke={M.ink} strokeWidth={3.5} strokeLinejoin="round" strokeLinecap="round" />
            <text x={pL} y={CARD_C[1] - CARD_H / 2 + 92} fontFamily={FONT_BODY} fontWeight={600} fontSize={34} fill={M.ink}>
              {PRACTICE[deal].label}
            </text>
            <text x={pR} y={CARD_C[1] - CARD_H / 2 + 92} textAnchor="end" fontFamily={FONT_BODY} fontWeight={500} fontSize={28} fill={M.ink2} style={{fontVariantNumeric: 'tabular-nums'}}>
              {`${deal + 1} / ${PRACTICE.length}`}
            </text>
          </g>
        ) : null}
        {capC ? <Caption y={capY} kicker="Practice" head="A new tracing every time." /> : null}

        {/* beat 5: the mark, the wordmark and its period */}
        {t >= TL.icon ? (
          <g transform={`translate(${tileC[0] - TILE * 0.32} ${tileC[1] - TILE * 0.32}) scale(${(TILE * 0.64) / 24})`}>
            <path d={WAVE_D} fill="none" stroke="#FFFFFF" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round" strokeDasharray={WAVE_LEN} strokeDashoffset={WAVE_LEN * (1 - iconK)} />
          </g>
        ) : null}
        {t >= TL.word ? (
          <>
            <text x={wordX} y={wordBase} fontFamily={FONT_HEAD} fontWeight={800} fontSize={WORD_SIZE} letterSpacing={-0.02 * WORD_SIZE} fill={M.ink}>
              {wordTyped}
            </text>
            <circle cx={periodX - 0.02 * WORD_SIZE * wordTyped.length} cy={wordBase - 11} r={11 * periodPop} fill={M.orb} />
          </>
        ) : null}
        {t >= TL.line1 ? (
          <text x={CX} y={lineY + 190} textAnchor="middle" fontFamily={FONT_HEAD} fontWeight={600} fontSize={VERT ? 60 : 52} fill={M.ink} opacity={fadeSmall(t, TL.line1)}>
            Learn to read the EKG.
          </text>
        ) : null}
        {t >= TL.line2 ? (
          <g opacity={fadeSmall(t, TL.line2)}>
            <text x={CX} y={lineY + (VERT ? 272 : 262)} textAnchor="middle" fontFamily={FONT_BODY} fontWeight={400} fontSize={VERT ? 36 : 30} fill={M.ink2}>
              Course and practice, part of Medzcool Basic
            </text>
            <text x={CX} y={lineY + (VERT ? 334 : 316)} textAnchor="middle" fontFamily={FONT_BODY} fontWeight={600} fontSize={VERT ? 36 : 30} fill={M.ink}>
              kardiograph.medzcool.com
            </text>
          </g>
        ) : null}

        {/* the orb on top of everything */}
        {orb ? (
          <g transform={`translate(${orb.x} ${orb.y}) scale(${orb.sx} ${orb.sy})`}>
            <circle r={orb.r} fill={M.orb} stroke={t >= TL.land ? M.ring : 'none'} strokeWidth={t >= TL.land ? 3 : 0} />
          </g>
        ) : null}
      </svg>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ parts
const Caption: React.FC<{y: number; kicker: string; head: string}> = ({y, kicker, head}) => (
  <g>
    <text x={CX} y={y} textAnchor="middle" fontFamily={FONT_HEAD} fontWeight={700} fontSize={23} letterSpacing={3} fill={M.ink2}>
      {kicker.toUpperCase()}
    </text>
    <text x={CX} y={y + 70} textAnchor="middle" fontFamily={FONT_HEAD} fontWeight={600} fontSize={VERT ? 64 : 56} fill={M.ink}>
      {head.split('\n').map((line, i) => (
        <tspan key={i} x={CX} dy={i ? (VERT ? 78 : 68) : 0}>{line}</tspan>
      ))}
    </text>
  </g>
);

const Slider: React.FC<{t: number; k: number; ms: number; y: number}> = ({k, ms, y}) => {
  const x0 = CX - SLIDER_HALF;
  const x1 = CX + SLIDER_HALF;
  const kx = lerp(x0, x1, k);
  return (
    <g>
      <text x={x0 - 40} y={y + 10} textAnchor="end" fontFamily={FONT_BODY} fontWeight={600} fontSize={30} fill={M.ink}>
        QRS
      </text>
      <line x1={x0} x2={x1} y1={y} y2={y} stroke={M.inactive} strokeWidth={6} strokeLinecap="round" />
      <line x1={x0} x2={kx} y1={y} y2={y} stroke={M.ink} strokeWidth={6} strokeLinecap="round" />
      <circle cx={kx} cy={y} r={15} fill={M.orb} stroke={M.ring} strokeWidth={3} />
      <text x={x1 + 40} y={y + 10} fontFamily={FONT_BODY} fontWeight={600} fontSize={30} fill={M.ink} style={{fontVariantNumeric: 'tabular-nums'}}>
        {`${Math.round(ms / 10) * 10} ms`}
      </text>
    </g>
  );
};

function mixHex(a: string, b: string, k: number): string {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  return '#' + pa.map((v, i) => Math.round(lerp(v, pb[i], clamp(k, 0, 1))).toString(16).padStart(2, '0')).join('');
}
